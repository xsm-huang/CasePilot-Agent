"""Explicit opt-in capability diagnostics, never part of startup."""

import argparse
import asyncio
import json
import math
from datetime import datetime, timezone

import httpx

from ..config import load_environment
from .config import read_model_config
from .errors import ModelError
from .transport import _provider_request


async def probe_model_capabilities(config):
    async with httpx.AsyncClient(
        timeout=config.timeout_ms / 1000, follow_redirects=False
    ) as client:

        async def request(path, body):
            return await _provider_request(client, config, path, body)

        defaults = {
            "model": config.chat_model,
            "stream": False,
            "max_tokens": 256,
            "thinking": {"type": "disabled"},
        }
        try:
            tool_response = await request(
                "chat/completions",
                {
                    **defaults,
                    "messages": [
                        {
                            "role": "user",
                            "content": "请调用 check_case 工具，caseId 必须为 DEMO-001。不要直接回答。",
                        }
                    ],
                    "tools": [
                        {
                            "type": "function",
                            "function": {
                                "name": "check_case",
                                "description": "检查演示案件",
                                "parameters": {
                                    "type": "object",
                                    "properties": {
                                        "caseId": {"type": "string", "enum": ["DEMO-001"]}
                                    },
                                    "required": ["caseId"],
                                    "additionalProperties": False,
                                },
                            },
                        }
                    ],
                    "tool_choice": "auto",
                },
            )
            calls = tool_response["choices"][0]["message"]["tool_calls"]
            if (
                len(calls) != 1
                or calls[0]["type"] != "function"
                or calls[0]["function"]["name"] != "check_case"
                or json.loads(calls[0]["function"]["arguments"]) != {"caseId": "DEMO-001"}
            ):
                raise ModelError("TOOL_CALLING_NOT_VERIFIED")
            structured = await request(
                "chat/completions",
                {
                    **defaults,
                    "messages": [
                        {
                            "role": "user",
                            "content": '仅输出一个 JSON 对象：{"caseId":"DEMO-001","needsReview":true}。不要添加任何其他字段。',
                        }
                    ],
                    "response_format": {"type": "json_object"},
                },
            )
            structured_result = json.loads(structured["choices"][0]["message"]["content"])
            if (
                not isinstance(structured_result, dict)
                or structured_result != {"caseId": "DEMO-001", "needsReview": True}
                or structured_result.get("needsReview") is not True
            ):
                raise ModelError("STRUCTURED_OUTPUT_NOT_VERIFIED")
            embedded = await request(
                "embeddings",
                {
                    "model": config.embedding_model,
                    "input": ["理赔申请需要提供维修费用凭证。"],
                    "dimensions": config.embedding_dimensions,
                },
            )
            vector = embedded["data"][0]["embedding"]
            if (
                len(embedded["data"]) != 1
                or len(vector) != config.embedding_dimensions
                or not all(type(v) in (int, float) and math.isfinite(v) for v in vector)
                or not any(vector)
            ):
                raise ModelError("EMBEDDING_NOT_VERIFIED")
        except (KeyError, IndexError, TypeError, json.JSONDecodeError):
            raise ModelError("MODEL_RESPONSE_INVALID") from None
    return {
        "chatModel": config.chat_model,
        "embeddingModel": config.embedding_model,
        "embeddingDimensions": config.embedding_dimensions,
        "toolCalling": True,
        "structuredOutput": True,
        "checkedAt": datetime.now(timezone.utc).isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Three small paid provider requests; explicit --live required."
    )
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if not args.live:
        parser.error("--live is required to authorize provider calls")
    load_environment()
    try:
        print(
            json.dumps(
                asyncio.run(probe_model_capabilities(read_model_config())), ensure_ascii=False
            )
        )
    except ModelError as exc:
        print(json.dumps({"error": str(exc), **exc.diagnostics()}))
        raise SystemExit(1) from None
