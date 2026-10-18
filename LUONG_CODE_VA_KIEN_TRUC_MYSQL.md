# 🗺️ BẢN ĐỒ KIẾN TRÚC & LUỒNG CODE TOÀN BỘ DỰ ÁN TRAVEL BOOKING SYSTEM (MYSQL THUẦN)

> **Mục tiêu:** Tự tay code từng file từ đầu theo kiến trúc chuẩn Clean Architecture.  
> **Công nghệ:** Python (FastAPI) + MySQL Local (aiomysql) + HTML/CSS/JS (Vanilla).  
> **Đặc điểm:** Không dùng Docker, không dùng PostgreSQL, không dùng ORM nặng nề — Code tối giản, logic, dễ hiểu nhất.

---

## 🏗️ 1. MÔ HÌNH KIẾN TRÚC (CLEAN ARCHITECTURE 4 TẦNG)

```
[ Client / Giao diện Web (HTML/CSS/JS) ]
                  │
                  ▼
         [ Middleware Pipeline ]
   (Request ID ➔ Timing ➔ Security ➔ Logging ➔ CORS)
                  │
                  ▼
         [ API Routers (v1) ]  <─── DTOs (Pydantic v2 Validate dữ liệu)
                  │
                  ▼
         [ Services (Nghiệp vụ) ] <─── Tính tiền, trừ chỗ, kiểm tra logic
                  │
                  ▼
         [ Repositories (Dữ liệu) ]
                  │
                  ▼
         [ MySQL Database Pool ]
```

---

## 📋 2. THỨ TỰ 35 FILE CODE (BƯỚC NÀO TRƯỚC, BƯỚC NÀO SAU)

1. `requirements.txt` — Danh sách thư viện Python cần thiết (FastAPI, aiomysql, pydantic, jose, bcrypt...).
2. `.env` & `.env.example` — Cấu hình thông số kết nối MySQL local (`localhost:3306`), JWT Secret Key.
3. `database/schema.sql` — Toàn bộ câu lệnh SQL tạo Database và các bảng dữ liệu chuẩn MySQL.
4. `app/core/config.py` — Đọc cấu hình từ file `.env` bằng Pydantic BaseSettings.
5. `app/core/exceptions.py` — Bộ xử lý lỗi chuẩn hóa (NotFoundError, BadRequestError, ForbiddenError...).
6. `app/core/database.py` — Quản lý Connection Pool `aiomysql` tới MySQL local và hàm `get_db`.
7. `app/core/security.py` — Băm mật khẩu (bcrypt), sinh và xác thực mã JWT Access Token / Refresh Token.
8. `app/middleware/request_id.py` — Gắn `X-Request-ID` cho mỗi request để theo dõi vết.
9. `app/middleware/timing.py` — Bấm giờ thời gian xử lý API, trả header `X-Process-Time`.
10. `app/middleware/security_headers.py` — Đính kèm header bảo mật HTTP chuẩn OWASP.
11. `app/middleware/logging.py` — Ghi log chi tiết mỗi khi có request gửi đến và trả về.
12. `app/domain/value_objects/enums.py` — Định nghĩa các Enum: Role, TourStatus, BookingStatus, PassengerType.
13. `app/application/dto/common.py` — DTO dùng chung cho phân trang danh sách (`PaginatedResponse`).
14. `app/application/dto/auth.py` — DTO đầu vào/đầu ra cho Đăng ký, Đăng nhập, Token.
15. `app/application/dto/user.py` — DTO thông tin User và phân quyền Admin.
16. `app/application/dto/tour.py` — DTO Tour, Lịch trình theo ngày (`Itinerary`), Hoạt động (`Activity`).
17. `app/application/dto/booking.py` — DTO Đặt vé, thông tin hành khách (`Passenger`), chi tiết đơn.
18. `app/infrastructure/repositories/user_repository.py` — Thao tác dữ liệu bảng `users`, `roles`.
19. `app/infrastructure/repositories/tour_repository.py` — Thao tác dữ liệu bảng `tours`, `itineraries`, `activities`.
20. `app/infrastructure/repositories/booking_repository.py` — Thao tác dữ liệu bảng `bookings`, `booking_passengers`.
21. `app/core/dependencies.py` — Các dependency kiểm tra đăng nhập (`get_current_user`), kiểm tra quyền Admin/Staff.
22. `app/application/services/auth_service.py` — Xử lý nghiệp vụ đăng ký tài khoản, đăng nhập, cấp token.
23. `app/application/services/user_service.py` — Xử lý nghiệp vụ quản lý người dùng, đổi role.
24. `app/application/services/tour_service.py` — Xử lý nghiệp vụ tạo tour, xuất bản mở bán, tìm kiếm tour.
25. `app/application/services/booking_service.py` — Xử lý nghiệp vụ đặt vé, tự tính tổng tiền, trừ chỗ, hủy vé, duyệt đơn.
26. `app/api/v1/auth.py` — Router API xác thực tài khoản.
27. `app/api/v1/users.py` — Router API quản lý người dùng.
28. `app/api/v1/tours.py` — Router API xem và quản lý Tour.
29. `app/api/v1/bookings.py` — Router API đặt tour, xem lịch sử đặt chỗ, duyệt và hủy đơn.
30. `app/api/v1/ai.py` — Router API trợ lý AI tư vấn và gợi ý tour.
31. `app/api/v1/router.py` — Gom toàn bộ router API v1 lại làm một.
32. `app/main.py` — Điểm khởi chạy FastAPI, mở/đóng kết nối MySQL, đăng ký middleware và static web.
33. `app/static/index.html` — Giao diện web người dùng trực quan.
34. `app/static/style.css` — Bộ style CSS sang trọng, tối ưu hiển thị.
35. `app/static/app.js` — JavaScript tương tác: gọi API, render tour, đặt tour, đăng nhập.
