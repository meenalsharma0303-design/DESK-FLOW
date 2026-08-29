from flask import Blueprint, jsonify, request
from database import db_cursor

guests_bp = Blueprint("guests", __name__)


@guests_bp.get("/api/guests")
def list_guests():
    search = request.args.get("search", "").strip()

    with db_cursor(dictionary=True) as (_, cursor):
        if search:
            pattern = f"%{search}%"
            cursor.execute("""
                SELECT *
                FROM customers
                WHERE name LIKE %s
                   OR phone LIKE %s
                   OR email LIKE %s
                ORDER BY customer_id DESC
            """, (pattern, pattern, pattern))
        else:
            cursor.execute("""
                SELECT *
                FROM customers
                ORDER BY customer_id DESC
            """)
        guests = cursor.fetchall()

    return jsonify(guests)


@guests_bp.post("/api/guests")
def create_guest():
    data = request.get_json(silent=True) or {}

    if not all(data.get(k) for k in ("name", "phone", "email")):
        return jsonify({"error": "name, phone and email are required"}), 400

    with db_cursor() as (_, cursor):
        cursor.execute("""
            INSERT INTO customers (name, phone, email, address)
            VALUES (%s, %s, %s, %s)
        """, (
            data["name"],
            data["phone"],
            data["email"],
            data.get("address", ""),
        ))
        guest_id = cursor.lastrowid

    return jsonify({"message": "Guest created", "customer_id": guest_id}), 201


@guests_bp.put("/api/guests/<int:customer_id>")
def update_guest(customer_id):
    data = request.get_json(silent=True) or {}

    with db_cursor() as (_, cursor):
        cursor.execute("""
            UPDATE customers
            SET name = %s,
                phone = %s,
                email = %s,
                address = %s
            WHERE customer_id = %s
        """, (
            data.get("name"),
            data.get("phone"),
            data.get("email"),
            data.get("address", ""),
            customer_id,
        ))

        if cursor.rowcount == 0:
            return jsonify({"error": "Guest not found"}), 404

    return jsonify({"message": "Guest updated"})


@guests_bp.delete("/api/guests/<int:customer_id>")
def delete_guest(customer_id):
    with db_cursor() as (_, cursor):
        cursor.execute(
            "DELETE FROM customers WHERE customer_id = %s",
            (customer_id,),
        )
        if cursor.rowcount == 0:
            return jsonify({"error": "Guest not found"}), 404

    return jsonify({"message": "Guest deleted"})
