"""Redacted provider diagnostics."""


class ModelError(ValueError):
    """Safe provider diagnostics, never raw response bodies or credentials."""

    def __init__(
        self,
        code: str,
        http_status: int | None = None,
        *,
        provider_code: str | None = None,
        request_id: str | None = None,
        retry_after: int | None = None,
    ):
        self.code = code
        self.http_status = http_status
        self.provider_code = provider_code
        self.request_id = request_id
        self.retry_after = retry_after
        super().__init__(f"{code} ({http_status})" if http_status is not None else code)

    def diagnostics(self) -> dict:
        return {
            key: value
            for key, value in {
                "code": self.code,
                "httpStatus": self.http_status,
                "providerCode": self.provider_code,
                "requestId": self.request_id,
                "retryAfter": self.retry_after,
            }.items()
            if value is not None
        }
