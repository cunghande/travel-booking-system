-- ============================================================
-- Travel Booking System — Stored Procedures cho Auth Service
-- Quản lý toàn bộ nghiệp vụ dữ liệu cho Đăng ký / Đăng nhập
-- ============================================================

USE `travel_booking`;

-- Xóa thủ tục cũ nếu đã tồn tại để tránh xung đột
DROP PROCEDURE IF EXISTS `sp_register_user`;
DROP PROCEDURE IF EXISTS `sp_get_user_by_email`;
DROP PROCEDURE IF EXISTS `sp_get_user_by_id`;

DELIMITER $$

-- ------------------------------------------------------------
-- 1. Thủ tục Đăng ký người dùng mới (sp_register_user)
-- Chức năng:
-- - Kiểm tra trùng email (Nếu đã có -> Báo lỗi)
-- - Tạo bản ghi trong bảng `users`
-- - Tự động gán quyền mặc định là 'CUSTOMER' trong `user_roles`
-- ------------------------------------------------------------
CREATE PROCEDURE `sp_register_user`(
    IN p_id VARCHAR(36),
    IN p_email VARCHAR(255),
    IN p_hashed_password VARCHAR(255),
    IN p_full_name VARCHAR(255),
    IN p_phone_number VARCHAR(20)
)
BEGIN
    DECLARE v_role_id INT;
    DECLARE v_email_exists INT DEFAULT 0;

    -- 1. Kiểm tra xem email đã được đăng ký chưa
    SELECT COUNT(*) INTO v_email_exists FROM `users` WHERE `email` = p_email;
    IF v_email_exists > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Email đã tồn tại trong hệ thống';
    END IF;

    -- 2. Thêm người dùng mới vào bảng users
    INSERT INTO `users` (`id`, `email`, `hashed_password`, `full_name`, `phone_number`, `is_active`)
    VALUES (p_id, p_email, p_hashed_password, p_full_name, p_phone_number, 1);

    -- 3. Tìm role_id của quyền 'CUSTOMER'
    SELECT `id` INTO v_role_id FROM `roles` WHERE `name` = 'CUSTOMER' LIMIT 1;

    -- Nếu chưa có role CUSTOMER thì tạo mặc định
    IF v_role_id IS NULL THEN
        INSERT INTO `roles` (`name`, `description`) VALUES ('CUSTOMER', 'Khách hàng đặt tour');
        SET v_role_id = LAST_INSERT_ID();
    END IF;

    -- 4. Gán quyền CUSTOMER cho người dùng mới trong bảng user_roles
    INSERT INTO `user_roles` (`user_id`, `role_id`) VALUES (p_id, v_role_id);

END $$


-- ------------------------------------------------------------
-- 2. Thủ tục Lấy thông tin User theo Email để Đăng nhập (sp_get_user_by_email)
-- Chức năng:
-- - Lấy thông tin user kèm theo hashed_password và Tên Role (ADMIN, CUSTOMER...)
-- ------------------------------------------------------------
CREATE PROCEDURE `sp_get_user_by_email`(
    IN p_email VARCHAR(255)
)
BEGIN
    SELECT 
        u.`id`,
        u.`email`,
        u.`hashed_password`,
        u.`full_name`,
        u.`phone_number`,
        u.`is_active`,
        r.`name` AS `role`
    FROM `users` u
    JOIN `user_roles` ur ON u.`id` = ur.`user_id`
    JOIN `roles` r ON ur.`role_id` = r.`id`
    WHERE u.`email` = p_email
    LIMIT 1;
END $$


-- ------------------------------------------------------------
-- 3. Thủ tục Lấy thông tin User theo ID (sp_get_user_by_id)
-- Chức năng:
-- - Dùng cho API xem thông tin cá nhân (/me) hoặc xác thực token
-- ------------------------------------------------------------
CREATE PROCEDURE `sp_get_user_by_id`(
    IN p_user_id VARCHAR(36)
)
BEGIN
    SELECT 
        u.`id`,
        u.`email`,
        u.`full_name`,
        u.`phone_number`,
        u.`is_active`,
        r.`name` AS `role`
    FROM `users` u
    JOIN `user_roles` ur ON u.`id` = ur.`user_id`
    JOIN `roles` r ON ur.`role_id` = r.`id`
    WHERE u.`id` = p_user_id
    LIMIT 1;
END $$

DELIMITER ;
