# ============================================================
# Travel Booking System — Xử lý lỗi tập trung (Exceptions)
# ============================================================
# Định nghĩa các loại lỗi nghiệp vụ chuẩn hóa.
# Khi có lỗi, hệ thống trả về JSON rõ ràng cho client,
# KHÔNG BAO GIỜ lộ thông tin nội bộ (stack trace, tên file...).
#
# Ví dụ response khi lỗi:
# {
#     "error": {
#         "code": "NOT_FOUND",
#         "message": "Không tìm thấy tour với ID '123'"
#     }
# }
# ============================================================

from typing import Any


class AppException(Exception):
    """
    Lỗi cơ bản của ứng dụng. Tất cả lỗi nghiệp vụ kế thừa từ class này.

    Attributes:
        message    : Thông báo lỗi hiển thị cho người dùng
        status_code: Mã HTTP trả về (400, 401, 403, 404, 409, 422, 500)
        error_code : Mã lỗi ngắn gọn (NOT_FOUND, UNAUTHORIZED...)
        details    : Thông tin bổ sung (tùy chọn)
    """

    def __init__(
        self,
        message: str = "Đã xảy ra lỗi không xác định",
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
        """Chuyển lỗi thành JSON để trả về cho client."""
        response = {
            "error": {
                "code": self.error_code,
                "message": self.message,
            }
        }
        if self.details:
            response["error"]["details"] = self.details
        return response


# --- Các loại lỗi cụ thể ---

class NotFoundError(AppException):
    """Lỗi 404: Không tìm thấy tài nguyên (tour, user, booking...)."""
    def __init__(self, message: str = "Không tìm thấy tài nguyên"):
        super().__init__(message=message, status_code=404, error_code="NOT_FOUND")


class BadRequestError(AppException):
    """Lỗi 400: Yêu cầu không hợp lệ (dữ liệu sai, logic không đúng)."""
    def __init__(self, message: str = "Yêu cầu không hợp lệ"):
        super().__init__(message=message, status_code=400, error_code="BAD_REQUEST")


class UnauthorizedError(AppException):
    """Lỗi 401: Chưa đăng nhập hoặc token hết hạn."""
    def __init__(self, message: str = "Vui lòng đăng nhập"):
        super().__init__(message=message, status_code=401, error_code="UNAUTHORIZED")


class ForbiddenError(AppException):
    """Lỗi 403: Không có quyền truy cập (VD: Customer cố truy cập API Admin)."""
    def __init__(self, message: str = "Bạn không có quyền thực hiện thao tác này"):
        super().__init__(message=message, status_code=403, error_code="FORBIDDEN")


class ConflictError(AppException):
    """Lỗi 409: Xung đột dữ liệu (VD: email đã đăng ký, mã tour đã tồn tại)."""
    def __init__(self, message: str = "Dữ liệu đã tồn tại"):
        super().__init__(message=message, status_code=409, error_code="CONFLICT")


class ValidationError(AppException):
    """Lỗi 422: Dữ liệu không hợp lệ (VD: giá âm, ngày kết thúc trước ngày bắt đầu)."""
    def __init__(self, message: str = "Dữ liệu không hợp lệ", details: dict | None = None):
        super().__init__(message=message, status_code=422, error_code="VALIDATION_ERROR", details=details)
