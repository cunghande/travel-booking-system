-- ============================================================
-- FILE: 04_du_lieu_mau.sql (MySQL)
-- MỤC ĐÍCH: Chèn dữ liệu mẫu ban đầu để hệ thống hoạt động
-- HỆ QUẢN TRỊ: MySQL 5.7+ / MySQL 8.0+ / MariaDB / XAMPP
-- ============================================================
-- HƯỚNG DẪN CHẠY:
--   mysql -u root -p tour_booking_db < 04_du_lieu_mau.sql
-- ============================================================

USE tour_booking_db;

-- 1. TẠO CÁC VAI TRÒ MẶC ĐỊNH
INSERT IGNORE INTO roles (id, name, description) VALUES
    (1, 'ADMIN',    'Quản trị viên hệ thống - toàn quyền quản lý'),
    (2, 'STAFF',    'Nhân viên - quản lý tour và duyệt đơn đặt'),
    (3, 'CUSTOMER', 'Khách hàng - tìm kiếm và đặt tour du lịch');


-- 2. TẠO TÀI KHOẢN ADMIN MẶC ĐỊNH
-- Mật khẩu gốc: Admin@123456 (đã hash bằng bcrypt)
INSERT IGNORE INTO users (id, email, hashed_password, full_name, phone_number, is_active, created_at)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'admin@travelbooking.com',
    '$2b$12$LJ3m4ys3LzQXx7Xj0fR8kuO6QpYLFEJBR0ULpXxNjR6BzVsgklWq2',
    'Quản trị viên Hệ thống',
    '0901234567',
    1,
    NOW()
);

-- Gán vai trò ADMIN (role_id = 1)
INSERT IGNORE INTO user_roles (user_id, role_id)
VALUES ('a0000000-0000-0000-0000-000000000001', 1);


-- 3. TẠO TÀI KHOẢN KHÁCH HÀNG MẪU
-- Mật khẩu gốc: 123456
INSERT IGNORE INTO users (id, email, hashed_password, full_name, phone_number, is_active, created_at)
VALUES (
    'a0000000-0000-0000-0000-000000000002',
    'customer@gmail.com',
    '$2b$12$LJ3m4ys3LzQXx7Xj0fR8kuO6QpYLFEJBR0ULpXxNjR6BzVsgklWq2',
    'Nguyễn Văn Du Khách',
    '0988776655',
    1,
    NOW()
);

-- Gán vai trò CUSTOMER (role_id = 3)
INSERT IGNORE INTO user_roles (user_id, role_id)
VALUES ('a0000000-0000-0000-0000-000000000002', 3);


-- 4. TẠO TOUR DU LỊCH MẪU
-- Tour 1: Hạ Long
INSERT IGNORE INTO tours (
    id, tour_code, title, description, category, destination,
    base_price_adult, base_price_child, max_participants, available_slots,
    start_date, end_date, status, created_by, created_at
) VALUES (
    'f1a2b3c4-0001-4000-8000-000000000001',
    'TOUR-HALONG',
    'Vịnh Hạ Long 3 Ngày 2 Đêm — Du Thuyền 5 Sao',
    'Khám phá di sản thiên nhiên thế giới UNESCO, chèo kayak qua hang Luồn, tắm biển đảo Ti Tốp và thưởng thức tiệc nướng hoàng hôn trên vịnh.',
    'Adventure',
    'Vịnh Hạ Long, Quảng Ninh',
    250.00, 125.00, 30, 28,
    '2027-04-15', '2027-04-18', 'PUBLISHED',
    'a0000000-0000-0000-0000-000000000001', NOW()
);

-- Lịch trình Tour 1
INSERT IGNORE INTO itineraries (id, tour_id, day_number, title) VALUES
    ('i1a2b3c4-0001-4000-8000-000000000001', 'f1a2b3c4-0001-4000-8000-000000000001', 1, 'Ngày 1: Hà Nội - Vịnh Hạ Long & Ngắm Hoàng Hôn'),
    ('i1a2b3c4-0002-4000-8000-000000000002', 'f1a2b3c4-0001-4000-8000-000000000001', 2, 'Ngày 2: Chèo Kayak Hang Luồn & Đảo Ti Tốp'),
    ('i1a2b3c4-0003-4000-8000-000000000003', 'f1a2b3c4-0001-4000-8000-000000000001', 3, 'Ngày 3: Làng Chài Cửa Vạn - Trở Về Hà Nội');

-- Hoạt động Tour 1
INSERT IGNORE INTO itinerary_activities (id, itinerary_id, time_slot, place_name, description) VALUES
    (UUID(), 'i1a2b3c4-0001-4000-8000-000000000001', '08:00:00', 'Phố Cổ Hà Nội', 'Xe limousine đón quý khách khởi hành đi Hạ Long.'),
    (UUID(), 'i1a2b3c4-0001-4000-8000-000000000001', '12:00:00', 'Cảng Tuần Châu', 'Lên du thuyền thưởng thức đồ uống chào mừng và nhận phòng.'),
    (UUID(), 'i1a2b3c4-0001-4000-8000-000000000001', '15:00:00', 'Hang Sửng Sốt', 'Khám phá hang động thạch nhũ kỳ vĩ nhất vịnh.'),
    (UUID(), 'i1a2b3c4-0002-4000-8000-000000000002', '07:00:00', 'Sundeck Du Thuyền', 'Tập thái cực quyền đón bình minh trên vịnh.'),
    (UUID(), 'i1a2b3c4-0002-4000-8000-000000000002', '09:30:00', 'Hang Luồn', 'Trải nghiệm chèo thuyền kayak ngắm cảnh thiên nhiên.'),
    (UUID(), 'i1a2b3c4-0002-4000-8000-000000000002', '14:00:00', 'Đảo Ti Tốp', 'Tắm biển và chinh phục đỉnh Ti Tốp ngắm toàn cảnh 360 độ.'),
    (UUID(), 'i1a2b3c4-0003-4000-8000-000000000003', '08:30:00', 'Làng Chài Cửa Vạn', 'Tìm hiểu cuộc sống văn hóa của cư dân vạn chài.'),
    (UUID(), 'i1a2b3c4-0003-4000-8000-000000000003', '11:30:00', 'Cảng Tuần Châu', 'Cập bến, xe đưa quý khách trở về trung tâm Hà Nội.');


-- Tour 2: Đà Nẵng - Hội An
INSERT IGNORE INTO tours (
    id, tour_code, title, description, category, destination,
    base_price_adult, base_price_child, max_participants, available_slots,
    start_date, end_date, status, created_by, created_at
) VALUES (
    'f1a2b3c4-0002-4000-8000-000000000002',
    'TOUR-DANANG',
    'Đà Nẵng - Hội An - Bà Nà Hills 4 Ngày 3 Đêm',
    'Khám phá Cầu Vàng lơ lửng giữa mây ngàn, phố cổ đèn lồng Hội An lung linh về đêm và bãi biển Mỹ Khê tuyệt đẹp.',
    'Beach & Resort',
    'Đà Nẵng & Hội An',
    180.00, 90.00, 25, 25,
    '2027-05-10', '2027-05-14', 'PUBLISHED',
    'a0000000-0000-0000-0000-000000000001', NOW()
);

-- Tour 3: Phú Quốc
INSERT IGNORE INTO tours (
    id, tour_code, title, description, category, destination,
    base_price_adult, base_price_child, max_participants, available_slots,
    start_date, end_date, status, created_by, created_at
) VALUES (
    'f1a2b3c4-0003-4000-8000-000000000003',
    'TOUR-PHUQUOC',
    'Thiên Đường Nghỉ Dưỡng Phú Quốc 3 Ngày 2 Đêm',
    'Lặn ngắm san hô tại hòn Mây Rút, cáp treo vượt biển Hòn Thơm dài nhất thế giới và thưởng thức hải sản tươi sống Làng chài Hàm Ninh.',
    'Beach & Resort',
    'Phú Quốc, Kiên Giang',
    320.00, 160.00, 20, 20,
    '2027-06-01', '2027-06-04', 'PUBLISHED',
    'a0000000-0000-0000-0000-000000000001', NOW()
);


-- 5. TẠO 1 ĐƠN ĐẶT TOUR MẪU (TEST LỊCH SỬ)
INSERT IGNORE INTO bookings (
    id, booking_code, user_id, tour_id, status,
    num_adults, num_children, total_price,
    contact_name, contact_email, contact_phone, special_requests,
    created_at
) VALUES (
    'b1a2b3c4-0001-4000-8000-000000000001',
    'BK-20261003-DEMO01',
    'a0000000-0000-0000-0000-000000000002',
    'f1a2b3c4-0001-4000-8000-000000000001',
    'CONFIRMED',
    2, 0, 500.00,
    'Nguyễn Văn Du Khách', 'customer@gmail.com', '0988776655', 'Cần phòng tầng cao view biển',
    NOW()
);

-- Hành khách đi kèm đơn mẫu
INSERT IGNORE INTO booking_passengers (id, booking_id, full_name, passenger_type, id_card_number) VALUES
    (UUID(), 'b1a2b3c4-0001-4000-8000-000000000001', 'Nguyễn Văn Du Khách', 'ADULT', '001200001234'),
    (UUID(), 'b1a2b3c4-0001-4000-8000-000000000001', 'Trần Thị Bạn Đồng Hành', 'ADULT', '001200005678');
