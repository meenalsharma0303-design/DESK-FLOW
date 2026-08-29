from datetime import date
from decimal import Decimal
import secrets

from flask import Blueprint, jsonify, redirect, render_template, request, url_for

from database import db_cursor
from services.invoice import generate_invoice
from services.email_service import send_booking_confirmation

booking_bp = Blueprint("booking", __name__)


def make_booking_code():
    return "DF-" + secrets.token_hex(4).upper()


def fetch_booking(booking_id):
    with db_cursor(dictionary=True) as (_, cursor):
        cursor.execute("""
            SELECT
                b.booking_id,
                b.booking_code,
                b.customer_id,
                b.room_id,
                c.name AS customer_name,
                c.email AS customer_email,
                c.phone AS customer_phone,
                c.address AS customer_address,
                r.room_number,
                r.room_type,
                r.price AS room_price,
                b.check_in,
                b.check_out,
                b.number_of_guests,
                b.total_amount,
                b.booking_status,
                b.booking_date
            FROM bookings b
            JOIN customers c ON c.customer_id = b.customer_id
            JOIN rooms r ON r.room_id = b.room_id
            WHERE b.booking_id = %s
        """, (booking_id,))
        booking = cursor.fetchone()

    if booking:
        booking["check_in"] = str(booking["check_in"])
        booking["check_out"] = str(booking["check_out"])
        booking["booking_date"] = str(booking["booking_date"])
        booking["total_amount"] = float(booking["total_amount"])
        booking["room_price"] = float(booking["room_price"])
        booking["nights"] = (
            date.fromisoformat(booking["check_out"])
            - date.fromisoformat(booking["check_in"])
        ).days

    return booking


def get_request_value(data, *names, default=None):
    for name in names:
        value = data.get(name)
        if value is not None and value != "":
            return value
    return default


@booking_bp.route("/booking", methods=["POST"])
def create_booking():
    # Supports both normal HTML form submissions and JSON.
    data = request.form if request.form else (request.get_json(silent=True) or {})

    check_in = get_request_value(data, "checkin", "check_in")
    check_out = get_request_value(data, "checkout", "check_out")
    room_id = get_request_value(data, "room", "room_id")
    guests = int(get_request_value(data, "guests", "number_of_guests", default=1))
    name = get_request_value(data, "name", "customer_name")
    email = get_request_value(data, "email", "customer_email")
    phone = get_request_value(data, "phone", "customer_phone")
    address = get_request_value(data, "address", "customer_address", default="")
    special_requests = get_request_value(
        data, "requests", "special_requests", default=""
    )

    if not all([check_in, check_out, room_id, name, email, phone]):
        return jsonify({"error": "Required booking fields are missing"}), 400

    try:
        check_in_date = date.fromisoformat(check_in)
        check_out_date = date.fromisoformat(check_out)
    except ValueError:
        return jsonify({"error": "Invalid check-in or check-out date"}), 400

    nights = (check_out_date - check_in_date).days
    if nights <= 0:
        return jsonify({"error": "Check-out must be after check-in"}), 400

    with db_cursor(dictionary=True) as (_, cursor):
        cursor.execute("""
            SELECT room_id, room_number, room_type, price, status
            FROM rooms
            WHERE room_id = %s
            FOR UPDATE
        """, (room_id,))
        room = cursor.fetchone()

        if not room:
            return jsonify({"error": "Room not found"}), 404

        if room["status"] != "Available":
            return jsonify({"error": "Selected room is not available"}), 409

        cursor.execute("""
            SELECT customer_id
            FROM customers
            WHERE email = %s
            LIMIT 1
        """, (email,))
        customer = cursor.fetchone()

        if customer:
            customer_id = customer["customer_id"]
            cursor.execute("""
                UPDATE customers
                SET name = %s, phone = %s, address = %s
                WHERE customer_id = %s
            """, (name, phone, address, customer_id))
        else:
            cursor.execute("""
                INSERT INTO customers (name, phone, email, address)
                VALUES (%s, %s, %s, %s)
            """, (name, phone, email, address))
            customer_id = cursor.lastrowid

        total = Decimal(str(room["price"])) * nights
        booking_code = make_booking_code()

        cursor.execute("""
            INSERT INTO bookings
            (
                customer_id,
                room_id,
                booking_code,
                check_in,
                check_out,
                number_of_guests,
                special_requests,
                total_amount,
                booking_status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'Confirmed')
        """, (
            customer_id,
            room_id,
            booking_code,
            check_in_date,
            check_out_date,
            guests,
            special_requests,
            total,
        ))

        booking_id = cursor.lastrowid

        cursor.execute("""
            UPDATE rooms
            SET status = 'Booked'
            WHERE room_id = %s
        """, (room_id,))

    booking = fetch_booking(booking_id)

    invoice_path = generate_invoice(booking)

    try:
        send_booking_confirmation(booking, invoice_path)
    except Exception:
        # Booking remains valid even if SMTP is not configured.
        pass

    if request.form:
        return redirect(url_for("public.confirmation_page", booking_id=booking_id))

    return jsonify({
        "message": "Booking created successfully",
        "booking_id": booking_id,
        "booking_code": booking_code,
        "total_amount": float(total),
        "invoice": f"/invoice/{booking_id}",
    }), 201


@booking_bp.get("/invoice/<int:booking_id>")
def invoice(booking_id):
    booking = fetch_booking(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404

    from flask import send_file
    path = generate_invoice(booking)
    return send_file(
        path,
        as_attachment=True,
        download_name=f"{booking['booking_code']}-invoice.pdf",
        mimetype="application/pdf",
    )


@booking_bp.get("/api/bookings")
def list_bookings():
    with db_cursor(dictionary=True) as (_, cursor):
        cursor.execute("""
            SELECT
                b.booking_id,
                b.booking_code,
                c.name AS customer_name,
                c.email,
                c.phone,
                r.room_number,
                r.room_type,
                b.check_in,
                b.check_out,
                b.number_of_guests,
                b.total_amount,
                b.booking_status,
                b.booking_date
            FROM bookings b
            JOIN customers c ON c.customer_id = b.customer_id
            JOIN rooms r ON r.room_id = b.room_id
            ORDER BY b.booking_id DESC
        """)
        rows = cursor.fetchall()

    for row in rows:
        row["check_in"] = str(row["check_in"])
        row["check_out"] = str(row["check_out"])
        row["booking_date"] = str(row["booking_date"])
        row["total_amount"] = float(row["total_amount"])

    return jsonify(rows)


@booking_bp.route("/api/bookings/<int:booking_id>/cancel", methods=["PUT"])
def cancel_booking(booking_id):
    with db_cursor(dictionary=True) as (_, cursor):
        cursor.execute("""
            SELECT room_id, booking_status
            FROM bookings
            WHERE booking_id = %s
            FOR UPDATE
        """, (booking_id,))
        booking = cursor.fetchone()

        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        if booking["booking_status"] == "Cancelled":
            return jsonify({"error": "Booking already cancelled"}), 400

        cursor.execute("""
            UPDATE bookings
            SET booking_status = 'Cancelled'
            WHERE booking_id = %s
        """, (booking_id,))

        cursor.execute("""
            UPDATE rooms
            SET status = 'Available'
            WHERE room_id = %s
        """, (booking["room_id"],))

    return jsonify({"message": "Booking cancelled successfully"})


@booking_bp.route("/api/bookings/<int:booking_id>/check-in", methods=["PUT"])
def check_in(booking_id):
    with db_cursor() as (_, cursor):
        cursor.execute("""
            UPDATE bookings
            SET booking_status = 'Checked-In'
            WHERE booking_id = %s
              AND booking_status = 'Confirmed'
        """, (booking_id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "Booking cannot be checked in"}), 400

    return jsonify({"message": "Guest checked in successfully"})


@booking_bp.route("/api/bookings/<int:booking_id>/check-out", methods=["PUT"])
def check_out(booking_id):
    with db_cursor(dictionary=True) as (_, cursor):
        cursor.execute("""
            SELECT room_id
            FROM bookings
            WHERE booking_id = %s
              AND booking_status = 'Checked-In'
            FOR UPDATE
        """, (booking_id,))
        booking = cursor.fetchone()

        if not booking:
            return jsonify({"error": "Booking cannot be checked out"}), 400

        cursor.execute("""
            UPDATE bookings
            SET booking_status = 'Checked-Out'
            WHERE booking_id = %s
        """, (booking_id,))

        cursor.execute("""
            UPDATE rooms
            SET status = 'Available'
            WHERE room_id = %s
        """, (booking["room_id"],))

    return jsonify({"message": "Guest checked out successfully"})
