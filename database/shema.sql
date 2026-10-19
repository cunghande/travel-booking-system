-- 1. Tạo database
CREATE DATABASE IF NOT EXISTS `travel_booking`
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE `travel_booking`;
-- 2. Bảng roles
CREATE TABLE IF NOT EXISTS `roles` (
    `id`          INT AUTO_INCREMENT PRIMARY KEY,
    `name`        VARCHAR(50)  NOT NULL UNIQUE COMMENT 'ADMIN | STAFF | TOUR_GUIDE | CUSTOMER',
    `description` VARCHAR(255) NULL,
    `created_at`  DATETIME     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- 3. Bảng users — Tài khoản người dùng
CREATE TABLE IF NOT EXISTS `users` (
    `id`              CHAR(36)     PRIMARY KEY COMMENT 'UUID v4',
    `email`           VARCHAR(255) NOT NULL UNIQUE,
    `hashed_password` VARCHAR(255) NOT NULL,
    `full_name`       VARCHAR(255) NOT NULL,
    `phone_number`    VARCHAR(20)  NULL,
    `is_active`       TINYINT(1)   NOT NULL DEFAULT 1,
    `created_at`      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    `updated_at`      DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- 4. Bảng user_roles — Liên kết User và Role
CREATE TABLE IF NOT EXISTS `user_roles` (
    `user_id` CHAR(36) NOT NULL,
    `role_id` INT      NOT NULL,
    PRIMARY KEY (`user_id`, `role_id`),
    CONSTRAINT `fk_ur_user` FOREIGN KEY (`user_id`) REFERENCES `users`  (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_ur_role` FOREIGN KEY (`role_id`) REFERENCES `roles`  (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- 5. Bảng tours — Tour du lịch
CREATE TABLE IF NOT EXISTS `tours` (
    `id`                CHAR(36)      PRIMARY KEY COMMENT 'UUID v4',
    `tour_code`         VARCHAR(50)   NOT NULL UNIQUE COMMENT 'Mã tour duy nhất, vd: TOUR-202610-001',
    `title`             VARCHAR(500)  NOT NULL,
    `description`       TEXT          NULL,
    `category`          VARCHAR(100)  NULL COMMENT 'Biển đảo | Nghỉ dưỡng | Leo núi...',
    `destination`       VARCHAR(255)  NOT NULL,
    `base_price_adult`  DECIMAL(12,2) NOT NULL,
    `base_price_child`  DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    `max_participants`  INT           NOT NULL DEFAULT 20,
    `available_slots`   INT           NOT NULL DEFAULT 20,
    `start_date`        DATE          NOT NULL,
    `end_date`          DATE          NOT NULL,
    `status`            VARCHAR(20)   NOT NULL DEFAULT 'DRAFT' COMMENT 'DRAFT | PUBLISHED | ARCHIVED | CANCELLED',
    `created_by`        CHAR(36)      NULL,
    `created_at`        DATETIME      DEFAULT CURRENT_TIMESTAMP,
    `updated_at`        DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_tours_status`      (`status`),
    INDEX `idx_tours_destination` (`destination`),
    INDEX `idx_tours_start_date`  (`start_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- 6. Bảng itineraries — Lịch trình từng ngày của Tour
CREATE TABLE IF NOT EXISTS `itineraries` (
    `id`         CHAR(36)     PRIMARY KEY,
    `tour_id`    CHAR(36)     NOT NULL,
    `day_number` INT          NOT NULL COMMENT 'Ngày 1, 2, 3...',
    `title`      VARCHAR(500) NOT NULL,
    `created_at` DATETIME     DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_itin_tour` FOREIGN KEY (`tour_id`) REFERENCES `tours` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- 7. Bảng activities — Hoạt động chi tiết trong ngày
CREATE TABLE IF NOT EXISTS `activities` (
    `id`            CHAR(36)       PRIMARY KEY,
    `itinerary_id`  CHAR(36)       NOT NULL,
    `time_slot`     TIME           NULL COMMENT 'Khung giờ, vd: 08:00:00',
    `place_name`    VARCHAR(255)   NOT NULL,
    `description`   TEXT           NULL,
    `latitude`      DECIMAL(10,8)  NULL,
    `longitude`     DECIMAL(11,8)  NULL,
    `created_at`    DATETIME       DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_act_itin` FOREIGN KEY (`itinerary_id`) REFERENCES `itineraries` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- 8. Bảng bookings — Đơn đặt tour
CREATE TABLE IF NOT EXISTS `bookings` (
    `id`               CHAR(36)      PRIMARY KEY,
    `booking_code`     VARCHAR(50)   NOT NULL UNIQUE COMMENT 'Mã vé, vd: BK-20261019-ABCD',
    `user_id`          CHAR(36)      NULL,
    `tour_id`          CHAR(36)      NOT NULL,
    `status`           VARCHAR(20)   NOT NULL DEFAULT 'PENDING' COMMENT 'PENDING | CONFIRMED | CANCELLED | COMPLETED',
    `num_adults`       INT           NOT NULL DEFAULT 1,
    `num_children`     INT           NOT NULL DEFAULT 0,
    `total_price`      DECIMAL(12,2) NOT NULL,
    `contact_name`     VARCHAR(255)  NOT NULL,
    `contact_email`    VARCHAR(255)  NOT NULL,
    `contact_phone`    VARCHAR(20)   NOT NULL,
    `special_requests` TEXT          NULL,
    `created_at`       DATETIME      DEFAULT CURRENT_TIMESTAMP,
    `updated_at`       DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_book_user`   (`user_id`),
    INDEX `idx_book_tour`   (`tour_id`),
    INDEX `idx_book_status` (`status`),
    CONSTRAINT `fk_book_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_book_tour` FOREIGN KEY (`tour_id`) REFERENCES `tours` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- 9. Bảng booking_passengers — Danh sách hành khách đi kèm
CREATE TABLE IF NOT EXISTS `booking_passengers` (
    `id`             CHAR(36)    PRIMARY KEY,
    `booking_id`     CHAR(36)    NOT NULL,
    `full_name`      VARCHAR(255) NOT NULL,
    `passenger_type` VARCHAR(20)  NOT NULL DEFAULT 'ADULT' COMMENT 'ADULT | CHILD',
    `id_card_number` VARCHAR(50)  NULL COMMENT 'CCCD / Hộ chiếu',
    `created_at`     DATETIME     DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_pass_book` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- 10. Bảng audit_logs — Nhật ký thao tác hệ thống
CREATE TABLE IF NOT EXISTS `audit_logs` (
    `id`            BIGINT      AUTO_INCREMENT PRIMARY KEY,
    `user_id`       CHAR(36)    NULL,
    `action`        VARCHAR(100) NOT NULL COMMENT 'LOGIN | CREATE_TOUR | BOOKING | CANCEL...',
    `resource_type` VARCHAR(50)  NOT NULL,
    `resource_id`   VARCHAR(100) NULL,
    `details`       TEXT         NULL,
    `ip_address`    VARCHAR(45)  NULL,
    `created_at`    DATETIME     DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
-- 11. Seed Data — 4 quyền mặc định
INSERT INTO `roles` (`name`, `description`) VALUES
    ('ADMIN',      'Quản trị viên toàn quyền hệ thống'),
    ('STAFF',      'Nhân viên quản lý Tour và duyệt đơn'),
    ('TOUR_GUIDE', 'Hướng dẫn viên du lịch'),
    ('CUSTOMER',   'Khách hàng đặt Tour')
ON DUPLICATE KEY UPDATE `description` = VALUES(`description`);
-- Kiểm tra kết quả
SHOW TABLES;
SELECT * FROM `roles`;