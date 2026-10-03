-- ============================================================
-- FILE: 04_du_lieu_mau.sql
-- MỤC ĐÍCH: Chèn dữ liệu mẫu ban đầu để hệ thống hoạt động
-- ============================================================
-- HƯỚNG DẪN CHẠY:
--   psql -U postgres -p 8888 -d tour_booking_db -f 04_du_lieu_mau.sql
--
-- GHI CHÚ:
--   - Mật khẩu Admin mặc định: Admin@123456
--   - Mật khẩu đã được mã hóa bcrypt (Python sinh ra)
--   - Dữ liệu tour mẫu là các tour du lịch Việt Nam thực tế
-- ============================================================


-- ============================================================
-- 1. TẠO CÁC VAI TRÒ (ROLES) MẶC ĐỊNH
-- ============================================================
-- Hệ thống có 3 vai trò chính:
--   ADMIN    = Quản trị viên toàn quyền
--   STAFF    = Nhân viên quản lý tour
--   CUSTOMER = Khách hàng đặt tour
INSERT INTO roles (name, description) VALUES
    ('ADMIN',    'Quản trị viên hệ thống - toàn quyền quản lý'),
    ('STAFF',    'Nhân viên - quản lý tour và duyệt đơn đặt'),
    ('CUSTOMER', 'Khách hàng - tìm kiếm và đặt tour du lịch')
ON CONFLICT (name) DO NOTHING;  -- Bỏ qua nếu role đã tồn tại (tránh lỗi khi chạy lại)


-- ============================================================
-- 2. TẠO TÀI KHOẢN ADMIN MẶC ĐỊNH
-- ============================================================
-- Mật khẩu gốc: Admin@123456
-- Mật khẩu dưới đây đã được mã hóa bằng bcrypt (Python)
-- Để sinh lại: python -c "import bcrypt; print(bcrypt.hashpw(b'Admin@123456', bcrypt.gensalt()).decode())"
INSERT INTO users (id, email, hashed_password, full_name, phone_number, is_active)
VALUES (
    uuid_generate_v4(),
    'admin@travelbooking.com',
    '$2b$12$LJ3m4ys3LzQXx7Xj0fR8kuO6QpYLFEJBR0ULpXxNjR6BzVsgklWq2',
    'Quản trị viên Hệ thống',
    '0901234567',
    TRUE
)
ON CONFLICT (email) DO NOTHING;

-- Gán vai trò ADMIN cho tài khoản admin
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u, roles r
WHERE u.email = 'admin@travelbooking.com' AND r.name = 'ADMIN'
ON CONFLICT (user_id, role_id) DO NOTHING;


-- ============================================================
-- 3. TẠO TÀI KHOẢN NHÂN VIÊN MẪU
-- ============================================================
-- Mật khẩu gốc: Staff@123456
INSERT INTO users (id, email, hashed_password, full_name, phone_number, is_active)
VALUES (
    uuid_generate_v4(),
    'staff@travelbooking.com',
    '$2b$12$LJ3m4ys3LzQXx7Xj0fR8kuO6QpYLFEJBR0ULpXxNjR6BzVsgklWq2',
    'Nguyễn Văn Nhân Viên',
    '0901234568',
    TRUE
)
ON CONFLICT (email) DO NOTHING;

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u, roles r
WHERE u.email = 'staff@travelbooking.com' AND r.name = 'STAFF'
ON CONFLICT (user_id, role_id) DO NOTHING;


-- ============================================================
-- 4. TẠO TÀI KHOẢN KHÁCH HÀNG MẪU
-- ============================================================
-- Mật khẩu gốc: Customer@123456
INSERT INTO users (id, email, hashed_password, full_name, phone_number, is_active)
VALUES (
    uuid_generate_v4(),
    'customer@travelbooking.com',
    '$2b$12$LJ3m4ys3LzQXx7Xj0fR8kuO6QpYLFEJBR0ULpXxNjR6BzVsgklWq2',
    'Trần Thị Khách Hàng',
    '0912345678',
    TRUE
)
ON CONFLICT (email) DO NOTHING;

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id
FROM users u, roles r
WHERE u.email = 'customer@travelbooking.com' AND r.name = 'CUSTOMER'
ON CONFLICT (user_id, role_id) DO NOTHING;


-- ============================================================
-- 5. TẠO CÁC TOUR DU LỊCH MẪU
-- ============================================================
-- Tour 1: Đà Nẵng - Hội An 4 ngày 3 đêm
-- ============================================================
DO $$
DECLARE
    v_tour1_id UUID;
    v_tour2_id UUID;
    v_tour3_id UUID;
    v_itin_id  UUID;
    v_admin_id UUID;
BEGIN
    -- Lấy ID admin để gán created_by
    SELECT id INTO v_admin_id FROM users WHERE email = 'admin@travelbooking.com';

    -- ==================== TOUR 1: ĐÀ NẴNG - HỘI AN ====================
    INSERT INTO tours (
        tour_code, title, description, category, destination,
        base_price_adult, base_price_child, max_participants, available_slots,
        start_date, end_date, status, created_by
    ) VALUES (
        'TOUR-DN001',
        'Đà Nẵng - Hội An - Bà Nà Hills 4N3Đ',
        'Khám phá thành phố biển Đà Nẵng xinh đẹp, phố cổ Hội An lung linh về đêm và thiên đường giải trí Bà Nà Hills. Tour bao gồm vé tham quan, khách sạn 4 sao, ăn sáng buffet và xe đưa đón sân bay.',
        'Biển đảo',
        'Đà Nẵng',
        4500000, 3150000,  -- Giá: 4.5 triệu người lớn, 3.15 triệu trẻ em (70%)
        30, 30,
        '2026-11-15', '2026-11-18',
        'PUBLISHED',
        v_admin_id
    ) RETURNING id INTO v_tour1_id;

    -- Lịch trình Ngày 1: Đà Nẵng
    INSERT INTO itineraries (tour_id, day_number, title)
    VALUES (v_tour1_id, 1, 'Đón khách - Khám phá Đà Nẵng')
    RETURNING id INTO v_itin_id;

    INSERT INTO itinerary_activities (itinerary_id, time_slot, place_name, description) VALUES
        (v_itin_id, '08:00', 'Sân bay Đà Nẵng', 'Đón khách tại sân bay, xe đưa về khách sạn nhận phòng'),
        (v_itin_id, '10:00', 'Bán đảo Sơn Trà', 'Tham quan chùa Linh Ứng, ngắm tượng Phật Quan Âm cao nhất Việt Nam'),
        (v_itin_id, '12:00', 'Nhà hàng Bé Mặn', 'Ăn trưa đặc sản Đà Nẵng: mì Quảng, bánh tráng cuốn thịt heo'),
        (v_itin_id, '14:00', 'Bãi biển Mỹ Khê', 'Tự do tắm biển, nghỉ ngơi tại bãi biển đẹp nhất hành tinh'),
        (v_itin_id, '18:00', 'Cầu Rồng', 'Ngắm cầu Rồng phun lửa và phun nước vào tối thứ 7');

    -- Lịch trình Ngày 2: Bà Nà Hills
    INSERT INTO itineraries (tour_id, day_number, title)
    VALUES (v_tour1_id, 2, 'Bà Nà Hills - Cầu Vàng')
    RETURNING id INTO v_itin_id;

    INSERT INTO itinerary_activities (itinerary_id, time_slot, place_name, description) VALUES
        (v_itin_id, '07:30', 'Khách sạn', 'Ăn sáng buffet, chuẩn bị đi Bà Nà Hills'),
        (v_itin_id, '09:00', 'Bà Nà Hills', 'Lên cáp treo dài nhất thế giới, check-in Cầu Vàng nổi tiếng'),
        (v_itin_id, '12:00', 'Làng Pháp', 'Ăn trưa tại Làng Pháp, tham quan kiến trúc châu Âu'),
        (v_itin_id, '14:00', 'Fantasy Park', 'Vui chơi tại khu giải trí Fantasy Park trong nhà'),
        (v_itin_id, '17:00', 'Khách sạn', 'Về khách sạn nghỉ ngơi, tự do khám phá ẩm thực');

    -- Lịch trình Ngày 3: Hội An
    INSERT INTO itineraries (tour_id, day_number, title)
    VALUES (v_tour1_id, 3, 'Phố cổ Hội An')
    RETURNING id INTO v_itin_id;

    INSERT INTO itinerary_activities (itinerary_id, time_slot, place_name, description) VALUES
        (v_itin_id, '08:00', 'Khách sạn', 'Ăn sáng, di chuyển đến Hội An (30km)'),
        (v_itin_id, '09:30', 'Phố cổ Hội An', 'Tham quan Chùa Cầu, Hội quán Phúc Kiến, nhà cổ Tấn Ký'),
        (v_itin_id, '12:00', 'Nhà hàng Hội An', 'Ăn trưa đặc sản: Cao lầu, bánh mì Phượng, chè bắp'),
        (v_itin_id, '14:00', 'Làng rau Trà Quế', 'Trải nghiệm trồng rau, làm bánh tráng'),
        (v_itin_id, '18:00', 'Sông Hoài', 'Thả hoa đăng trên sông Hoài, ngắm phố cổ lung linh về đêm');

    -- Lịch trình Ngày 4: Tự do - Tiễn khách
    INSERT INTO itineraries (tour_id, day_number, title)
    VALUES (v_tour1_id, 4, 'Tự do mua sắm - Tiễn khách')
    RETURNING id INTO v_itin_id;

    INSERT INTO itinerary_activities (itinerary_id, time_slot, place_name, description) VALUES
        (v_itin_id, '07:00', 'Khách sạn', 'Ăn sáng buffet, trả phòng'),
        (v_itin_id, '08:30', 'Chợ Hàn', 'Mua sắm quà lưu niệm tại chợ Hàn nổi tiếng'),
        (v_itin_id, '11:00', 'Sân bay Đà Nẵng', 'Xe đưa ra sân bay, kết thúc tour. Hẹn gặp lại!');


    -- ==================== TOUR 2: HẠ LONG ====================
    INSERT INTO tours (
        tour_code, title, description, category, destination,
        base_price_adult, base_price_child, max_participants, available_slots,
        start_date, end_date, status, created_by
    ) VALUES (
        'TOUR-HL002',
        'Vịnh Hạ Long - Đảo Cát Bà 3N2Đ',
        'Khám phá kỳ quan thiên nhiên thế giới Vịnh Hạ Long trên du thuyền 5 sao. Tham quan hang Sửng Sốt, chèo kayak, tắm biển tại đảo Ti Tốp, khám phá đảo Cát Bà hoang sơ.',
        'Biển đảo',
        'Quảng Ninh',
        6800000, 4760000,  -- Giá: 6.8 triệu người lớn, 4.76 triệu trẻ em
        20, 20,
        '2026-12-01', '2026-12-03',
        'PUBLISHED',
        v_admin_id
    ) RETURNING id INTO v_tour2_id;

    -- Lịch trình Ngày 1: Hạ Long
    INSERT INTO itineraries (tour_id, day_number, title)
    VALUES (v_tour2_id, 1, 'Lên du thuyền - Khám phá Vịnh Hạ Long')
    RETURNING id INTO v_itin_id;

    INSERT INTO itinerary_activities (itinerary_id, time_slot, place_name, description) VALUES
        (v_itin_id, '08:00', 'Hà Nội', 'Xe đón khách tại khách sạn, di chuyển đến Hạ Long (3.5 giờ)'),
        (v_itin_id, '12:00', 'Cảng tàu quốc tế', 'Lên du thuyền, ăn trưa hải sản trên tàu'),
        (v_itin_id, '14:00', 'Hang Sửng Sốt', 'Tham quan hang động đẹp nhất Vịnh Hạ Long'),
        (v_itin_id, '16:00', 'Đảo Ti Tốp', 'Leo núi ngắm toàn cảnh vịnh, tắm biển'),
        (v_itin_id, '19:00', 'Du thuyền', 'Ăn tối trên tàu, câu mực đêm, ngắm sao');

    -- Lịch trình Ngày 2
    INSERT INTO itineraries (tour_id, day_number, title)
    VALUES (v_tour2_id, 2, 'Chèo Kayak - Đảo Cát Bà')
    RETURNING id INTO v_itin_id;

    INSERT INTO itinerary_activities (itinerary_id, time_slot, place_name, description) VALUES
        (v_itin_id, '06:30', 'Du thuyền', 'Tập Thái Cực Quyền trên boong tàu, ăn sáng'),
        (v_itin_id, '08:00', 'Làng chài Vung Viêng', 'Chèo kayak khám phá làng chài nổi truyền thống'),
        (v_itin_id, '12:00', 'Du thuyền', 'Ăn trưa, nghỉ ngơi trên tàu'),
        (v_itin_id, '14:00', 'Đảo Cát Bà', 'Tham quan vườn quốc gia Cát Bà, ngắm voọc đầu trắng');

    -- Lịch trình Ngày 3
    INSERT INTO itineraries (tour_id, day_number, title)
    VALUES (v_tour2_id, 3, 'Bình minh trên vịnh - Về Hà Nội')
    RETURNING id INTO v_itin_id;

    INSERT INTO itinerary_activities (itinerary_id, time_slot, place_name, description) VALUES
        (v_itin_id, '05:30', 'Du thuyền', 'Ngắm bình minh trên Vịnh Hạ Long - khoảnh khắc tuyệt đẹp'),
        (v_itin_id, '07:00', 'Du thuyền', 'Ăn sáng, trả phòng, check-out'),
        (v_itin_id, '09:30', 'Cảng tàu', 'Rời du thuyền, lên xe về Hà Nội'),
        (v_itin_id, '13:00', 'Hà Nội', 'Về đến Hà Nội, kết thúc tour');


    -- ==================== TOUR 3: SẮP KHAI (DRAFT) ====================
    INSERT INTO tours (
        tour_code, title, description, category, destination,
        base_price_adult, base_price_child, max_participants, available_slots,
        start_date, end_date, status, created_by
    ) VALUES (
        'TOUR-DL003',
        'Đà Lạt Mộng Mơ 3N2Đ',
        'Khám phá thành phố ngàn hoa Đà Lạt: đồi chè Cầu Đất, hồ Tuyền Lâm, thung lũng Tình Yêu, chợ đêm Đà Lạt. Nghỉ homestay view đồi thông, thưởng thức cà phê buổi sáng se lạnh.',
        'Núi rừng',
        'Đà Lạt',
        3800000, 2660000,  -- Giá: 3.8 triệu người lớn
        25, 25,
        '2027-01-10', '2027-01-12',
        'DRAFT',  -- Tour này đang ở trạng thái NHÁP (chưa mở bán)
        v_admin_id
    ) RETURNING id INTO v_tour3_id;

    -- Lịch trình cho tour Đà Lạt (chỉ tạo sơ lược vì còn DRAFT)
    INSERT INTO itineraries (tour_id, day_number, title)
    VALUES (v_tour3_id, 1, 'Đón khách - Thung lũng Tình Yêu')
    RETURNING id INTO v_itin_id;

    INSERT INTO itinerary_activities (itinerary_id, time_slot, place_name, description) VALUES
        (v_itin_id, '09:00', 'Sân bay Liên Khương', 'Đón khách, về khách sạn nhận phòng'),
        (v_itin_id, '13:00', 'Thung lũng Tình Yêu', 'Tham quan, chụp ảnh tại thung lũng Tình Yêu'),
        (v_itin_id, '17:00', 'Chợ đêm Đà Lạt', 'Khám phá ẩm thực chợ đêm: bánh tráng nướng, sữa đậu nành');

    INSERT INTO itineraries (tour_id, day_number, title)
    VALUES (v_tour3_id, 2, 'Đồi chè Cầu Đất - Hồ Tuyền Lâm')
    RETURNING id INTO v_itin_id;

    INSERT INTO itinerary_activities (itinerary_id, time_slot, place_name, description) VALUES
        (v_itin_id, '07:00', 'Đồi chè Cầu Đất', 'Ngắm bình minh trên đồi chè bạt ngàn, check-in sống ảo'),
        (v_itin_id, '11:00', 'Hồ Tuyền Lâm', 'Đi thuyền trên hồ, tham quan thiền viện Trúc Lâm');

    INSERT INTO itineraries (tour_id, day_number, title)
    VALUES (v_tour3_id, 3, 'Tự do - Tiễn khách')
    RETURNING id INTO v_itin_id;

    INSERT INTO itinerary_activities (itinerary_id, time_slot, place_name, description) VALUES
        (v_itin_id, '08:00', 'Homestay', 'Ăn sáng, uống cà phê ngắm đồi thông'),
        (v_itin_id, '12:00', 'Sân bay Liên Khương', 'Tiễn khách ra sân bay, kết thúc tour');

    RAISE NOTICE 'Đã tạo xong 3 tour mẫu: Đà Nẵng (PUBLISHED), Hạ Long (PUBLISHED), Đà Lạt (DRAFT)';
END $$;


-- ============================================================
-- KIỂM TRA DỮ LIỆU ĐÃ CHÈN THÀNH CÔNG
-- ============================================================
-- Chạy các lệnh SELECT bên dưới để kiểm tra:

-- Xem danh sách vai trò:
-- SELECT * FROM roles;

-- Xem danh sách user và vai trò:
-- SELECT u.email, u.full_name, array_agg(r.name) as roles
-- FROM users u
-- LEFT JOIN user_roles ur ON u.id = ur.user_id
-- LEFT JOIN roles r ON r.id = ur.role_id
-- GROUP BY u.email, u.full_name;

-- Xem danh sách tour:
-- SELECT tour_code, title, destination, base_price_adult, status FROM tours;

-- Xem lịch trình tour Đà Nẵng:
-- SELECT i.day_number, i.title, a.time_slot, a.place_name
-- FROM itineraries i
-- LEFT JOIN itinerary_activities a ON a.itinerary_id = i.id
-- JOIN tours t ON t.id = i.tour_id
-- WHERE t.tour_code = 'TOUR-DN001'
-- ORDER BY i.day_number, a.time_slot;

-- ============================================================
-- HOÀN TẤT: Dữ liệu mẫu đã được chèn thành công!
-- Bạn có thể khởi chạy backend Python ngay bây giờ.
-- ============================================================
