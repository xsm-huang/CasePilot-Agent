"""Analysis HTTP commands, snapshots and SSE framing."""

import asyncio
import json

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse

from ..analyses.status import TERMINAL
from ..schemas.analysis import V0AnalysisTask, V0ReviewAccepted

router = APIRouter()


@router.get("/api/analyses", response_model=list[V0AnalysisTask], response_model_exclude_none=True)
async def analyses(request: Request):
    return request.app.state.analyses.list()


@router.get(
    "/api/analyses/{task_id}", response_model=V0AnalysisTask, response_model_exclude_none=True
)
async def analysis(task_id: str, request: Request):
    return request.app.state.analyses.get(task_id)


async def body_object(request):
    try:
        body = await request.json()
        return body if isinstance(body, dict) else {}
    except (ValueError, UnicodeError):
        raise HTTPException(400, "无效的请求。") from None


@router.post(
    "/api/analyses",
    status_code=201,
    response_model=V0AnalysisTask,
    response_model_exclude_none=True,
)
async def create(request: Request):
    return await request.app.state.analyses.create(await body_object(request))


@router.post("/api/analyses/{task_id}/review", status_code=201, response_model=V0ReviewAccepted)
async def review(task_id: str, request: Request):
    return await request.app.state.analyses.review(task_id, await body_object(request))


@router.get("/api/analyses/{task_id}/events")
async def events(task_id: str, request: Request, last_event_id: str = Header(default="0")):
    try:
        cursor = int(last_event_id.strip() or "0")
        if (
            cursor < 0
            or cursor > 2**53 - 1
            or str(cursor) != last_event_id.strip()
            and last_event_id.strip() not in ("", "+0")
        ):
            raise ValueError()
    except ValueError:
        raise HTTPException(400, "无效的事件游标。") from None
    store = request.app.state.store
    store.get(task_id)

    async def stream():
        nonlocal cursor
        while not await request.is_disconnected():
            task = store.get(task_id)
            for event in task["events"]:
                if event["id"] > cursor:
                    cursor = event["id"]
                    yield f"id: {cursor}\nevent: timeline\ndata: {json.dumps(event, ensure_ascii=False)}\n\n"
            if task["status"] in TERMINAL:
                return
            await asyncio.sleep(0.05)

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
