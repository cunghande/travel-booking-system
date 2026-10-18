-- 1. TẠO DATABASE

CREATE DATABASE `travel_booking`
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

-- Chuyển sang sử dụng database travel_booking
USE `travel_booking`;

-- 2. BẢNG ROLES - PHÂN QUYỀN
--
-- Mục đích:
-- Lưu danh sách các vai trò (Role) trong hệ thống.
--
-- Ví dụ:
--   ADMIN       : Quản trị viên
--   STAFF       : Nhân viên
--   TOUR_GUIDE  : Hướng dẫn viên
--   CUSTOMER    : Khách hàng
--
-- Một User có thể có nhiều Role.
-- Vì vậy User và Role có quan hệ N-N thông qua bảng user_roles.
--
-- ============================================================
CREATE TABLE `roles` (
    -- ID tự tăng, dùng để định danh Role
    `id` INT AUTO_INCREMENT PRIMARY KEY,

    -- Tên Role
    -- UNIQUE đảm bảo không tồn tại 2 Role cùng tên
    `name` VARCHAR(50) NOT NULL UNIQUE
        COMMENT 'Tên vai trò: ADMIN, STAFF, TOUR_GUIDE, CUSTOMER',

    -- Mô tả quyền/vai trò
    `description` VARCHAR(255) NULL
        COMMENT 'Mô tả chức năng và quyền của Role',

    -- Thời điểm tạo Role
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
        COMMENT 'Thời điểm Role được tạo'
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;

-- 3. BẢNG USERS - NGƯỜI DÙNG
--
-- Mục đích:
-- Lưu thông tin tài khoản người dùng.
--
-- Bao gồm:
--   - Khách hàng
--   - Nhân viên
--   - Admin
--   - Hướng dẫn viên
--
-- Mật khẩu KHÔNG lưu dạng plaintext.
-- Cột hashed_password phải lưu mật khẩu đã được hash
-- bằng thuật toán phù hợp (ví dụ bcrypt/Argon2).
--
-- ============================================================

CREATE TABLE `users` (

    -- UUID của người dùng
    -- Ví dụ:
    -- 550e8400-e29b-41d4-a716-446655440000
    `id` CHAR(36) PRIMARY KEY
        COMMENT 'UUID v4 định danh duy nhất người dùng',

    -- Email dùng để đăng nhập
    -- UNIQUE: mỗi email chỉ được đăng ký một tài khoản
    `email` VARCHAR(255) NOT NULL UNIQUE
        COMMENT 'Email đăng nhập của người dùng',

    -- Mật khẩu đã HASH
    -- Không được lưu mật khẩu gốc
    `hashed_password` VARCHAR(255) NOT NULL
        COMMENT 'Mật khẩu đã được hash, không lưu plaintext',

    -- Họ tên người dùng
    `full_name` VARCHAR(255) NOT NULL
        COMMENT 'Họ và tên người dùng',

    -- Số điện thoại
    `phone_number` VARCHAR(20) NULL
        COMMENT 'Số điện thoại liên hệ',

    -- Trạng thái tài khoản
    -- TRUE  = đang hoạt động
    -- FALSE = bị khóa/vô hiệu hóa
    `is_active` BOOLEAN DEFAULT TRUE
        COMMENT 'Trạng thái tài khoản: TRUE = hoạt động',

    -- Thời điểm tạo tài khoản
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
        COMMENT 'Thời điểm tạo tài khoản',

    -- Thời điểm cập nhật gần nhất
    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
        COMMENT 'Thời điểm cập nhật thông tin gần nhất',

    -- Index phục vụ tìm kiếm user theo email
    INDEX `idx_users_email` (`email`)
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 4. BẢNG USER_ROLES - GÁN ROLE CHO USER
-- ============================================================
--
-- Đây là bảng trung gian giữa users và roles.
--
-- Quan hệ:
--
-- users 1 ----- N user_roles N ----- 1 roles
--
-- Ví dụ:
--
-- User A -> CUSTOMER
-- User B -> STAFF
-- User C -> ADMIN
--
-- Một User có thể có nhiều Role:
--
-- User A -> CUSTOMER
--        -> TOUR_GUIDE
--
-- PRIMARY KEY(user_id, role_id)
-- đảm bảo cùng một User không bị gán
-- cùng một Role hai lần.
--
-- ============================================================

CREATE TABLE `user_roles` (

    -- ID User
    `user_id` CHAR(36) NOT NULL
        COMMENT 'UUID của người dùng',

    -- ID Role
    `role_id` INT NOT NULL
        COMMENT 'ID của vai trò',

    -- Khóa chính kép
    `PRIMARY KEY` (`user_id`, `role_id`),

    -- Nếu User bị xóa thì các Role liên quan cũng bị xóa
    CONSTRAINT `fk_user_roles_user`
        FOREIGN KEY (`user_id`)
        REFERENCES `users` (`id`)
        ON DELETE CASCADE,

    -- Nếu Role bị xóa thì quan hệ User-Role cũng bị xóa
    CONSTRAINT `fk_user_roles_role`
        FOREIGN KEY (`role_id`)
        REFERENCES `roles` (`id`)
        ON DELETE CASCADE
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


-- 5. BẢNG TOURS - TOUR DU LỊCH
-- ============================================================
--
-- Mục đích:
-- Lưu thông tin chính của một tour.
--
-- Ví dụ:
--
-- TOUR-202610-001
-- Hà Nội - Hạ Long 3 ngày 2 đêm
--
-- Một Tour có thể có:
--   ├── nhiều ngày trong lịch trình
--   ├── nhiều hoạt động
--   └── nhiều Booking
--
-- ============================================================

CREATE TABLE `tours` (

    -- UUID của Tour
    `id` CHAR(36) PRIMARY KEY
        COMMENT 'UUID v4 của Tour',

    -- Mã Tour hiển thị cho người dùng
    -- Ví dụ: TOUR-202610-001
    `tour_code` VARCHAR(50) NOT NULL UNIQUE
        COMMENT 'Mã Tour duy nhất',

    -- Tên Tour
    `title` VARCHAR(500) NOT NULL
        COMMENT 'Tên tour du lịch',

    -- Mô tả chi tiết
    `description` TEXT NULL
        COMMENT 'Mô tả chi tiết về Tour',

    -- Loại Tour
    -- Ví dụ:
    -- Biển đảo
    -- Nghỉ dưỡng
    -- Leo núi
    -- Văn hóa
    `category` VARCHAR(100) NULL
        COMMENT 'Danh mục Tour',

    -- Địa điểm chính
    `destination` VARCHAR(255) NOT NULL
        COMMENT 'Điểm đến chính của Tour',

    -- Giá người lớn
    `base_price_adult` DECIMAL(12,2) NOT NULL
        COMMENT 'Giá Tour dành cho người lớn',

    -- Giá trẻ em
    `base_price_child` DECIMAL(12,2) NOT NULL DEFAULT 0.00
        COMMENT 'Giá Tour dành cho trẻ em',

    -- Tổng số người tối đa
    `max_participants` INT NOT NULL DEFAULT 20
        COMMENT 'Số lượng khách tối đa của Tour',

    -- Số chỗ còn trống
    `available_slots` INT NOT NULL DEFAULT 20
        COMMENT 'Số chỗ còn lại',

    -- Ngày bắt đầu
    `start_date` DATE NOT NULL
        COMMENT 'Ngày Tour bắt đầu',

    -- Ngày kết thúc
    `end_date` DATE NOT NULL
        COMMENT 'Ngày Tour kết thúc',

    -- Trạng thái Tour
    --
    -- DRAFT:
    --   Tour đang soạn, chưa công khai
    --
    -- PUBLISHED:
    --   Tour đã công khai cho khách đặt
    --
    -- ARCHIVED:
    --   Tour đã lưu trữ
    --
    -- CANCELLED:
    --   Tour đã bị hủy
    `status` VARCHAR(20) NOT NULL DEFAULT 'DRAFT'
        COMMENT 'DRAFT, PUBLISHED, ARCHIVED, CANCELLED',

    -- User tạo Tour
    `created_by` CHAR(36) NULL
        COMMENT 'UUID của User tạo Tour',

    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
        COMMENT 'Thời điểm tạo Tour',

    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
        COMMENT 'Thời điểm cập nhật Tour',

    -- Index để tìm Tour theo trạng thái
    INDEX `idx_tours_status` (`status`),

    -- Index để tìm Tour theo điểm đến
    INDEX `idx_tours_destination` (`destination`),

    -- Index để tìm Tour theo ngày bắt đầu
    INDEX `idx_tours_start_date` (`start_date`)
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 6. BẢNG ITINERARIES - LỊCH TRÌNH
-- ============================================================
--
-- Một Tour có nhiều ngày.
--
-- Ví dụ:
--
-- Tour Hạ Long 3 ngày
--
-- Day 1: Hà Nội -> Hạ Long
-- Day 2: Tham quan Vịnh Hạ Long
-- Day 3: Hạ Long -> Hà Nội
--
-- Quan hệ:
--
-- tours 1 ---- N itineraries
--
-- ============================================================

CREATE TABLE `itineraries` (

    `id` CHAR(36) PRIMARY KEY
        COMMENT 'UUID của lịch trình',

    `tour_id` CHAR(36) NOT NULL
        COMMENT 'Tour mà lịch trình thuộc về',

    -- Số thứ tự ngày
    `day_number` INT NOT NULL
        COMMENT 'Ngày thứ mấy trong Tour: 1, 2, 3...',

    -- Tiêu đề ngày
    `title` VARCHAR(500) NOT NULL
        COMMENT 'Tên/mô tả chính của ngày',

    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
        COMMENT 'Thời điểm tạo lịch trình',

    -- Xóa Tour -> xóa toàn bộ lịch trình
    CONSTRAINT `fk_itineraries_tour`
        FOREIGN KEY (`tour_id`)
        REFERENCES `tours` (`id`)
        ON DELETE CASCADE
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 7. BẢNG ACTIVITIES - HOẠT ĐỘNG
-- ============================================================
--
-- Mỗi ngày trong lịch trình có thể có nhiều hoạt động.
--
-- Ví dụ:
--
-- Day 1
--   08:00 - Khởi hành
--   10:00 - Đến Hạ Long
--   12:00 - Ăn trưa
--
-- Quan hệ:
--
-- itineraries 1 ---- N activities
--
-- ============================================================

CREATE TABLE `activities` (

    `id` CHAR(36) PRIMARY KEY
        COMMENT 'UUID của hoạt động',

    -- Hoạt động thuộc ngày nào
    `itinerary_id` CHAR(36) NOT NULL
        COMMENT 'ID lịch trình chứa hoạt động',

    -- Thời gian thực hiện
    `time_slot` TIME NULL
        COMMENT 'Thời gian bắt đầu hoạt động',

    -- Địa điểm
    `place_name` VARCHAR(255) NOT NULL
        COMMENT 'Tên địa điểm hoạt động',

    -- Mô tả
    `description` TEXT NULL
        COMMENT 'Mô tả chi tiết hoạt động',

    -- Tọa độ địa lý
    `latitude` DECIMAL(10,8) NULL
        COMMENT 'Vĩ độ địa điểm',

    `longitude` DECIMAL(11,8) NULL
        COMMENT 'Kinh độ địa điểm',

    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
        COMMENT 'Thời điểm tạo hoạt động',

    -- Xóa itinerary -> xóa activities
    CONSTRAINT `fk_activities_itinerary`
        FOREIGN KEY (`itinerary_id`)
        REFERENCES `itineraries` (`id`)
        ON DELETE CASCADE
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 8. BẢNG BOOKINGS - ĐƠN ĐẶT TOUR
-- ============================================================
--
-- Đây là bảng rất quan trọng.
--
-- Mỗi Booking đại diện cho một lần khách đặt Tour.
--
-- Ví dụ:
--
-- Nguyễn Văn A
--     ↓
-- Đặt Tour Hạ Long
--     ↓
-- Booking BK-20261006-ABCD
--
-- Quan hệ:
--
-- User 1 ---- N Bookings
-- Tour 1 ---- N Bookings
--
-- ============================================================

CREATE TABLE `bookings` (

    -- UUID Booking
    `id` CHAR(36) PRIMARY KEY
        COMMENT 'UUID của Booking',

    -- Mã Booking hiển thị
    `booking_code` VARCHAR(50) NOT NULL UNIQUE
        COMMENT 'Mã đơn đặt Tour',

    -- Người đặt
    `user_id` CHAR(36) NULL
        COMMENT 'User thực hiện đặt Tour',

    -- Tour được đặt
    `tour_id` CHAR(36) NOT NULL
        COMMENT 'Tour được đặt',

    -- Trạng thái Booking
    --
    -- PENDING:
    --   Chờ xác nhận
    --
    -- CONFIRMED:
    --   Đã xác nhận
    --
    -- CANCELLED:
    --   Đã hủy
    --
    -- COMPLETED:
    --   Đã hoàn thành
    `status` VARCHAR(20) NOT NULL DEFAULT 'PENDING'
        COMMENT 'PENDING, CONFIRMED, CANCELLED, COMPLETED',

    -- Số người lớn
    `num_adults` INT NOT NULL DEFAULT 1
        COMMENT 'Số lượng người lớn',

    -- Số trẻ em
    `num_children` INT NOT NULL DEFAULT 0
        COMMENT 'Số lượng trẻ em',

    -- Tổng tiền
    `total_price` DECIMAL(12,2) NOT NULL
        COMMENT 'Tổng tiền của Booking',

    -- Thông tin người liên hệ
    `contact_name` VARCHAR(255) NOT NULL
        COMMENT 'Tên người liên hệ',

    `contact_email` VARCHAR(255) NOT NULL
        COMMENT 'Email người liên hệ',

    `contact_phone` VARCHAR(20) NOT NULL
        COMMENT 'Số điện thoại người liên hệ',

    -- Yêu cầu đặc biệt
    `special_requests` TEXT NULL
        COMMENT 'Yêu cầu đặc biệt của khách',

    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
        COMMENT 'Thời điểm tạo Booking',

    `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
        COMMENT 'Thời điểm cập nhật Booking',

    INDEX `idx_bookings_user_id` (`user_id`),
    INDEX `idx_bookings_tour_id` (`tour_id`),
    INDEX `idx_bookings_status` (`status`),

    -- Nếu User bị xóa:
    -- Booking vẫn giữ lại nhưng user_id = NULL
    CONSTRAINT `fk_bookings_user`
        FOREIGN KEY (`user_id`)
        REFERENCES `users` (`id`)
        ON DELETE SET NULL,

    -- Không cho phép xóa Tour nếu đang có Booking
    CONSTRAINT `fk_bookings_tour`
        FOREIGN KEY (`tour_id`)
        REFERENCES `tours` (`id`)
        ON DELETE RESTRICT
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 9. BẢNG BOOKING_PASSENGERS - HÀNH KHÁCH
-- ============================================================
--
-- Một Booking có thể có nhiều hành khách.
--
-- Ví dụ:
--
-- Booking BK001
--   ├── Nguyễn Văn A - ADULT
--   ├── Nguyễn Thị B - ADULT
--   └── Nguyễn Văn C - CHILD
--
-- Quan hệ:
--
-- bookings 1 ---- N booking_passengers
--
-- ============================================================

CREATE TABLE `booking_passengers` (

    `id` CHAR(36) PRIMARY KEY
        COMMENT 'UUID của hành khách',

    `booking_id` CHAR(36) NOT NULL
        COMMENT 'Booking mà hành khách thuộc về',

    -- Tên hành khách
    `full_name` VARCHAR(255) NOT NULL
        COMMENT 'Họ và tên hành khách',

    -- Loại hành khách
    `passenger_type` VARCHAR(20) NOT NULL DEFAULT 'ADULT'
        COMMENT 'ADULT = người lớn, CHILD = trẻ em',

    -- CCCD / Passport
    `id_card_number` VARCHAR(50) NULL
        COMMENT 'Số CCCD hoặc hộ chiếu',

    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
        COMMENT 'Thời điểm thêm hành khách',

    -- Xóa Booking -> xóa hành khách
    CONSTRAINT `fk_passengers_booking`
        FOREIGN KEY (`booking_id`)
        REFERENCES `bookings` (`id`)
        ON DELETE CASCADE
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 10. BẢNG AUDIT_LOGS - NHẬT KÝ HỆ THỐNG
-- ============================================================
--
-- Mục đích:
-- Ghi lại các thao tác quan trọng của người dùng.
--
-- Ví dụ:
--
-- LOGIN
-- CREATE_TOUR
-- UPDATE_TOUR
-- BOOKING
-- CANCEL_BOOKING
--
-- Phục vụ:
--   - Kiểm tra lịch sử thao tác
--   - Debug
--   - Bảo mật
--   - Audit hệ thống
--
-- ============================================================

CREATE TABLE `audit_logs` (

    -- ID tự tăng
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,

    -- User thực hiện thao tác
    `user_id` CHAR(36) NULL
        COMMENT 'User thực hiện thao tác',

    -- Tên hành động
    `action` VARCHAR(100) NOT NULL
        COMMENT 'LOGIN, CREATE_TOUR, BOOKING, CANCEL_BOOKING...',

    -- Loại đối tượng bị tác động
    -- Ví dụ:
    -- USER
    -- TOUR
    -- BOOKING
    `resource_type` VARCHAR(50) NOT NULL
        COMMENT 'Loại tài nguyên bị tác động',

    -- ID của tài nguyên
    `resource_id` VARCHAR(100) NULL
        COMMENT 'ID của tài nguyên bị tác động',

    -- Chi tiết thao tác
    `details` TEXT NULL
        COMMENT 'Thông tin chi tiết về thao tác',

    -- IP của client
    `ip_address` VARCHAR(45) NULL
        COMMENT 'Địa chỉ IP thực hiện request',

    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
        COMMENT 'Thời điểm thao tác'
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_unicode_ci;


-- ============================================================
-- 11. SEED DATA - ROLE MẶC ĐỊNH
-- ============================================================
--
-- Tạo 4 Role mặc định cho hệ thống.
--
-- ADMIN:
--   Toàn quyền hệ thống
--
-- STAFF:
--   Quản lý Tour và Booking
--
-- TOUR_GUIDE:
--   Hướng dẫn viên
--
-- CUSTOMER:
--   Khách hàng
--
-- ============================================================

INSERT INTO `roles` (`name`, `description`)
VALUES
(
    'ADMIN',
    'Quản trị viên toàn quyền hệ thống'
),
(
    'STAFF',
    'Nhân viên quản lý Tour và duyệt đơn đặt Tour'
),
(
    'TOUR_GUIDE',
    'Hướng dẫn viên du lịch'
),
(
    'CUSTOMER',
    'Khách hàng đặt Tour'
);


-- ============================================================
-- 12. KIỂM TRA DATABASE SAU KHI KHỞI TẠO
-- ============================================================

SHOW TABLES;

-- Kiểm tra dữ liệu Role
SELECT * FROM `roles`;