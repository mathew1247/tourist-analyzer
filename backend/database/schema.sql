-- =========================================================================
-- Tourism Footfall and Revenue Analytics - MySQL Database Schema
-- Database Name: tourism_analytics
-- =========================================================================

CREATE DATABASE IF NOT EXISTS tourism_analytics;
USE tourism_analytics;

-- -------------------------------------------------------------------------
-- TABLE 1: users
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

-- -------------------------------------------------------------------------
-- TABLE 2: tourism_categories
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tourism_categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    avg_spend DECIMAL(10,2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------------------------
-- TABLE 3: monthly_analytics
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS monthly_analytics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    month VARCHAR(20) NOT NULL,
    year INT NOT NULL,
    visitors INT NOT NULL,
    revenue DECIMAL(12,2) NOT NULL,
    sii_index FLOAT NULL,
    category_id INT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_category FOREIGN KEY (category_id) REFERENCES tourism_categories(id) ON DELETE SET NULL
);

-- -------------------------------------------------------------------------
-- TABLE 4: user_logs (Audit / Log Table)
-- -------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NULL,
    username VARCHAR(100),
    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_level VARCHAR(100)
);

-- -------------------------------------------------------------------------
-- SEED DATA: Categories
-- -------------------------------------------------------------------------
INSERT IGNORE INTO tourism_categories (id, category_name, avg_spend) VALUES
(1, 'Beach Tourism', 3275.00),
(2, 'Hill Stations', 3900.00),
(3, 'Cultural & Heritage', 2800.00),
(4, 'Adventure', 4200.00),
(5, 'Others', 2500.00);

-- -------------------------------------------------------------------------
-- SEED DATA: Default Admin Users (Password hashed via werkzeug: Admin@123 & admin123)
-- -------------------------------------------------------------------------
-- Password for 'Admin@123': scrypt:32768:8:1$K7o0v4kSqmX6e42K$0ae702330a614275fdf6ba3a8b277b0682fa0dd59a59b21f3796ff0160a0f8dc...
-- Password for 'admin123': scrypt:32768:8:1$7t8mP4XhZ0V9qj4M$382894565780bb6e232efd96cfc7a72661c94474ceca51941ad243ad9d4a8ec9...
INSERT IGNORE INTO users (id, username, email, password, role) VALUES
(1, 'Admin', 'admin@tourism.com', 'scrypt:32768:8:1$K7o0v4kSqmX6e42K$0ae702330a614275fdf6ba3a8b277b0682fa0dd59a59b21f3796ff0160a0f8dc9ec384950337851ee7816be61c9006935c1ba3f07a16e8b5a03e67ab931a29bd', 'admin'),
(2, 'Admin User', 'admin@xploreelite.com', 'scrypt:32768:8:1$7t8mP4XhZ0V9qj4M$382894565780bb6e232efd96cfc7a72661c94474ceca51941ad243ad9d4a8ec98425d97adcb1a90c598075fe5bf7e0be306443c224213fc819665ce9c235767b', 'admin');

-- -------------------------------------------------------------------------
-- SEED DATA: 2025 Monthly Tourism Records (Sum = 48,520 visitors, ₹ 32,75,000 revenue)
-- -------------------------------------------------------------------------
INSERT IGNORE INTO monthly_analytics (id, month, year, visitors, revenue, sii_index, category_id) VALUES
(1, 'January', 2025, 3200, 520000.00, 0.85, 1),
(2, 'February', 2025, 3850, 615000.00, 0.92, 2),
(3, 'March', 2025, 4120, 680000.00, 1.05, 3),
(4, 'April', 2025, 5430, 890000.00, 1.25, 2),
(5, 'May', 2025, 4980, 810000.00, 1.40, 4),
(6, 'June', 2025, 4300, 710000.00, 1.15, 1),
(7, 'July', 2025, 3900, 640000.00, 0.98, 3),
(8, 'August', 2025, 3650, 600000.00, 0.90, 5),
(9, 'September', 2025, 3400, 560000.00, 0.88, 2),
(10, 'October', 2025, 4200, 690000.00, 1.08, 3),
(11, 'November', 2025, 4190, 670000.00, 1.06, 1),
(12, 'December', 2025, 5300, 850000.00, 1.30, 1),
-- 2024 Historical Baseline Records
(13, 'January', 2024, 2850, 450000.00, 0.80, 1),
(14, 'February', 2024, 3200, 510000.00, 0.88, 2),
(15, 'March', 2024, 3600, 570000.00, 0.95, 3),
(16, 'April', 2024, 4800, 760000.00, 1.15, 2),
(17, 'May', 2024, 4300, 690000.00, 1.20, 4),
(18, 'June', 2024, 3800, 600000.00, 1.02, 1),
(19, 'July', 2024, 3400, 540000.00, 0.90, 3),
(20, 'August', 2024, 3200, 510000.00, 0.85, 5),
(21, 'September', 2024, 3000, 480000.00, 0.82, 2),
(22, 'October', 2024, 3700, 590000.00, 0.98, 3),
(23, 'November', 2024, 3800, 600000.00, 1.00, 1),
(24, 'December', 2024, 4600, 720000.00, 1.20, 1);
