"""Bounded chat/tool/JSON requests, with no automatic provider retry."""

import json

import httpx

from .errors import ModelError
from .transport import _provider_request


class ChatClient:
    def __init__(self, config, *, client=None):
        self.config, self.client = config, client

    async def complete(self, messages, *, tools=None, json_mode=False):
        if tools and json_mode:
            raise ModelError("MODEL_REQUEST_INVALID")
        if (
            not isinstance(messages, list)
            or not messages
            or len(json.dumps(messages, ensure_ascii=False)) > 60000
        ):
            raise ModelError("MODEL_CONTEXT_LIMIT")
        body = {
            "model": self.config.chat_model,
            "messages": messages,
            "stream": False,
            "max_tokens": 2048,
            "thinking": {"type": "disabled"},
        }
        if tools:
            body.update(tools=tools, tool_choice="auto")
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        if self.client is not None:
            response = await _provider_request(self.client, self.config, "chat/completions", body)
        else:
            async with httpx.AsyncClient(
                timeout=self.config.timeout_ms / 1000, follow_redirects=False
            ) as client:
                response = await _provider_request(client, self.config, "chat/completions", body)
        try:
            if response.get("model", self.config.chat_model) != self.config.chat_model:
                raise ModelError("MODEL_PROFILE_MISMATCH")
            choices = response["choices"]
            if not isinstance(choices, list) or len(choices) != 1:
                raise ValueError()
            choice = choices[0]
            if not isinstance(choice, dict) or not isinstance(choice.get("message"), dict):
                raise ValueError()
            if choice.get("finish_reason") == "length":
                raise ModelError("MODEL_OUTPUT_TRUNCATED")
            message = choice["message"]
            content = message.get("content") or ""
            calls = message.get("tool_calls") or []
            if (
                not isinstance(content, str)
                or len(content) > 16000
                or not isinstance(calls, list)
                or len(calls) > 1
                or (not content.strip() and not calls)
            ):
                raise ValueError()
            allowed = {tool["function"]["name"] for tool in tools or []}
            parsed_calls = []
            for call in calls:
                if (
                    call["type"] != "function"
                    or call["function"]["name"] not in allowed
                    or not isinstance(call["id"], str)
                    or not 1 <= len(call["id"]) <= 128
                ):
                    raise ValueError()
                arguments = json.loads(call["function"]["arguments"])
                if not isinstance(arguments, dict):
                    raise ValueError()
                parsed_calls.append(
                    {"id": call["id"], "name": call["function"]["name"], "arguments": arguments}
                )
            usage = response.get("usage", {})
            if not isinstance(usage, dict):
                raise ValueError()
            safe_usage = {}
            for field in ("prompt_tokens", "completion_tokens", "total_tokens"):
                if field in usage:
                    if type(usage[field]) is not int or not 0 <= usage[field] <= 2**53 - 1:
                        raise ValueError()
                    safe_usage[field] = usage[field]
            return {"content": content, "toolCalls": parsed_calls, "usage": safe_usage}
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            if isinstance(exc, ModelError):
                raise
            raise ModelError("MODEL_RESPONSE_INVALID") from None
