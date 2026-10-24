"""Provider adapter contract with MockTransport only; never live evidence."""

import dataclasses
import json

import httpx
import pytest
from casepilot.model import probe as model
from casepilot.model.config import read_model_config

KEY = "test-only-placeholder"
CONFIG = read_model_config({"ZHIPU_API_KEY": KEY})
TOOL = {
    "choices": [
        {
            "message": {
                "tool_calls": [
                    {
                        "type": "function",
                        "function": {"name": "check_case", "arguments": '{"caseId":"DEMO-001"}'},
                    }
                ]
            }
        }
    ]
}
STRUCTURED = {"choices": [{"message": {"content": '{"caseId":"DEMO-001","needsReview":true}'}}]}
VECTOR = {"data": [{"embedding": [0.25] * 1024}]}


def mock_client(monkeypatch, responses):
    calls = []
    original = httpx.AsyncClient

    def handle(request):
        calls.append(request)
        assert len(calls) <= len(responses), "Unexpected retry or additional request"
        result = responses[len(calls) - 1]
        if isinstance(result, Exception):
            raise result
        if isinstance(result, httpx.Response):
            return result
        return httpx.Response(200, json=result)

    def factory(**kwargs):
        assert kwargs["follow_redirects"] is False
        assert kwargs["timeout"] == 30
        return original(transport=httpx.MockTransport(handle), **kwargs)

    monkeypatch.setattr(model.httpx, "AsyncClient", factory)
    return calls


def test_immutable_profile_hides_credentials():
    assert CONFIG.chat_model == "glm-4.7-flash"
    assert CONFIG.embedding_model == "embedding-3"
    assert CONFIG.embedding_dimensions == 1024
    assert KEY not in repr(CONFIG)
    with pytest.raises(dataclasses.FrozenInstanceError):
        CONFIG.chat_model = "other"


@pytest.mark.parametrize(
    "field,value",
    [
        ("ZHIPU_API_KEY", ""),
        ("ZHIPU_API_KEY", " "),
        ("ZHIPU_API_KEY", "first\nsecret"),
        ("ZHIPU_BASE_URL", "https://example.com/api/paas/v4"),
        ("ZHIPU_BASE_URL", "http://open.bigmodel.cn/api/paas/v4"),
        ("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4?token=secret"),
        ("ZHIPU_BASE_URL", "https://username:secret@open.bigmodel.cn/api/paas/v4"),
        ("CHAT_MODEL", "other"),
        ("EMBEDDING_MODEL", "other"),
        ("EMBEDDING_DIMENSIONS", "NaN"),
        ("EMBEDDING_DIMENSIONS", "1024.5"),
        ("EMBEDDING_DIMENSIONS", "0"),
        ("EMBEDDING_DIMENSIONS", "2048"),
        ("MODEL_TIMEOUT_MS", "0"),
        ("MODEL_TIMEOUT_MS", "120001"),
    ],
)
def test_invalid_configuration_is_explicit_and_redacted(field, value):
    with pytest.raises(model.ModelError) as caught:
        read_model_config({"ZHIPU_API_KEY": KEY, field: value})
    assert str(caught.value) == field
    assert "secret" not in str(caught.value)


async def test_three_mock_requests_and_fixed_profile(monkeypatch):
    calls = mock_client(monkeypatch, [TOOL, STRUCTURED, VECTOR])
    result = await model.probe_model_capabilities(CONFIG)
    assert result["toolCalling"] is True
    assert result["structuredOutput"] is True
    assert result["embeddingDimensions"] == 1024
    assert len(calls) == 3
    assert all(str(call.url).startswith("https://open.bigmodel.cn/api/paas/v4/") for call in calls)
    bodies = [json.loads(call.content) for call in calls]
    assert bodies[0]["model"] == "glm-4.7-flash"
    assert bodies[1]["response_format"] == {"type": "json_object"}
    assert bodies[2]["model"] == "embedding-3"
    assert bodies[2]["dimensions"] == 1024


@pytest.mark.parametrize(
    "responses,error,count",
    [
        ([httpx.Response(401, text="private-provider-response")], "MODEL_HTTP_ERROR (401)", 1),
        ([httpx.ReadTimeout("private-timeout-details")], "MODEL_TIMEOUT", 1),
        ([{"choices": [{"message": {"content": "no tool"}}]}], "MODEL_RESPONSE_INVALID", 1),
        ([TOOL, {"choices": [{"message": {"content": "{broken"}}]}], "MODEL_RESPONSE_INVALID", 2),
        (
            [
                TOOL,
                {"choices": [{"message": {"content": '{"caseId":"DEMO-001","needsReview":1}'}}]},
            ],
            "STRUCTURED_OUTPUT_NOT_VERIFIED",
            2,
        ),
        ([TOOL, STRUCTURED, {"data": [{"embedding": [0.25]}]}], "EMBEDDING_NOT_VERIFIED", 3),
        ([TOOL, STRUCTURED, {"data": [{"embedding": [0] * 1024}]}], "EMBEDDING_NOT_VERIFIED", 3),
        ([TOOL, STRUCTURED, {"data": [{"embedding": [True] * 1024}]}], "EMBEDDING_NOT_VERIFIED", 3),
    ],
)
async def test_failed_probe_stops_without_retry_and_redacts(monkeypatch, responses, error, count):
    calls = mock_client(monkeypatch, responses)
    with pytest.raises(model.ModelError) as caught:
        await model.probe_model_capabilities(CONFIG)
    assert str(caught.value) == error
    assert "private" not in str(caught.value)
    assert KEY not in str(caught.value)
    assert len(calls) == count
