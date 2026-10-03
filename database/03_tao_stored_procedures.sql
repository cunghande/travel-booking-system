-- ============================================================
-- FILE: 03_tao_stored_procedures.sql (MySQL)
-- MỤC ĐÍCH: Tạo toàn bộ Stored Procedures nghiệp vụ cho hệ thống đặt tour
-- HỆ QUẢN TRỊ: MySQL 5.7+ / MySQL 8.0+ / MariaDB / XAMPP
-- ============================================================
-- HƯỚNG DẪN CHẠY:
--   mysql -u root -p tour_booking_db < 03_tao_stored_procedures.sql
-- ============================================================

USE tour_booking_db;

DELIMITER $$

-- ████████████████████████████████████████████████████████████
-- PHẦN 1: THỦ TỤC XÁC THỰC & NGƯỜI DÙNG (AUTH & USERS)
-- ████████████████████████████████████████████████████████████

-- ------------------------------------------------------------
-- 1.1: Đăng ký tài khoản mới (gán mặc định vai trò CUSTOMER)
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_dang_ky_tai_khoan$$
CREATE PROCEDURE sp_dang_ky_tai_khoan(
    IN p_email           VARCHAR(255),
    IN p_hashed_password VARCHAR(255),
    IN p_full_name       VARCHAR(255),
    IN p_phone_number    VARCHAR(20),
    IN p_ip_address      VARCHAR(45)
)
BEGIN
    DECLARE v_user_id CHAR(36);
    DECLARE v_role_id INT;

    -- Kiểm tra email trùng lặp
    IF EXISTS (SELECT 1 FROM users WHERE email = p_email) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Email đã được đăng ký trong hệ thống trước đó';
    END IF;

    -- Sinh UUID mới cho người dùng
    SET v_user_id = UUID();

    -- Tạo tài khoản mới
    INSERT INTO users (id, email, hashed_password, full_name, phone_number, is_active, created_at)
    VALUES (v_user_id, p_email, p_hashed_password, p_full_name, p_phone_number, 1, NOW());

    -- Gán vai trò CUSTOMER
    SELECT id INTO v_role_id FROM roles WHERE name = 'CUSTOMER' LIMIT 1;
    IF v_role_id IS NOT NULL THEN
        INSERT INTO user_roles (user_id, role_id) VALUES (v_user_id, v_role_id);
    END IF;

    -- Ghi nhật ký
    INSERT INTO audit_logs (id, user_id, action, resource, resource_id, ip_address, created_at)
    VALUES (UUID(), v_user_id, 'USER_REGISTERED', 'users', v_user_id, p_ip_address, NOW());

    -- Trả về thông tin vừa tạo
    SELECT
        u.id AS user_id,
        u.email,
        u.full_name,
        u.phone_number,
        u.is_active,
        u.created_at,
        'CUSTOMER' AS role_names
    FROM users u
    WHERE u.id = v_user_id;
END$$


-- ------------------------------------------------------------
-- 1.2: Lấy thông tin người dùng theo Email (dùng khi đăng nhập)
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_lay_user_theo_email$$
CREATE PROCEDURE sp_lay_user_theo_email(
    IN p_email VARCHAR(255)
)
BEGIN
    SELECT
        u.id AS user_id,
        u.email,
        u.hashed_password,
        u.full_name,
        u.phone_number,
        u.is_active,
        u.created_at,
        COALESCE(GROUP_CONCAT(r.name SEPARATOR ','), 'CUSTOMER') AS role_names
    FROM users u
    LEFT JOIN user_roles ur ON u.id = ur.user_id
    LEFT JOIN roles r ON ur.role_id = r.id
    WHERE u.email = p_email
    GROUP BY u.id, u.email, u.hashed_password, u.full_name, u.phone_number, u.is_active, u.created_at;
END$$


-- ------------------------------------------------------------
-- 1.3: Lấy thông tin người dùng theo ID (UUID)
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_lay_user_theo_id$$
CREATE PROCEDURE sp_lay_user_theo_id(
    IN p_user_id CHAR(36)
)
BEGIN
    SELECT
        u.id AS user_id,
        u.email,
        u.full_name,
        u.phone_number,
        u.is_active,
        u.created_at,
        u.updated_at,
        COALESCE(GROUP_CONCAT(r.name SEPARATOR ','), 'CUSTOMER') AS role_names
    FROM users u
    LEFT JOIN user_roles ur ON u.id = ur.user_id
    LEFT JOIN roles r ON ur.role_id = r.id
    WHERE u.id = p_user_id
    GROUP BY u.id, u.email, u.full_name, u.phone_number, u.is_active, u.created_at, u.updated_at;
END$$


-- ------------------------------------------------------------
-- 1.4: Ghi log đăng nhập
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_ghi_log_dang_nhap$$
CREATE PROCEDURE sp_ghi_log_dang_nhap(
    IN p_user_id    CHAR(36),
    IN p_ip_address VARCHAR(45)
)
BEGIN
    INSERT INTO audit_logs (id, user_id, action, resource, resource_id, ip_address, created_at)
    VALUES (UUID(), p_user_id, 'USER_LOGIN', 'users', p_user_id, p_ip_address, NOW());
END$$


-- ------------------------------------------------------------
-- 1.5: Lấy danh sách người dùng phân trang (Admin)
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_lay_danh_sach_users$$
CREATE PROCEDURE sp_lay_danh_sach_users(
    IN p_skip      INT,
    IN p_limit     INT,
    IN p_is_active INT  -- -1 = tất cả, 1 = active, 0 = inactive
)
BEGIN
    SELECT
        u.id AS user_id,
        u.email,
        u.full_name,
        u.phone_number,
        u.is_active,
        u.created_at,
        COALESCE(GROUP_CONCAT(r.name SEPARATOR ','), '') AS role_names,
        (SELECT COUNT(*) FROM users u2 WHERE (p_is_active = -1 OR u2.is_active = p_is_active)) AS total_count
    FROM users u
    LEFT JOIN user_roles ur ON u.id = ur.user_id
    LEFT JOIN roles r ON ur.role_id = r.id
    WHERE (p_is_active = -1 OR u.is_active = p_is_active)
    GROUP BY u.id, u.email, u.full_name, u.phone_number, u.is_active, u.created_at
    ORDER BY u.created_at DESC
    LIMIT p_skip, p_limit;
END$$


-- ------------------------------------------------------------
-- 1.6: Gán vai trò cho người dùng
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_gan_vai_tro$$
CREATE PROCEDURE sp_gan_vai_tro(
    IN p_user_id   CHAR(36),
    IN p_role_name VARCHAR(50),
    IN p_admin_id  CHAR(36)
)
BEGIN
    DECLARE v_role_id INT;

    SELECT id INTO v_role_id FROM roles WHERE name = p_role_name LIMIT 1;
    IF v_role_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Vai trò yêu cầu không tồn tại';
    END IF;

    -- Thêm vai trò nếu chưa có
    INSERT IGNORE INTO user_roles (user_id, role_id) VALUES (p_user_id, v_role_id);

    -- Ghi nhật ký
    INSERT INTO audit_logs (id, user_id, action, resource, resource_id, created_at)
    VALUES (UUID(), p_admin_id, 'ROLE_ASSIGNED', 'users', p_user_id, NOW());

    SELECT p_user_id AS user_id, p_role_name AS assigned_role;
END$$


-- ████████████████████████████████████████████████████████████
-- PHẦN 2: THỦ TỤC QUẢN LÝ TOUR DU LỊCH (TOURS)
-- ████████████████████████████████████████████████████████████

-- ------------------------------------------------------------
-- 2.1: Tạo tour mới (ở trạng thái DRAFT)
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_tao_tour$$
CREATE PROCEDURE sp_tao_tour(
    IN p_title            VARCHAR(500),
    IN p_description      TEXT,
    IN p_category         VARCHAR(100),
    IN p_destination      VARCHAR(255),
    IN p_base_price_adult DECIMAL(12, 2),
    IN p_base_price_child DECIMAL(12, 2),
    IN p_max_participants INT,
    IN p_start_date       DATE,
    IN p_end_date         DATE,
    IN p_created_by       CHAR(36),
    IN p_ip_address       VARCHAR(45)
)
BEGIN
    DECLARE v_tour_id   CHAR(36);
    DECLARE v_tour_code VARCHAR(50);

    SET v_tour_id = UUID();
    SET v_tour_code = CONCAT('TOUR-', UPPER(SUBSTRING(MD5(RAND()), 1, 6)));

    INSERT INTO tours (
        id, tour_code, title, description, category, destination,
        base_price_adult, base_price_child, max_participants, available_slots,
        start_date, end_date, status, created_by, created_at, updated_at
    )
    VALUES (
        v_tour_id, v_tour_code, p_title, p_description, p_category, p_destination,
        p_base_price_adult, p_base_price_child, p_max_participants, p_max_participants,
        p_start_date, p_end_date, 'DRAFT', p_created_by, NOW(), NOW()
    );

    INSERT INTO audit_logs (id, user_id, action, resource, resource_id, ip_address, created_at)
    VALUES (UUID(), p_created_by, 'TOUR_CREATED', 'tours', v_tour_id, p_ip_address, NOW());

    SELECT
        t.id AS tour_id,
        t.tour_code,
        t.title,
        t.description,
        t.category,
        t.destination,
        t.base_price_adult,
        t.base_price_child,
        t.max_participants,
        t.available_slots,
        t.start_date,
        t.end_date,
        t.status,
        t.created_by,
        t.created_at,
        t.updated_at
    FROM tours t
    WHERE t.id = v_tour_id;
END$$


-- ------------------------------------------------------------
-- 2.2: Thêm ngày lịch trình cho Tour
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_them_lich_trinh$$
CREATE PROCEDURE sp_them_lich_trinh(
    IN p_tour_id    CHAR(36),
    IN p_day_number INT,
    IN p_title      VARCHAR(500)
)
BEGIN
    DECLARE v_itin_id CHAR(36);
    SET v_itin_id = UUID();

    INSERT INTO itineraries (id, tour_id, day_number, title, created_at)
    VALUES (v_itin_id, p_tour_id, p_day_number, p_title, NOW());

    SELECT v_itin_id AS itinerary_id, p_tour_id AS tour_id, p_day_number AS day_number, p_title AS title;
END$$


-- ------------------------------------------------------------
-- 2.3: Thêm hoạt động chi tiết trong ngày lịch trình
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_them_hoat_dong$$
CREATE PROCEDURE sp_them_hoat_dong(
    IN p_itinerary_id CHAR(36),
    IN p_time_slot    TIME,
    IN p_place_name   VARCHAR(255),
    IN p_description  TEXT
)
BEGIN
    DECLARE v_act_id CHAR(36);
    SET v_act_id = UUID();

    INSERT INTO itinerary_activities (id, itinerary_id, time_slot, place_name, description, created_at)
    VALUES (v_act_id, p_itinerary_id, p_time_slot, p_place_name, p_description, NOW());

    SELECT v_act_id AS activity_id, p_itinerary_id AS itinerary_id, p_time_slot AS time_slot, p_place_name AS place_name, p_description AS description;
END$$


-- ------------------------------------------------------------
-- 2.4: Lấy chi tiết một Tour
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_lay_chi_tiet_tour$$
CREATE PROCEDURE sp_lay_chi_tiet_tour(
    IN p_tour_id CHAR(36)
)
BEGIN
    SELECT
        t.id AS tour_id,
        t.tour_code,
        t.title,
        t.description,
        t.category,
        t.destination,
        t.base_price_adult,
        t.base_price_child,
        t.max_participants,
        t.available_slots,
        t.start_date,
        t.end_date,
        t.status,
        t.created_by,
        t.created_at,
        t.updated_at
    FROM tours t
    WHERE t.id = p_tour_id;
END$$


-- ------------------------------------------------------------
-- 2.5: Lấy toàn bộ lịch trình và hoạt động của một Tour
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_lay_lich_trinh_tour$$
CREATE PROCEDURE sp_lay_lich_trinh_tour(
    IN p_tour_id CHAR(36)
)
BEGIN
    SELECT
        i.id AS itinerary_id,
        i.day_number,
        i.title AS itinerary_title,
        a.id AS activity_id,
        a.time_slot,
        a.place_name,
        a.description AS activity_desc
    FROM itineraries i
    LEFT JOIN itinerary_activities a ON a.itinerary_id = i.id
    WHERE i.tour_id = p_tour_id
    ORDER BY i.day_number ASC, a.time_slot ASC;
END$$


-- ------------------------------------------------------------
-- 2.6: Tìm kiếm và lọc danh sách Tour (phân trang)
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_tim_kiem_tour$$
CREATE PROCEDURE sp_tim_kiem_tour(
    IN p_destination     VARCHAR(255),
    IN p_category        VARCHAR(100),
    IN p_status          VARCHAR(30),
    IN p_min_price       DECIMAL(12, 2),
    IN p_max_price       DECIMAL(12, 2),
    IN p_start_date_from DATE,
    IN p_start_date_to   DATE,
    IN p_search          VARCHAR(255),
    IN p_skip            INT,
    IN p_limit           INT
)
BEGIN
    -- Lấy danh sách tour kèm total_count bằng subquery
    SELECT
        t.id AS tour_id,
        t.tour_code,
        t.title,
        t.category,
        t.destination,
        t.base_price_adult,
        t.base_price_child,
        t.max_participants,
        t.available_slots,
        t.start_date,
        t.end_date,
        t.status,
        t.created_at,
        (
            SELECT COUNT(*) FROM tours t2
            WHERE (p_destination IS NULL OR t2.destination LIKE CONCAT('%', p_destination, '%'))
              AND (p_category IS NULL OR t2.category = p_category)
              AND (p_status IS NULL OR t2.status = p_status)
              AND (p_min_price IS NULL OR t2.base_price_adult >= p_min_price)
              AND (p_max_price IS NULL OR t2.base_price_adult <= p_max_price)
              AND (p_start_date_from IS NULL OR t2.start_date >= p_start_date_from)
              AND (p_start_date_to IS NULL OR t2.start_date <= p_start_date_to)
              AND (p_search IS NULL OR t2.title LIKE CONCAT('%', p_search, '%') OR t2.description LIKE CONCAT('%', p_search, '%'))
        ) AS total_count
    FROM tours t
    WHERE (p_destination IS NULL OR t.destination LIKE CONCAT('%', p_destination, '%'))
      AND (p_category IS NULL OR t.category = p_category)
      AND (p_status IS NULL OR t.status = p_status)
      AND (p_min_price IS NULL OR t.base_price_adult >= p_min_price)
      AND (p_max_price IS NULL OR t.base_price_adult <= p_max_price)
      AND (p_start_date_from IS NULL OR t.start_date >= p_start_date_from)
      AND (p_start_date_to IS NULL OR t.start_date <= p_start_date_to)
      AND (p_search IS NULL OR t.title LIKE CONCAT('%', p_search, '%') OR t.description LIKE CONCAT('%', p_search, '%'))
    ORDER BY t.created_at DESC
    LIMIT p_skip, p_limit;
END$$


-- ------------------------------------------------------------
-- 2.7: Cập nhật thông tin Tour
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_cap_nhat_tour$$
CREATE PROCEDURE sp_cap_nhat_tour(
    IN p_tour_id           CHAR(36),
    IN p_title             VARCHAR(500),
    IN p_description       TEXT,
    IN p_category          VARCHAR(100),
    IN p_destination       VARCHAR(255),
    IN p_base_price_adult  DECIMAL(12, 2),
    IN p_base_price_child  DECIMAL(12, 2),
    IN p_max_participants  INT,
    IN p_start_date        DATE,
    IN p_end_date          DATE,
    IN p_user_id           CHAR(36),
    IN p_ip_address        VARCHAR(45)
)
BEGIN
    UPDATE tours
    SET
        title = COALESCE(p_title, title),
        description = COALESCE(p_description, description),
        category = COALESCE(p_category, category),
        destination = COALESCE(p_destination, destination),
        base_price_adult = COALESCE(p_base_price_adult, base_price_adult),
        base_price_child = COALESCE(p_base_price_child, base_price_child),
        max_participants = COALESCE(p_max_participants, max_participants),
        start_date = COALESCE(p_start_date, start_date),
        end_date = COALESCE(p_end_date, end_date),
        updated_at = NOW()
    WHERE id = p_tour_id;

    INSERT INTO audit_logs (id, user_id, action, resource, resource_id, ip_address, created_at)
    VALUES (UUID(), p_user_id, 'TOUR_UPDATED', 'tours', p_tour_id, p_ip_address, NOW());

    SELECT id AS tour_id, tour_code, title, status FROM tours WHERE id = p_tour_id;
END$$


-- ------------------------------------------------------------
-- 2.8: Xuất bản Tour (DRAFT -> PUBLISHED)
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_xuat_ban_tour$$
CREATE PROCEDURE sp_xuat_ban_tour(
    IN p_tour_id    CHAR(36),
    IN p_user_id    CHAR(36),
    IN p_ip_address VARCHAR(45)
)
BEGIN
    DECLARE v_status VARCHAR(30);
    SELECT status INTO v_status FROM tours WHERE id = p_tour_id;

    IF v_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Tour không tồn tại';
    END IF;

    UPDATE tours SET status = 'PUBLISHED', updated_at = NOW() WHERE id = p_tour_id;

    INSERT INTO audit_logs (id, user_id, action, resource, resource_id, ip_address, created_at)
    VALUES (UUID(), p_user_id, 'TOUR_PUBLISHED', 'tours', p_tour_id, p_ip_address, NOW());

    SELECT p_tour_id AS tour_id, 'PUBLISHED' AS status, 'Xuất bản tour thành công' AS message;
END$$


-- ------------------------------------------------------------
-- 2.9: Đóng Tour (PUBLISHED -> ARCHIVED)
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_dong_tour$$
CREATE PROCEDURE sp_dong_tour(
    IN p_tour_id    CHAR(36),
    IN p_user_id    CHAR(36),
    IN p_ip_address VARCHAR(45)
)
BEGIN
    UPDATE tours SET status = 'ARCHIVED', updated_at = NOW() WHERE id = p_tour_id;

    INSERT INTO audit_logs (id, user_id, action, resource, resource_id, ip_address, created_at)
    VALUES (UUID(), p_user_id, 'TOUR_ARCHIVED', 'tours', p_tour_id, p_ip_address, NOW());

    SELECT p_tour_id AS tour_id, 'ARCHIVED' AS status, 'Đóng tour thành công' AS message;
END$$


-- ------------------------------------------------------------
-- 2.10: Hủy Tour (-> CANCELLED)
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_huy_tour$$
CREATE PROCEDURE sp_huy_tour(
    IN p_tour_id    CHAR(36),
    IN p_user_id    CHAR(36),
    IN p_ip_address VARCHAR(45)
)
BEGIN
    UPDATE tours SET status = 'CANCELLED', updated_at = NOW() WHERE id = p_tour_id;

    -- Tự động hủy các booking đang chờ thanh toán
    UPDATE bookings SET status = 'CANCELLED', updated_at = NOW()
    WHERE tour_id = p_tour_id AND status = 'PENDING_PAYMENT';

    INSERT INTO audit_logs (id, user_id, action, resource, resource_id, ip_address, created_at)
    VALUES (UUID(), p_user_id, 'TOUR_CANCELLED', 'tours', p_tour_id, p_ip_address, NOW());

    SELECT p_tour_id AS tour_id, 'CANCELLED' AS status, 'Hủy tour thành công' AS message;
END$$


-- ████████████████████████████████████████████████████████████
-- PHẦN 3: THỦ TỤC ĐẶT TOUR (BOOKINGS - BẢO VỆ RACE CONDITION)
-- ████████████████████████████████████████████████████████████

-- ------------------------------------------------------------
-- 3.1: Tạo đơn đặt tour (Khóa dòng FOR UPDATE an toàn chỗ trống)
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_tao_don_dat_tour$$
CREATE PROCEDURE sp_tao_don_dat_tour(
    IN p_user_id          CHAR(36),
    IN p_tour_id          CHAR(36),
    IN p_num_adults       INT,
    IN p_num_children     INT,
    IN p_contact_name     VARCHAR(255),
    IN p_contact_email    VARCHAR(255),
    IN p_contact_phone    VARCHAR(20),
    IN p_special_requests TEXT,
    IN p_ip_address       VARCHAR(45)
)
BEGIN
    DECLARE v_tour_status     VARCHAR(30);
    DECLARE v_tour_title      VARCHAR(500);
    DECLARE v_price_adult     DECIMAL(12, 2);
    DECLARE v_price_child     DECIMAL(12, 2);
    DECLARE v_available_slots INT;
    DECLARE v_req_seats       INT;
    DECLARE v_total_price     DECIMAL(12, 2);
    DECLARE v_booking_id      CHAR(36);
    DECLARE v_booking_code    VARCHAR(50);

    -- 1. Khóa dòng tour bằng FOR UPDATE để loại bỏ race condition
    SELECT status, title, base_price_adult, base_price_child, available_slots
    INTO v_tour_status, v_tour_title, v_price_adult, v_price_child, v_available_slots
    FROM tours
    WHERE id = p_tour_id
    FOR UPDATE;

    IF v_tour_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Tour không tồn tại';
    END IF;

    IF v_tour_status != 'PUBLISHED' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Tour hiện không mở bán đặt chỗ';
    END IF;

    SET v_req_seats = p_num_adults + p_num_children;
    IF v_available_slots < v_req_seats THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Tour không đủ số chỗ trống yêu cầu';
    END IF;

    -- 2. Tính tiền và trừ số chỗ trống
    SET v_total_price = (p_num_adults * v_price_adult) + (p_num_children * v_price_child);
    SET v_booking_id = UUID();
    SET v_booking_code = CONCAT('BK-', DATE_FORMAT(NOW(), '%Y%m%d'), '-', UPPER(SUBSTRING(MD5(RAND()), 1, 6)));

    -- Trừ số chỗ còn trống
    UPDATE tours SET available_slots = available_slots - v_req_seats WHERE id = p_tour_id;

    -- Lưu đơn đặt tour
    INSERT INTO bookings (
        id, booking_code, user_id, tour_id, status, num_adults, num_children,
        total_price, contact_name, contact_email, contact_phone, special_requests,
        created_at, updated_at
    )
    VALUES (
        v_booking_id, v_booking_code, p_user_id, p_tour_id, 'PENDING_PAYMENT',
        p_num_adults, p_num_children, v_total_price, p_contact_name, p_contact_email,
        p_contact_phone, p_special_requests, NOW(), NOW()
    );

    -- Ghi nhật ký
    INSERT INTO audit_logs (id, user_id, action, resource, resource_id, ip_address, created_at)
    VALUES (UUID(), p_user_id, 'BOOKING_CREATED', 'bookings', v_booking_id, p_ip_address, NOW());

    -- Trả về thông tin đơn vừa tạo
    SELECT
        b.id AS booking_id,
        b.booking_code,
        b.tour_id,
        v_tour_title AS tour_title,
        b.status,
        b.num_adults,
        b.num_children,
        b.total_price,
        b.contact_name,
        b.contact_email,
        b.contact_phone,
        b.special_requests,
        b.created_at
    FROM bookings b
    WHERE b.id = v_booking_id;
END$$


-- ------------------------------------------------------------
-- 3.2: Thêm hành khách vào đơn đặt tour
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_them_hanh_khach$$
CREATE PROCEDURE sp_them_hanh_khach(
    IN p_booking_id     CHAR(36),
    IN p_full_name      VARCHAR(255),
    IN p_passenger_type VARCHAR(20),
    IN p_id_card_number VARCHAR(50)
)
BEGIN
    DECLARE v_id CHAR(36);
    SET v_id = UUID();

    INSERT INTO booking_passengers (id, booking_id, full_name, passenger_type, id_card_number, created_at)
    VALUES (v_id, p_booking_id, p_full_name, p_passenger_type, p_id_card_number, NOW());

    SELECT v_id AS passenger_id, p_booking_id AS booking_id, p_full_name AS full_name, p_passenger_type AS passenger_type, p_id_card_number AS id_card_number;
END$$


-- ------------------------------------------------------------
-- 3.3: Xem chi tiết đơn đặt tour
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_lay_chi_tiet_booking$$
CREATE PROCEDURE sp_lay_chi_tiet_booking(
    IN p_booking_id CHAR(36)
)
BEGIN
    SELECT
        b.id AS booking_id,
        b.booking_code,
        b.user_id,
        b.tour_id,
        t.title AS tour_title,
        b.status,
        b.num_adults,
        b.num_children,
        b.total_price,
        b.contact_name,
        b.contact_email,
        b.contact_phone,
        b.special_requests,
        b.created_at,
        b.updated_at
    FROM bookings b
    JOIN tours t ON t.id = b.tour_id
    WHERE b.id = p_booking_id;
END$$


-- ------------------------------------------------------------
-- 3.4: Lấy danh sách hành khách của 1 đơn đặt tour
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_lay_hanh_khach_booking$$
CREATE PROCEDURE sp_lay_hanh_khach_booking(
    IN p_booking_id CHAR(36)
)
BEGIN
    SELECT
        bp.id AS passenger_id,
        bp.full_name,
        bp.passenger_type,
        bp.id_card_number
    FROM booking_passengers bp
    WHERE bp.booking_id = p_booking_id
    ORDER BY bp.created_at ASC;
END$$


-- ------------------------------------------------------------
-- 3.5: Lấy danh sách đơn đặt tour của cá nhân (phân trang)
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_lay_booking_cua_toi$$
CREATE PROCEDURE sp_lay_booking_cua_toi(
    IN p_user_id CHAR(36),
    IN p_skip    INT,
    IN p_limit   INT
)
BEGIN
    SELECT
        b.id AS booking_id,
        b.booking_code,
        b.tour_id,
        t.title AS tour_title,
        b.status,
        b.num_adults,
        b.num_children,
        b.total_price,
        b.contact_name,
        b.created_at,
        (SELECT COUNT(*) FROM bookings b2 WHERE b2.user_id = p_user_id) AS total_count
    FROM bookings b
    JOIN tours t ON t.id = b.tour_id
    WHERE b.user_id = p_user_id
    ORDER BY b.created_at DESC
    LIMIT p_skip, p_limit;
END$$


-- ------------------------------------------------------------
-- 3.6: Xem toàn bộ đơn đặt tour trong hệ thống (Admin / Staff)
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_lay_tat_ca_booking$$
CREATE PROCEDURE sp_lay_tat_ca_booking(
    IN p_skip    INT,
    IN p_limit   INT,
    IN p_status  VARCHAR(30),
    IN p_tour_id CHAR(36)
)
BEGIN
    SELECT
        b.id AS booking_id,
        b.booking_code,
        b.user_id,
        b.tour_id,
        t.title AS tour_title,
        b.status,
        b.num_adults,
        b.num_children,
        b.total_price,
        b.contact_name,
        b.created_at,
        (
            SELECT COUNT(*) FROM bookings b2
            WHERE (p_status IS NULL OR b2.status = p_status)
              AND (p_tour_id IS NULL OR b2.tour_id = p_tour_id)
        ) AS total_count
    FROM bookings b
    JOIN tours t ON t.id = b.tour_id
    WHERE (p_status IS NULL OR b.status = p_status)
      AND (p_tour_id IS NULL OR b.tour_id = p_tour_id)
    ORDER BY b.created_at DESC
    LIMIT p_skip, p_limit;
END$$


-- ------------------------------------------------------------
-- 3.7: Hủy đơn đặt tour và tự động hoàn trả chỗ trống cho Tour
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_huy_don_dat_tour$$
CREATE PROCEDURE sp_huy_don_dat_tour(
    IN p_booking_id       CHAR(36),
    IN p_current_user_id  CHAR(36),
    IN p_is_admin         BOOLEAN,
    IN p_ip_address       VARCHAR(45)
)
BEGIN
    DECLARE v_user_id  CHAR(36);
    DECLARE v_status   VARCHAR(30);
    DECLARE v_tour_id  CHAR(36);
    DECLARE v_seats    INT;
    DECLARE v_code     VARCHAR(50);

    SELECT user_id, status, tour_id, (num_adults + num_children), booking_code
    INTO v_user_id, v_status, v_tour_id, v_seats, v_code
    FROM bookings
    WHERE id = p_booking_id
    FOR UPDATE;

    IF v_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Đơn đặt tour không tồn tại';
    END IF;

    IF NOT p_is_admin AND v_user_id != p_current_user_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Bạn không có quyền hủy đơn đặt tour này';
    END IF;

    IF v_status = 'CANCELLED' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Đơn đặt tour này đã bị hủy trước đó rồi';
    END IF;

    -- Cập nhật trạng thái hủy
    UPDATE bookings SET status = 'CANCELLED', updated_at = NOW() WHERE id = p_booking_id;

    -- Hoàn trả số chỗ cho tour
    IF v_status IN ('PENDING_PAYMENT', 'CONFIRMED') THEN
        UPDATE tours SET available_slots = available_slots + v_seats WHERE id = v_tour_id;
    END IF;

    INSERT INTO audit_logs (id, user_id, action, resource, resource_id, ip_address, created_at)
    VALUES (UUID(), p_current_user_id, 'BOOKING_CANCELLED', 'bookings', p_booking_id, p_ip_address, NOW());

    SELECT p_booking_id AS booking_id, v_code AS booking_code, 'CANCELLED' AS status, 'Hủy đơn đặt tour thành công' AS message;
END$$


-- ------------------------------------------------------------
-- 3.8: Xác nhận duyệt đơn đặt tour (Admin / Staff)
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_xac_nhan_don_dat_tour$$
CREATE PROCEDURE sp_xac_nhan_don_dat_tour(
    IN p_booking_id CHAR(36),
    IN p_admin_id   CHAR(36),
    IN p_ip_address VARCHAR(45)
)
BEGIN
    UPDATE bookings SET status = 'CONFIRMED', updated_at = NOW() WHERE id = p_booking_id;

    INSERT INTO audit_logs (id, user_id, action, resource, resource_id, ip_address, created_at)
    VALUES (UUID(), p_admin_id, 'BOOKING_CONFIRMED', 'bookings', p_booking_id, p_ip_address, NOW());

    SELECT p_booking_id AS booking_id, 'CONFIRMED' AS status, 'Xác nhận duyệt đơn thành công' AS message;
END$$


-- ------------------------------------------------------------
-- 3.9: Ghi nhật ký chung (Audit Log)
-- ------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_ghi_nhat_ky$$
CREATE PROCEDURE sp_ghi_nhat_ky(
    IN p_user_id     CHAR(36),
    IN p_action      VARCHAR(100),
    IN p_resource    VARCHAR(100),
    IN p_resource_id VARCHAR(100),
    IN p_details     JSON,
    IN p_ip_address  VARCHAR(45)
)
BEGIN
    DECLARE v_log_id CHAR(36);
    SET v_log_id = UUID();

    INSERT INTO audit_logs (id, user_id, action, resource, resource_id, details, ip_address, created_at)
    VALUES (v_log_id, p_user_id, p_action, p_resource, p_resource_id, p_details, p_ip_address, NOW());

    SELECT v_log_id AS log_id;
END$$

DELIMITER ;
