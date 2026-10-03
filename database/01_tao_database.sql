-- ============================================================
-- FILE: 01_tao_database.sql
-- MỤC ĐÍCH: Tạo database cho hệ thống đặt tour du lịch
-- ============================================================
-- HƯỚNG DẪN CHẠY:
--   Mở pgAdmin hoặc psql, kết nối vào PostgreSQL với user "postgres"
--   Rồi chạy file này để tạo database mới.
--
--   Lệnh chạy qua psql:
--   psql -U postgres -p 8888 -f 01_tao_database.sql
-- ============================================================

-- Bước 1: Xóa database cũ nếu tồn tại (CHỈ dùng khi phát triển, KHÔNG dùng production)
-- DROP DATABASE IF EXISTS tour_booking_db;

-- Bước 2: Tạo database mới
-- Encoding UTF8 để hỗ trợ Tiếng Việt đầy đủ
CREATE DATABASE tour_booking_db
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0
    CONNECTION LIMIT = -1;     -- Không giới hạn số kết nối

-- Ghi chú: Sau khi tạo xong database, hãy kết nối vào database "tour_booking_db"
-- rồi chạy tiếp file 02_tao_bang.sql
-- Lệnh kết nối: \c tour_booking_db
