"""Closed-claim review workspace HTTP commands and persisted SSE."""

import asyncio
import json
import re
import time

from fastapi import APIRouter, File, Form, Header, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse

from ..analyses.errors import AnalysisError
from ..analyses.workspace_store import TERMINAL
from ..schemas.workspace import (
    AnalysisTask,
    Citation,
    CitationContext,
    CommandAccepted,
    Conversation,
    ConversationSummary,
    CreateAnalysis,
    CreateConversation,
    EvidenceSupplement,
    RecoverRequest,
    ReviewRequest,
)

router = APIRouter()


def idempotency_key(value):
    if not value.strip() or len(value) > 200 or any(c in value for c in "\r\n\x00"):
        raise AnalysisError("INVALID_INPUT", "幂等键无效。")
    return value


@router.get("/api/analyses", response_model=list[AnalysisTask])
async def analyses(request: Request):
    return request.app.state.analyses.list()


@router.get("/api/analyses/{task_id}", response_model=AnalysisTask)
async def analysis(task_id: str, request: Request):
    return request.app.state.analyses.get(task_id)


@router.post(
    "/api/cases/{case_id}/conversations", status_code=201, response_model=ConversationSummary
)
async def create_conversation(case_id: str, body: CreateConversation, request: Request):
    return await request.app.state.analyses.create_conversation(case_id, body.title)


@router.get("/api/conversations", response_model=list[ConversationSummary])
async def conversations(request: Request, caseId: str | None = None):
    return request.app.state.analyses.conversations(caseId)


@router.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def conversation(conversation_id: str, request: Request, before: str | None = None):
    return await request.app.state.analyses.conversation(conversation_id, before)


@router.post("/api/analyses", status_code=202, response_model=AnalysisTask)
async def create(
    body: CreateAnalysis,
    request: Request,
    idempotency_key_header: str = Header(alias="Idempotency-Key"),
):
    return await request.app.state.analyses.create(
        body.model_dump(), idempotency_key(idempotency_key_header)
    )


@router.post("/api/analyses/{task_id}/review", status_code=202, response_model=CommandAccepted)
async def review(
    task_id: str,
    body: ReviewRequest,
    request: Request,
    idempotency_key_header: str = Header(alias="Idempotency-Key"),
):
    return await request.app.state.analyses.review(
        task_id, body.model_dump(), idempotency_key(idempotency_key_header)
    )


@router.post("/api/analyses/{task_id}/recover", status_code=202, response_model=CommandAccepted)
async def recover(
    task_id: str,
    body: RecoverRequest,
    request: Request,
    idempotency_key_header: str = Header(alias="Idempotency-Key"),
):
    return await request.app.state.analyses.recover(
        task_id, body.model_dump(), idempotency_key(idempotency_key_header)
    )


@router.post(
    "/api/analyses/{task_id}/supplements", status_code=201, response_model=EvidenceSupplement
)
async def add_supplement(
    task_id: str,
    request: Request,
    file: UploadFile = File(),
    title: str = Form(min_length=1, max_length=200),
    material_type: str = Form(alias="materialType", min_length=1, max_length=100),
    entity_ids: str = Form(default="[]", alias="entityIds"),
):
    try:
        parsed_ids = json.loads(entity_ids)
    except json.JSONDecodeError:
        raise AnalysisError("INVALID_INPUT", "关联对象必须是 JSON 字符串数组。") from None
    if not isinstance(parsed_ids, list) or not all(
        isinstance(item, str) and item and len(item) <= 200 for item in parsed_ids
    ):
        raise AnalysisError("INVALID_INPUT", "关联对象必须是 JSON 字符串数组。")
    return await request.app.state.analyses.add_supplement(
        task_id,
        title=title,
        material_type=material_type,
        entity_ids=parsed_ids,
        content=await file.read(10 * 1024 * 1024 + 1),
    )


@router.get("/api/analyses/{task_id}/supplements/{supplement_id}/content")
async def supplement_content(task_id: str, supplement_id: str, request: Request):
    path, title = request.app.state.analyses.supplement_content(task_id, supplement_id)
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"{title}.pdf" if not title.lower().endswith(".pdf") else title,
        content_disposition_type="inline",
    )


@router.get("/api/analyses/{task_id}/citations/{citation_id}", response_model=Citation)
async def citation(task_id: str, citation_id: str, request: Request):
    return request.app.state.analyses.citation(task_id, citation_id)


@router.get(
    "/api/analyses/{task_id}/citations/{citation_id}/context", response_model=CitationContext
)
async def citation_context(task_id: str, citation_id: str, request: Request):
    return await request.app.state.analyses.citation_context(task_id, citation_id)


@router.get("/api/analyses/{task_id}/events")
async def events(
    task_id: str,
    request: Request,
    after: str = "0",
    last_event_id: str | None = Header(default=None),
):
    raw = last_event_id if last_event_id is not None else after
    if len(raw) > 16 or not re.fullmatch(r"0|[1-9][0-9]*", raw) or int(raw) > 2**53 - 1:
        raise AnalysisError("INVALID_INPUT", "无效的事件游标。")
    cursor = int(raw)
    store = request.app.state.store
    task = store.writable(task_id)
    if cursor > task["lastEventSeq"]:
        raise AnalysisError("CURSOR_CONFLICT", "事件游标超出任务范围，请重新读取快照。")

    async def stream():
        nonlocal cursor
        heartbeat = time.monotonic()
        while not await request.is_disconnected():
            for event in await store.repository.events_after(task_id, cursor):
                cursor = event["seq"]
                yield f"id: {cursor}\nevent: timeline\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
            task = store.get(task_id)
            if task["status"] in TERMINAL and cursor >= task["lastEventSeq"]:
                return
            if time.monotonic() - heartbeat >= 10:
                yield ": heartbeat\n\n"
                heartbeat = time.monotonic()
            await asyncio.sleep(0.05)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
