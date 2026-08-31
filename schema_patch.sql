USE hotel;

-- Run this patch if your existing bookings table was created
-- from the earlier database script.

ALTER TABLE bookings
    ADD COLUMN booking_code VARCHAR(30) NULL UNIQUE AFTER booking_id;

ALTER TABLE bookings
    ADD COLUMN special_requests TEXT NULL AFTER number_of_guests;

-- If your table already has rows, create temporary booking codes:
UPDATE bookings
SET booking_code = CONCAT('DF-', LPAD(booking_id, 6, '0'))
WHERE booking_code IS NULL;

ALTER TABLE bookings
    MODIFY booking_code VARCHAR(30) NOT NULL UNIQUE;

