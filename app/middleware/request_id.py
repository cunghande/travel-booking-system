import uuid
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware xử lý định danh duy nhất cho từng HTTP request (Request ID Tracing).

    Vai trò:
    1. Kiểm tra xem Client hoặc Reverse Proxy (Nginx, Cloudflare, API Gateway)
       có truyền header 'X-Request-ID' lên không.
       - Nếu có: Giữ nguyên ID này để duy trì Distributed Tracing xuyên suốt các hệ thống.
       - Nếu không: Sinh mới một UUID version 4 ngẫu nhiên và đảm bảo tính duy nhất.
    2. Lưu ID này vào `request.state.request_id` để các tầng tiếp theo (Logging Middleware,
       Services, Exception Handlers) có thể truy cập mà không cần parse lại headers.
    3. Đính kèm `X-Request-ID` vào HTTP response header để Client/Frontend có mã đối soát
       khi cần tra cứu lỗi hoặc liên hệ bộ phận hỗ trợ.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # 1. Trích xuất hoặc sinh mới Request ID
        incoming_request_id = request.headers.get(REQUEST_ID_HEADER)
        request_id = incoming_request_id if incoming_request_id else str(uuid.uuid4())

        # 2. Gắn vào request.state để chia sẻ trạng thái trong phạm vi request hiện tại
        request.state.request_id = request_id

        # 3. Chuyển quyền xử lý cho middleware hoặc route handler tiếp theo trong chuỗi (Middleware Chain)
        response = await call_next(request)

        # 4. Gắn Request ID vào response headers trả về cho Client
        response.headers[REQUEST_ID_HEADER] = request_id

        return response
