import logging
import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Khởi tạo logger riêng cho middleware này
logger = logging.getLogger("app.middleware.logging")
if not logger.handlers:
    # Cấu hình định dạng log chuẩn nếu logger chưa có handler
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware ghi log truy vết (Access & Audit Logging) cho mọi HTTP request.

    Vai trò & Nguyên tắc:
    1. Ghi nhận thông tin cơ bản: HTTP Method, URL Path, Client IP, Request ID.
    2. Đo lường thời gian thực thi (Latency) chính xác bằng `time.perf_counter()`.
    3. Phân loại mức độ nghiêm trọng (Log Level) dựa trên HTTP Status Code:
       - 2xx, 3xx: INFO (Thành công, chuyển hướng bình thường)
       - 4xx: WARNING (Lỗi từ phía client: sai dữ liệu, 401, 403, 404)
       - 5xx: ERROR (Lỗi hệ thống / server exception cần can thiệp)
    4. BẢO MẬT (Security Compliance): Tuyệt đối KHÔNG log Request Body hoặc
       Authorization Header để tránh lộ mật khẩu, JWT token, mã OTP, hoặc dữ liệu thẻ.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        start_time = time.perf_counter()

        # 1. Trích xuất thông tin truy vết từ request
        # Lấy Request ID đã được RequestIdMiddleware gán vào request.state từ trước
        request_id = getattr(request.state, "request_id", "N/A")
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path

        # 2. Ghi log khi request vừa đi vào (Inbound)
        logger.info(
            f"--> INBOUND  | ID: {request_id} | {method} {path} | Client: {client_ip}"
        )

        try:
            # 3. Chuyển request cho các tầng xử lý tiếp theo
            response = await call_next(request)

            # 4. Tính toán thời gian xử lý (đơn vị: mili-giây)
            duration_ms = (time.perf_counter() - start_time) * 1000
            status_code = response.status_code

            # 5. Định dạng thông điệp log phản hồi (Outbound)
            log_message = (
                f"<-- OUTBOUND | ID: {request_id} | {method} {path} | "
                f"Status: {status_code} | Duration: {duration_ms:.2f}ms"
            )

            # 6. Phân cấp mức độ log theo tiêu chuẩn HTTP status
            if status_code >= 500:
                logger.error(log_message)
            elif status_code >= 400:
                logger.warning(log_message)
            else:
                logger.info(log_message)

            return response

        except Exception as exc:
            # 7. Xử lý khi có Unhandled Exception trong quá trình thực thi
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                f"<-- FAILED   | ID: {request_id} | {method} {path} | "
                f"Error: {type(exc).__name__}: {str(exc)} | Duration: {duration_ms:.2f}ms"
            )
            # Re-raise exception để Exception Handlers hoặc FastAPI xử lý trả về JSON lỗi chuẩn
            raise exc
