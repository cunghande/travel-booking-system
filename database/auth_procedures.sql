-- ============================================================
-- Travel Booking System — Stored Procedures cho Auth Service
-- Chạy file này sau khi đã chạy shema.sql
-- ============================================================

USE `travel_booking`;

DROP PROCEDURE IF EXISTS `sp_register_user`;
DROP PROCEDURE IF EXISTS `sp_get_user_by_email`;
DROP PROCEDURE IF EXISTS `sp_get_user_by_id`;

DELIMITER $$

-- Đăng ký người dùng mới: kiểm tra email trùng, tạo user, gán role CUSTOMER
CREATE PROCEDURE `sp_register_user`(
    IN p_id           VARCHAR(36),
    IN p_email        VARCHAR(255),
    IN p_hashed_pwd   VARCHAR(255),
    IN p_full_name    VARCHAR(255),
    IN p_phone        VARCHAR(20)
)
BEGIN
    DECLARE v_role_id      INT;
    DECLARE v_email_exists INT DEFAULT 0;

    SELECT COUNT(*) INTO v_email_exists FROM `users` WHERE `email` = p_email;
    IF v_email_exists > 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Email đã tồn tại trong hệ thống';
    END IF;

    INSERT INTO `users` (`id`, `email`, `hashed_password`, `full_name`, `phone_number`, `is_active`)
    VALUES (p_id, p_email, p_hashed_pwd, p_full_name, p_phone, 1);

    SELECT `id` INTO v_role_id FROM `roles` WHERE `name` = 'CUSTOMER' LIMIT 1;

    IF v_role_id IS NULL THEN
        INSERT INTO `roles` (`name`, `description`) VALUES ('CUSTOMER', 'Khách hàng đặt tour');
        SET v_role_id = LAST_INSERT_ID();
    END IF;

    INSERT INTO `user_roles` (`user_id`, `role_id`) VALUES (p_id, v_role_id);
END $$


-- Lấy thông tin user theo email (dùng cho đăng nhập, trả về cả hashed_password)
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
    JOIN `roles`      r  ON ur.`role_id` = r.`id`
    WHERE u.`email` = p_email
    LIMIT 1;
END $$


-- Lấy thông tin user theo ID (dùng cho /me và refresh token)
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
    JOIN `roles`      r  ON ur.`role_id` = r.`id`
    WHERE u.`id` = p_user_id
    LIMIT 1;
END $$

DELIMITER ;
