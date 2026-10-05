from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Danh sách các HTTP Security Headers chuẩn theo khuyến nghị của OWASP Secure Headers Project
SECURITY_HEADERS = {
    # 1. Chống MIME-sniffing: Ngăn trình duyệt tự ý suy đoán loại nội dung khác với Content-Type server khai báo
    "X-Content-Type-Options": "nosniff",
    # 2. Chống Clickjacking: Ngăn chặn website/API bị nhúng vào <iframe> trên các trang web độc hại khác
    "X-Frame-Options": "DENY",
    # 3. Chống Cross-Site Scripting (XSS) cho các trình duyệt cũ
    "X-XSS-Protection": "1; mode=block",
    # 4. HSTS: Ép trình duyệt luôn giao tiếp qua giao thức bảo mật HTTPS trong vòng 1 năm
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    # 5. Kiểm soát thông tin URL chuyển tiếp để không làm lộ query parameters nhạy cảm
    "Referrer-Policy": "strict-origin-when-cross-origin",
    # 6. Vô hiệu hóa các API phần cứng không cần thiết của trình duyệt (Camera, Mic, GPS)
    "Permissions-Policy": "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware bổ sung các HTTP Security Headers nhằm tăng cường khả năng phòng vệ
    cho API trước các cuộc tấn công phổ biến (OWASP Top 10).

    Vai trò:
    - Tự động chèn các tiêu đề bảo mật vào mọi HTTP Response trước khi gửi về Client.
    - Cấu hình Content-Security-Policy (CSP) thông minh: Áp dụng CSP nghiêm ngặt cho
      các API endpoint thông thường, nhưng nới lỏng hợp lý cho Swagger UI (/docs)
      để giao diện tài liệu API có thể tải CSS/JS từ CDN chính thống của FastAPI.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)

        # 1. Bổ sung các header bảo mật tĩnh
        for header_name, header_value in SECURITY_HEADERS.items():
            response.headers[header_name] = header_value

        # 2. Xử lý Content-Security-Policy (CSP)
        # Trang Swagger UI (/docs), ReDoc (/redoc) và Giao diện Frontend (/)
        path = request.url.path
        if path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi.json"):
            # CSP cho Swagger UI
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://fastapi.tiangolo.com;"
            )
        elif path == "/" or path.startswith("/static"):
            # CSP cho Giao diện Frontend Web
            response.headers["Content-Security-Policy"] = (
                "default-src 'self' 'unsafe-inline' data:; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
                "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com data:; "
                "img-src 'self' data: https: blob:; "
                "connect-src 'self' http://127.0.0.1:8000 http://localhost:8000; "
                "frame-ancestors 'none';"
            )
        else:
            # CSP cho các API endpoint còn lại
            response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"

        return response
