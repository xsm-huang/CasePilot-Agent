"""Local-only real provider acceptance server, with a shared fail-stop budget."""

import json
import os
import time

import httpx
import uvicorn
from casepilot.main import create_app
from casepilot.model.chat import ChatClient
from casepilot.model.config import read_model_config
from casepilot.model.embeddings import embed_texts
from casepilot.model.errors import ModelError
from fastapi import HTTPException

from .budget import BudgetTransport, write_json
from .data import load, manifest


async def capability_gate(chat, embedder):
    tools = [
        {
            "type": "function",
            "function": {
                "name": "check_case",
                "description": "检查虚构演示案件",
                "parameters": {
                    "type": "object",
                    "properties": {"caseId": {"type": "string", "enum": ["DEMO-001"]}},
                    "required": ["caseId"],
                    "additionalProperties": False,
                },
            },
        }
    ]
    turn = await chat.complete(
        [
            {
                "role": "user",
                "content": "请调用 check_case 工具，caseId 必须为 DEMO-001，不要直接回答。",
            }
        ],
        tools=tools,
    )
    if len(turn["toolCalls"]) != 1 or turn["toolCalls"][0]["arguments"] != {"caseId": "DEMO-001"}:
        raise ModelError("TOOL_CALLING_NOT_VERIFIED")
    structured = await chat.complete(
        [
            {
                "role": "user",
                "content": '只输出 JSON 对象 {"caseId":"DEMO-001","needsReview":true}，不得添加其他字段。',
            }
        ],
        json_mode=True,
    )
    structured_result = json.loads(structured["content"])
    if (
        structured_result != {"caseId": "DEMO-001", "needsReview": True}
        or structured_result.get("needsReview") is not True
    ):
        raise ModelError("STRUCTURED_OUTPUT_NOT_VERIFIED")
    vectors = await embedder(["理赔申请需要提供维修费用凭证。"])
    if len(vectors) != 1 or len(vectors[0]) != 1024:
        raise ModelError("EMBEDDING_NOT_VERIFIED")


async def serve(args):
    config = read_model_config()
    budget = BudgetTransport(
        args.budget_ledger,
        args.model_limit,
        args.embedding_limit,
        run_id=args.run_id,
    )
    budget.ledger.ensure_active()
    async with httpx.AsyncClient(
        transport=budget, timeout=config.timeout_ms / 1000, follow_redirects=False
    ) as client:
        chat = ChatClient(config, client=client)

        async def embeddings(texts):
            return await embed_texts(config, texts, client=client)

        capability_path = args.output / "capabilities.json"
        cached_capability = (
            json.loads(capability_path.read_text(encoding="utf-8"))
            if capability_path.exists()
            else None
        )
        expected_capability = {
            "chatModel": config.chat_model,
            "embeddingModel": config.embedding_model,
            "embeddingDimensions": config.embedding_dimensions,
            "dataHashes": manifest(),
        }
        if cached_capability is not None and (
            cached_capability.get("status") != "passed"
            or any(cached_capability.get(key) != value for key, value in expected_capability.items())
        ):
            budget.stop("CAPABILITY_GATE_FAILED")
            return 1
        if cached_capability is None:
            try:
                await capability_gate(chat, embeddings)
            except Exception as exc:
                diagnostic = (
                    exc.diagnostics()
                    if isinstance(exc, ModelError)
                    else {"code": "CAPABILITY_NOT_VERIFIED", "errorType": type(exc).__name__}
                )
                budget.stop("CAPABILITY_GATE_FAILED")
                write_json(
                    capability_path,
                    {"status": "failed", "error": diagnostic, "used": budget.state["used"]},
                )
                return 1
            write_json(capability_path, {"status": "passed", **expected_capability})
        app = create_app(chat=chat, embedder=embeddings)

        @app.get("/evaluation/state")
        async def state():
            return {
                "used": budget.state["used"],
                "limits": budget.state["limits"],
                "stopped": budget.state["stopped"],
                "schema": os.environ["CASEPILOT_DB_SCHEMA"],
                "runId": args.run_id,
            }

        @app.get("/evaluation/retrieval/{generation_id}")
        async def retrieval(generation_id: str):
            artifact = args.output / "retrieval-results.json"
            if artifact.exists():
                cached = json.loads(artifact.read_text(encoding="utf-8"))
                if cached["generationId"] != generation_id:
                    raise HTTPException(409, "Evaluation generation is already frozen")
                return cached
            corpus = load("corpus.json")
            questions = load("retrieval.json")
            vectors = await embeddings([q["question"] for q in questions])
            rows = []
            for question, vector in zip(questions, vectors, strict=True):
                hits = await app.state.knowledge.repository.search(
                    corpus["productCode"], corpus["clauseVersion"], generation_id, vector
                )
                row = {
                    **question,
                    "hits": hits,
                    "hit": any(h["page"] in question["pages"] for h in hits)
                    if question["kind"] == "answer"
                    else None,
                    "scopeCorrect": all(
                        h["generationId"] == generation_id
                        and h["productCode"] == corpus["productCode"]
                        and h["clauseVersion"] == corpus["clauseVersion"]
                        for h in hits
                    ),
                }
                rows.append(row)
            answered = [r for r in rows if r["kind"] == "answer"]
            hit_rate = sum(r["hit"] for r in answered) / len(answered)
            result = {
                "generationId": generation_id,
                "hitAt4": hit_rate,
                "metadataIsolation": all(r["scopeCorrect"] for r in rows),
                "rows": rows,
                "status": "passed"
                if hit_rate >= 0.9 and all(r["scopeCorrect"] for r in rows)
                else "failed",
                "unanswerablePolicy": "Nearest neighbours are recorded only; semantic support is reviewed in report samples.",
            }
            write_json(artifact, result)
            return result

        @app.get("/evaluation/tasks/{task_id}")
        async def audit_task(task_id: str):
            task = app.state.store.get(task_id)
            agent = task["_agent"]
            result = {
                "counts": agent["counts"],
                "context": task["context"],
                "analysis": task["_artifacts"].get("analysis"),
                "calls": [
                    {
                        "key": key,
                        "kind": call["kind"],
                        "status": call["status"],
                        "usage": call.get("result", {}).get("usage", {})
                        if isinstance(call.get("result"), dict)
                        else {},
                    }
                    for key, call in agent["calls"].items()
                ],
            }
            write_json(args.output / "tasks" / f"{task_id}-audit.json", result)
            return result

        @app.post("/evaluation/freeze")
        async def freeze():
            budget.stop("EVALUATION_FINISHED")
            return {"frozen": True, "used": budget.state["used"]}

        write_json(
            args.output / "server.json",
            {
                "pid": os.getpid(),
                "port": args.port,
                "schema": os.environ["CASEPILOT_DB_SCHEMA"],
                "runId": args.run_id,
                "budgetLedger": str(args.budget_ledger),
                "status": "starting",
                "startedAt": time.time(),
            },
        )
        await uvicorn.Server(
            uvicorn.Config(app, host="127.0.0.1", port=args.port, log_level="warning")
        ).serve()
    return 0
