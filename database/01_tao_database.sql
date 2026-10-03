-- ============================================================
-- FILE: 01_tao_database.sql (MySQL)
-- MỤC ĐÍCH: Tạo Database MySQL cho hệ thống Đặt Tour Du Lịch
-- ============================================================
-- HƯỚNG DẪN CHẠY:
--   Mở MySQL Workbench, phpMyAdmin, DBeaver, Navicat hoặc Terminal MySQL
--   kết nối với user "root" hoặc user có quyền tạo database.
--
--   Lệnh chạy qua Terminal MySQL:
--   mysql -u root -p < 01_tao_database.sql
-- ============================================================

-- Bước 1: Xóa database cũ nếu cần làm mới (bỏ comment dòng dưới khi muốn reset)
-- DROP DATABASE IF EXISTS tour_booking_db;

-- Bước 2: Tạo database mới với bảng mã utf8mb4 hỗ trợ Tiếng Việt và icon đầy đủ
CREATE DATABASE IF NOT EXISTS tour_booking_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

-- Bước 3: Chọn database vừa tạo để sẵn sàng thực thi các bước tiếp theo
USE tour_booking_db;

-- Ghi chú: Sau khi chạy file này, hãy chạy tiếp file 02_tao_bang.sql
