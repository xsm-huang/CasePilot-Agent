"""Real chat request formatting and safe response parsing with MockTransport."""

import json

import httpx
import pytest
from casepilot.model.chat import ChatClient, assistant_message
from casepilot.model.config import read_model_config
from casepilot.model.errors import ModelError

CONFIG = read_model_config({"ZHIPU_API_KEY": "test-only-secret"})
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_clauses",
            "description": "test",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    }
]


async def test_real_tool_and_json_requests_preserve_internal_reasoning():
    calls = []

    def handle(request):
        calls.append(json.loads(request.content))
        if len(calls) == 1:
            return httpx.Response(
                200,
                json={
                    "model": "glm-5.3-flash",
                    "choices": [
                        {
                            "message": {
                                "content": None,
                                "reasoning_content": "not public",
                                "tool_calls": [
                                    {
                                        "id": "call-1",
                                        "type": "function",
                                        "function": {
                                            "name": "search_clauses",
                                            "arguments": '{"query":"repair evidence"}',
                                        },
                                    }
                                ],
                            }
                        }
                    ],
                    "usage": {"total_tokens": 20},
                },
            )
        return httpx.Response(
            200, json={"choices": [{"message": {"content": '{"summary":"result"}'}}]}
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        adapter = ChatClient(CONFIG, client=client)
        turn = await adapter.complete([{"role": "user", "content": "test"}], tools=TOOLS)
        assert turn["toolCalls"][0]["arguments"] == {"query": "repair evidence"}
        assert turn["_reasoningContent"] == "not public"
        await adapter.complete(
            [
                {"role": "user", "content": "test"},
                assistant_message(turn),
                {"role": "tool", "tool_call_id": "call-1", "content": "[]"},
            ],
            json_mode=True,
        )
    assert calls[0]["tools"] == TOOLS and "response_format" not in calls[0]
    assert calls[1]["response_format"] == {"type": "json_object"} and "tools" not in calls[1]
    assert calls[1]["messages"][1]["reasoning_content"] == "not public"
    assert calls[1]["messages"][1]["tool_calls"][0]["id"] == "call-1"
    assert all(call["thinking"] == {"type": "enabled", "clear_thinking": False} for call in calls)
    assert all(call["reasoning_effort"] == "low" for call in calls)
    assert all(call["max_tokens"] == 4096 for call in calls)


@pytest.mark.parametrize(
    "patch",
    [
        {"choices": []},
        {"choices": [{"message": []}]},
        {"choices": [{"finish_reason": "length", "message": {"content": "partial"}}]},
        {"choices": [{"message": {"content": ""}}]},
        {"choices": [{"message": {"content": "valid", "reasoning_content": []}}]},
        {"usage": {"total_tokens": True}},
        {"model": "another-model"},
    ],
)
async def test_malformed_or_truncated_chat_is_an_explicit_safe_failure(patch):
    response = {"choices": [{"message": {"content": "valid"}}]} | patch
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=response))
    ) as client:
        with pytest.raises(ModelError):
            await ChatClient(CONFIG, client=client).complete([{"role": "user", "content": "test"}])


@pytest.mark.parametrize(
    "arguments,name",
    [("not json", "search_clauses"), ("[]", "search_clauses"), ('{"query":"q"}', "delete_case")],
)
async def test_unknown_tools_and_non_object_arguments_are_rejected(arguments, name):
    response = {
        "choices": [
            {
                "message": {
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "type": "function",
                            "function": {"name": name, "arguments": arguments},
                        }
                    ]
                }
            }
        ]
    }
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json=response))
    ) as client:
        with pytest.raises(ModelError, match="MODEL_RESPONSE_INVALID"):
            await ChatClient(CONFIG, client=client).complete(
                [{"role": "user", "content": "test"}], tools=TOOLS
            )


async def test_provider_failure_is_not_retried_and_request_limits_apply_before_network():
    calls = []

    def handle(request):
        calls.append(1)
        return httpx.Response(429, json={"error": {"code": "1305", "message": "private secret"}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        adapter = ChatClient(CONFIG, client=client)
        with pytest.raises(ModelError) as caught:
            await adapter.complete([{"role": "user", "content": "test"}])
        assert caught.value.provider_code == "1305" and "private" not in str(caught.value)
        with pytest.raises(ModelError, match="MODEL_REQUEST_INVALID"):
            await adapter.complete(
                [{"role": "user", "content": "test"}], tools=TOOLS, json_mode=True
            )
        with pytest.raises(ModelError, match="MODEL_CONTEXT_LIMIT"):
            await adapter.complete([{"role": "user", "content": "a" * 60001}])
    assert len(calls) == 1


async def test_network_failure_is_not_reported_as_invalid_model_output():
    def handle(request):
        raise httpx.ConnectError("private transport details", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ModelError, match="DEPENDENCY_UNAVAILABLE") as caught:
            await ChatClient(CONFIG, client=client).complete([{"role": "user", "content": "test"}])
    assert "private" not in str(caught.value)
