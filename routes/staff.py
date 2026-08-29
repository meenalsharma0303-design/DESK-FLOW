from functools import wraps

from flask import Blueprint, jsonify, request, session, render_template
from werkzeug.security import check_password_hash

from database import db_cursor

staff_bp = Blueprint("staff", __name__)


def staff_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Login required"}), 401
            return render_template("staff-login.html"), 401
        return view(*args, **kwargs)
    return wrapped


@staff_bp.get("/staff/login")
def login_page():
    return render_template("staff-login.html")


@staff_bp.post("/api/staff/login")
def login():
    data = request.get_json(silent=True) or {}

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    with db_cursor(dictionary=True) as (_, cursor):
        cursor.execute("""
            SELECT user_id, username, password_hash, role
            FROM users
            WHERE username = %s
        """, (username,))
        user = cursor.fetchone()

    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid username or password"}), 401

    session["user_id"] = user["user_id"]
    session["username"] = user["username"]
    session["role"] = user["role"]

    return jsonify({
        "message": "Login successful",
        "username": user["username"],
        "role": user["role"],
    })


@staff_bp.post("/api/staff/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})


@staff_bp.get("/staff/dashboard")
@staff_required
def dashboard_page():
    with db_cursor(dictionary=True) as (_, cursor):
        cursor.execute("SELECT COUNT(*) AS n FROM rooms")
        total_rooms = cursor.fetchone()["n"]

        cursor.execute("""
            SELECT COUNT(*) AS n FROM rooms WHERE status = 'Available'
        """)
        available_rooms = cursor.fetchone()["n"]

        cursor.execute("""
            SELECT COUNT(*) AS n FROM rooms WHERE status = 'Booked'
        """)
        booked_rooms = cursor.fetchone()["n"]

        cursor.execute("SELECT COUNT(*) AS n FROM customers")
        total_guests = cursor.fetchone()["n"]

        cursor.execute("""
            SELECT COUNT(*) AS n
            FROM bookings
            WHERE DATE(booking_date) = CURDATE()
        """)
        today_bookings = cursor.fetchone()["n"]

    occupancy = round((booked_rooms / total_rooms) * 100, 1) if total_rooms else 0

    return render_template(
        "dashboard.html",
        total_rooms=total_rooms,
        available_rooms=available_rooms,
        booked_rooms=booked_rooms,
        total_guests=total_guests,
        today_bookings=today_bookings,
        occupancy=occupancy,
    )
