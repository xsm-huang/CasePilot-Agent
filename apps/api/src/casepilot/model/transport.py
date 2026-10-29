"""Bounded provider HTTP requests and safe error conversion."""

import re

import httpx

from .errors import ModelError


def _provider_error(response: httpx.Response, api_key: str) -> ModelError:
    try:
        payload = response.json()
    except ValueError:
        payload = {}
    payload = payload if isinstance(payload, dict) else {}
    error = payload.get("error")
    error = error if isinstance(error, dict) else {}
    raw_code = str(error.get("code", ""))
    provider_code = (
        raw_code if re.fullmatch(r"[0-9]{1,8}", raw_code) and api_key not in raw_code else None
    )
    raw_id = payload.get("request_id") or response.headers.get("x-request-id")
    request_id = (
        raw_id
        if isinstance(raw_id, str)
        and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", raw_id)
        and api_key not in raw_id
        else None
    )
    raw_retry = response.headers.get("retry-after", "")
    retry_after = int(raw_retry) if re.fullmatch(r"[0-9]{1,6}", raw_retry) else None
    return ModelError(
        "MODEL_HTTP_ERROR",
        response.status_code,
        provider_code=provider_code,
        request_id=request_id,
        retry_after=retry_after,
    )


async def _provider_request(client, config, path, body):
    try:
        response = await client.post(
            f"{config.base_url}/{path}",
            headers={"Authorization": f"Bearer {config.api_key}"},
            json=body,
        )
        if response.status_code != 200:
            raise _provider_error(response, config.api_key)
        result = response.json()
        if not isinstance(result, dict):
            raise ModelError("MODEL_RESPONSE_INVALID")
        return result
    except httpx.TimeoutException:
        raise ModelError("MODEL_TIMEOUT") from None
    except httpx.HTTPError:
        raise ModelError("DEPENDENCY_UNAVAILABLE") from None
    except ValueError as exc:
        if isinstance(exc, ModelError):
            raise
        raise ModelError("MODEL_RESPONSE_INVALID") from None
