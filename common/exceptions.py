# file ý nghĩa là bảo mật thông tin và đưa về shema thống nhất để thông báo lỗi đến người dùng, dùng cho toàn bộ Microservices của hệ thống
# import các thư viện cần thiết
from typing import Any, Dict, Optional
from fastapi import HTTPException, status


from typing import Any, Dict, Optional
from fastapi import HTTPException, status
class AppException(HTTPException):
    """Lớp ngoại lệ cơ sở cho toàn bộ hệ thống."""
    # hàm tạo các biến và định nghĩa kiểu dữ liệu
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: str = "ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
    # kế thừa từ lớp AppException và định nghĩa shema chung
        super().__init__(
            status_code=status_code,
            detail={
                "success": False,
                "error_code": error_code,
                "message": message,
                "details": details or {},
            },
        )
class NotFoundError(AppException):
    """Lỗi không tìm thấy tài nguyên (HTTP 404)."""
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=f"Không tìm thấy {resource} với định danh: {identifier}",
            error_code="RESOURCE_NOT_FOUND",
        )
class BadRequestError(AppException):
    """Lỗi dữ liệu gửi lên không hợp lệ (HTTP 400)."""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            message=message,
            error_code="BAD_REQUEST",
            details=details,
        )
class UnauthorizedError(AppException):
    """Lỗi chưa đăng nhập hoặc Token JWT không hợp lệ / hết hạn (HTTP 401)."""
    def __init__(self, message: str = "Yêu cầu đăng nhập hoặc Token không hợp lệ"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_code="UNAUTHORIZED",
        )
class ForbiddenError(AppException):
    """Lỗi không có quyền truy cập, ví dụ không phải ADMIN (HTTP 403)."""
    def __init__(self, message: str = "Bạn không có quyền thực hiện thao tác này"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_code="FORBIDDEN",
        )
class ConflictError(AppException):
    """Lỗi xung đột dữ liệu, ví dụ email đã tồn tại (HTTP 409)."""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            error_code="CONFLICT",
        )
