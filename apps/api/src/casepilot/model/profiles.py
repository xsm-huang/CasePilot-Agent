"""Model-specific wire settings. Keep provider differences outside business workflows."""

from dataclasses import dataclass

from .errors import ModelError


@dataclass(frozen=True)
class ChatProfile:
    name: str
    thinking: bool
    preserve_thinking: bool
    max_tokens: int
    probe_max_tokens: int
    manual_max_tokens: int

    def request_options(self, purpose="analysis"):
        limits = {
            "analysis": self.max_tokens,
            "probe": self.probe_max_tokens,
            "manual": self.manual_max_tokens,
        }
        thinking = {"type": "enabled" if self.thinking else "disabled"}
        if self.preserve_thinking:
            thinking["clear_thinking"] = False
        return {"max_tokens": limits[purpose], "thinking": thinking}

    def response_metadata(self, message):
        reasoning = message.get("reasoning_content")
        if reasoning is None:
            return {}
        if not isinstance(reasoning, str) or len(reasoning) > 60000:
            raise ModelError("MODEL_RESPONSE_INVALID")
        # Private ledger/checkpoint data; never part of reports or public events.
        return {"_reasoningContent": reasoning} if self.preserve_thinking and reasoning else {}


DEFAULT_CHAT_MODEL = "glm-5.3-flash"
CHAT_PROFILES = {
    DEFAULT_CHAT_MODEL: ChatProfile(
        name=DEFAULT_CHAT_MODEL,
        thinking=True,
        preserve_thinking=True,
        max_tokens=4096,
        probe_max_tokens=2048,
        manual_max_tokens=1024,
    ),
}


def chat_profile(name):
    try:
        return CHAT_PROFILES[name]
    except KeyError:
        raise ModelError("CHAT_MODEL") from None
