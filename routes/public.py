from flask import Blueprint, render_template
from database import db_cursor

public_bp = Blueprint("public", __name__)


@public_bp.get("/")
def home():
    return render_template("index.html")


@public_bp.get("/rooms")
def rooms_page():
    with db_cursor(dictionary=True) as (_, cursor):
        cursor.execute("""
            SELECT room_id, room_number, room_type, price, status,
                   description, image
            FROM rooms
            ORDER BY room_number
        """)
        rooms = cursor.fetchall()
    return render_template("rooms.html", rooms=rooms)


@public_bp.get("/booking")
def booking_page():
    with db_cursor(dictionary=True) as (_, cursor):
        cursor.execute("""
            SELECT room_id, room_number, room_type, price
            FROM rooms
            WHERE status = 'Available'
            ORDER BY room_number
        """)
        rooms = cursor.fetchall()
    return render_template("booking.html", rooms=rooms)


@public_bp.get("/confirmation/<int:booking_id>")
def confirmation_page(booking_id):
    from routes.booking import fetch_booking
    booking = fetch_booking(booking_id)
    if not booking:
        return render_template("404.html"), 404
    return render_template("confirmation.html", booking=booking)
