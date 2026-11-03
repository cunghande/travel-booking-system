USE `travel_booking`;

DELIMITER $$

-- ============================================================
-- 1. Tạo đơn đặt tour (Kiểm tra slot, tự tính tiền, trừ slot)
-- ============================================================
DROP PROCEDURE IF EXISTS `sp_create_booking`$$
CREATE PROCEDURE `sp_create_booking`(
    IN  p_id               CHAR(36),
    IN  p_booking_code     VARCHAR(50),
    IN  p_user_id          CHAR(36),
    IN  p_tour_id          CHAR(36),
    IN  p_num_adults       INT,
    IN  p_num_children     INT,
    IN  p_contact_name     VARCHAR(255),
    IN  p_contact_email    VARCHAR(255),
    IN  p_contact_phone    VARCHAR(20),
    IN  p_special_requests TEXT
)
BEGIN
    DECLARE v_adult_price  DECIMAL(12,2);
    DECLARE v_child_price  DECIMAL(12,2);
    DECLARE v_avail_slots  INT;
    DECLARE v_tour_status  VARCHAR(20);
    DECLARE v_needed_slots INT;
    DECLARE v_total_price  DECIMAL(12,2);

    -- Khóa dòng dữ liệu của tour để tránh Race Condition khi nhiều người cùng đặt vé
    SELECT 
        `base_price_adult`, `base_price_child`, `available_slots`, `status`
    INTO 
        v_adult_price, v_child_price, v_avail_slots, v_tour_status
    FROM `tours`
    WHERE `id` = p_tour_id
    FOR UPDATE;

    -- Kiểm tra tour có tồn tại không
    IF v_tour_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Tour không tồn tại';
    END IF;

    -- Kiểm tra trạng thái tour
    IF v_tour_status = 'CANCELLED' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Tour này đã bị hủy, không thể đặt vé';
    END IF;

    -- Kiểm tra số chỗ còn trống
    SET v_needed_slots = p_num_adults + p_num_children;
    IF v_avail_slots < v_needed_slots THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Tour không đủ chỗ trống cho số lượng khách yêu cầu';
    END IF;

    -- Tự động tính tổng tiền theo đơn giá từ bảng tours
    SET v_total_price = (p_num_adults * v_adult_price) + (p_num_children * v_child_price);

    -- 1. Tạo bản ghi booking (mặc định trạng thái PENDING)
    INSERT INTO `bookings` (
        `id`, `booking_code`, `user_id`, `tour_id`, `status`,
        `num_adults`, `num_children`, `total_price`,
        `contact_name`, `contact_email`, `contact_phone`, `special_requests`
    ) VALUES (
        p_id, p_booking_code, p_user_id, p_tour_id, 'PENDING',
        p_num_adults, p_num_children, v_total_price,
        p_contact_name, p_contact_email, p_contact_phone, p_special_requests
    );

    -- 2. Trừ bớt chỗ trống của tour
    UPDATE `tours`
    SET `available_slots` = `available_slots` - v_needed_slots
    WHERE `id` = p_tour_id;

    -- Trả về đơn booking vừa tạo
    SELECT * FROM `bookings` WHERE `id` = p_id;
END$$


-- ============================================================
-- 2. Thêm hành khách đi kèm vào đơn đặt tour
-- ============================================================
DROP PROCEDURE IF EXISTS `sp_add_booking_passenger`$$
CREATE PROCEDURE `sp_add_booking_passenger`(
    IN p_id             CHAR(36),
    IN p_booking_id     CHAR(36),
    IN p_full_name      VARCHAR(255),
    IN p_passenger_type VARCHAR(20),
    IN p_id_card_number VARCHAR(50)
)
BEGIN
    INSERT INTO `booking_passengers` (
        `id`, `booking_id`, `full_name`, `passenger_type`, `id_card_number`
    ) VALUES (
        p_id, p_booking_id, p_full_name, p_passenger_type, p_id_card_number
    );

    SELECT * FROM `booking_passengers` WHERE `id` = p_id;
END$$


-- ============================================================
-- 3. Lấy chi tiết đơn đặt vé kèm thông tin tour và danh sách khách
-- ============================================================
DROP PROCEDURE IF EXISTS `sp_get_booking_by_id`$$
CREATE PROCEDURE `sp_get_booking_by_id`(
    IN p_booking_id CHAR(36)
)
BEGIN
    -- Result set 1: Thông tin booking + tóm tắt thông tin tour
    SELECT 
        b.*,
        t.`title` AS `tour_title`,
        t.`tour_code` AS `tour_code`,
        t.`destination` AS `tour_destination`,
        t.`start_date` AS `tour_start_date`,
        t.`end_date` AS `tour_end_date`
    FROM `bookings` b
    JOIN `tours` t ON b.`tour_id` = t.`id`
    WHERE b.`id` = p_booking_id;

    -- Result set 2: Danh sách hành khách đi cùng
    SELECT * 
    FROM `booking_passengers`
    WHERE `booking_id` = p_booking_id
    ORDER BY `created_at` ASC;
END$$


-- ============================================================
-- 4. Lấy danh sách vé đã đặt của 1 khách hàng cụ thể
-- ============================================================
DROP PROCEDURE IF EXISTS `sp_get_user_bookings`$$
CREATE PROCEDURE `sp_get_user_bookings`(
    IN p_user_id CHAR(36)
)
BEGIN
    SELECT 
        b.*,
        t.`title` AS `tour_title`,
        t.`tour_code` AS `tour_code`,
        t.`destination` AS `tour_destination`,
        t.`start_date` AS `tour_start_date`,
        t.`end_date` AS `tour_end_date`
    FROM `bookings` b
    JOIN `tours` t ON b.`tour_id` = t.`id`
    WHERE b.`user_id` = p_user_id
    ORDER BY b.`created_at` DESC;
END$$


-- ============================================================
-- 5. Lấy toàn bộ đơn đặt vé (ADMIN / STAFF quản lý, có phân trang)
-- ============================================================
DROP PROCEDURE IF EXISTS `sp_get_all_bookings`$$
CREATE PROCEDURE `sp_get_all_bookings`(
    IN  p_status VARCHAR(20),
    IN  p_limit  INT,
    IN  p_offset INT,
    OUT p_total  INT
)
BEGIN
    -- Đếm tổng số đơn thỏa điều kiện
    SELECT COUNT(*) INTO p_total
    FROM `bookings`
    WHERE (p_status IS NULL OR `status` = p_status);

    -- Lấy danh sách phân trang
    SELECT 
        b.*,
        t.`title` AS `tour_title`,
        t.`tour_code` AS `tour_code`,
        t.`destination` AS `tour_destination`,
        t.`start_date` AS `tour_start_date`,
        t.`end_date` AS `tour_end_date`
    FROM `bookings` b
    JOIN `tours` t ON b.`tour_id` = t.`id`
    WHERE (p_status IS NULL OR b.`status` = p_status)
    ORDER BY b.`created_at` DESC
    LIMIT p_limit OFFSET p_offset;
END$$


-- ============================================================
-- 6. Hủy đơn đặt vé (Đổi status thành CANCELLED & HOÀN LẠI CHỖ TRỐNG)
-- ============================================================
DROP PROCEDURE IF EXISTS `sp_cancel_booking`$$
CREATE PROCEDURE `sp_cancel_booking`(
    IN p_booking_id CHAR(36)
)
BEGIN
    DECLARE v_tour_id      CHAR(36);
    DECLARE v_curr_status  VARCHAR(20);
    DECLARE v_seats        INT;

    -- Khóa bản ghi booking để kiểm tra
    SELECT 
        `tour_id`, `status`, (`num_adults` + `num_children`)
    INTO 
        v_tour_id, v_curr_status, v_seats
    FROM `bookings`
    WHERE `id` = p_booking_id
    FOR UPDATE;

    IF v_curr_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Đơn đặt không tồn tại';
    END IF;

    IF v_curr_status = 'CANCELLED' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Đơn đặt này đã bị hủy trước đó';
    END IF;

    -- 1. Cập nhật trạng thái booking sang CANCELLED
    UPDATE `bookings`
    SET `status` = 'CANCELLED', `updated_at` = CURRENT_TIMESTAMP
    WHERE `id` = p_booking_id;

    -- 2. Hoàn trả lại số chỗ trống cho Tour
    UPDATE `tours`
    SET `available_slots` = `available_slots` + v_seats
    WHERE `id` = v_tour_id;

    SELECT * FROM `bookings` WHERE `id` = p_booking_id;
END$$


-- ============================================================
-- 7. Cập nhật trạng thái đơn (CONFIRMED / COMPLETED)
-- ============================================================
DROP PROCEDURE IF EXISTS `sp_update_booking_status`$$
CREATE PROCEDURE `sp_update_booking_status`(
    IN p_booking_id CHAR(36),
    IN p_new_status VARCHAR(20)
)
BEGIN
    IF NOT EXISTS (SELECT 1 FROM `bookings` WHERE `id` = p_booking_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Đơn đặt không tồn tại';
    END IF;

    UPDATE `bookings`
    SET `status` = p_new_status, `updated_at` = CURRENT_TIMESTAMP
    WHERE `id` = p_booking_id;

    SELECT * FROM `bookings` WHERE `id` = p_booking_id;
END$$

DELIMITER ;
