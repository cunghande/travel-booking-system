USE `travel_booking`;

DELIMITER $$

-- ============================================================
-- 1. Lấy danh sách tour (lọc theo destination, category, status)
-- ============================================================
DROP PROCEDURE IF EXISTS `sp_get_tours`$$
CREATE PROCEDURE `sp_get_tours`(
    IN  p_destination   VARCHAR(255),
    IN  p_category      VARCHAR(100),
    IN  p_status        VARCHAR(20),
    IN  p_limit         INT,
    IN  p_offset        INT,
    OUT p_total         INT
)
BEGIN
    -- Đếm tổng số tour thỏa điều kiện
    SELECT COUNT(*) INTO p_total
    FROM `tours`
    WHERE
        (p_destination IS NULL OR `destination` LIKE CONCAT('%', p_destination, '%'))
        AND (p_category   IS NULL OR `category`    = p_category)
        AND (p_status     IS NULL OR `status`      = p_status)
        AND (`status` != 'CANCELLED');

    -- Lấy danh sách tour theo trang
    SELECT *
    FROM `tours`
    WHERE
        (p_destination IS NULL OR `destination` LIKE CONCAT('%', p_destination, '%'))
        AND (p_category   IS NULL OR `category`    = p_category)
        AND (p_status     IS NULL OR `status`      = p_status)
        AND (`status` != 'CANCELLED')
    ORDER BY `created_at` DESC
    LIMIT p_limit OFFSET p_offset;
END$$


-- ============================================================
-- 2. Lấy chi tiết 1 tour theo ID
-- ============================================================
DROP PROCEDURE IF EXISTS `sp_get_tour_by_id`$$
CREATE PROCEDURE `sp_get_tour_by_id`(
    IN p_tour_id VARCHAR(36)
)
BEGIN
    -- Thông tin tour
    SELECT * FROM `tours` WHERE `id` = p_tour_id;

    -- Lịch trình theo ngày
    SELECT * FROM `itineraries`
    WHERE `tour_id` = p_tour_id
    ORDER BY `day_number`;

    -- Hoạt động chi tiết
    SELECT a.* FROM `activities` a
    JOIN `itineraries` i ON a.`itinerary_id` = i.`id`
    WHERE i.`tour_id` = p_tour_id
    ORDER BY i.`day_number`, a.`time_slot`;
END$$


-- ============================================================
-- 3. Tạo tour mới
-- ============================================================
DROP PROCEDURE IF EXISTS `sp_create_tour`$$
CREATE PROCEDURE `sp_create_tour`(
    IN p_id                 CHAR(36),
    IN p_tour_code          VARCHAR(50),
    IN p_title              VARCHAR(500),
    IN p_description        TEXT,
    IN p_category           VARCHAR(100),
    IN p_destination        VARCHAR(255),
    IN p_base_price_adult   DECIMAL(12,2),
    IN p_base_price_child   DECIMAL(12,2),
    IN p_max_participants   INT,
    IN p_start_date         DATE,
    IN p_end_date           DATE,
    IN p_created_by         CHAR(36)
)
BEGIN
    -- Kiểm tra mã tour có bị trùng không
    IF EXISTS (SELECT 1 FROM `tours` WHERE `tour_code` = p_tour_code) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Mã tour đã tồn tại';
    END IF;

    INSERT INTO `tours`
        (id, tour_code, title, description, category, destination,
         base_price_adult, base_price_child, max_participants, available_slots,
         start_date, end_date, status, created_by)
    VALUES
        (p_id, p_tour_code, p_title, p_description, p_category, p_destination,
         p_base_price_adult, p_base_price_child, p_max_participants, p_max_participants,
         p_start_date, p_end_date, 'DRAFT', p_created_by);

    -- Trả về tour vừa tạo
    SELECT * FROM `tours` WHERE `id` = p_id;
END$$


-- ============================================================
-- 4. Cập nhật thông tin tour
-- ============================================================
DROP PROCEDURE IF EXISTS `sp_update_tour`$$
CREATE PROCEDURE `sp_update_tour`(
    IN p_tour_id            CHAR(36),
    IN p_title              VARCHAR(500),
    IN p_description        TEXT,
    IN p_category           VARCHAR(100),
    IN p_destination        VARCHAR(255),
    IN p_base_price_adult   DECIMAL(12,2),
    IN p_base_price_child   DECIMAL(12,2),
    IN p_max_participants   INT,
    IN p_start_date         DATE,
    IN p_end_date           DATE,
    IN p_status             VARCHAR(20)
)
BEGIN
    IF NOT EXISTS (SELECT 1 FROM `tours` WHERE `id` = p_tour_id) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Tour không tồn tại';
    END IF;

    UPDATE `tours` SET
        `title`            = COALESCE(p_title,            `title`),
        `description`      = COALESCE(p_description,      `description`),
        `category`         = COALESCE(p_category,         `category`),
        `destination`      = COALESCE(p_destination,      `destination`),
        `base_price_adult` = COALESCE(p_base_price_adult, `base_price_adult`),
        `base_price_child` = COALESCE(p_base_price_child, `base_price_child`),
        `max_participants` = COALESCE(p_max_participants,  `max_participants`),
        `start_date`       = COALESCE(p_start_date,       `start_date`),
        `end_date`         = COALESCE(p_end_date,         `end_date`),
        `status`           = COALESCE(p_status,           `status`),
        `updated_at`       = CURRENT_TIMESTAMP
    WHERE `id` = p_tour_id;

    SELECT * FROM `tours` WHERE `id` = p_tour_id;
END$$


-- ============================================================
-- 5. Hủy tour (Soft delete — đổi status thành CANCELLED)
-- ============================================================
DROP PROCEDURE IF EXISTS `sp_cancel_tour`$$
CREATE PROCEDURE `sp_cancel_tour`(
    IN p_tour_id CHAR(36)
)
BEGIN
    IF NOT EXISTS (SELECT 1 FROM `tours` WHERE `id` = p_tour_id) THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Tour không tồn tại';
    END IF;

    UPDATE `tours` SET
        `status` = 'CANCELLED',
        `updated_at` = CURRENT_TIMESTAMP
    WHERE `id` = p_tour_id;
END$$


-- ============================================================
-- 6. Thêm 1 itinerary (lịch trình ngày) vào tour
-- ============================================================
DROP PROCEDURE IF EXISTS `sp_add_itinerary`$$
CREATE PROCEDURE `sp_add_itinerary`(
    IN p_id         CHAR(36),
    IN p_tour_id    CHAR(36),
    IN p_day_number INT,
    IN p_title      VARCHAR(500)
)
BEGIN
    INSERT INTO `itineraries` (id, tour_id, day_number, title)
    VALUES (p_id, p_tour_id, p_day_number, p_title);

    SELECT * FROM `itineraries` WHERE `id` = p_id;
END$$


-- ============================================================
-- 7. Thêm 1 activity (hoạt động) vào itinerary
-- ============================================================
DROP PROCEDURE IF EXISTS `sp_add_activity`$$
CREATE PROCEDURE `sp_add_activity`(
    IN p_id             CHAR(36),
    IN p_itinerary_id   CHAR(36),
    IN p_time_slot      TIME,
    IN p_place_name     VARCHAR(255),
    IN p_description    TEXT,
    IN p_latitude       DECIMAL(10,8),
    IN p_longitude      DECIMAL(11,8)
)
BEGIN
    INSERT INTO `activities`
        (id, itinerary_id, time_slot, place_name, description, latitude, longitude)
    VALUES
        (p_id, p_itinerary_id, p_time_slot, p_place_name, p_description, p_latitude, p_longitude);

    SELECT * FROM `activities` WHERE `id` = p_id;
END$$


DELIMITER ;
