# 🌍 Wanderlust — Hệ Thống Đặt Tour Du Lịch Cao Cấp (Travel Booking System)

> **Hệ Thống Đặt Tour & Quản Lý Du Lịch Tích Hợp AI & Giao Diện Hiện Đại 5 Sao**

**Tác giả:** Đỗ Văn Cung  
**Kiến trúc:** Clean Architecture (FastAPI + MySQL 8.0 + Stored Procedures)  
**Giao diện:** Modern High-End Travel UI (Traveloka / Airbnb Style - Bright & Vibrant)  
**Trạng thái hiện tại:** **Hoàn thiện Core Auth, Tour Catalog, Booking Engine (Chống Race Condition) & Giao Diện Người Dùng (UI/UX) ✅**

---

## 🎨 Giao Diện Người Dùng (Frontend UI Features)

- **Phong cách thiết kế:** Modern Bright Travel Aesthetic (Trắng tinh khôi `#FFFFFF` kết hợp Air Slate `#F8FAFC`, điểm xuyết Cyan `#0284C7` & Nút bấm Coral Sunset `#FF5A36`).
- **Header & Navbar:** Thanh điều hướng kính mờ (`backdrop-filter`), logo la bàn cam nổi bật, responsive trên mọi thiết bị.
- **Hero & Search Widget:** Banner trình chiếu ken-burns hoành tráng, widget tìm kiếm đa năng (Tour trọn gói, Vé máy bay, Resort).
- **Danh Sách Tour & Thẻ Tour:** Hiển thị dạng lưới đẹp mắt, badge phân loại (`Adventure`, `Beach & Resort`, `Cultural`), điểm đánh giá sao, thời lượng tour và giá trọn gói.
- **Modal Lịch Trình (Bento Grid Gallery):** Xem chi tiết hành trình từng ngày, hình ảnh bento grid, chi phí bao gồm & thông tin kiểm định.
- **Modal Đặt Vé 3 Bước (Booking Stepper):** 
  - **Bước 1:** Chọn số lượng người lớn / trẻ em & Chọn vị trí boong tàu / ghế ngồi (Seat Picker).
  - **Bước 2:** Nhập thông tin người liên hệ & danh sách hành khách.
  - **Bước 3:** Xác nhận & Xuất vé điện tử **E-Ticket Boarding Pass** kèm mã vạch Barcode.

---

## 🏗️ Kiến Trúc Hệ Thống (Clean Architecture)

```text
Presentation Layer (FastAPI Routes & Static Frontend UI)
       ↓
Application Layer (BookingService, TourService, AuthService, DTOs)
       ↓
Domain Layer (Entities, Value Objects, Business Enums)
       ↓
Infrastructure Layer (MySQL 8.0 Connection Pool, Repositories, Stored Procedures)
```

---

## 🚀 Hướng Dẫn Khởi Chạy Dự Án (Quick Start)

### 1. Cấu hình Cơ sở dữ liệu MySQL 8.0
Chạy lần lượt 4 file SQL trong thư mục `database/` vào MySQL 8.0 theo thứ tự:

```bash
database/
├── 01_tao_database.sql         # Tạo CSDL tour_booking_db
├── 02_tao_bang.sql             # Tạo bảng users, tours, itineraries, bookings, passengers
├── 03_tao_stored_procedures.sql # Tích hợp SP chống tranh chấp chỗ (FOR UPDATE)
└── 04_du_lieu_mau.sql          # Nạp dữ liệu tour mẫu và tài khoản Admin
```

### 2. Khởi chạy Server Backend (FastAPI + Uvicorn)

#### Trên Windows (PowerShell):
```powershell
# 1. Kích hoạt môi trường ảo (nếu có)
venv\Scripts\activate

# 2. Cài đặt thư viện phụ thuộc
pip install -r requirements.txt

# 3. Đặt biến môi trường UTF-8 và chạy Uvicorn Server
$env:PYTHONUTF8=1
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

#### Trên Linux / macOS:
```bash
PYTHONUTF8=1 python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Truy cập Hệ thống
- **Giao diện Web:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Kiểm tra Sức khỏe API:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)
- **Tài liệu API (Swagger UI):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🔐 Tài Khoản Thử Nghiệm (Default Credentials)

| Vai trò | Email | Mật khẩu |
|---------|-------|----------|
| **Quản trị viên (Admin)** | `admin@travelbooking.com` | `Admin@123456` |
| **Khách hàng (Customer)** | `customer@travelbooking.com` | `Customer@123456` |

---

## 📡 Các API Endpoints Chính (API Routes)

### 🔑 Authentication (`/api/v1/auth`)
- `POST /api/v1/auth/register` — Đăng ký tài khoản người dùng mới.
- `POST /api/v1/auth/login` — Đăng nhập, nhận JWT Token (Access Token + Refresh Token).
- `GET /api/v1/auth/me` — Lấy thông tin tài khoản hiện tại.

### 🏝️ Tour Management (`/api/v1/tours`)
- `GET /api/v1/tours` — Lấy danh sách tour công khai (Phân trang, Lọc điểm đến, Thể loại, Mức giá).
- `GET /api/v1/tours/{id}` — Lấy thông tin chi tiết tour & lịch trình từng ngày.
- `POST /api/v1/tours` — Tạo tour mới (Admin / Staff).
- `PUT /api/v1/tours/{id}` — Cập nhật tour.

### 🎟️ Booking Engine (`/api/v1/bookings`)
- `POST /api/v1/bookings` — Đặt tour (Gọi Stored Procedure `fn_tao_don_dat_tour` kiểm tra chỗ, giữ khóa bản ghi `FOR UPDATE`, trừ `available_slots` và sinh mã `BK-XXXXX`).
- `GET /api/v1/bookings/my-bookings` — Xem lịch sử danh sách đơn đặt của tôi.
- `GET /api/v1/bookings/{id}` — Xem chi tiết đơn đặt và danh sách hành khách đi kèm.
- `POST /api/v1/bookings/{id}/cancel` — Hủy đơn đặt (Tự động hoàn lại chỗ trống cho tour).

---

## ⚙️ Công Nghệ Sử Dụng (Tech Stack)

| Thành phần | Công nghệ |
|-----------|-----------|
| **Backend Framework** | FastAPI 0.115 (Python 3.11+) |
| **Giao diện (Frontend)** | Vanilla HTML5, CSS3 Custom Properties, Modern JavaScript (ES6+), FontAwesome 6, Google Fonts (Outfit & Plus Jakarta Sans) |
| **Cơ sở dữ liệu** | MySQL 8.0 (Async Execution, Stored Procedures, Connection Pool) |
| **Bảo mật** | JWT Authentication, Passlib (Bcrypt), Security Headers Middleware (CSP, HSTS) |
| **Logging & Monitoring** | Loguru + Timing & Request ID Middleware |

---

## 📁 Cấu Trúc Thư Mục Dự Án

```text
Travel-Booking-System/
├── app/
│   ├── api/v1/               # API Routes (Controllers)
│   ├── application/          # Business Services & DTO Schemas
│   ├── domain/               # Domain Entities & Enums
│   ├── infrastructure/       # DB Repositories & Connection Pool
│   ├── middleware/           # Security Headers, Timing, Logging Middleware
│   ├── static/               # Frontend Assets (index.html, style.css, app.js)
│   └── main.py               # FastAPI App Factory & Routing
├── database/                 # Các file kịch bản SQL khởi tạo CSDL & Stored Procedures
├── tests/                    # Unit Tests & Integration Tests
├── requirements.txt          # Danh sách thư viện Python dependencies
└── README.md                 # Tài liệu hướng dẫn dự án
```
