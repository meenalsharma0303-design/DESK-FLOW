CREATE DATABASE IF NOT EXISTS deskflow;
USE deskflow;

DROP TABLE IF EXISTS housekeeping;
DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS guests;
DROP TABLE IF EXISTS rooms;
DROP TABLE IF EXISTS staff_users;

CREATE TABLE staff_users (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin','receptionist') NOT NULL DEFAULT 'receptionist',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE rooms (
    room_id INT AUTO_INCREMENT PRIMARY KEY,
    room_number VARCHAR(10) NOT NULL UNIQUE,
    room_name VARCHAR(100) NOT NULL,
    room_type ENUM('room','suite','premium') NOT NULL,
    price_per_night DECIMAL(10,2) NOT NULL,
    max_guests INT NOT NULL DEFAULT 2,
    status ENUM('available','occupied','cleaning','maintenance') NOT NULL DEFAULT 'available'
);

CREATE TABLE guests (
    guest_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(120) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    phone VARCHAR(30) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE bookings (
    booking_id INT AUTO_INCREMENT PRIMARY KEY,
    guest_id INT NOT NULL,
    room_id INT NOT NULL,
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    guests_count INT NOT NULL,
    special_requests TEXT,
    total_amount DECIMAL(10,2) NOT NULL,
    status ENUM('confirmed','checked_in','checked_out','cancelled') NOT NULL DEFAULT 'confirmed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (guest_id) REFERENCES guests(guest_id),
    FOREIGN KEY (room_id) REFERENCES rooms(room_id),
    INDEX idx_booking_dates (room_id, check_in, check_out)
);

CREATE TABLE housekeeping (
    task_id INT AUTO_INCREMENT PRIMARY KEY,
    room_id INT NOT NULL UNIQUE,
    task_status ENUM('pending','cleaning','completed') NOT NULL DEFAULT 'completed',
    notes VARCHAR(255),
    FOREIGN KEY (room_id) REFERENCES rooms(room_id)
);
