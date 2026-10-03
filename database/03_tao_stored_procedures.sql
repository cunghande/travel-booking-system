-- ============================================================
-- FILE: 03_tao_stored_procedures.sql
-- MỤC ĐÍCH: Tạo tất cả Stored Procedures (hàm) xử lý nghiệp vụ
-- ============================================================
-- THUẬT NGỮ:
--   FUNCTION  = Hàm trả về giá trị (dùng SELECT)
--   PROCEDURE = Thủ tục không trả về giá trị (dùng CALL)
--   Trong PostgreSQL, ta dùng FUNCTION cho cả 2 vì linh hoạt hơn.
--
-- HƯỚNG DẪN CHẠY:
--   psql -U postgres -p 8888 -d tour_booking_db -f 03_tao_stored_procedures.sql
-- ============================================================


-- ████████████████████████████████████████████████████████████
-- PHẦN 1: HÀM XỬ LÝ TÀI KHOẢN & XÁC THỰC (AUTH)
-- ████████████████████████████████████████████████████████████


-- ============================================================
-- HÀM 1.1: Đăng ký tài khoản mới
-- ============================================================
-- Đầu vào: email, mật khẩu đã mã hóa, họ tên, số điện thoại
-- Đầu ra : Thông tin tài khoản vừa tạo (kèm vai trò CUSTOMER)
-- Logic  :
--   1. Kiểm tra email đã tồn tại chưa → nếu có thì báo lỗi
--   2. Tạo tài khoản mới trong bảng users
--   3. Gán vai trò CUSTOMER mặc định
--   4. Ghi nhật ký audit_logs
--   5. Trả về thông tin user
-- ============================================================
CREATE OR REPLACE FUNCTION fn_dang_ky_tai_khoan(
    p_email           VARCHAR,      -- Email đăng ký
    p_hashed_password VARCHAR,      -- Mật khẩu ĐÃ MÃ HÓA (bcrypt) - Python sẽ mã hóa trước khi gọi
    p_full_name       VARCHAR,      -- Họ và tên
    p_phone_number    VARCHAR DEFAULT NULL,  -- SĐT (tùy chọn)
    p_ip_address      VARCHAR DEFAULT NULL   -- IP người đăng ký (ghi log)
)
RETURNS TABLE (
    user_id     UUID,
    email       VARCHAR,
    full_name   VARCHAR,
    phone_number VARCHAR,
    is_active   BOOLEAN,
    created_at  TIMESTAMPTZ,
    role_names  TEXT[]           -- Mảng tên các vai trò (VD: {'CUSTOMER'})
) AS $$
DECLARE
    v_user_id   UUID;           -- Biến lưu ID user vừa tạo
    v_role_id   INTEGER;        -- Biến lưu ID của vai trò CUSTOMER
BEGIN
    -- Bước 1: Kiểm tra email trùng
    IF EXISTS (SELECT 1 FROM users u WHERE u.email = p_email) THEN
        RAISE EXCEPTION 'Email "%" đã được đăng ký trước đó', p_email
            USING ERRCODE = '23505';  -- Mã lỗi unique_violation
    END IF;

    -- Bước 2: Tạo tài khoản mới
    INSERT INTO users (email, hashed_password, full_name, phone_number, is_active)
    VALUES (p_email, p_hashed_password, p_full_name, p_phone_number, TRUE)
    RETURNING id INTO v_user_id;

    -- Bước 3: Gán vai trò CUSTOMER
    SELECT r.id INTO v_role_id FROM roles r WHERE r.name = 'CUSTOMER';
    IF v_role_id IS NOT NULL THEN
        INSERT INTO user_roles (user_id, role_id) VALUES (v_user_id, v_role_id);
    END IF;

    -- Bước 4: Ghi nhật ký
    INSERT INTO audit_logs (user_id, action, resource, resource_id, ip_address, details)
    VALUES (v_user_id, 'USER_REGISTERED', 'users', v_user_id::TEXT, p_ip_address,
            jsonb_build_object('email', p_email));

    -- Bước 5: Trả về thông tin user kèm danh sách vai trò
    RETURN QUERY
    SELECT
        u.id,
        u.email,
        u.full_name,
        u.phone_number,
        u.is_active,
        u.created_at,
        ARRAY(
            SELECT r.name FROM roles r
            JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = v_user_id
        )::TEXT[] AS role_names
    FROM users u
    WHERE u.id = v_user_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_dang_ky_tai_khoan IS 'Đăng ký tài khoản mới với vai trò CUSTOMER mặc định';


-- ============================================================
-- HÀM 1.2: Lấy thông tin user theo email (dùng khi đăng nhập)
-- ============================================================
-- Python sẽ gọi hàm này để lấy hashed_password rồi so sánh bcrypt
-- Logic: Truy vấn user + danh sách vai trò theo email
-- ============================================================
CREATE OR REPLACE FUNCTION fn_lay_user_theo_email(
    p_email VARCHAR
)
RETURNS TABLE (
    user_id         UUID,
    email           VARCHAR,
    hashed_password VARCHAR,
    full_name       VARCHAR,
    phone_number    VARCHAR,
    is_active       BOOLEAN,
    created_at      TIMESTAMPTZ,
    role_names      TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id,
        u.email,
        u.hashed_password,
        u.full_name,
        u.phone_number,
        u.is_active,
        u.created_at,
        ARRAY(
            SELECT r.name FROM roles r
            JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = u.id
        )::TEXT[] AS role_names
    FROM users u
    WHERE u.email = p_email;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_lay_user_theo_email IS 'Lấy thông tin user + roles theo email (dùng khi đăng nhập)';


-- ============================================================
-- HÀM 1.3: Lấy thông tin user theo ID
-- ============================================================
-- Dùng khi: xác thực JWT token, xem profile...
-- ============================================================
CREATE OR REPLACE FUNCTION fn_lay_user_theo_id(
    p_user_id UUID
)
RETURNS TABLE (
    user_id         UUID,
    email           VARCHAR,
    full_name       VARCHAR,
    phone_number    VARCHAR,
    is_active       BOOLEAN,
    created_at      TIMESTAMPTZ,
    updated_at      TIMESTAMPTZ,
    role_names      TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id,
        u.email,
        u.full_name,
        u.phone_number,
        u.is_active,
        u.created_at,
        u.updated_at,
        ARRAY(
            SELECT r.name FROM roles r
            JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = u.id
        )::TEXT[] AS role_names
    FROM users u
    WHERE u.id = p_user_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_lay_user_theo_id IS 'Lấy thông tin user + roles theo UUID';


-- ============================================================
-- HÀM 1.4: Ghi nhật ký đăng nhập
-- ============================================================
CREATE OR REPLACE FUNCTION fn_ghi_log_dang_nhap(
    p_user_id    UUID,
    p_ip_address VARCHAR DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO audit_logs (user_id, action, resource, resource_id, ip_address)
    VALUES (p_user_id, 'USER_LOGIN', 'users', p_user_id::TEXT, p_ip_address);
END;
$$ LANGUAGE plpgsql;


-- ████████████████████████████████████████████████████████████
-- PHẦN 2: HÀM QUẢN LÝ NGƯỜI DÙNG (ADMIN)
-- ████████████████████████████████████████████████████████████


-- ============================================================
-- HÀM 2.1: Lấy danh sách tất cả người dùng (phân trang)
-- ============================================================
CREATE OR REPLACE FUNCTION fn_lay_danh_sach_users(
    p_skip   INTEGER DEFAULT 0,     -- Bỏ qua bao nhiêu dòng (phân trang)
    p_limit  INTEGER DEFAULT 20,    -- Lấy tối đa bao nhiêu dòng
    p_is_active BOOLEAN DEFAULT NULL -- Lọc theo trạng thái (NULL = tất cả)
)
RETURNS TABLE (
    user_id         UUID,
    email           VARCHAR,
    full_name       VARCHAR,
    phone_number    VARCHAR,
    is_active       BOOLEAN,
    created_at      TIMESTAMPTZ,
    role_names      TEXT[],
    total_count     BIGINT          -- Tổng số user (để tính phân trang)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        u.id,
        u.email,
        u.full_name,
        u.phone_number,
        u.is_active,
        u.created_at,
        ARRAY(
            SELECT r.name FROM roles r
            JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = u.id
        )::TEXT[],
        -- Đếm tổng số user thỏa mãn điều kiện lọc (dùng window function)
        COUNT(*) OVER()::BIGINT AS total_count
    FROM users u
    WHERE (p_is_active IS NULL OR u.is_active = p_is_active)
    ORDER BY u.created_at DESC
    OFFSET p_skip
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- HÀM 2.2: Gán vai trò cho người dùng
-- ============================================================
CREATE OR REPLACE FUNCTION fn_gan_vai_tro(
    p_user_id   UUID,       -- ID người dùng
    p_role_name VARCHAR,    -- Tên vai trò cần gán (VD: 'STAFF')
    p_admin_id  UUID DEFAULT NULL  -- Admin thực hiện (ghi log)
)
RETURNS TABLE (
    user_id    UUID,
    email      VARCHAR,
    full_name  VARCHAR,
    role_names TEXT[]
) AS $$
DECLARE
    v_role_id INTEGER;
BEGIN
    -- Tìm vai trò theo tên
    SELECT r.id INTO v_role_id FROM roles r WHERE r.name = p_role_name;
    IF v_role_id IS NULL THEN
        RAISE EXCEPTION 'Vai trò "%" không tồn tại trong hệ thống', p_role_name;
    END IF;

    -- Kiểm tra user tồn tại
    IF NOT EXISTS (SELECT 1 FROM users u WHERE u.id = p_user_id) THEN
        RAISE EXCEPTION 'Không tìm thấy người dùng với ID "%"', p_user_id;
    END IF;

    -- Gán vai trò (bỏ qua nếu đã có)
    INSERT INTO user_roles (user_id, role_id)
    VALUES (p_user_id, v_role_id)
    ON CONFLICT (user_id, role_id) DO NOTHING;

    -- Ghi nhật ký
    INSERT INTO audit_logs (user_id, action, resource, resource_id, details)
    VALUES (p_admin_id, 'ROLE_ASSIGNED', 'users', p_user_id::TEXT,
            jsonb_build_object('role', p_role_name));

    -- Trả về thông tin user sau khi gán
    RETURN QUERY
    SELECT
        u.id, u.email, u.full_name,
        ARRAY(
            SELECT r.name FROM roles r
            JOIN user_roles ur ON r.id = ur.role_id
            WHERE ur.user_id = u.id
        )::TEXT[]
    FROM users u WHERE u.id = p_user_id;
END;
$$ LANGUAGE plpgsql;


-- ████████████████████████████████████████████████████████████
-- PHẦN 3: HÀM QUẢN LÝ TOUR DU LỊCH
-- ████████████████████████████████████████████████████████████


-- ============================================================
-- HÀM 3.1: Tạo tour mới (trạng thái DRAFT)
-- ============================================================
-- Logic:
--   1. Sinh mã tour tự động (TOUR-XXXXXX)
--   2. Tạo bản ghi tour với trạng thái DRAFT
--   3. Ghi nhật ký
--   4. Trả về thông tin tour vừa tạo
-- ============================================================
CREATE OR REPLACE FUNCTION fn_tao_tour(
    p_title             VARCHAR,
    p_description       TEXT,
    p_category          VARCHAR,
    p_destination       VARCHAR,
    p_base_price_adult  NUMERIC,
    p_base_price_child  NUMERIC,
    p_max_participants  INTEGER,
    p_start_date        DATE,
    p_end_date          DATE,
    p_created_by        UUID,
    p_ip_address        VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    tour_id           UUID,
    tour_code         VARCHAR,
    title             VARCHAR,
    description       TEXT,
    category          VARCHAR,
    destination       VARCHAR,
    base_price_adult  NUMERIC,
    base_price_child  NUMERIC,
    max_participants  INTEGER,
    available_slots   INTEGER,
    start_date        DATE,
    end_date          DATE,
    status            VARCHAR,
    created_by        UUID,
    created_at        TIMESTAMPTZ,
    updated_at        TIMESTAMPTZ
) AS $$
DECLARE
    v_tour_id   UUID;
    v_tour_code VARCHAR;
BEGIN
    -- Bước 1: Sinh mã tour duy nhất
    -- Lặp tối đa 10 lần để tránh trùng mã (xác suất trùng rất thấp)
    FOR i IN 1..10 LOOP
        v_tour_code := 'TOUR-' || UPPER(SUBSTR(md5(random()::text), 1, 6));
        EXIT WHEN NOT EXISTS (SELECT 1 FROM tours t WHERE t.tour_code = v_tour_code);
    END LOOP;

    -- Bước 2: Tạo tour
    INSERT INTO tours (
        tour_code, title, description, category, destination,
        base_price_adult, base_price_child,
        max_participants, available_slots,
        start_date, end_date, status, created_by
    )
    VALUES (
        v_tour_code, p_title, p_description, p_category, p_destination,
        p_base_price_adult, p_base_price_child,
        p_max_participants, p_max_participants,  -- Ban đầu available_slots = max_participants
        p_start_date, p_end_date, 'DRAFT', p_created_by
    )
    RETURNING id INTO v_tour_id;

    -- Bước 3: Ghi nhật ký
    INSERT INTO audit_logs (user_id, action, resource, resource_id, ip_address, details)
    VALUES (p_created_by, 'TOUR_CREATED', 'tours', v_tour_id::TEXT, p_ip_address,
            jsonb_build_object('tour_code', v_tour_code, 'title', p_title));

    -- Bước 4: Trả về thông tin tour
    RETURN QUERY
    SELECT t.id, t.tour_code, t.title, t.description, t.category, t.destination,
           t.base_price_adult, t.base_price_child,
           t.max_participants, t.available_slots,
           t.start_date, t.end_date, t.status, t.created_by,
           t.created_at, t.updated_at
    FROM tours t WHERE t.id = v_tour_id;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- HÀM 3.2: Thêm lịch trình 1 ngày cho tour
-- ============================================================
CREATE OR REPLACE FUNCTION fn_them_lich_trinh(
    p_tour_id    UUID,
    p_day_number INTEGER,
    p_title      VARCHAR
)
RETURNS TABLE (
    itinerary_id UUID,
    tour_id      UUID,
    day_number   INTEGER,
    title        VARCHAR
) AS $$
DECLARE
    v_id UUID;
BEGIN
    -- Kiểm tra tour tồn tại
    IF NOT EXISTS (SELECT 1 FROM tours t WHERE t.id = p_tour_id) THEN
        RAISE EXCEPTION 'Không tìm thấy tour với ID "%"', p_tour_id;
    END IF;

    INSERT INTO itineraries (tour_id, day_number, title)
    VALUES (p_tour_id, p_day_number, p_title)
    RETURNING id INTO v_id;

    RETURN QUERY
    SELECT i.id, i.tour_id, i.day_number, i.title
    FROM itineraries i WHERE i.id = v_id;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- HÀM 3.3: Thêm hoạt động vào lịch trình
-- ============================================================
CREATE OR REPLACE FUNCTION fn_them_hoat_dong(
    p_itinerary_id UUID,
    p_time_slot    TIME,
    p_place_name   VARCHAR,
    p_description  TEXT DEFAULT NULL,
    p_latitude     DOUBLE PRECISION DEFAULT NULL,
    p_longitude    DOUBLE PRECISION DEFAULT NULL
)
RETURNS TABLE (
    activity_id  UUID,
    itinerary_id UUID,
    time_slot    TIME,
    place_name   VARCHAR,
    description  TEXT
) AS $$
DECLARE
    v_id UUID;
BEGIN
    INSERT INTO itinerary_activities (itinerary_id, time_slot, place_name, description, latitude, longitude)
    VALUES (p_itinerary_id, p_time_slot, p_place_name, p_description, p_latitude, p_longitude)
    RETURNING id INTO v_id;

    RETURN QUERY
    SELECT a.id, a.itinerary_id, a.time_slot, a.place_name, a.description
    FROM itinerary_activities a WHERE a.id = v_id;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- HÀM 3.4: Lấy chi tiết tour (kèm lịch trình + hoạt động)
-- ============================================================
-- Trả về thông tin tour kèm số chỗ thực tế còn trống
-- (tính bằng cách đếm tổng booking chưa hủy)
-- ============================================================
CREATE OR REPLACE FUNCTION fn_lay_chi_tiet_tour(
    p_tour_id UUID
)
RETURNS TABLE (
    tour_id           UUID,
    tour_code         VARCHAR,
    title             VARCHAR,
    description       TEXT,
    category          VARCHAR,
    destination       VARCHAR,
    base_price_adult  NUMERIC,
    base_price_child  NUMERIC,
    max_participants  INTEGER,
    available_slots   INTEGER,
    booked_seats      INTEGER,    -- Số chỗ đã đặt (chưa hủy)
    start_date        DATE,
    end_date          DATE,
    status            VARCHAR,
    created_by        UUID,
    created_at        TIMESTAMPTZ,
    updated_at        TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id, t.tour_code, t.title, t.description, t.category, t.destination,
        t.base_price_adult, t.base_price_child,
        t.max_participants, t.available_slots,
        -- Tính số chỗ đã đặt = SUM(người lớn + trẻ em) của các booking chưa hủy
        COALESCE((
            SELECT SUM(b.num_adults + b.num_children)::INTEGER
            FROM bookings b
            WHERE b.tour_id = t.id
            AND b.status IN ('PENDING_PAYMENT', 'CONFIRMED')
        ), 0)::INTEGER AS booked_seats,
        t.start_date, t.end_date, t.status, t.created_by,
        t.created_at, t.updated_at
    FROM tours t
    WHERE t.id = p_tour_id;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- HÀM 3.5: Lấy lịch trình + hoạt động của 1 tour
-- ============================================================
CREATE OR REPLACE FUNCTION fn_lay_lich_trinh_tour(p_tour_id UUID)
RETURNS TABLE (
    itinerary_id    UUID,
    day_number      INTEGER,
    itinerary_title VARCHAR,
    activity_id     UUID,
    time_slot       TIME,
    place_name      VARCHAR,
    activity_desc   TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        i.id, i.day_number, i.title,
        a.id, a.time_slot, a.place_name, a.description
    FROM itineraries i
    LEFT JOIN itinerary_activities a ON a.itinerary_id = i.id
    WHERE i.tour_id = p_tour_id
    ORDER BY i.day_number, a.time_slot NULLS LAST;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- HÀM 3.6: Tìm kiếm và lọc danh sách tour (phân trang)
-- ============================================================
-- Hỗ trợ lọc theo: điểm đến, danh mục, trạng thái, khoảng giá,
-- ngày khởi hành, và tìm kiếm theo tên/mô tả.
-- ============================================================
CREATE OR REPLACE FUNCTION fn_tim_kiem_tour(
    p_destination     VARCHAR DEFAULT NULL,    -- Lọc theo điểm đến
    p_category        VARCHAR DEFAULT NULL,    -- Lọc theo danh mục
    p_status          VARCHAR DEFAULT NULL,    -- Lọc theo trạng thái
    p_min_price       NUMERIC DEFAULT NULL,    -- Giá tối thiểu
    p_max_price       NUMERIC DEFAULT NULL,    -- Giá tối đa
    p_start_date_from DATE DEFAULT NULL,       -- Ngày khởi hành từ
    p_start_date_to   DATE DEFAULT NULL,       -- Ngày khởi hành đến
    p_search          VARCHAR DEFAULT NULL,    -- Từ khóa tìm kiếm
    p_sort_by         VARCHAR DEFAULT 'created_at',  -- Sắp xếp theo: price, start_date, created_at
    p_sort_order      VARCHAR DEFAULT 'desc',        -- Thứ tự: asc, desc
    p_skip            INTEGER DEFAULT 0,
    p_limit           INTEGER DEFAULT 20
)
RETURNS TABLE (
    tour_id           UUID,
    tour_code         VARCHAR,
    title             VARCHAR,
    category          VARCHAR,
    destination       VARCHAR,
    base_price_adult  NUMERIC,
    base_price_child  NUMERIC,
    max_participants  INTEGER,
    available_slots   INTEGER,
    start_date        DATE,
    end_date          DATE,
    status            VARCHAR,
    created_at        TIMESTAMPTZ,
    total_count       BIGINT       -- Tổng số tour thỏa mãn (dùng cho phân trang)
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        t.id, t.tour_code, t.title, t.category, t.destination,
        t.base_price_adult, t.base_price_child,
        t.max_participants, t.available_slots,
        t.start_date, t.end_date, t.status, t.created_at,
        COUNT(*) OVER()::BIGINT AS total_count
    FROM tours t
    WHERE
        -- Lọc theo điểm đến (tìm kiếm gần đúng, không phân biệt hoa thường)
        (p_destination IS NULL OR t.destination ILIKE '%' || p_destination || '%')
        AND (p_category IS NULL OR t.category = p_category)
        AND (p_status IS NULL OR t.status = p_status)
        AND (p_min_price IS NULL OR t.base_price_adult >= p_min_price)
        AND (p_max_price IS NULL OR t.base_price_adult <= p_max_price)
        AND (p_start_date_from IS NULL OR t.start_date >= p_start_date_from)
        AND (p_start_date_to IS NULL OR t.start_date <= p_start_date_to)
        -- Tìm kiếm trong tên hoặc mô tả tour
        AND (p_search IS NULL OR t.title ILIKE '%' || p_search || '%'
             OR t.description ILIKE '%' || p_search || '%')
    ORDER BY
        -- Sắp xếp linh hoạt theo tham số
        CASE WHEN p_sort_by = 'price' AND p_sort_order = 'asc' THEN t.base_price_adult END ASC,
        CASE WHEN p_sort_by = 'price' AND p_sort_order = 'desc' THEN t.base_price_adult END DESC,
        CASE WHEN p_sort_by = 'start_date' AND p_sort_order = 'asc' THEN t.start_date END ASC,
        CASE WHEN p_sort_by = 'start_date' AND p_sort_order = 'desc' THEN t.start_date END DESC,
        CASE WHEN p_sort_by = 'created_at' AND p_sort_order = 'asc' THEN t.created_at END ASC,
        CASE WHEN p_sort_by = 'created_at' AND p_sort_order = 'desc' THEN t.created_at END DESC,
        t.created_at DESC  -- Mặc định sắp xếp theo ngày tạo mới nhất
    OFFSET p_skip
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- HÀM 3.7: Xuất bản tour (DRAFT → PUBLISHED)
-- ============================================================
-- Quy tắc:
--   - Chỉ tour ở trạng thái DRAFT mới được xuất bản
--   - Tour phải có ngày khởi hành trong tương lai
--   - Tour phải có max_participants > 0
-- ============================================================
CREATE OR REPLACE FUNCTION fn_xuat_ban_tour(
    p_tour_id    UUID,
    p_user_id    UUID,
    p_ip_address VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    tour_id  UUID,
    status   VARCHAR,
    message  TEXT
) AS $$
DECLARE
    v_current_status VARCHAR;
    v_start_date     DATE;
    v_max_part       INTEGER;
BEGIN
    -- Lấy thông tin hiện tại của tour
    SELECT t.status, t.start_date, t.max_participants
    INTO v_current_status, v_start_date, v_max_part
    FROM tours t WHERE t.id = p_tour_id;

    -- Kiểm tra tour tồn tại
    IF v_current_status IS NULL THEN
        RAISE EXCEPTION 'Không tìm thấy tour với ID "%"', p_tour_id;
    END IF;

    -- Kiểm tra trạng thái hiện tại phải là DRAFT
    IF v_current_status != 'DRAFT' THEN
        RAISE EXCEPTION 'Chỉ tour ở trạng thái DRAFT mới được xuất bản. Hiện tại: %', v_current_status;
    END IF;

    -- Kiểm tra ngày khởi hành phải ở tương lai
    IF v_start_date <= CURRENT_DATE THEN
        RAISE EXCEPTION 'Ngày khởi hành phải sau ngày hôm nay để xuất bản tour';
    END IF;

    -- Cập nhật trạng thái
    UPDATE tours SET status = 'PUBLISHED' WHERE id = p_tour_id;

    -- Ghi nhật ký
    INSERT INTO audit_logs (user_id, action, resource, resource_id, ip_address)
    VALUES (p_user_id, 'TOUR_PUBLISHED', 'tours', p_tour_id::TEXT, p_ip_address);

    RETURN QUERY SELECT p_tour_id, 'PUBLISHED'::VARCHAR, 'Tour đã được xuất bản thành công'::TEXT;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- HÀM 3.8: Đóng tour (PUBLISHED → ARCHIVED)
-- ============================================================
CREATE OR REPLACE FUNCTION fn_dong_tour(
    p_tour_id    UUID,
    p_user_id    UUID,
    p_ip_address VARCHAR DEFAULT NULL
)
RETURNS TABLE (tour_id UUID, status VARCHAR, message TEXT) AS $$
DECLARE
    v_current_status VARCHAR;
    v_booked INTEGER;
BEGIN
    SELECT t.status INTO v_current_status FROM tours t WHERE t.id = p_tour_id;

    IF v_current_status IS NULL THEN
        RAISE EXCEPTION 'Không tìm thấy tour với ID "%"', p_tour_id;
    END IF;

    IF v_current_status = 'ARCHIVED' THEN
        RAISE EXCEPTION 'Tour đã được đóng (ARCHIVED) trước đó rồi';
    END IF;

    -- Kiểm tra booking đang hoạt động
    SELECT COALESCE(SUM(b.num_adults + b.num_children), 0)::INTEGER
    INTO v_booked
    FROM bookings b WHERE b.tour_id = p_tour_id AND b.status IN ('PENDING_PAYMENT', 'CONFIRMED');

    IF v_booked > 0 AND v_current_status = 'PUBLISHED' THEN
        RAISE EXCEPTION 'Không thể đóng tour khi còn % chỗ đã đặt. Hãy hủy các đơn trước.', v_booked;
    END IF;

    UPDATE tours SET status = 'ARCHIVED' WHERE id = p_tour_id;

    INSERT INTO audit_logs (user_id, action, resource, resource_id, ip_address)
    VALUES (p_user_id, 'TOUR_ARCHIVED', 'tours', p_tour_id::TEXT, p_ip_address);

    RETURN QUERY SELECT p_tour_id, 'ARCHIVED'::VARCHAR, 'Tour đã được đóng thành công'::TEXT;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- HÀM 3.9: Hủy tour (bất kỳ trạng thái → CANCELLED)
-- ============================================================
CREATE OR REPLACE FUNCTION fn_huy_tour(
    p_tour_id    UUID,
    p_user_id    UUID,
    p_ip_address VARCHAR DEFAULT NULL
)
RETURNS TABLE (tour_id UUID, status VARCHAR, message TEXT) AS $$
DECLARE
    v_current_status VARCHAR;
BEGIN
    SELECT t.status INTO v_current_status FROM tours t WHERE t.id = p_tour_id;

    IF v_current_status IS NULL THEN
        RAISE EXCEPTION 'Không tìm thấy tour với ID "%"', p_tour_id;
    END IF;

    IF v_current_status = 'CANCELLED' THEN
        RAISE EXCEPTION 'Tour đã bị hủy trước đó rồi';
    END IF;

    UPDATE tours SET status = 'CANCELLED' WHERE id = p_tour_id;

    -- Tự động hủy tất cả booking đang chờ của tour này
    UPDATE bookings SET status = 'CANCELLED'
    WHERE bookings.tour_id = p_tour_id AND bookings.status IN ('PENDING_PAYMENT');

    INSERT INTO audit_logs (user_id, action, resource, resource_id, ip_address, details)
    VALUES (p_user_id, 'TOUR_CANCELLED', 'tours', p_tour_id::TEXT, p_ip_address,
            jsonb_build_object('previous_status', v_current_status));

    RETURN QUERY SELECT p_tour_id, 'CANCELLED'::VARCHAR, 'Tour đã bị hủy thành công'::TEXT;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- HÀM 3.10: Cập nhật thông tin tour
-- ============================================================
CREATE OR REPLACE FUNCTION fn_cap_nhat_tour(
    p_tour_id           UUID,
    p_title             VARCHAR DEFAULT NULL,
    p_description       TEXT DEFAULT NULL,
    p_category          VARCHAR DEFAULT NULL,
    p_destination       VARCHAR DEFAULT NULL,
    p_base_price_adult  NUMERIC DEFAULT NULL,
    p_base_price_child  NUMERIC DEFAULT NULL,
    p_max_participants  INTEGER DEFAULT NULL,
    p_start_date        DATE DEFAULT NULL,
    p_end_date          DATE DEFAULT NULL,
    p_user_id           UUID DEFAULT NULL,
    p_ip_address        VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    tour_id UUID, tour_code VARCHAR, title VARCHAR, status VARCHAR, message TEXT
) AS $$
DECLARE
    v_status VARCHAR;
BEGIN
    SELECT t.status INTO v_status FROM tours t WHERE t.id = p_tour_id;

    IF v_status IS NULL THEN
        RAISE EXCEPTION 'Không tìm thấy tour với ID "%"', p_tour_id;
    END IF;

    IF v_status NOT IN ('DRAFT', 'PUBLISHED') THEN
        RAISE EXCEPTION 'Không thể sửa tour ở trạng thái "%". Chỉ sửa được DRAFT hoặc PUBLISHED.', v_status;
    END IF;

    -- Cập nhật từng trường nếu có giá trị mới (NULL = giữ nguyên)
    UPDATE tours SET
        title = COALESCE(p_title, tours.title),
        description = COALESCE(p_description, tours.description),
        category = COALESCE(p_category, tours.category),
        destination = COALESCE(p_destination, tours.destination),
        base_price_adult = COALESCE(p_base_price_adult, tours.base_price_adult),
        base_price_child = COALESCE(p_base_price_child, tours.base_price_child),
        max_participants = COALESCE(p_max_participants, tours.max_participants),
        start_date = COALESCE(p_start_date, tours.start_date),
        end_date = COALESCE(p_end_date, tours.end_date)
    WHERE id = p_tour_id;

    -- Ghi log
    INSERT INTO audit_logs (user_id, action, resource, resource_id, ip_address)
    VALUES (p_user_id, 'TOUR_UPDATED', 'tours', p_tour_id::TEXT, p_ip_address);

    RETURN QUERY
    SELECT t.id, t.tour_code, t.title, t.status, 'Cập nhật tour thành công'::TEXT
    FROM tours t WHERE t.id = p_tour_id;
END;
$$ LANGUAGE plpgsql;


-- ████████████████████████████████████████████████████████████
-- PHẦN 4: HÀM QUẢN LÝ ĐẶT TOUR (BOOKING)
-- ████████████████████████████████████████████████████████████


-- ============================================================
-- HÀM 4.1: Tạo đơn đặt tour (HÀM QUAN TRỌNG NHẤT)
-- ============================================================
-- THUẬT TOÁN:
--   1. Kiểm tra tour tồn tại và đang mở bán (PUBLISHED)
--   2. Tính tổng số chỗ đã đặt (chưa hủy) trên tour
--   3. Kiểm tra còn đủ chỗ trống không
--   4. Tính tổng tiền: (số người lớn × giá người lớn) + (số trẻ em × giá trẻ em)
--   5. Sinh mã đặt tour duy nhất (BK-YYYYMMDD-XXXXXX)
--   6. Lưu đơn đặt tour vào bảng bookings
--   7. Ghi nhật ký
--   8. Trả về thông tin đơn vừa tạo
--
-- BẢO MẬT: Toàn bộ logic kiểm tra chỗ trống được xử lý trong DB,
-- tránh race condition (2 người đặt cùng lúc) nhờ transaction
-- ============================================================
CREATE OR REPLACE FUNCTION fn_tao_don_dat_tour(
    p_user_id          UUID,
    p_tour_id          UUID,
    p_num_adults       INTEGER,
    p_num_children     INTEGER DEFAULT 0,
    p_contact_name     VARCHAR DEFAULT NULL,
    p_contact_email    VARCHAR DEFAULT NULL,
    p_contact_phone    VARCHAR DEFAULT NULL,
    p_special_requests TEXT DEFAULT NULL,
    p_ip_address       VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    booking_id      UUID,
    booking_code    VARCHAR,
    tour_id         UUID,
    tour_title      VARCHAR,
    status          VARCHAR,
    num_adults      INTEGER,
    num_children    INTEGER,
    total_price     NUMERIC,
    contact_name    VARCHAR,
    contact_email   VARCHAR,
    contact_phone   VARCHAR,
    special_requests TEXT,
    created_at      TIMESTAMPTZ
) AS $$
DECLARE
    v_tour_status       VARCHAR;        -- Trạng thái hiện tại của tour
    v_tour_title        VARCHAR;        -- Tên tour
    v_price_adult       NUMERIC;        -- Giá vé người lớn
    v_price_child       NUMERIC;        -- Giá vé trẻ em
    v_max_participants  INTEGER;        -- Tổng số chỗ tối đa
    v_booked_seats      INTEGER;        -- Số chỗ đã đặt (chưa hủy)
    v_available         INTEGER;        -- Số chỗ còn trống
    v_requested_seats   INTEGER;        -- Số chỗ khách yêu cầu
    v_total_price       NUMERIC;        -- Tổng tiền vé
    v_booking_code      VARCHAR;        -- Mã đặt tour
    v_booking_id        UUID;           -- ID đơn đặt tour
    v_user_name         VARCHAR;        -- Tên user (dùng làm contact_name mặc định)
    v_user_email        VARCHAR;        -- Email user
BEGIN
    -- ========== BƯỚC 1: Lấy thông tin tour ==========
    SELECT t.status, t.title, t.base_price_adult, t.base_price_child, t.max_participants
    INTO v_tour_status, v_tour_title, v_price_adult, v_price_child, v_max_participants
    FROM tours t
    WHERE t.id = p_tour_id
    FOR UPDATE;  -- FOR UPDATE: Khóa dòng này lại, tránh 2 người đặt cùng lúc (race condition)

    -- Kiểm tra tour có tồn tại không
    IF v_tour_status IS NULL THEN
        RAISE EXCEPTION 'Không tìm thấy tour với ID "%"', p_tour_id;
    END IF;

    -- Kiểm tra tour đang mở bán
    IF v_tour_status != 'PUBLISHED' THEN
        RAISE EXCEPTION 'Tour "%" hiện không mở đặt chỗ (Trạng thái: %)', v_tour_title, v_tour_status;
    END IF;

    -- ========== BƯỚC 2: Kiểm tra chỗ trống ==========
    -- Đếm tổng số chỗ đã đặt (booking chưa hủy và chưa hết hạn)
    SELECT COALESCE(SUM(b.num_adults + b.num_children), 0)::INTEGER
    INTO v_booked_seats
    FROM bookings b
    WHERE b.tour_id = p_tour_id
    AND b.status IN ('PENDING_PAYMENT', 'CONFIRMED');

    v_available := v_max_participants - v_booked_seats;
    v_requested_seats := p_num_adults + p_num_children;

    IF v_requested_seats > v_available THEN
        RAISE EXCEPTION 'Tour không đủ chỗ trống. Yêu cầu % chỗ nhưng chỉ còn % chỗ.',
            v_requested_seats, GREATEST(v_available, 0);
    END IF;

    -- ========== BƯỚC 3: Tính tổng tiền ==========
    -- Công thức: (số người lớn × giá người lớn) + (số trẻ em × giá trẻ em)
    v_total_price := (p_num_adults * v_price_adult) + (p_num_children * v_price_child);

    -- ========== BƯỚC 4: Lấy thông tin liên hệ mặc định từ user ==========
    SELECT u.full_name, u.email INTO v_user_name, v_user_email
    FROM users u WHERE u.id = p_user_id;

    -- ========== BƯỚC 5: Sinh mã booking ==========
    -- Format: BK-YYYYMMDD-XXXXXX (6 ký tự ngẫu nhiên)
    v_booking_code := 'BK-' || TO_CHAR(NOW(), 'YYYYMMDD') || '-' || UPPER(SUBSTR(md5(random()::text), 1, 6));

    -- ========== BƯỚC 6: Lưu đơn đặt tour ==========
    INSERT INTO bookings (
        booking_code, user_id, tour_id, status,
        num_adults, num_children, total_price,
        contact_name, contact_email, contact_phone, special_requests
    )
    VALUES (
        v_booking_code, p_user_id, p_tour_id, 'PENDING_PAYMENT',
        p_num_adults, p_num_children, v_total_price,
        COALESCE(p_contact_name, v_user_name),
        COALESCE(p_contact_email, v_user_email),
        COALESCE(p_contact_phone, ''),
        p_special_requests
    )
    RETURNING id INTO v_booking_id;

    -- ========== BƯỚC 7: Cập nhật số chỗ trống trên tour ==========
    UPDATE tours SET available_slots = available_slots - v_requested_seats
    WHERE id = p_tour_id;

    -- ========== BƯỚC 8: Ghi nhật ký ==========
    INSERT INTO audit_logs (user_id, action, resource, resource_id, ip_address, details)
    VALUES (p_user_id, 'BOOKING_CREATED', 'bookings', v_booking_id::TEXT, p_ip_address,
            jsonb_build_object(
                'booking_code', v_booking_code,
                'tour_title', v_tour_title,
                'total_price', v_total_price,
                'seats', v_requested_seats
            ));

    -- ========== BƯỚC 9: Trả về kết quả ==========
    RETURN QUERY
    SELECT
        v_booking_id, v_booking_code::VARCHAR, p_tour_id, v_tour_title,
        'PENDING_PAYMENT'::VARCHAR,
        p_num_adults, p_num_children, v_total_price,
        COALESCE(p_contact_name, v_user_name)::VARCHAR,
        COALESCE(p_contact_email, v_user_email)::VARCHAR,
        COALESCE(p_contact_phone, '')::VARCHAR,
        p_special_requests::TEXT,
        NOW();
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_tao_don_dat_tour IS 'Tạo đơn đặt tour - tự động tính tiền, kiểm tra chỗ trống, chống race condition';


-- ============================================================
-- HÀM 4.2: Thêm hành khách vào đơn đặt tour
-- ============================================================
CREATE OR REPLACE FUNCTION fn_them_hanh_khach(
    p_booking_id     UUID,
    p_full_name      VARCHAR,
    p_passenger_type VARCHAR DEFAULT 'ADULT',
    p_id_card_number VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    passenger_id    UUID,
    booking_id      UUID,
    full_name       VARCHAR,
    passenger_type  VARCHAR,
    id_card_number  VARCHAR
) AS $$
DECLARE
    v_id UUID;
BEGIN
    INSERT INTO booking_passengers (booking_id, full_name, passenger_type, id_card_number)
    VALUES (p_booking_id, p_full_name, p_passenger_type, p_id_card_number)
    RETURNING id INTO v_id;

    RETURN QUERY
    SELECT bp.id, bp.booking_id, bp.full_name, bp.passenger_type, bp.id_card_number
    FROM booking_passengers bp WHERE bp.id = v_id;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- HÀM 4.3: Xem chi tiết đơn đặt tour
-- ============================================================
CREATE OR REPLACE FUNCTION fn_lay_chi_tiet_booking(
    p_booking_id UUID
)
RETURNS TABLE (
    booking_id       UUID,
    booking_code     VARCHAR,
    user_id          UUID,
    tour_id          UUID,
    tour_title       VARCHAR,
    status           VARCHAR,
    num_adults       INTEGER,
    num_children     INTEGER,
    total_price      NUMERIC,
    contact_name     VARCHAR,
    contact_email    VARCHAR,
    contact_phone    VARCHAR,
    special_requests TEXT,
    created_at       TIMESTAMPTZ,
    updated_at       TIMESTAMPTZ
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        b.id, b.booking_code, b.user_id, b.tour_id,
        t.title AS tour_title,
        b.status, b.num_adults, b.num_children, b.total_price,
        b.contact_name, b.contact_email, b.contact_phone,
        b.special_requests, b.created_at, b.updated_at
    FROM bookings b
    JOIN tours t ON t.id = b.tour_id
    WHERE b.id = p_booking_id;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- HÀM 4.4: Lấy danh sách hành khách của 1 đơn
-- ============================================================
CREATE OR REPLACE FUNCTION fn_lay_hanh_khach_booking(p_booking_id UUID)
RETURNS TABLE (
    passenger_id   UUID,
    full_name      VARCHAR,
    passenger_type VARCHAR,
    id_card_number VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT bp.id, bp.full_name, bp.passenger_type, bp.id_card_number
    FROM booking_passengers bp
    WHERE bp.booking_id = p_booking_id
    ORDER BY bp.created_at;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- HÀM 4.5: Xem lịch sử đặt tour của bản thân (phân trang)
-- ============================================================
CREATE OR REPLACE FUNCTION fn_lay_booking_cua_toi(
    p_user_id UUID,
    p_skip    INTEGER DEFAULT 0,
    p_limit   INTEGER DEFAULT 10
)
RETURNS TABLE (
    booking_id   UUID,
    booking_code VARCHAR,
    tour_id      UUID,
    tour_title   VARCHAR,
    status       VARCHAR,
    num_adults   INTEGER,
    num_children INTEGER,
    total_price  NUMERIC,
    contact_name VARCHAR,
    created_at   TIMESTAMPTZ,
    total_count  BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        b.id, b.booking_code, b.tour_id,
        t.title, b.status,
        b.num_adults, b.num_children, b.total_price,
        b.contact_name, b.created_at,
        COUNT(*) OVER()::BIGINT
    FROM bookings b
    JOIN tours t ON t.id = b.tour_id
    WHERE b.user_id = p_user_id
    ORDER BY b.created_at DESC
    OFFSET p_skip LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- HÀM 4.6: Xem toàn bộ đơn đặt tour (Admin/Staff, phân trang)
-- ============================================================
CREATE OR REPLACE FUNCTION fn_lay_tat_ca_booking(
    p_skip       INTEGER DEFAULT 0,
    p_limit      INTEGER DEFAULT 20,
    p_status     VARCHAR DEFAULT NULL,    -- Lọc theo trạng thái
    p_tour_id    UUID DEFAULT NULL        -- Lọc theo tour
)
RETURNS TABLE (
    booking_id   UUID,
    booking_code VARCHAR,
    user_id      UUID,
    tour_id      UUID,
    tour_title   VARCHAR,
    status       VARCHAR,
    num_adults   INTEGER,
    num_children INTEGER,
    total_price  NUMERIC,
    contact_name VARCHAR,
    created_at   TIMESTAMPTZ,
    total_count  BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        b.id, b.booking_code, b.user_id, b.tour_id,
        t.title, b.status,
        b.num_adults, b.num_children, b.total_price,
        b.contact_name, b.created_at,
        COUNT(*) OVER()::BIGINT
    FROM bookings b
    JOIN tours t ON t.id = b.tour_id
    WHERE
        (p_status IS NULL OR b.status = p_status)
        AND (p_tour_id IS NULL OR b.tour_id = p_tour_id)
    ORDER BY b.created_at DESC
    OFFSET p_skip LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- HÀM 4.7: Hủy đơn đặt tour
-- ============================================================
-- THUẬT TOÁN:
--   1. Kiểm tra đơn tồn tại
--   2. Kiểm tra quyền: chỉ chủ đơn hoặc Admin mới được hủy
--   3. Kiểm tra trạng thái: đơn đã hủy thì không hủy lại
--   4. Cập nhật trạng thái → CANCELLED
--   5. Hoàn trả số chỗ trống cho tour
--   6. Ghi nhật ký
-- ============================================================
CREATE OR REPLACE FUNCTION fn_huy_don_dat_tour(
    p_booking_id     UUID,
    p_current_user_id UUID,
    p_is_admin       BOOLEAN DEFAULT FALSE,
    p_ip_address     VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    booking_id   UUID,
    booking_code VARCHAR,
    status       VARCHAR,
    message      TEXT
) AS $$
DECLARE
    v_booking_user_id UUID;
    v_current_status  VARCHAR;
    v_tour_id         UUID;
    v_seats           INTEGER;
    v_code            VARCHAR;
BEGIN
    -- Lấy thông tin đơn hiện tại
    SELECT b.user_id, b.status, b.tour_id, (b.num_adults + b.num_children), b.booking_code
    INTO v_booking_user_id, v_current_status, v_tour_id, v_seats, v_code
    FROM bookings b WHERE b.id = p_booking_id;

    IF v_current_status IS NULL THEN
        RAISE EXCEPTION 'Không tìm thấy đơn đặt tour với ID "%"', p_booking_id;
    END IF;

    -- Kiểm tra quyền
    IF NOT p_is_admin AND v_booking_user_id != p_current_user_id THEN
        RAISE EXCEPTION 'Bạn không có quyền hủy đơn đặt tour này';
    END IF;

    -- Kiểm tra trạng thái
    IF v_current_status = 'CANCELLED' THEN
        RAISE EXCEPTION 'Đơn đặt tour này đã bị hủy trước đó rồi';
    END IF;

    -- Cập nhật trạng thái
    UPDATE bookings SET status = 'CANCELLED' WHERE id = p_booking_id;

    -- Hoàn trả chỗ cho tour (chỉ hoàn nếu trước đó chưa hủy/hết hạn)
    IF v_current_status IN ('PENDING_PAYMENT', 'CONFIRMED') THEN
        UPDATE tours SET available_slots = available_slots + v_seats WHERE id = v_tour_id;
    END IF;

    -- Ghi log
    INSERT INTO audit_logs (user_id, action, resource, resource_id, ip_address, details)
    VALUES (p_current_user_id, 'BOOKING_CANCELLED', 'bookings', p_booking_id::TEXT, p_ip_address,
            jsonb_build_object('booking_code', v_code, 'reason', 'Người dùng yêu cầu hủy'));

    RETURN QUERY SELECT p_booking_id, v_code::VARCHAR, 'CANCELLED'::VARCHAR, 'Đơn đặt tour đã được hủy thành công'::TEXT;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- HÀM 4.8: Xác nhận đơn đặt tour (Admin duyệt)
-- ============================================================
-- Chuyển trạng thái: PENDING_PAYMENT → CONFIRMED
-- ============================================================
CREATE OR REPLACE FUNCTION fn_xac_nhan_don_dat_tour(
    p_booking_id UUID,
    p_admin_id   UUID,
    p_ip_address VARCHAR DEFAULT NULL
)
RETURNS TABLE (
    booking_id   UUID,
    booking_code VARCHAR,
    status       VARCHAR,
    message      TEXT
) AS $$
DECLARE
    v_current_status VARCHAR;
    v_code           VARCHAR;
BEGIN
    SELECT b.status, b.booking_code INTO v_current_status, v_code
    FROM bookings b WHERE b.id = p_booking_id;

    IF v_current_status IS NULL THEN
        RAISE EXCEPTION 'Không tìm thấy đơn đặt tour với ID "%"', p_booking_id;
    END IF;

    IF v_current_status = 'CANCELLED' THEN
        RAISE EXCEPTION 'Không thể xác nhận đơn đã bị hủy';
    END IF;

    IF v_current_status = 'CONFIRMED' THEN
        RAISE EXCEPTION 'Đơn này đã được xác nhận trước đó rồi';
    END IF;

    UPDATE bookings SET status = 'CONFIRMED' WHERE id = p_booking_id;

    INSERT INTO audit_logs (user_id, action, resource, resource_id, ip_address, details)
    VALUES (p_admin_id, 'BOOKING_CONFIRMED', 'bookings', p_booking_id::TEXT, p_ip_address,
            jsonb_build_object('booking_code', v_code));

    RETURN QUERY SELECT p_booking_id, v_code::VARCHAR, 'CONFIRMED'::VARCHAR, 'Đơn đặt tour đã được xác nhận thành công'::TEXT;
END;
$$ LANGUAGE plpgsql;


-- ████████████████████████████████████████████████████████████
-- PHẦN 5: HÀM TIỆN ÍCH (UTILITY)
-- ████████████████████████████████████████████████████████████

-- ============================================================
-- HÀM 5.1: Ghi nhật ký chung (Audit Log)
-- ============================================================
CREATE OR REPLACE FUNCTION fn_ghi_nhat_ky(
    p_user_id     UUID,
    p_action      VARCHAR,
    p_resource    VARCHAR DEFAULT NULL,
    p_resource_id VARCHAR DEFAULT NULL,
    p_details     JSONB DEFAULT NULL,
    p_ip_address  VARCHAR DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_log_id UUID;
BEGIN
    INSERT INTO audit_logs (user_id, action, resource, resource_id, details, ip_address)
    VALUES (p_user_id, p_action, p_resource, p_resource_id, p_details, p_ip_address)
    RETURNING id INTO v_log_id;

    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- HOÀN TẤT: Tất cả stored procedures đã được tạo thành công
-- Tiếp theo chạy file 04_du_lieu_mau.sql để chèn dữ liệu mẫu
-- ============================================================
