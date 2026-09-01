
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from database import db_cursor
from dotenv import load_dotenv
from decimal import Decimal
from datetime import datetime
from io import BytesIO
import os
import secrets
import string

# Optional PDF/email libraries
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "hotel-secret-key")


# ============================================================
# GENERATE UNIQUE BOOKING CODE
# ============================================================

def generate_booking_code():
    """Generate a unique booking code such as HTL-A8K29P."""

    characters = string.ascii_uppercase + string.digits

    while True:

        code = "HTL-" + "".join(
            secrets.choice(characters)
            for _ in range(6)
        )

        with db_cursor(dictionary=True) as cursor:

            cursor.execute(
                """
                SELECT booking_id
                FROM bookings
                WHERE booking_code = %s
                """,
                (code,)
            )

            if cursor.fetchone() is None:
                return code


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template("index.html")


# ============================================================
# ROOMS
# ============================================================

@app.route("/rooms")
def rooms():

    with db_cursor(dictionary=True) as cursor:

        cursor.execute("""
            SELECT
                room_id,
                room_number,
                room_type,
                price,
                status,
                description,
                image
            FROM rooms
            ORDER BY room_id
        """)

        room_list = cursor.fetchall()

    return render_template(
        "rooms.html",
        rooms=room_list
    )


# ============================================================
# BOOKING
# ============================================================

@app.route("/booking", methods=["GET", "POST"])
def booking():

    # --------------------------------------------------------
    # SHOW BOOKING FORM
    # --------------------------------------------------------

    if request.method == "GET":

        with db_cursor(dictionary=True) as cursor:

            # IMPORTANT:
            #
            # Do NOT filter using room.status = 'Available'.
            #
            # A room can have an existing booking for one date
            # range and still be available for another date range.
            #
            # Actual availability is checked when the user submits
            # the booking based on overlapping bookings.

            cursor.execute("""
                SELECT
                    room_id,
                    room_number,
                    room_type,
                    price,
                    status,
                    description,
                    image
                FROM rooms
                ORDER BY room_id
            """)

            available_rooms = cursor.fetchall()

        return render_template(
            "booking.html",
            rooms=available_rooms
        )


    # --------------------------------------------------------
    # GET FORM DATA
    # --------------------------------------------------------

    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    email = request.form.get("email", "").strip()
    address = request.form.get("address", "").strip()

    room_id = request.form.get("room_id")
    check_in = request.form.get("check_in")
    check_out = request.form.get("check_out")

    number_of_guests = request.form.get(
        "number_of_guests",
        request.form.get("guests", "1")
    )

    special_requests = request.form.get(
        "special_requests",
        ""
    ).strip()


    # --------------------------------------------------------
    # BASIC VALIDATION
    # --------------------------------------------------------

    if not name or not phone or not email:

        flash(
            "Please enter your name, phone number and email."
        )

        return redirect(url_for("booking"))


    if not room_id or not check_in or not check_out:

        flash(
            "Please select a room and booking dates."
        )

        return redirect(url_for("booking"))


    try:

        room_id = int(room_id)

        number_of_guests = int(
            number_of_guests
        )

        if number_of_guests < 1:
            raise ValueError

    except (ValueError, TypeError):

        flash(
            "Invalid room or guest information."
        )

        return redirect(url_for("booking"))


    # --------------------------------------------------------
    # VALIDATE DATES
    # --------------------------------------------------------

    try:

        check_in_date = datetime.strptime(
            check_in,
            "%Y-%m-%d"
        ).date()

        check_out_date = datetime.strptime(
            check_out,
            "%Y-%m-%d"
        ).date()


        if check_out_date <= check_in_date:

            flash(
                "Check-out date must be after check-in date."
            )

            return redirect(url_for("booking"))


    except ValueError:

        flash(
            "Invalid booking dates."
        )

        return redirect(url_for("booking"))


    # --------------------------------------------------------
    # FIND / CREATE CUSTOMER
    # --------------------------------------------------------

    with db_cursor(dictionary=True) as cursor:

        cursor.execute(
            """
            SELECT customer_id
            FROM customers
            WHERE email = %s
            """,
            (email,)
        )

        customer = cursor.fetchone()


        if customer:

            customer_id = customer["customer_id"]

            cursor.execute(
                """
                UPDATE customers

                SET
                    name = %s,
                    phone = %s,
                    address = %s

                WHERE customer_id = %s
                """,
                (
                    name,
                    phone,
                    address or None,
                    customer_id
                )
            )

        else:

            cursor.execute(
                """
                INSERT INTO customers
                (
                    name,
                    phone,
                    email,
                    address
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    name,
                    phone,
                    email,
                    address or None
                )
            )

            customer_id = cursor.lastrowid


        # ----------------------------------------------------
        # GET SELECTED ROOM
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT
                room_id,
                room_number,
                room_type,
                price,
                status

            FROM rooms

            WHERE room_id = %s
            """,
            (room_id,)
        )

        room = cursor.fetchone()


        if not room:

            flash(
                "Selected room does not exist."
            )

            return redirect(url_for("booking"))


        # ----------------------------------------------------
        # IMPORTANT:
        #
        # DO NOT CHECK:
        #
        #     room["status"] != "Available"
        #
        # because status is no longer being used to determine
        # whether a room is booked for a particular date.
        #
        # ----------------------------------------------------


        # ----------------------------------------------------
        # CHECK FOR OVERLAPPING BOOKINGS
        # ----------------------------------------------------
        #
        # Two date ranges overlap when:
        #
        # existing check-in < requested check-out
        #
        # AND
        #
        # existing check-out > requested check-in
        #
        # Example:
        #
        # Existing: 10th -> 15th
        # New:      12th -> 18th
        #
        # OVERLAP = YES
        #
        # Existing: 10th -> 15th
        # New:      15th -> 20th
        #
        # OVERLAP = NO
        #
        # This allows checkout and another guest's check-in
        # to happen on the same day.
        # ----------------------------------------------------

        cursor.execute(
            """
            SELECT booking_id

            FROM bookings

            WHERE room_id = %s

              AND booking_status != 'Cancelled'

              AND check_in < %s

              AND check_out > %s

            LIMIT 1
            """,
            (
                room_id,
                check_out_date,
                check_in_date
            )
        )

        existing_booking = cursor.fetchone()


        if existing_booking:

            flash(
                "This room is already booked for those dates. "
                "Please choose different dates or another room."
            )

            return redirect(
                url_for("booking")
            )


        # ----------------------------------------------------
        # CALCULATE TOTAL
        # ----------------------------------------------------

        nights = (
            check_out_date - check_in_date
        ).days

        total_amount = (
            Decimal(str(room["price"]))
            * nights
        )


        # ----------------------------------------------------
        # GENERATE BOOKING CODE
        # ----------------------------------------------------

        booking_code = generate_booking_code()


        # ----------------------------------------------------
        # INSERT BOOKING
        # ----------------------------------------------------

        cursor.execute(
            """
            INSERT INTO bookings
            (
                customer_id,
                room_id,
                check_in,
                check_out,
                number_of_guests,
                total_amount,
                booking_status,
                booking_code,
                special_requests
            )

            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                'Confirmed',
                %s,
                %s
            )
            """,
            (
                customer_id,
                room_id,
                check_in_date,
                check_out_date,
                number_of_guests,
                total_amount,
                booking_code,
                special_requests or None
            )
        )

        booking_id = cursor.lastrowid


        # ----------------------------------------------------
        # IMPORTANT:
        #
        # DO NOT UPDATE rooms.status TO 'Booked'.
        #
        # The booking dates in the bookings table now control
        # availability.
        #
        # This means the same room can be booked again for a
        # different date range.
        #
        # ----------------------------------------------------


    # ========================================================
    # GET COMPLETE BOOKING DETAILS
    # ========================================================

    with db_cursor(dictionary=True) as cursor:

        cursor.execute(
            """
            SELECT

                b.booking_id,
                b.booking_code,
                b.check_in,
                b.check_out,
                b.number_of_guests,
                b.total_amount,
                b.booking_status,
                b.booking_timestamp,
                b.special_requests,

                c.customer_id,
                c.name,
                c.phone,
                c.email,
                c.address,

                r.room_id,
                r.room_number,
                r.room_type,
                r.price

            FROM bookings b

            JOIN customers c
                ON b.customer_id = c.customer_id

            JOIN rooms r
                ON b.room_id = r.room_id

            WHERE b.booking_id = %s
            """,
            (booking_id,)
        )

        booking_data = cursor.fetchone()


    return render_template(
        "confirmation.html",
        booking=booking_data
    )


# ============================================================
# CONFIRMATION
# ============================================================

@app.route("/confirmation/<int:booking_id>")
def confirmation(booking_id):

    with db_cursor(dictionary=True) as cursor:

        cursor.execute(
            """
            SELECT

                b.*,

                c.name,
                c.phone,
                c.email,
                c.address,

                r.room_number,
                r.room_type,
                r.price

            FROM bookings b

            JOIN customers c
                ON b.customer_id = c.customer_id

            JOIN rooms r
                ON b.room_id = r.room_id

            WHERE b.booking_id = %s
            """,
            (booking_id,)
        )

        booking_data = cursor.fetchone()


    if not booking_data:

        return "Booking not found", 404


    return render_template(
        "confirmation.html",
        booking=booking_data
    )


# ============================================================
# INVOICE PDF
# ============================================================

@app.route("/invoice/<int:booking_id>")
def invoice(booking_id):

    with db_cursor(dictionary=True) as cursor:

        cursor.execute(
            """
            SELECT

                b.*,

                c.name,
                c.phone,
                c.email,
                c.address,

                r.room_number,
                r.room_type,
                r.price

            FROM bookings b

            JOIN customers c
                ON b.customer_id = c.customer_id

            JOIN rooms r
                ON b.room_id = r.room_id

            WHERE b.booking_id = %s
            """,
            (booking_id,)
        )

        booking_data = cursor.fetchone()


    if not booking_data:

        return "Booking not found", 404


    # --------------------------------------------------------
    # CREATE PDF IN MEMORY
    # --------------------------------------------------------

    pdf_buffer = BytesIO()

    pdf = canvas.Canvas(
        pdf_buffer,
        pagesize=A4
    )

    width, height = A4

    y = height - 60


    pdf.setFont(
        "Helvetica-Bold",
        20
    )

    pdf.drawString(
        50,
        y,
        "HOTEL BOOKING INVOICE"
    )


    y -= 40

    pdf.setFont(
        "Helvetica",
        11
    )

    pdf.drawString(
        50,
        y,
        f"Booking Code: {booking_data['booking_code']}"
    )


    y -= 20

    pdf.drawString(
        50,
        y,
        f"Booking ID: {booking_data['booking_id']}"
    )


    y -= 40

    pdf.setFont(
        "Helvetica-Bold",
        13
    )

    pdf.drawString(
        50,
        y,
        "Guest Details"
    )


    y -= 25

    pdf.setFont(
        "Helvetica",
        11
    )

    pdf.drawString(
        50,
        y,
        f"Name: {booking_data['name']}"
    )


    y -= 20

    pdf.drawString(
        50,
        y,
        f"Phone: {booking_data['phone']}"
    )


    y -= 20

    pdf.drawString(
        50,
        y,
        f"Email: {booking_data['email']}"
    )


    y -= 40

    pdf.setFont(
        "Helvetica-Bold",
        13
    )

    pdf.drawString(
        50,
        y,
        "Room Details"
    )


    y -= 25

    pdf.setFont(
        "Helvetica",
        11
    )

    pdf.drawString(
        50,
        y,
        f"Room Number: {booking_data['room_number']}"
    )


    y -= 20

    pdf.drawString(
        50,
        y,
        f"Room Type: {booking_data['room_type']}"
    )


    y -= 20

    pdf.drawString(
        50,
        y,
        f"Check-in: {booking_data['check_in']}"
    )


    y -= 20

    pdf.drawString(
        50,
        y,
        f"Check-out: {booking_data['check_out']}"
    )


    y -= 20

    pdf.drawString(
        50,
        y,
        f"Guests: {booking_data['number_of_guests']}"
    )


    y -= 40

    pdf.setFont(
        "Helvetica-Bold",
        14
    )

    pdf.drawString(
        50,
        y,
        f"Total Amount: ₹{booking_data['total_amount']}"
    )


    y -= 40

    pdf.setFont(
        "Helvetica",
        10
    )

    pdf.drawString(
        50,
        y,
        "Thank you for choosing our hotel."
    )


    pdf.save()

    pdf_buffer.seek(0)


    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=(
            f"invoice_{booking_data['booking_code']}.pdf"
        ),
        mimetype="application/pdf"
    )


# ============================================================
# API — ROOMS
# ============================================================

@app.route("/api/rooms")
def api_rooms():

    with db_cursor(dictionary=True) as cursor:

        cursor.execute("""
            SELECT
                room_id,
                room_number,
                room_type,
                price,
                status,
                description,
                image
            FROM rooms
            ORDER BY room_id
        """)

        room_list = cursor.fetchall()


    return {
        "rooms": room_list
    }


# ============================================================
# API — BOOKING
# ============================================================

@app.route("/api/booking/<int:booking_id>")
def api_booking(booking_id):

    with db_cursor(dictionary=True) as cursor:

        cursor.execute(
            """
            SELECT

                b.*,

                c.name,
                c.phone,
                c.email,
                c.address,

                r.room_number,
                r.room_type,
                r.price

            FROM bookings b

            JOIN customers c
                ON b.customer_id = c.customer_id

            JOIN rooms r
                ON b.room_id = r.room_id

            WHERE b.booking_id = %s
            """,
            (booking_id,)
        )

        booking_data = cursor.fetchone()


    if not booking_data:

        return {
            "error": "Booking not found"
        }, 404


    return booking_data


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )

