# 🚀 Hướng dẫn Chạy Dự án Backend & Web UI — Travel Booking System

Tài liệu này hướng dẫn chi tiết các bước khởi động và chạy giao diện trang web trên máy tính (Windows / macOS).

---

## ⚡ 1. Câu lệnh chạy nhanh nhất (Khuyên dùng)

Mở terminal **PowerShell** tại thư mục dự án `d:\Code\Travel-Booking-System` và copy/paste lệnh sau (đã sửa lỗi UTF-8):

```powershell
$env:PYTHONUTF8=1; & "C:\Users\Admin\AppData\Local\Python\pythoncore-3.14-64\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

> **Lưu ý:** Bạn có thể dùng lệnh rút gọn nếu `python` đã nhận đường dẫn global:
> ```powershell
> $env:PYTHONUTF8=1; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
> ```

---

## 🛠️ 2. Các bước chuẩn bị chi tiết

### Bước 1: Khởi tạo Cơ sở dữ liệu MySQL 8.0
Mở công cụ MySQL Workbench / Navicat / DBeaver và chạy 4 file SQL trong thư mục `database/` theo thứ tự:
1. `01_tao_database.sql` (Tạo CSDL `tour_booking_db`)
2. `02_tao_bang.sql` (Tạo các bảng `users`, `tours`, `bookings`, `passengers`)
3. `03_tao_stored_procedures.sql` (Tích hợp Stored Procedure chống tranh chấp chỗ `FOR UPDATE`)
4. `04_du_lieu_mau.sql` (Nạp tour mẫu và tài khoản Admin)

### Bước 2: Khởi chạy Backend Server & Giao Diện Web
Mở PowerShell tại thư mục dự án và chạy:
```powershell
$env:PYTHONUTF8=1; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Khi terminal hiện dòng:
```text
INFO:     Started server process
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```
tức là hệ thống đã sẵn sàng!

---

## 🌐 3. Mở trang web và kiểm tra

Mở trình duyệt web (Chrome, Edge, Brave...) và truy cập các liên kết sau:

| Mục | Đường dẫn (URL) | Mô tả |
| :--- | :--- | :--- |
| **Giao diện Trang chủ Web (Frontend UI)** | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) | Đặt tour du lịch 5 sao trực quan |
| **Kiểm tra sức khỏe hệ thống (Health Check)** | [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) | Trả về `{"status": "healthy"}` |
| **Tài liệu API (Swagger UI)** | [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) | Trang kiểm thử API công khai |

---

## 🧪 4. Hướng dẫn Test API bằng Postman

Kéo thả file `Travel_Booking_System.postman_collection.json` trong thư mục dự án vào **Postman**:
1. **01. Auth**: Nhấn Send `Login Admin` (để nhận JWT Token).
2. **03. Tour Management**: Nhấn Send `Get Tours` hoặc `Create Tour`.
3. **04. Booking Management**: Nhấn Send `Create Booking (Customer)` để thử tạo đơn đặt tour.
