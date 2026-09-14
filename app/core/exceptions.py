# ============================================================
# Travel Booking System — Custom Exceptions & Error Handling
# ============================================================
# Structured error responses — never expose stack traces to client.
# ============================================================

from __future__ import annotations

from typing import Any


class AppException(Exception):
    """Base application exception with structured error data."""

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        response = {
            "error": {
                "code": self.error_code,
                "message": self.message,
            }
        }
        if self.details:
            response["error"]["details"] = self.details
        return response


class NotFoundError(AppException):
    """Resource not found."""

    def __init__(self, resource: str = "Resource", resource_id: Any = None):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} with id '{resource_id}' not found"
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
        )


class ConflictError(AppException):
    """Resource conflict (e.g. duplicate)."""

    def __init__(self, message: str = "Resource already exists"):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
        )


class ForbiddenError(AppException):
    """Access denied."""

    def __init__(self, message: str = "You do not have permission to perform this action"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="FORBIDDEN",
        )


class UnauthorizedError(AppException):
    """Authentication failure."""

    def __init__(self, message: str = "Invalid or expired credentials"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED",
        )


class ValidationError(AppException):
    """Business validation failure."""

    def __init__(self, message: str = "Validation failed", details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class BadRequestError(AppException):
    """Generic bad request."""

    def __init__(self, message: str = "Bad request"):
        super().__init__(
            message=message,
            status_code=400,
            error_code="BAD_REQUEST",
        )
