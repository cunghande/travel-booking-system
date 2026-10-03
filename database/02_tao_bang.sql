-- ============================================================
-- FILE: 02_tao_bang.sql
-- MỤC ĐÍCH: Tạo tất cả các bảng dữ liệu cho hệ thống đặt tour
-- ============================================================
-- HƯỚNG DẪN CHẠY:
--   Kết nối vào database "tour_booking_db" rồi chạy file này.
--   psql -U postgres -p 8888 -d tour_booking_db -f 02_tao_bang.sql
-- ============================================================

-- Bật extension tạo UUID tự động (dùng uuid_generate_v4())
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- Bật extension hỗ trợ tìm kiếm gần đúng (fuzzy search)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================
-- BẢNG 1: roles (Vai trò người dùng)
-- ============================================================
-- Mỗi người dùng có thể có 1 hoặc nhiều vai trò.
-- Ví dụ: ADMIN (quản trị), STAFF (nhân viên), CUSTOMER (khách hàng)
CREATE TABLE IF NOT EXISTS roles (
    id          SERIAL PRIMARY KEY,                          -- Khóa chính tự tăng
    name        VARCHAR(50) UNIQUE NOT NULL,                 -- Tên vai trò (ADMIN, STAFF, CUSTOMER)
    description VARCHAR(255),                                -- Mô tả vai trò
    created_at  TIMESTAMPTZ DEFAULT NOW() NOT NULL           -- Thời điểm tạo
);

-- Tạo index để tìm kiếm vai trò theo tên nhanh hơn
CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);

COMMENT ON TABLE roles IS 'Bảng lưu trữ các vai trò (quyền hạn) trong hệ thống';
COMMENT ON COLUMN roles.name IS 'Tên vai trò: ADMIN, STAFF, CUSTOMER';


-- ============================================================
-- BẢNG 2: users (Tài khoản người dùng)
-- ============================================================
-- Lưu thông tin đăng nhập và hồ sơ cá nhân của người dùng.
-- Mật khẩu được mã hóa bằng bcrypt trước khi lưu (KHÔNG lưu mật khẩu gốc).
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),  -- Khóa chính dạng UUID (bảo mật hơn số tự tăng)
    email           VARCHAR(255) UNIQUE NOT NULL,                 -- Email đăng nhập (duy nhất)
    hashed_password VARCHAR(255) NOT NULL,                        -- Mật khẩu đã được mã hóa bcrypt
    full_name       VARCHAR(255) NOT NULL,                        -- Họ và tên đầy đủ
    phone_number    VARCHAR(20),                                  -- Số điện thoại (tùy chọn)
    is_active       BOOLEAN DEFAULT TRUE NOT NULL,                -- Tài khoản có đang hoạt động không
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,           -- Thời điểm đăng ký
    updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL            -- Thời điểm cập nhật lần cuối
);

-- Index giúp tìm user theo email cực nhanh (dùng khi đăng nhập)
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

COMMENT ON TABLE users IS 'Bảng tài khoản người dùng - lưu thông tin đăng nhập và hồ sơ';
COMMENT ON COLUMN users.hashed_password IS 'Mật khẩu đã mã hóa bcrypt - KHÔNG BAO GIỜ lưu mật khẩu gốc';


-- ============================================================
-- BẢNG 3: user_roles (Liên kết Người dùng - Vai trò)
-- ============================================================
-- Bảng trung gian quan hệ nhiều-nhiều (Many-to-Many):
-- 1 User có thể có nhiều Role, 1 Role có thể thuộc nhiều User
CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,   -- Khi xóa user → xóa luôn vai trò liên kết
    role_id INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE, -- Khi xóa role → xóa luôn liên kết
    PRIMARY KEY (user_id, role_id)                                   -- Khóa chính kép: 1 user chỉ có 1 lần 1 role
);

COMMENT ON TABLE user_roles IS 'Bảng liên kết nhiều-nhiều giữa users và roles (phân quyền RBAC)';


-- ============================================================
-- BẢNG 4: tours (Tour du lịch)
-- ============================================================
-- Lưu thông tin chính của tour: tên, điểm đến, giá, ngày khởi hành...
-- Mỗi tour có vòng đời trạng thái: DRAFT → PUBLISHED → ARCHIVED / CANCELLED
CREATE TABLE IF NOT EXISTS tours (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tour_code         VARCHAR(50) UNIQUE NOT NULL,                    -- Mã tour duy nhất (VD: TOUR-A1B2C3)
    title             VARCHAR(500) NOT NULL,                          -- Tên tour du lịch
    description       TEXT,                                           -- Mô tả chi tiết tour
    category          VARCHAR(100),                                   -- Danh mục (Biển, Núi, Văn hóa...)
    destination       VARCHAR(255) NOT NULL,                          -- Điểm đến chính
    base_price_adult  NUMERIC(15,2) NOT NULL CHECK (base_price_adult > 0),   -- Giá vé người lớn (phải > 0)
    base_price_child  NUMERIC(15,2) NOT NULL CHECK (base_price_child >= 0),  -- Giá vé trẻ em (có thể = 0)
    max_participants  INTEGER NOT NULL CHECK (max_participants > 0),          -- Số chỗ tối đa
    available_slots   INTEGER NOT NULL CHECK (available_slots >= 0),          -- Số chỗ còn trống
    start_date        DATE NOT NULL,                                         -- Ngày khởi hành
    end_date          DATE NOT NULL,                                         -- Ngày kết thúc
    status            VARCHAR(20) NOT NULL DEFAULT 'DRAFT',                  -- Trạng thái tour
    created_by        UUID REFERENCES users(id) ON DELETE SET NULL,          -- Người tạo tour
    created_at        TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at        TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    -- Ràng buộc: ngày kết thúc phải sau ngày bắt đầu
    CONSTRAINT chk_tour_dates CHECK (end_date > start_date),
    -- Ràng buộc: chỗ trống không được lớn hơn tổng chỗ
    CONSTRAINT chk_slots CHECK (available_slots <= max_participants),
    -- Ràng buộc: trạng thái chỉ được là 1 trong 4 giá trị hợp lệ
    CONSTRAINT chk_tour_status CHECK (status IN ('DRAFT', 'PUBLISHED', 'ARCHIVED', 'CANCELLED'))
);

-- Các index giúp tìm kiếm và lọc tour nhanh
CREATE INDEX IF NOT EXISTS idx_tours_destination ON tours(destination);
CREATE INDEX IF NOT EXISTS idx_tours_category ON tours(category);
CREATE INDEX IF NOT EXISTS idx_tours_status ON tours(status);
CREATE INDEX IF NOT EXISTS idx_tours_start_date ON tours(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_tours_price ON tours(base_price_adult);
-- Index hỗ trợ tìm kiếm gần đúng theo tên tour (dùng pg_trgm)
CREATE INDEX IF NOT EXISTS idx_tours_title_trgm ON tours USING gin(title gin_trgm_ops);

COMMENT ON TABLE tours IS 'Bảng chính lưu thông tin các tour du lịch';
COMMENT ON COLUMN tours.status IS 'Vòng đời: DRAFT (nháp) → PUBLISHED (mở bán) → ARCHIVED (đóng) / CANCELLED (hủy)';
COMMENT ON COLUMN tours.available_slots IS 'Số chỗ còn trống = max_participants - tổng đã đặt (chưa hủy)';


-- ============================================================
-- BẢNG 5: itineraries (Lịch trình từng ngày)
-- ============================================================
-- Mỗi tour có nhiều ngày, mỗi ngày có 1 lịch trình riêng.
-- Ví dụ: Ngày 1 - Đà Nẵng, Ngày 2 - Hội An, Ngày 3 - Bà Nà Hills
CREATE TABLE IF NOT EXISTS itineraries (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tour_id     UUID NOT NULL REFERENCES tours(id) ON DELETE CASCADE,  -- Khi xóa tour → xóa luôn lịch trình
    day_number  INTEGER NOT NULL CHECK (day_number > 0),               -- Ngày thứ mấy (1, 2, 3...)
    title       VARCHAR(500) NOT NULL,                                 -- Tiêu đề ngày (VD: "Khám phá Hội An")

    -- Ràng buộc: 1 tour không được có 2 ngày trùng số
    CONSTRAINT uq_itinerary_day UNIQUE (tour_id, day_number)
);

CREATE INDEX IF NOT EXISTS idx_itineraries_tour_id ON itineraries(tour_id);

COMMENT ON TABLE itineraries IS 'Lịch trình từng ngày của tour - sắp xếp theo day_number';


-- ============================================================
-- BẢNG 6: itinerary_activities (Hoạt động trong ngày)
-- ============================================================
-- Mỗi ngày có nhiều hoạt động theo thứ tự thời gian.
-- Ví dụ: 08:00 Tham quan chùa, 12:00 Ăn trưa, 14:00 Tắm biển
CREATE TABLE IF NOT EXISTS itinerary_activities (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    itinerary_id    UUID NOT NULL REFERENCES itineraries(id) ON DELETE CASCADE,
    time_slot       TIME,                                  -- Khung giờ (VD: 08:00, 14:30)
    place_name      VARCHAR(255) NOT NULL,                 -- Tên địa điểm/hoạt động
    description     TEXT,                                  -- Mô tả chi tiết
    latitude        DOUBLE PRECISION,                      -- Tọa độ GPS vĩ độ (tùy chọn)
    longitude       DOUBLE PRECISION                       -- Tọa độ GPS kinh độ (tùy chọn)
);

CREATE INDEX IF NOT EXISTS idx_activities_itinerary_id ON itinerary_activities(itinerary_id);

COMMENT ON TABLE itinerary_activities IS 'Các hoạt động cụ thể trong 1 ngày của lịch trình tour';


-- ============================================================
-- BẢNG 7: bookings (Đơn đặt tour)
-- ============================================================
-- Khi khách hàng đặt tour, hệ thống tạo 1 bản ghi booking.
-- Trạng thái đơn: PENDING_PAYMENT → CONFIRMED / CANCELLED / EXPIRED
CREATE TABLE IF NOT EXISTS bookings (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    booking_code     VARCHAR(30) UNIQUE NOT NULL,                     -- Mã vé duy nhất (VD: BK-20261003-AB12)
    user_id          UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tour_id          UUID NOT NULL REFERENCES tours(id) ON DELETE RESTRICT,  -- RESTRICT: không xóa tour khi còn booking
    status           VARCHAR(20) NOT NULL DEFAULT 'PENDING_PAYMENT',
    num_adults       INTEGER NOT NULL DEFAULT 1 CHECK (num_adults >= 1),     -- Ít nhất 1 người lớn
    num_children     INTEGER NOT NULL DEFAULT 0 CHECK (num_children >= 0),
    total_price      NUMERIC(15,2) NOT NULL CHECK (total_price >= 0),        -- Tổng tiền phải >= 0
    contact_name     VARCHAR(255) NOT NULL,                                  -- Tên người liên hệ
    contact_email    VARCHAR(255) NOT NULL,                                  -- Email nhận thông tin
    contact_phone    VARCHAR(50) NOT NULL,                                   -- SĐT liên hệ
    special_requests TEXT,                                                    -- Yêu cầu đặc biệt (ăn chay, phòng...)
    created_at       TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at       TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    -- Ràng buộc: trạng thái chỉ được là 1 trong các giá trị hợp lệ
    CONSTRAINT chk_booking_status CHECK (
        status IN ('PENDING_PAYMENT', 'CONFIRMED', 'CANCELLED', 'EXPIRED', 'REFUND_REQUESTED', 'REFUNDED')
    )
);

CREATE INDEX IF NOT EXISTS idx_bookings_user_id ON bookings(user_id);
CREATE INDEX IF NOT EXISTS idx_bookings_tour_id ON bookings(tour_id);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);
CREATE INDEX IF NOT EXISTS idx_bookings_code ON bookings(booking_code);

COMMENT ON TABLE bookings IS 'Đơn đặt tour - mỗi khách hàng có thể đặt nhiều tour khác nhau';
COMMENT ON COLUMN bookings.booking_code IS 'Mã vé duy nhất theo format BK-YYYYMMDD-XXXXXX';


-- ============================================================
-- BẢNG 8: booking_passengers (Hành khách đi cùng)
-- ============================================================
-- Lưu chi tiết từng hành khách trong 1 đơn đặt tour.
-- Phục vụ cho việc làm thủ tục, bảo hiểm du lịch.
CREATE TABLE IF NOT EXISTS booking_passengers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    booking_id      UUID NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    full_name       VARCHAR(255) NOT NULL,                          -- Họ tên hành khách
    passenger_type  VARCHAR(20) NOT NULL DEFAULT 'ADULT',           -- Loại: ADULT hoặc CHILD
    id_card_number  VARCHAR(50),                                    -- Số CCCD / Hộ chiếu (tùy chọn)
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    CONSTRAINT chk_passenger_type CHECK (passenger_type IN ('ADULT', 'CHILD'))
);

CREATE INDEX IF NOT EXISTS idx_passengers_booking_id ON booking_passengers(booking_id);

COMMENT ON TABLE booking_passengers IS 'Chi tiết từng hành khách trong đơn đặt tour';


-- ============================================================
-- BẢNG 9: audit_logs (Nhật ký hệ thống)
-- ============================================================
-- Ghi lại mọi hành động quan trọng: đăng nhập, tạo tour, đặt tour, hủy...
-- Giúp truy vết khi có sự cố hoặc kiểm toán.
CREATE TABLE IF NOT EXISTS audit_logs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID REFERENCES users(id) ON DELETE SET NULL,  -- Người thực hiện (null nếu hệ thống tự chạy)
    action      VARCHAR(100) NOT NULL,                          -- Hành động (VD: USER_REGISTERED, BOOKING_CREATED)
    resource    VARCHAR(100),                                   -- Loại tài nguyên (users, tours, bookings)
    resource_id VARCHAR(100),                                   -- ID của tài nguyên bị tác động
    details     JSONB,                                          -- Chi tiết bổ sung (dạng JSON linh hoạt)
    ip_address  VARCHAR(45),                                    -- Địa chỉ IP của người thực hiện
    created_at  TIMESTAMPTZ DEFAULT NOW() NOT NULL              -- Thời điểm ghi log
);

CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at);

COMMENT ON TABLE audit_logs IS 'Nhật ký kiểm toán - ghi lại mọi hành động quan trọng trong hệ thống';


-- ============================================================
-- TRIGGER: Tự động cập nhật cột updated_at khi có UPDATE
-- ============================================================
-- Hàm trigger dùng chung cho mọi bảng có cột updated_at
CREATE OR REPLACE FUNCTION trigger_cap_nhat_thoi_gian()
RETURNS TRIGGER AS $$
BEGIN
    -- Mỗi khi dòng dữ liệu bị UPDATE, tự động đặt updated_at = thời điểm hiện tại
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION trigger_cap_nhat_thoi_gian() IS 'Trigger function tự động cập nhật cột updated_at khi UPDATE';

-- Gắn trigger vào bảng users
DROP TRIGGER IF EXISTS trg_users_updated_at ON users;
CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION trigger_cap_nhat_thoi_gian();

-- Gắn trigger vào bảng tours
DROP TRIGGER IF EXISTS trg_tours_updated_at ON tours;
CREATE TRIGGER trg_tours_updated_at
    BEFORE UPDATE ON tours
    FOR EACH ROW
    EXECUTE FUNCTION trigger_cap_nhat_thoi_gian();

-- Gắn trigger vào bảng bookings
DROP TRIGGER IF EXISTS trg_bookings_updated_at ON bookings;
CREATE TRIGGER trg_bookings_updated_at
    BEFORE UPDATE ON bookings
    FOR EACH ROW
    EXECUTE FUNCTION trigger_cap_nhat_thoi_gian();

-- ============================================================
-- HOÀN TẤT: Tất cả 9 bảng + trigger đã được tạo thành công
-- Tiếp theo chạy file 03_tao_stored_procedures.sql
-- ============================================================
