# 📋 BẢNG THEO DÕI TIẾN ĐỘ & KIẾN TRÚC DỰ ÁN (PROJECT TRACKING)
> **Dự án:** Travel Booking System (Hệ thống Quản lý & Đặt Tour Du Lịch)  
> **Ngôn ngữ & Công nghệ:** Python (FastAPI), PostgreSQL (Asyncpg), Redis, Docker, Vanilla HTML/CSS/JS  
> **Kiến trúc:** Clean Architecture (Domain - Application - Infrastructure - API)  
> **Cập nhật lần cuối:** 03/10/2026

---

## 📌 1. LỜI NHẮC DÀNH CHO AI TIẾP QUẢN (AI INSTRUCTIONS)
Khi một AI mới bắt đầu phiên làm việc:
1. **ĐỌC KỸ FILE NÀY ĐẦU TIÊN** để nắm toàn bộ cấu trúc thư mục, các tính năng đã làm xong và các việc chưa hoàn thành.
2. **Tuân thủ quy tắc Code:**
   - Luôn viết chú thích (comments) và tài liệu bằng **Tiếng Việt**, code ngắn gọn, phân tách lớp rõ ràng (Entity -> DTO -> Repository -> Service -> Router).
   - Mọi thay đổi về database phải tạo migration bằng **Alembic**.
   - Mọi API mới phải viết unit tests và cập nhật vào file này cũng như Postman Collection `Travel_Booking_System.postman_collection.json`.
3. **Cập nhật tiến độ:** Ngay khi hoàn thành một tính năng mới, hãy cập nhật trạng thái `[x]` vào mục **3. Tiến độ thực hiện** bên dưới.

---

## 🏗️ 2. KIẾN TRÚC HỆ THỐNG & CẤU TRÚC THƯ MỤC

```text
Travel-Booking-System/
├── app/
│   ├── api/
│   │   └── v1/                   # Các Router API phiên bản v1
│   │       ├── auth.py           # Đăng ký, đăng nhập, refresh token, me
│   │       ├── users.py          # Quản lý người dùng, phân quyền (Admin)
│   │       ├── tours.py          # Quản lý tour, lịch trình, mở bán, tìm kiếm
│   │       ├── bookings.py       # Đặt tour, duyệt đơn, hủy đơn, lịch sử
│   │       └── router.py         # Tập hợp toàn bộ v1 routers
│   ├── application/
│   │   ├── dto/                  # Data Transfer Objects (Pydantic schemas)
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── tour.py
│   │   │   └── booking.py
│   │   └── services/             # Business Logic Layer
│   │       ├── auth_service.py
│   │       ├── user_service.py
│   │       ├── tour_service.py
│   │       └── booking_service.py
│   ├── core/                     # Cấu hình lõi (Config, Security, Database)
│   │   ├── config.py             # Đọc biến môi trường từ .env
│   │   ├── database.py           # Async SQLAlchemy session engine
│   │   ├── security.py           # Hash mật khẩu (bcrypt), tạo & verify JWT
│   │   └── exceptions.py         # Custom Exception handlers
│   ├── domain/
│   │   ├── entities/             # SQLAlchemy ORM Models
│   │   │   ├── user.py           # User, Role, UserRole, AuditLog
│   │   │   ├── tour.py           # Tour, Itinerary, Activity
│   │   │   └── booking.py        # Booking, BookingPassenger, BookingStatus
│   │   └── repositories/         # Interface định nghĩa thao tác dữ liệu
│   ├── infrastructure/
│   │   └── repositories/         # Triển khai truy vấn DB thực tế (SQLAlchemy)
│   │       ├── user_repository.py
│   │       ├── tour_repository.py
│   │       └── booking_repository.py
│   ├── middleware/               # Pipeline middleware cho Request
│   │   ├── request_id.py         # Gắn X-Request-ID theo dõi vết
│   │   ├── logging.py            # Ghi log request/response
│   │   ├── timing.py             # Đo thời gian xử lý (X-Process-Time)
│   │   └── security.py           # Security Headers & CORS
│   ├── static/                   # Giao diện Web (Frontend trực quan)
│   │   ├── index.html            # Trang chủ, xem tour, modal đặt vé
│   │   ├── style.css             # Luxury Dark Theme
│   │   └── app.js                # Logic gọi API backend & render UI
│   └── main.py                   # Điểm khởi chạy FastAPI, mount middleware & static
├── docker/                       # Dockerfile cho development & production
├── migrations/                   # Quản lý phiên bản Database (Alembic)
│   └── versions/
│       ├── 001_initial_schema.py # Bảng users, roles, tours, itineraries, activities
│       └── 002_create_bookings.py# Bảng bookings, booking_passengers
├── tests/                        # Automated Unit & Integration Tests (Pytest)
│   └── unit/
│       ├── test_auth_service.py
│       ├── test_tour_service.py
│       └── test_booking_service.py
├── HUONG_DAN_CHAY.md             # Hướng dẫn chi tiết cách chạy dự án trên Windows
├── Travel_Booking_System.postman_collection.json # 29 API test mẫu có sẵn script
└── docker-compose.yml            # Khởi chạy PostgreSQL, Redis, API
```

---

## 📊 3. TIẾN ĐỘ THỰC HIỆN (ROADMAP & CHECKLIST)

### ✅ ĐÃ HOÀN THÀNH (COMPLETED)
- [x] **Khởi tạo & Cấu hình Hạ tầng (Sprint 1 - Foundation)**
  - Docker Compose (PostgreSQL 16, Redis 7).
  - Kết nối Async Database với `asyncpg` + SQLAlchemy 2.0.
  - Hệ thống Alembic Migration tự động cập nhật schema.
  - Bộ Middleware bảo mật: `RequestId`, `Logging`, `Timing`, `SecurityHeaders`, `CORS`.
- [x] **Phân hệ Tài khoản & Xác thực (Sprint 1 - Auth & Users)**
  - Đăng ký tài khoản khách hàng (`Customer`).
  - Đăng nhập cấp phát JWT Access Token (ngắn hạn) & Refresh Token (dài hạn).
  - Thu hồi token (Logout) & Cấp mới (Refresh Token).
  - Phân quyền theo vai trò (RBAC): `Admin`, `Staff`, `Tour Guide`, `Customer`.
  - Quản lý danh sách người dùng và gán role (Admin only).
- [x] **Phân hệ Quản lý Tour & Lịch trình (Sprint 2 - Tour Management)**
  - Tạo tour kèm lịch trình nhiều ngày (`Itinerary`) và các hoạt động chi tiết (`Activity`).
  - Quy trình vòng đời Tour: `Draft` $\rightarrow$ `Published` (mở bán) $\rightarrow$ `Archived` (đóng).
  - Tìm kiếm và lọc tour theo từ khóa, mức giá, địa điểm, ngày khởi hành.
  - Caching danh sách và chi tiết tour bằng Redis để tăng tốc độ phản hồi.
- [x] **Phân hệ Đặt Tour (Sprint 3 - Booking Management)**
  - Entity `Booking` và `BookingPassenger` (Hỗ trợ nhiều hành khách: Người lớn, Trẻ em, Em bé).
  - Migration `002_create_bookings.py` tạo bảng thành công.
  - DTOs kiểm tra dữ liệu đầu vào & tính tiền vé tự động theo loại hành khách.
  - Kiểm tra số chỗ còn trống (`available_seats`) tránh overbooking.
  - Quản lý trạng thái đơn: `Pending` $\rightarrow$ `Confirmed` / `Cancelled` / `Completed`.
  - 6 API endpoints chuyên sâu (Khách xem đơn cá nhân, Admin duyệt đơn).
  - Bộ 10 Unit Tests kiểm thử toàn bộ logic đặt chỗ và hủy vé.
- [x] **Giao diện Web Trực quan (Frontend Web UI)**
  - Trang Single Page sang trọng (Luxury Dark Theme) tại `http://localhost:8000/`.
  - Thanh tìm kiếm và bộ lọc tour thông minh.
  - Modal xem chi tiết lịch trình từng ngày (Itinerary & Activities).
  - Modal Đặt tour trực tiếp: Thêm/bớt hành khách, tự động tính tổng tiền theo thời gian thực.
  - Modal Đăng nhập / Đăng ký và Drawer xem danh sách lịch sử đặt chỗ (`My Bookings`).
- [x] **Kiến trúc Stored Procedures & Database Local (Sprint 3.5 - Stored Procedures Migration)**
  - Toàn bộ cơ sở dữ liệu chuyển sang PostgreSQL Stored Procedures và Functions thuần trong thư mục `database/` (01_tao_database, 02_tao_bang, 03_tao_stored_procedures, 04_du_lieu_mau).
  - Không dùng ORM: Kết nối bằng Connection Pool `asyncpg` thuần, bảo mật cao, kiểm soát chặt chẽ race condition với row locks `FOR UPDATE`.
  - Tái cấu trúc Clean Architecture: DTOs Pydantic v2 thuần, Repositories, Services, Routers.
- [x] **Trợ lý Du lịch Thông minh AI (AI Tour Recommendation)**
  - Tích hợp endpoint `/api/v1/ai/recommend` tư vấn tour thông minh theo sở thích và ngân sách.
  - Sẵn sàng mở rộng tích hợp Google Gemini hoặc OpenAI.
- [x] **Tài liệu & Hướng dẫn Kết nối**
  - Tài liệu chi tiết `HUONG_DAN_KET_NOI_FRONTEND_VA_AI.md` giải thích luồng kết nối Frontend - Backend và AI.
  - Collection Postman gồm **29 API mẫu** với kịch bản tự động lưu Bearer Token.
  - Tài liệu `HUONG_DAN_CHAY.md` chi tiết từ cài đặt đến chạy thử.

---

### ⏳ KẾ HOẠCH TIẾP THEO (NEXT MILESTONES)
- [ ] **Sprint 4: Cổng Thanh toán (Payment Gateway)**
  - Tích hợp VNPay / MoMo / Stripe Sandbox để thanh toán tiền cọc / toàn bộ tour.
  - Xử lý Webhook (IPN) để tự động chuyển trạng thái đơn đặt sang `Confirmed` khi thanh toán thành công.
  - Quản lý hoàn tiền (Refund) khi khách hủy tour hợp lệ.
- [ ] **Sprint 4: Tác vụ Ngầm & Gửi Email Tự động (Celery & Background Tasks)**
  - Cấu hình Celery Worker với Redis làm Message Broker.
  - Gửi email tự động xác nhận đơn đặt vé, gửi vé điện tử (E-ticket có mã QR).
  - Email nhắc nhở khách hàng 1 ngày trước ngày khởi hành.
- [ ] **Sprint 5: Đánh giá & Nhận xét (Reviews & Ratings)**
  - Cho phép khách hàng đã hoàn thành tour gửi đánh giá (1-5 sao, bình luận, ảnh).
  - Tự động cập nhật điểm đánh giá trung bình cho Tour.
- [ ] **Sprint 5: Trang Quản trị Toàn diện (Admin Dashboard)**
  - Giao diện Admin quản lý danh sách tour, lịch khởi hành, duyệt đơn đặt tour.
  - Báo cáo biểu đồ doanh thu theo tháng, thống kê tour bán chạy nhất.

---

## 🔌 4. DANH SÁCH TOÀN BỘ API HIỆN CÓ (19 ENDPOINTS)

| Nhóm API | Method | Endpoint URL | Quyền hạn | Mô tả |
| :--- | :---: | :--- | :---: | :--- |
| **Hệ thống** | `GET` | `/health` | Public | Kiểm tra tình trạng server |
| **Giao diện** | `GET` | `/` | Public | Trang chủ Web UI đặt tour |
| **Xác thực** | `POST` | `/api/v1/auth/register` | Public | Đăng ký tài khoản khách hàng |
| | `POST` | `/api/v1/auth/login` | Public | Đăng nhập lấy Access + Refresh Token |
| | `POST` | `/api/v1/auth/refresh` | Public | Làm mới Access Token khi hết hạn |
| | `POST` | `/api/v1/auth/logout` | Authenticated | Đăng xuất, hủy token |
| | `GET` | `/api/v1/auth/me` | Authenticated | Xem thông tin tài khoản hiện tại |
| **Người dùng** | `GET` | `/api/v1/users` | Admin | Lấy danh sách tất cả người dùng |
| | `GET` | `/api/v1/users/{id}` | Admin | Xem chi tiết thông tin 1 người dùng |
| | `POST` | `/api/v1/users/{id}/roles` | Admin | Gán vai trò mới cho người dùng |
| **Quản lý Tour** | `GET` | `/api/v1/tours` | Public | Lấy danh sách tour mở bán (có lọc/tìm kiếm) |
| | `POST` | `/api/v1/tours` | Admin / Staff | Tạo tour mới kèm lịch trình & hoạt động |
| | `GET` | `/api/v1/tours/{id}` | Public | Xem chi tiết tour, lịch trình, số chỗ còn |
| | `POST` | `/api/v1/tours/{id}/publish` | Admin / Staff | Xuất bản mở bán tour |
| | `POST` | `/api/v1/tours/{id}/archive` | Admin / Staff | Đóng tour, ngừng bán |
| **Đặt Tour** | `POST` | `/api/v1/bookings` | Customer | Đặt chỗ tour (kèm danh sách hành khách) |
| | `GET` | `/api/v1/bookings/my` | Customer | Xem danh sách các tour mình đã đặt |
| | `GET` | `/api/v1/bookings/{id}` | Owner / Admin | Xem chi tiết đơn đặt chỗ và hành khách |
| | `POST` | `/api/v1/bookings/{id}/cancel`| Owner / Admin | Hủy đơn đặt tour |
| | `GET` | `/api/v1/bookings` | Admin / Staff | Danh sách toàn bộ đơn đặt trong hệ thống |
| | `POST` | `/api/v1/bookings/{id}/confirm`| Admin / Staff| Xác nhận thanh toán & duyệt đơn |

---

## 💾 5. SƠ ĐỒ DỮ LIỆU CHÍNH (DATABASE SCHEMA)

1. **`users`**: `id (UUID)`, `email`, `hashed_password`, `full_name`, `phone_number`, `is_active`, `is_verified`.
2. **`roles`**: `id`, `name` (`ADMIN`, `STAFF`, `TOUR_GUIDE`, `CUSTOMER`), `description`.
3. **`user_roles`**: Bảng liên kết nhiều-nhiều giữa `user_id` và `role_id`.
4. **`tours`**: `id (UUID)`, `title`, `slug`, `description`, `price`, `duration_days`, `duration_nights`, `max_participants`, `status` (`DRAFT`, `PUBLISHED`, `ARCHIVED`), `departure_location`, `destination`, `start_date`, `end_date`.
5. **`itineraries`**: `id (UUID)`, `tour_id`, `day_number`, `title`, `description`.
6. **`activities`**: `id (UUID)`, `itinerary_id`, `time`, `activity_name`, `description`.
7. **`bookings`**: `id (UUID)`, `booking_code` (Mã vé duy nhất, vd: `BK-20261003-ABCD`), `user_id`, `tour_id`, `status` (`PENDING`, `CONFIRMED`, `CANCELLED`, `COMPLETED`), `total_amount`, `contact_name`, `contact_email`, `contact_phone`, `special_requests`.
8. **`booking_passengers`**: `id (UUID)`, `booking_id`, `full_name`, `passenger_type` (`ADULT`: 100% giá, `CHILD`: 70% giá, `INFANT`: 10% giá), `date_of_birth`, `passport_or_id`.
9. **`audit_logs`**: `id`, `user_id`, `action`, `resource_type`, `resource_id`, `details`, `created_at`.

---

## 🚀 6. HƯỚNG DẪN KHỞI CHẠY NHANH CHO DEVELOPER & AI

### 1. Kích hoạt môi trường và chạy Server:
```powershell
# Chạy với Python có sẵn trên Windows:
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
> *(Lưu ý trên Windows: Để tránh bị Windows Defender App Control chặn file .exe, luôn dùng cú pháp `python -m uvicorn` thay vì gọi trực tiếp file .exe)*.

### 2. Kiểm tra giao diện và API Docs:
- **Giao diện Web UI:** [http://localhost:8000/](http://localhost:8000/)
- **Swagger UI Tài liệu API:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Kiểm tra trạng thái:** [http://localhost:8000/health](http://localhost:8000/health)

### 3. Chạy toàn bộ Unit Tests kiểm tra tính đúng đắn:
```powershell
python -m pytest tests/unit/ -v
```
