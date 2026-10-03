# 📘 HƯỚNG DẪN KẾT NỐI FRONTEND & TÍNH NĂNG AI VỚI BACKEND

> **Dành cho:** Người học lập trình và phát triển hệ thống Travel Booking System  
> **Kiến trúc:** PostgreSQL Local (Stored Procedures) ➔ FastAPI (asyncpg thuần, không ORM) ➔ Vanilla Web / AI Assistant

---

## 🌟 1. CÁCH KHỞI CHẠY HỆ THỐNG TRÊN MÁY LOCAL (KHÔNG DÙNG DOCKER)

### Bước 1: Khởi tạo Cơ sở Dữ liệu PostgreSQL Local
Mở công cụ quản lý cơ sở dữ liệu của bạn (**pgAdmin**, **DBeaver** hoặc chạy bằng lệnh `psql` trong terminal).  
Thực thi tuần tự **4 file SQL** có sẵn trong thư mục `database/`:

1. **`01_tao_database.sql`**: Tạo database `tour_booking_db` và kích hoạt các extension UUID, mật mã.
2. **`02_tao_bang.sql`**: Tạo tất cả bảng dữ liệu (`users`, `roles`, `tours`, `itineraries`, `bookings`, `passengers`, `audit_logs`).
3. **`03_tao_stored_procedures.sql`**: Nạp toàn bộ các Stored Procedures / Functions nghiệp vụ (đăng ký, tìm kiếm tour, đặt tour chống race condition, hủy vé, duyệt đơn...).
4. **`04_du_lieu_mau.sql`**: Chèn dữ liệu mẫu các tour du lịch (Hạ Long, Đà Nẵng, Phú Quốc, Sapa) và tài khoản Admin để kiểm thử.

> 💡 **Cấu hình kết nối**: Kiểm tra file [app/core/config.py](file:///d:/Code/Travel-Booking-System/app/core/config.py) để đảm bảo `POSTGRES_PORT` (mặc định 8888 hoặc 5432) và `POSTGRES_PASSWORD` khớp với máy của bạn.

---

### Bước 2: Cài đặt thư viện Python & Chạy Backend
Mở Terminal trong thư mục dự án:

```bash
# 1. Cài đặt các thư viện cần thiết
pip install fastapi uvicorn asyncpg pydantic pydantic-settings python-jose bcrypt loguru python-multipart

# 2. Chạy ứng dụng FastAPI
uvicorn app.main:app --reload --port 8000
```

- **Giao diện Web người dùng**: Mở trình duyệt vào `http://localhost:8000/`
- **Tài liệu API Swagger UI tương tác**: Mở `http://localhost:8000/docs`

---

## 🌐 2. CƠ CHẾ KẾT NỐI GIỮA FRONTEND VÀ BACKEND

Frontend giao tiếp với Backend thông qua chuẩn **RESTful JSON API**. Mọi dữ liệu trao đổi đều ở định dạng JSON.

### A. Luồng Xác thực (Authentication Flow với JWT)

```
[ Khách hàng ] ──( 1. Gửi Email & Mật khẩu )──> [ Backend API: /api/v1/auth/login ]
[ Khách hàng ] <──( 2. Nhận access_token )────── [ Backend: Mã hóa bằng SECRET_KEY ]
       │
  (Lưu token vào localStorage)
       │
       ▼
[ Khách hàng ] ──( 3. Gửi Bearer Token trong Header )──> [ Các API cần đăng nhập (/bookings) ]
```

#### Code mẫu JavaScript trong Frontend ([app/static/app.js](file:///d:/Code/Travel-Booking-System/app/static/app.js)):
```javascript
// 1. Đăng nhập và lưu Token
async function loginUser(email, password) {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: email, password: password })
  });

  const data = await response.json();
  if (response.ok) {
    // Lưu token vào bộ nhớ trình duyệt
    localStorage.setItem('access_token', data.access_token);
    alert('Đăng nhập thành công!');
  } else {
    alert('Đăng nhập thất bại: ' + data.error.message);
  }
}

// 2. Gửi request kèm Token để thực hiện thao tác bảo mật (Ví dụ: Đặt tour)
async function bookTour(tourId, numAdults, contactName, contactEmail, contactPhone) {
  const token = localStorage.getItem('access_token');
  if (!token) {
    alert('Vui lòng đăng nhập trước khi đặt tour!');
    return;
  }

  const response = await fetch('/api/v1/bookings', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}` // <--- GẮN TOKEN TẠI ĐÂY
    },
    body: JSON.stringify({
      tour_id: tourId,
      num_adults: numAdults,
      num_children: 0,
      contact_name: contactName,
      contact_email: contactEmail,
      contact_phone: contactPhone,
      passengers: []
    })
  });

  const result = await response.json();
  if (response.ok) {
    alert(`🎉 Đặt tour thành công! Mã đơn của bạn là: ${result.booking_code}`);
  } else {
    alert(`Lỗi: ${result.error.message}`);
  }
}
```

---

### B. Luồng Tìm kiếm & Lọc Tour (Tours Search & Filter)

Frontend gửi các tham số lọc qua URL Query String:
```javascript
async function searchTours(destination, category, maxPrice) {
  // Tạo URL với các bộ lọc linh hoạt
  let url = '/api/v1/tours?page=1&page_size=20';
  if (destination) url += `&destination=${encodeURIComponent(destination)}`;
  if (category) url += `&category=${encodeURIComponent(category)}`;
  if (maxPrice) url += `&max_price=${maxPrice}`;

  const response = await fetch(url);
  const data = await response.json();

  // data.items: danh sách các tour tìm thấy
  // data.total: tổng số lượng tour thỏa mãn
  console.log('Danh sách tour:', data.items);
  renderToursToHtml(data.items);
}
```

---

## 🤖 3. CƠ CHẾ HOẠT ĐỘNG CỦA TÍNH NĂNG AI TRỢ LÝ DU LỊCH

Backend đã được tích hợp sẵn endpoint AI tư vấn tour thông minh:  
`POST /api/v1/ai/recommend` ([app/api/v1/ai.py](file:///d:/Code/Travel-Booking-System/app/api/v1/ai.py)).

### A. Cách Frontend gọi tính năng AI:
```javascript
async function askAITourAssistant(destination, maxBudget, category, notes) {
  const response = await fetch('/api/v1/ai/recommend', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      destination: destination,      // Ví dụ: "Đà Nẵng"
      max_budget: maxBudget,          // Ví dụ: 200 ($)
      category: category,            // Ví dụ: "Biển"
      travelers_count: 2,
      notes: notes                   // Ví dụ: "Thích không gian thư giãn, yên tĩnh"
    })
  });

  const aiResult = await response.json();
  
  // 1. Lời khuyên tổng quan từ AI:
  console.log(aiResult.summary);
  
  // 2. Danh sách tour kèm điểm phù hợp & lý do AI đề xuất:
  aiResult.recommendations.forEach(item => {
    console.log(`Tour: ${item.tour.title}`);
    console.log(`Độ phù hợp: ${item.match_score}%`);
    console.log(`Lý do đề xuất: ${item.ai_reason}`);
  });
}
```

### B. Cách Mở Rộng: Tích hợp trực tiếp Google Gemini API hoặc OpenAI
Trong file [app/api/v1/ai.py](file:///d:/Code/Travel-Booking-System/app/api/v1/ai.py), bạn có thể gọi thư viện `google-generativeai` hoặc `openai` rất đơn giản:
```python
import google.generativeai as genai

genai.configure(api_key="API_KEY_CUA_BAN")
model = genai.GenerativeModel("gemini-1.5-flash")

prompt = f"""
Bạn là chuyên gia tư vấn du lịch. Khách hàng muốn đi {data.destination} với ngân sách ${data.max_budget}.
Danh sách tour hiện có: {tours_json}.
Hãy chọn và giải thích ngắn gọn 2 tour phù hợp nhất.
"""
response = model.generate_content(prompt)
ai_advice = response.text
```

---

## 🎯 4. TỔNG KẾT BẢNG MÃ API QUAN TRỌNG

| Chức năng | Phương thức | Endpoint API | Quyền hạn (Role) |
| :--- | :--- | :--- | :--- |
| **Đăng ký** | `POST` | `/api/v1/auth/register` | Công khai |
| **Đăng nhập** | `POST` | `/api/v1/auth/login` | Công khai |
| **Lấy hồ sơ cá nhân** | `GET` | `/api/v1/auth/me` | Cần Bearer Token |
| **Tìm kiếm tour** | `GET` | `/api/v1/tours` | Công khai |
| **Xem chi tiết tour** | `GET` | `/api/v1/tours/{id}` | Công khai |
| **Tạo tour mới** | `POST` | `/api/v1/tours` | Staff / Admin |
| **Xuất bản tour** | `POST` | `/api/v1/tours/{id}/publish` | Staff / Admin |
| **Đặt tour** | `POST` | `/api/v1/bookings` | Khách hàng đăng nhập |
| **Lịch sử đặt vé** | `GET` | `/api/v1/bookings/my` | Khách hàng đăng nhập |
| **Hủy đơn đặt tour** | `POST` | `/api/v1/bookings/{id}/cancel` | Khách hàng / Admin |
| **Duyệt đơn đặt tour**| `POST` | `/api/v1/bookings/{id}/confirm`| Staff / Admin |
| **AI Gợi ý Tour** | `POST` | `/api/v1/ai/recommend` | Công khai |
