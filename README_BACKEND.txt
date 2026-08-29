DESKFLOW HOTEL - BACKEND

1. Copy .env.example to .env and enter MySQL/SMTP settings.
2. Make sure the "hotel" MySQL database exists.
3. Run schema_patch.sql if your existing bookings table does not have:
   - booking_code
   - special_requests
4. Install:
      pip install -r requirements.txt
5. Put your existing HTML files into:
      templates/
6. Put your existing CSS/JS/images into:
      static/
7. Start:
      python app.py

Important:
- booking.html should POST to /booking.
- confirmation.html should display the "booking" Jinja object.
- Invoice download URL:
      /invoice/<booking_id>
- The email service sends the invoice PDF as an attachment.
- AI is intentionally kept as a safe starter endpoint. It does not directly
  execute database mutations.
