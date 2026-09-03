USE deskflow;

-- Beginner/demo staff login:
-- Email: admin@deskflow.com
-- Password: admin123
-- INSERT INTO staff_users(full_name,email,password_hash,role)
-- VALUES ('Staff Admin','admin@deskflow.com',
-- 'pbkdf2:sha256:600000$alGh4W4yHVFWUyMl$J3xvbAdrxV+dtQP+eXH12S74L/KxlI7is+9N1EzLgmU','admin');
-- The hash above is only a placeholder. Run: python seed_admin.py
DELETE FROM rooms;
INSERT INTO rooms(room_number,room_name,room_type,price_per_night,max_guests,status) VALUES
('101','Cloud Room','room',4999,2,'available'),
('102','Garden Room','room',5499,2,'available'),
('201','Sunset Suite','suite',7999,3,'available'),
('301','DESKFLOW Suite','premium',9999,4,'available'),
('103','Meadow Room','room',4999,2,'available'),
('104','Moon Room','room',4999,2,'available'),
('105','Cozy Room','room',4999,2,'available'),
('106','Olive Room','room',5499,2,'available'),
('107','Sunrise Room','room',5499,2,'available'),
('108','River Room','room',5499,2,'available'),
('109','Sky Room','room',4999,2,'available'),
('110','Willow Room','room',5499,2,'available'),
('111','Pearl Room','room',5499,2,'available'),
('112','Linen Room','room',4999,2,'available'),
('113','Breeze Room','room',4999,2,'available'),
('114','Bloom Room','room',5499,2,'available'),
('202','Terrace Suite','suite',7999,3,'available'),
('203','Garden Suite','suite',7999,3,'available'),
('204','Sunset Premium','premium',8999,3,'available'),
('302','Skyline Suite','premium',9999,4,'available'),
('303','Moonlight Suite','premium',9999,4,'available'),
('304','Garden Premium','premium',8999,4,'available'),
('305','Cloud Premium','premium',8999,4,'available'),
('306','DESKFLOW Grand Suite','premium',12999,4,'available'),
('307','Aurora Premium','premium',10999,4,'available'),
('308','Meadow Premium','premium',10999,4,'available'),
('309','Horizon Premium','premium',11999,4,'available'),
('310','Signature Suite','premium',11999,4,'available'),
('311','Heritage Suite','suite',8499,3,'available');

INSERT INTO housekeeping(room_id,task_status,notes)
SELECT room_id,'completed','Room ready' FROM rooms;

-- Optional demo data so the staff dashboard is not empty.
INSERT INTO guests(full_name,email,phone) VALUES
('Aarav Mehta','aarav@example.com','+91 98765 10001'),
('Riya Kapoor','riya@example.com','+91 98765 10002'),
('Kabir Singh','kabir@example.com','+91 98765 10003'),
('Ananya Sharma','ananya@example.com','+91 98765 10004'),
('Ishaan Verma','ishaan@example.com','+91 98765 10005');

INSERT INTO bookings(guest_id,room_id,check_in,check_out,guests_count,special_requests,total_amount,status) VALUES
(1,1,'2026-09-05','2026-09-07',2,'Late check-in',9998,'confirmed'),
(2,3,'2026-09-06','2026-09-08',2,'Quiet room',15998,'confirmed'),
(3,2,'2026-09-10','2026-09-11',1,'',5499,'confirmed'),
(4,4,'2026-09-12','2026-09-14',4,'Birthday setup',19998,'confirmed'),
(5,5,'2026-09-15','2026-09-18',2,'',14997,'confirmed');

UPDATE housekeeping SET task_status='cleaning', notes='Guest departure / cleaning in progress'
WHERE room_id=1;
UPDATE housekeeping SET task_status='pending', notes='Scheduled for cleaning'
WHERE room_id=2;
