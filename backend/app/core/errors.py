from __future__ import annotations


class AppError(Exception):
    def __init__(self, status_code: int, code: str, message: str, detail: object | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.detail = detail

    def as_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {"code": self.code, "message": self.message}
        if self.detail is not None:
            payload["detail"] = self.detail
        return {"error": payload}


class ValidationError(AppError):
    def __init__(self, message: str, detail: object | None = None) -> None:
        super().__init__(400, "validation_error", message, detail)


class NotFoundError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(404, "not_found", message)


class UpstreamError(AppError):
    def __init__(self, message: str, status_code: int = 502, detail: object | None = None) -> None:
        super().__init__(status_code, "upstream_error", message, detail)
