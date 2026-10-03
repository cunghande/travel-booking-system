import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

PROCESS_TIME_HEADER = "X-Process-Time"


class TimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware đo lường thời gian xử lý nội bộ của API (API Latency Tracking).

    Vai trò & Nguyên tắc:
    1. Đo lường chính xác thời gian server cần để xử lý một request (từ lúc qua middleware
       này, gọi DB/Services, cho đến khi sinh ra Response).
    2. Lưu thời gian xử lý vào `request.state.process_time`.
    3. Đính kèm header `X-Process-Time` vào HTTP Response Header để Client, API Gateway,
       hoặc các công cụ benchmark (Locust, Prometheus, Grafana) đo lường SLA P95/P99.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Bắt đầu bấm giờ với Monotonic Clock độ phân giải nano-giây
        start_time = time.perf_counter()

        # Chuyển request cho các middleware bên trong hoặc route handler
        response = await call_next(request)

        # Tính toán tổng thời gian xử lý (đơn vị: giây)
        process_time = time.perf_counter() - start_time

        # 1. Lưu vào request.state để chia sẻ trạng thái nếu cần
        request.state.process_time = process_time

        # 2. Đính kèm vào Response Header gửi về cho Client (ví dụ: "0.001254s")
        response.headers[PROCESS_TIME_HEADER] = f"{process_time:.6f}s"

        return response
