# 🚀 Hướng dẫn Chạy Dự án Backend — Travel Booking System

Tài liệu này hướng dẫn chi tiết các bước khởi động và chạy thử Backend trên máy tính cá nhân (Windows).

---

## ⚡ 1. Câu lệnh chạy nhanh (Quick Start)

Mở terminal (PowerShell) tại thư mục `d:\Code\Travel-Booking-System` và chạy lệnh:

```powershell
# Chạy server với chế độ tự động reload khi sửa code:
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

> 💡 Hoặc nếu bạn đã kích hoạt virtual environment:
> ```powershell
> .\venv\Scripts\Activate.ps1
> uvicorn app.main:app --reload
> ```

---

## 🛠️ 2. Hướng dẫn các cách chạy chi tiết

### 👉 Cách 1: Chạy trực tiếp trên Windows (Khuyên dùng khi dev)

#### Bước 1: Đảm bảo PostgreSQL & Redis đang chạy
Hệ thống cần Database PostgreSQL (cổng `5432`) và Redis (cổng `6379`). Nếu bạn đã cài Docker Desktop, bạn có thể bật riêng Database và Redis cực nhẹ bằng lệnh:
```powershell
docker compose up -d postgres redis
```

#### Bước 2: Chạy Database Migration (Tạo các bảng nếu chưa có)
```powershell
.\venv\Scripts\python.exe -m alembic upgrade head
```

#### Bước 3: Khởi chạy Backend Server
```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Khi màn hình hiện:
```text
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```
tức là server backend đã sẵn sàng nhận request!

---

### 👉 Cách 2: Chạy trọn gói qua Docker Compose (Không cần cài Python)

Nếu máy bạn đã có **Docker Desktop**:
```powershell
# 1. Khởi động toàn bộ dịch vụ (API + PostgreSQL + Redis)
docker compose up -d

# 2. Xem logs server
docker compose logs -f api

# 3. Dừng hệ thống khi không dùng
docker compose down
```

---

## 🔍 3. Kiểm tra xem Server đã chạy thành công chưa

Sau khi chạy lệnh ở mục 1 hoặc 2, bạn mở trình duyệt web:

| Mục | Đường dẫn (URL) | Mô tả |
| :--- | :--- | :--- |
| **Trang tài liệu tương tác (Swagger UI)** | [http://localhost:8000/docs](http://localhost:8000/docs) | Giao diện trực quan để xem và test thử ngay tất cả các API |
| **Tài liệu dạng ReDoc** | [http://localhost:8000/redoc](http://localhost:8000/redoc) | Đọc tài liệu chuẩn OpenAPI |
| **Kiểm tra sức khỏe (Health Check)** | [http://localhost:8000/health](http://localhost:8000/health) | Trả về `{"status": "healthy"}` |

---

## 🧪 4. Hướng dẫn Test API bằng Postman

Dự án đã chuẩn bị sẵn file Collection gồm **23 API mẫu** có sẵn script tự động lưu Token:

1. Mở ứng dụng **Postman**.
2. Nhấn nút **Import** (góc trên bên trái) $\rightarrow$ Kéo thả file:
   `d:\Code\Travel-Booking-System\Travel_Booking_System.postman_collection.json`
3. Thứ tự test khuyến nghị:
   - **Bước 1**: Mở thư mục `01. Auth` $\rightarrow$ Nhấn Send request **`Login Admin`** (hoặc `Register Customer` rồi `Login Customer`). Token sẽ tự động được lưu vào Postman.
   - **Bước 2**: Mở thư mục `03. Tour Management` $\rightarrow$ Nhấn Send request **`Create Tour (with Itinerary)`** để tạo tour du lịch Hạ Long mẫu.
   - **Bước 3**: Chạy tiếp các request **`List Tours`**, **`Search Tours`**, **`Filter Tours`**, **`Publish Tour`** để kiểm tra hoạt động.

---

## 🧪 5. Chạy Automated Tests (Kiểm thử tự động)

Để kiểm tra độ ổn định và tính đúng đắn của toàn bộ code:

```powershell
# Chạy toàn bộ unit test
.\venv\Scripts\python.exe -m pytest tests/unit -v

# Chạy riêng kiểm thử nghiệp vụ Tour
.\venv\Scripts\python.exe -m pytest tests/unit/test_tour_service.py -v
```
