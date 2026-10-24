"""Embedding boundary evidence uses HTTPX MockTransport, never a live provider."""

import json

import httpx
import pytest
from casepilot.model import (
    ModelError,
    embed_texts,
    embedding_profile,
    read_model_config,
    validate_embedding,
)

CONFIG = read_model_config({"ZHIPU_API_KEY": "test-no-network-secret"})


async def test_embedding_batch_request_and_response_order():
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(
            200,
            json={
                "model": "embedding-3",
                "data": [
                    {"index": 1, "embedding": [0.5] * 1024},
                    {"index": 0, "embedding": [0.25] * 1024},
                ],
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        vectors = await embed_texts(CONFIG, ["first", "second"], client=client)
    assert [v[0] for v in vectors] == [0.25, 0.5]
    assert len(calls) == 1
    assert str(calls[0].url) == "https://open.bigmodel.cn/api/paas/v4/embeddings"
    assert json.loads(calls[0].content) == {
        "model": "embedding-3",
        "dimensions": 1024,
        "input": ["first", "second"],
    }
    assert embedding_profile(CONFIG) == "zhipu:embedding-3:1024:v1"


@pytest.mark.parametrize("texts", [[], [""], [" "], [None], "text", ["ok"] * 65])
async def test_invalid_inputs_never_send_request(texts):
    def forbidden(request):
        pytest.fail("Invalid input must fail before provider request")

    async with httpx.AsyncClient(transport=httpx.MockTransport(forbidden)) as client:
        with pytest.raises(ModelError, match="^EMBEDDING_INPUT_INVALID$"):
            await embed_texts(CONFIG, texts, client=client)


@pytest.mark.parametrize(
    "vector",
    [
        [],
        [0.25],
        [0] * 1024,
        [True] * 1024,
        [float("nan")] * 1024,
        [float("inf")] * 1024,
        [1e40] * 1024,
        [1e-50] * 1024,
        [".25"] * 1024,
        tuple([0.25] * 1024),
    ],
)
def test_invalid_vectors_are_rejected_before_pgvector(vector):
    with pytest.raises(ModelError, match="^EMBEDDING_NOT_VERIFIED$"):
        validate_embedding(vector)


@pytest.mark.parametrize(
    "data",
    [
        None,
        [],
        [{"index": 0, "embedding": [0.25] * 1024}],
        [{"index": 0, "embedding": [0.25] * 1024}] * 2,
        [{"index": True, "embedding": [0.25] * 1024}, {"index": 0, "embedding": [0.25] * 1024}],
        [{"index": 0, "embedding": [0.25] * 1024}, {"index": 2, "embedding": [0.25] * 1024}],
    ],
)
async def test_embedding_response_requires_exact_unique_indexes(data):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"data": data}))
    ) as client:
        with pytest.raises(ModelError, match="^EMBEDDING_NOT_VERIFIED$"):
            await embed_texts(CONFIG, ["first", "second"], client=client)


async def test_provider_model_mismatch_is_explicit():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200, json={"model": "other", "data": [{"index": 0, "embedding": [0.25] * 1024}]}
            )
        )
    ) as client:
        with pytest.raises(ModelError, match="^EMBEDDING_PROFILE_MISMATCH$"):
            await embed_texts(CONFIG, ["first"], client=client)


async def test_1305_diagnostics_are_bounded_and_redacted_without_retry():
    calls = []

    def handle(request):
        calls.append(request)
        return httpx.Response(
            429,
            json={
                "request_id": "req_safe_123",
                "error": {"code": "1305", "message": "private provider secret"},
            },
            headers={"retry-after": "60"},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ModelError) as caught:
            await embed_texts(CONFIG, ["first"], client=client)
    assert caught.value.diagnostics() == {
        "code": "MODEL_HTTP_ERROR",
        "httpStatus": 429,
        "providerCode": "1305",
        "requestId": "req_safe_123",
        "retryAfter": 60,
    }
    assert "private" not in json.dumps(caught.value.diagnostics())
    assert "secret" not in str(caught.value)
    assert len(calls) == 1


async def test_embedding_timeout_is_redacted():
    def handle(request):
        raise httpx.ReadTimeout("private internal connection details")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        with pytest.raises(ModelError, match="^MODEL_TIMEOUT$"):
            await embed_texts(CONFIG, ["first"], client=client)
