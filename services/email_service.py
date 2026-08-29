import os
import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv

load_dotenv()


def send_booking_confirmation(booking, invoice_path):
    host = os.getenv("SMTP_HOST")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")
    port = int(os.getenv("SMTP_PORT", "587"))
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

    if not all([host, user, password]):
        raise RuntimeError("SMTP is not configured")

    msg = EmailMessage()
    msg["Subject"] = f"Booking Confirmation - {booking['booking_code']}"
    msg["From"] = user
    msg["To"] = booking["customer_email"]

    msg.set_content(
        f"""Dear {booking['customer_name']},

Your booking at {os.getenv('HOTEL_NAME', 'DeskFlow Hotel')} is confirmed.

Booking ID: {booking['booking_code']}
Room: {booking['room_number']} - {booking['room_type']}
Check-in: {booking['check_in']}
Check-out: {booking['check_out']}
Guests: {booking['number_of_guests']}
Nights: {booking['nights']}
Total: ₹{booking['total_amount']:,.2f}

Your PDF invoice is attached.

Thank you.
"""
    )

    with open(invoice_path, "rb") as f:
        msg.add_attachment(
            f.read(),
            maintype="application",
            subtype="pdf",
            filename=os.path.basename(invoice_path),
        )

    with smtplib.SMTP(host, port) as server:
        if use_tls:
            server.starttls()
        server.login(user, password)
        server.send_message(msg)
