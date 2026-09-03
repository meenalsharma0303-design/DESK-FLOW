from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import date, datetime
import os

from db import get_connection
from invoice_generator import create_invoice_pdf

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "deskflow-beginner-secret-key-change-me")


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "staff_id" not in session:
            return redirect(url_for("staff_login"))
        return view(*args, **kwargs)
    return wrapped


ROOM_PRICES = {
    "Cloud Room": 4999,
    "Sunset Suite": 7999,
    "Garden Room": 5499,
    "DESKFLOW Suite": 9999,
}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/rooms.html")
def rooms():
    return render_template("rooms.html")


@app.route("/booking.html")
def booking():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT room_id, room_name, room_type, price_per_night, max_guests FROM rooms WHERE status <> 'maintenance' ORDER BY room_id")
    rooms = cur.fetchall()
    cur.close(); conn.close()
    return render_template("booking.html", rooms=rooms)


@app.route("/api/booking", methods=["POST"])
def create_booking():
    data = request.get_json(silent=True) or request.form
    print("BOOKING DATA RECEIVED:", data)
    required = ["checkin", "checkout", "room", "guests", "name", "email", "phone"]
    missing = [x for x in required if not data.get(x)]
    if missing:
        return {"success": False, "message": "Please fill all required fields."}, 400

    try:
        checkin = datetime.strptime(data["checkin"], "%Y-%m-%d").date()
        checkout = datetime.strptime(data["checkout"], "%Y-%m-%d").date()
        guests = int(data["guests"])
    except (ValueError, TypeError):
        return {"success": False, "message": "Invalid booking details."}, 400

    if checkout <= checkin:
        return {"success": False, "message": "Check-out must be after check-in."}, 400
    if checkin < date.today():
        return {"success": False, "message": "Check-in cannot be in the past."}, 400

    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        # Lock the selected room row so two simultaneous bookings are handled safely.
        cur.execute("SELECT * FROM rooms WHERE room_name=%s FOR UPDATE", (data["room"],))
        room = cur.fetchone()
        if not room:
            conn.rollback()
            return {"success": False, "message": "Selected room does not exist."}, 404
        if guests > room["max_guests"]:
            conn.rollback()
            return {"success": False, "message": f"This room allows up to {room['max_guests']} guests."}, 400

        cur.execute("""
            SELECT booking_id FROM bookings
            WHERE room_id=%s
              AND status IN ('confirmed','checked_in')
              AND check_in < %s AND check_out > %s
            FOR UPDATE
        """, (room["room_id"], checkout, checkin))
        if cur.fetchone():
            conn.rollback()
            return {"success": False, "message": "Sorry, this room is not available for those dates."}, 409

        cur.execute("SELECT guest_id FROM guests WHERE email=%s", (data["email"],))
        guest = cur.fetchone()
        if guest:
            guest_id = guest["guest_id"]
            cur.execute("""
                UPDATE guests SET full_name=%s, phone=%s
                WHERE guest_id=%s
            """, (data["name"], data["phone"], guest_id))
        else:
            cur.execute("""
                INSERT INTO guests(full_name,email,phone) VALUES(%s,%s,%s)
            """, (data["name"], data["email"], data["phone"]))
            guest_id = cur.lastrowid

        nights = (checkout - checkin).days
        total = nights * float(room["price_per_night"])

        cur.execute("""
            INSERT INTO bookings
            (guest_id, room_id, check_in, check_out, guests_count, special_requests, total_amount, status)
            VALUES(%s,%s,%s,%s,%s,%s,%s,'confirmed')
        """, (guest_id, room["room_id"], checkin, checkout, guests,
              data.get("requests", ""), total))
        booking_id = cur.lastrowid
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close(); conn.close()

    booking_code = f"DF-{booking_id:04d}"
    return {"success": True, "booking_id": booking_id, "booking_code": booking_code,
            "redirect": url_for("confirmation", booking_id=booking_id)}


@app.route("/confirmation.html")
def confirmation():
    booking_id = request.args.get("booking_id", type=int)
    if not booking_id:
        return redirect(url_for("booking"))
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT b.*, g.full_name, g.email, g.phone, r.room_name, r.price_per_night
        FROM bookings b
        JOIN guests g ON b.guest_id=g.guest_id
        JOIN rooms r ON b.room_id=r.room_id
        WHERE b.booking_id=%s
    """, (booking_id,))
    booking_data = cur.fetchone()
    cur.close(); conn.close()
    if not booking_data:
        return "Booking not found", 404
    booking_data["booking_code"] = f"DF-{booking_id:04d}"
    return render_template("confirmation.html", booking=booking_data)


@app.route("/invoice/<int:booking_id>")
def invoice(booking_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT b.*, g.full_name, g.email, g.phone, r.room_name, r.price_per_night
        FROM bookings b
        JOIN guests g ON b.guest_id=g.guest_id
        JOIN rooms r ON b.room_id=r.room_id
        WHERE b.booking_id=%s
    """, (booking_id,))
    b = cur.fetchone()
    cur.close(); conn.close()
    if not b:
        return "Booking not found", 404
    path = create_invoice_pdf(b)
    return send_file(path, as_attachment=True, download_name=f"DESKFLOW-Invoice-DF-{booking_id:04d}.pdf")


@app.route("/staff-login.html", methods=["GET", "POST"])
def staff_login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        conn = get_connection()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM staff_users WHERE email=%s AND is_active=1", (email,))
        user = cur.fetchone()
        cur.close(); conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session["staff_id"] = user["staff_id"]
            session["staff_name"] = user["full_name"]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.")
    return render_template("staff-login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("staff_login"))


@app.route("/dashboard.html")
@login_required
def dashboard():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT COUNT(*) total FROM rooms"); total_rooms = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) total FROM rooms WHERE status='available'"); available = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) total FROM rooms WHERE status='occupied'"); occupied = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) total FROM rooms WHERE status='cleaning'"); cleaning = cur.fetchone()["total"]
    cur.execute("SELECT COUNT(*) total FROM bookings WHERE status IN ('confirmed','checked_in')"); active_bookings = cur.fetchone()["total"]
    cur.execute("SELECT COALESCE(SUM(total_amount),0) total FROM bookings WHERE status <> 'cancelled'"); revenue = cur.fetchone()["total"]
    cur.execute("""
        SELECT b.booking_id,g.full_name,r.room_name,b.check_in,b.check_out,b.total_amount,b.status
        FROM bookings b JOIN guests g ON b.guest_id=g.guest_id JOIN rooms r ON b.room_id=r.room_id
        ORDER BY b.created_at DESC LIMIT 8
    """)
    recent = cur.fetchall()
    cur.close(); conn.close()
    stats = dict(total_rooms=total_rooms, available=available, occupied=occupied,
                 cleaning=cleaning, active_bookings=active_bookings, revenue=revenue)
    return render_template("dashboard.html", stats=stats, recent=recent)


@app.route("/bookings.html")
@login_required
def bookings():
    q = request.args.get("q", "").strip()
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    if q:
        like = f"%{q}%"
        cur.execute("""
            SELECT b.*, CONCAT('DF-',LPAD(b.booking_id,4,'0')) booking_code,
                   g.full_name,g.email,r.room_name
            FROM bookings b JOIN guests g ON b.guest_id=g.guest_id JOIN rooms r ON b.room_id=r.room_id
            WHERE g.full_name LIKE %s OR g.email LIKE %s OR CAST(b.booking_id AS CHAR) LIKE %s
            ORDER BY b.created_at DESC
        """, (like,like,like))
    else:
        cur.execute("""
            SELECT b.*, CONCAT('DF-',LPAD(b.booking_id,4,'0')) booking_code,
                   g.full_name,g.email,r.room_name
            FROM bookings b JOIN guests g ON b.guest_id=g.guest_id JOIN rooms r ON b.room_id=r.room_id
            ORDER BY b.created_at DESC
        """)
    rows=cur.fetchall(); cur.close(); conn.close()
    return render_template("bookings.html", bookings=rows, search=q)


@app.route("/guests.html")
@login_required
def guests():
    conn=get_connection(); cur=conn.cursor(dictionary=True)
    cur.execute("""
        SELECT g.*, COUNT(b.booking_id) bookings_count,
               MAX(b.check_out) last_checkout
        FROM guests g LEFT JOIN bookings b ON g.guest_id=b.guest_id
        GROUP BY g.guest_id ORDER BY g.created_at DESC
    """)
    rows=cur.fetchall(); cur.close(); conn.close()
    return render_template("guests.html", guests=rows)


@app.route("/rooms-management.html")
@login_required
def rooms_management():
    conn=get_connection(); cur=conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM rooms ORDER BY room_id")
    rows=cur.fetchall(); cur.close(); conn.close()
    return render_template("rooms-management.html", rooms=rows)


@app.route("/housekeeping.html")
@login_required
def housekeeping():
    conn=get_connection(); cur=conn.cursor(dictionary=True)
    cur.execute("""
        SELECT r.room_id,r.room_number,r.room_name,r.status,
               h.task_id,h.task_status,h.notes
        FROM rooms r LEFT JOIN housekeeping h ON r.room_id=h.room_id
        ORDER BY r.room_number
    """)
    rows=cur.fetchall(); cur.close(); conn.close()
    return render_template("housekeeping.html", rooms=rows)


@app.post("/api/housekeeping/<int:task_id>")
@login_required
def update_housekeeping(task_id):
    status=request.form.get("status")
    if status not in ("pending","cleaning","completed"):
        return "Invalid status",400
    conn=get_connection(); cur=conn.cursor()
    cur.execute("UPDATE housekeeping SET task_status=%s WHERE task_id=%s",(status,task_id))
    conn.commit(); cur.close(); conn.close()
    return redirect(url_for("housekeeping"))


if __name__ == "__main__":
    app.run(debug=True)
