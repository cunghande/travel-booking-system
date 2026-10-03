-- ============================================================
-- FILE: 02_tao_bang.sql (MySQL)
-- MỤC ĐÍCH: Tạo cấu trúc các bảng dữ liệu cho hệ thống đặt tour
-- HỆ QUẢN TRỊ: MySQL 5.7+ / MySQL 8.0+ / MariaDB / XAMPP
-- ============================================================
-- HƯỚNG DẪN CHẠY:
--   mysql -u root -p tour_booking_db < 02_tao_bang.sql
-- ============================================================

USE tour_booking_db;

-- Tắt kiểm tra khóa ngoại tạm thời để tránh xung đột khi drop/create bảng
SET FOREIGN_KEY_CHECKS = 0;

-- ============================================================
-- 1. BẢNG roles (Vai trò người dùng trong hệ thống)
-- ============================================================
DROP TABLE IF EXISTS user_roles;
DROP TABLE IF EXISTS roles;
CREATE TABLE roles (
    id          INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Mã định danh vai trò (1, 2, 3...)',
    name        VARCHAR(50) NOT NULL UNIQUE COMMENT 'Tên vai trò (ADMIN, STAFF, CUSTOMER, TOUR_GUIDE)',
    description VARCHAR(255) NULL COMMENT 'Mô tả chi tiết quyền hạn của vai trò'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Bảng định nghĩa các vai trò hệ thống';


-- ============================================================
-- 2. BẢNG users (Tài khoản người dùng)
-- ============================================================
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    id              CHAR(36) NOT NULL PRIMARY KEY COMMENT 'Mã định danh duy nhất (UUID v4)',
    email           VARCHAR(255) NOT NULL UNIQUE COMMENT 'Email đăng nhập duy nhất',
    hashed_password VARCHAR(255) NOT NULL COMMENT 'Mật khẩu đã mã hóa một chiều bằng bcrypt',
    full_name       VARCHAR(255) NOT NULL COMMENT 'Họ và tên đầy đủ',
    phone_number    VARCHAR(20) NULL COMMENT 'Số điện thoại liên hệ',
    is_active       BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Trạng thái hoạt động (1=kích hoạt, 0=khóa)',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Thời điểm đăng ký tài khoản',
    updated_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Thời điểm cập nhật hồ sơ gần nhất'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Bảng thông tin tài khoản người dùng';


-- ============================================================
-- 3. BẢNG user_roles (Quan hệ nhiều - nhiều giữa users và roles)
-- ============================================================
CREATE TABLE user_roles (
    user_id     CHAR(36) NOT NULL COMMENT 'Tham chiếu tới bảng users(id)',
    role_id     INT NOT NULL COMMENT 'Tham chiếu tới bảng roles(id)',
    PRIMARY KEY (user_id, role_id),
    CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_user_roles_role FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Phân quyền vai trò cho từng người dùng';


-- ============================================================
-- 4. BẢNG tours (Thông tin Tour du lịch)
-- ============================================================
DROP TABLE IF EXISTS tours;
CREATE TABLE tours (
    id                  CHAR(36) NOT NULL PRIMARY KEY COMMENT 'Mã định danh duy nhất của Tour (UUID v4)',
    tour_code           VARCHAR(50) NOT NULL UNIQUE COMMENT 'Mã tour kinh doanh (VD: TOUR-A1B2C3)',
    title               VARCHAR(500) NOT NULL COMMENT 'Tên/tiêu đề chuyến đi',
    description         TEXT NULL COMMENT 'Mô tả chi tiết trải nghiệm tour',
    category            VARCHAR(100) NULL COMMENT 'Danh mục tour (Biển, Núi, Văn hóa, Nghỉ dưỡng...)',
    destination         VARCHAR(255) NOT NULL COMMENT 'Điểm đến chính (Hạ Long, Đà Nẵng, Phú Quốc...)',
    base_price_adult    DECIMAL(12, 2) NOT NULL COMMENT 'Giá vé cơ bản cho người lớn (VNĐ hoặc USD)',
    base_price_child    DECIMAL(12, 2) NOT NULL DEFAULT 0.00 COMMENT 'Giá vé trẻ em',
    max_participants    INT NOT NULL COMMENT 'Số lượng khách tối đa cho chuyến đi',
    available_slots     INT NOT NULL COMMENT 'Số chỗ thực tế còn trống cho phép đặt',
    start_date          DATE NOT NULL COMMENT 'Ngày khởi hành',
    end_date            DATE NOT NULL COMMENT 'Ngày kết thúc',
    status              VARCHAR(30) NOT NULL DEFAULT 'DRAFT' COMMENT 'Trạng thái: DRAFT, PUBLISHED, ARCHIVED, CANCELLED',
    created_by          CHAR(36) NULL COMMENT 'Người tạo tour (tham chiếu users(id))',
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Thời điểm tạo',
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Thời điểm sửa đổi gần nhất',
    CONSTRAINT fk_tours_created_by FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_tours_destination (destination),
    INDEX idx_tours_status (status),
    INDEX idx_tours_category (category),
    INDEX idx_tours_price (base_price_adult),
    INDEX idx_tours_start_date (start_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Bảng danh sách Tour du lịch';


-- ============================================================
-- 5. BẢNG itineraries (Lịch trình từng ngày của Tour)
-- ============================================================
DROP TABLE IF EXISTS itineraries;
CREATE TABLE itineraries (
    id          CHAR(36) NOT NULL PRIMARY KEY COMMENT 'Mã lịch trình ngày (UUID v4)',
    tour_id     CHAR(36) NOT NULL COMMENT 'Thuộc tour nào',
    day_number  INT NOT NULL COMMENT 'Ngày thứ mấy (1, 2, 3...)',
    title       VARCHAR(500) NOT NULL COMMENT 'Tiêu đề ngày (VD: Ngày 1: Đón khách - Nhận phòng)',
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_itineraries_tour FOREIGN KEY (tour_id) REFERENCES tours(id) ON DELETE CASCADE,
    UNIQUE KEY uq_tour_day (tour_id, day_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Lịch trình chia theo ngày của Tour';


-- ============================================================
-- 6. BẢNG itinerary_activities (Hoạt động chi tiết trong ngày)
-- ============================================================
DROP TABLE IF EXISTS itinerary_activities;
CREATE TABLE itinerary_activities (
    id              CHAR(36) NOT NULL PRIMARY KEY COMMENT 'Mã hoạt động (UUID v4)',
    itinerary_id    CHAR(36) NOT NULL COMMENT 'Thuộc ngày lịch trình nào',
    time_slot       TIME NULL COMMENT 'Khung giờ hoạt động (VD: 08:30:00)',
    place_name      VARCHAR(255) NOT NULL COMMENT 'Tên địa điểm / điểm tham quan',
    description     TEXT NULL COMMENT 'Mô tả hoạt động cụ thể',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_activities_itinerary FOREIGN KEY (itinerary_id) REFERENCES itineraries(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Chi tiết các hoạt động trong từng ngày';


-- ============================================================
-- 7. BẢNG bookings (Đơn đặt tour của khách hàng)
-- ============================================================
DROP TABLE IF EXISTS bookings;
CREATE TABLE bookings (
    id                  CHAR(36) NOT NULL PRIMARY KEY COMMENT 'Mã định danh đơn (UUID v4)',
    booking_code        VARCHAR(50) NOT NULL UNIQUE COMMENT 'Mã đơn đặt tour (VD: BK-20261003-XXXXXX)',
    user_id             CHAR(36) NULL COMMENT 'Khách hàng đặt vé (users(id))',
    tour_id             CHAR(36) NOT NULL COMMENT 'Tour được đặt (tours(id))',
    status              VARCHAR(30) NOT NULL DEFAULT 'PENDING_PAYMENT' COMMENT 'Trạng thái: PENDING_PAYMENT, CONFIRMED, CANCELLED, COMPLETED',
    num_adults          INT NOT NULL DEFAULT 1 COMMENT 'Số vé người lớn',
    num_children        INT NOT NULL DEFAULT 0 COMMENT 'Số vé trẻ em',
    total_price         DECIMAL(12, 2) NOT NULL COMMENT 'Tổng số tiền phải thanh toán',
    contact_name        VARCHAR(255) NOT NULL COMMENT 'Họ tên người nhận thông tin',
    contact_email       VARCHAR(255) NOT NULL COMMENT 'Email nhận vé điện tử',
    contact_phone       VARCHAR(20) NOT NULL COMMENT 'Số điện thoại liên hệ',
    special_requests    TEXT NULL COMMENT 'Yêu cầu đặc biệt (ăn chay, dị ứng, phòng đơn...)',
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Thời điểm đặt tour',
    updated_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_bookings_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_bookings_tour FOREIGN KEY (tour_id) REFERENCES tours(id) ON DELETE RESTRICT,
    INDEX idx_bookings_user (user_id),
    INDEX idx_bookings_tour (tour_id),
    INDEX idx_bookings_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Bảng đơn đặt tour của khách hàng';


-- ============================================================
-- 8. BẢNG booking_passengers (Danh sách hành khách trong đơn)
-- ============================================================
DROP TABLE IF EXISTS booking_passengers;
CREATE TABLE booking_passengers (
    id              CHAR(36) NOT NULL PRIMARY KEY COMMENT 'Mã hành khách (UUID v4)',
    booking_id      CHAR(36) NOT NULL COMMENT 'Thuộc đơn đặt tour nào',
    full_name       VARCHAR(255) NOT NULL COMMENT 'Họ và tên hành khách',
    passenger_type  VARCHAR(20) NOT NULL DEFAULT 'ADULT' COMMENT 'Loại vé: ADULT, CHILD, INFANT',
    id_card_number  VARCHAR(50) NULL COMMENT 'Số CCCD hoặc Hộ chiếu',
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_passengers_booking FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Danh sách chi tiết hành khách của từng đơn';


-- ============================================================
-- 9. BẢNG payments (Giao dịch thanh toán)
-- ============================================================
DROP TABLE IF EXISTS payments;
CREATE TABLE payments (
    id                  CHAR(36) NOT NULL PRIMARY KEY,
    booking_id          CHAR(36) NOT NULL,
    amount              DECIMAL(12, 2) NOT NULL COMMENT 'Số tiền thanh toán',
    payment_method      VARCHAR(50) NOT NULL DEFAULT 'VNPAY' COMMENT 'VNPAY, MOMO, STRIPE, CASH',
    status              VARCHAR(30) NOT NULL DEFAULT 'PENDING' COMMENT 'PENDING, SUCCESS, FAILED, REFUNDED',
    transaction_code    VARCHAR(100) NULL COMMENT 'Mã giao dịch từ cổng thanh toán',
    payment_date        DATETIME NULL,
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_payments_booking FOREIGN KEY (booking_id) REFERENCES bookings(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Lịch sử giao dịch thanh toán';


-- ============================================================
-- 10. BẢNG reviews (Đánh giá và nhận xét Tour)
-- ============================================================
DROP TABLE IF EXISTS reviews;
CREATE TABLE reviews (
    id          CHAR(36) NOT NULL PRIMARY KEY,
    user_id     CHAR(36) NOT NULL,
    tour_id     CHAR(36) NOT NULL,
    rating      TINYINT NOT NULL COMMENT 'Điểm đánh giá từ 1 đến 5 sao',
    comment     TEXT NULL COMMENT 'Nội dung nhận xét',
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_reviews_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_reviews_tour FOREIGN KEY (tour_id) REFERENCES tours(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Đánh giá của khách hàng sau khi đi tour';


-- ============================================================
-- 11. BẢNG audit_logs (Nhật ký kiểm toán & bảo mật)
-- ============================================================
DROP TABLE IF EXISTS audit_logs;
CREATE TABLE audit_logs (
    id          CHAR(36) NOT NULL PRIMARY KEY,
    user_id     CHAR(36) NULL COMMENT 'Người thực hiện hành động',
    action      VARCHAR(100) NOT NULL COMMENT 'Tên hành động (USER_LOGIN, TOUR_CREATED...)',
    resource    VARCHAR(100) NULL COMMENT 'Tài nguyên bị tác động (users, tours, bookings)',
    resource_id VARCHAR(100) NULL COMMENT 'ID của tài nguyên bị tác động',
    details     JSON NULL COMMENT 'Chi tiết bổ sung dạng JSON',
    ip_address  VARCHAR(45) NULL COMMENT 'Địa chỉ IP của client (hỗ trợ IPv4 & IPv6)',
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Thời điểm ghi nhận',
    INDEX idx_audit_user (user_id),
    INDEX idx_audit_action (action),
    INDEX idx_audit_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Nhật ký kiểm toán an ninh toàn hệ thống';

-- Bật lại kiểm tra khóa ngoại
SET FOREIGN_KEY_CHECKS = 1;
