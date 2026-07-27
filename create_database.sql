CREATE DATABASE IF NOT EXISTS ocr_intelligence
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE ocr_intelligence;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) DEFAULT NULL,
    last_name VARCHAR(100) DEFAULT NULL,
    profile_image VARCHAR(500) DEFAULT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    is_email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255) DEFAULT NULL,
    email_verification_token_expiry DATETIME DEFAULT NULL,
    reset_token VARCHAR(255) DEFAULT NULL,
    reset_token_expiry DATETIME DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME DEFAULT NULL,
    INDEX idx_users_email_token (email_verification_token),
    INDEX idx_users_reset_token (reset_token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS otp_codes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    otp_token VARCHAR(128) NOT NULL UNIQUE,
    code_hash VARCHAR(128) NOT NULL,
    expires_at DATETIME NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    attempts SMALLINT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_otp_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_otp_user_id (user_id),
    INDEX idx_otp_expires_at (expires_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS ocr_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(50) DEFAULT NULL,
    file_path VARCHAR(1000) DEFAULT NULL,
    model_id VARCHAR(50) DEFAULT NULL,
    model_name VARCHAR(100) DEFAULT NULL,
    extracted_text TEXT DEFAULT NULL,
    word_count INT DEFAULT 0,
    char_count INT DEFAULT 0,
    confidence_score FLOAT DEFAULT 0,
    execution_time FLOAT DEFAULT 0,
    init_time_s FLOAT DEFAULT 0,
    detected_language VARCHAR(10) DEFAULT 'auto',
    precision_score FLOAT DEFAULT NULL,
    robustness FLOAT DEFAULT NULL,
    global_score FLOAT DEFAULT NULL,
    status VARCHAR(50) DEFAULT 'success',
    error_message TEXT DEFAULT NULL,
    client_ip VARCHAR(50) DEFAULT NULL,
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ocr_history_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_ocr_user_id (user_id),
    INDEX idx_ocr_model_id (model_id),
    INDEX idx_ocr_status (status),
    INDEX idx_ocr_processed_at (processed_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
