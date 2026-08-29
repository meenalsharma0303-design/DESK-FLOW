from flask import Blueprint, jsonify, request
from database import db_cursor

rooms_bp = Blueprint("rooms", __name__)


@rooms_bp.get("/api/rooms")
def list_rooms():
    status = request.args.get("status")

    with db_cursor(dictionary=True) as (_, cursor):
        if status:
            cursor.execute("""
                SELECT * FROM rooms
                WHERE status = %s
                ORDER BY room_number
            """, (status,))
        else:
            cursor.execute("""
                SELECT * FROM rooms
                ORDER BY room_number
            """)
        rooms = cursor.fetchall()

    for room in rooms:
        room["price"] = float(room["price"])

    return jsonify(rooms)


@rooms_bp.post("/api/rooms")
def create_room():
    data = request.get_json(silent=True) or {}

    required = ["room_number", "room_type", "price"]
    if any(not data.get(k) for k in required):
        return jsonify({"error": "room_number, room_type and price are required"}), 400

    with db_cursor() as (_, cursor):
        cursor.execute("""
            INSERT INTO rooms
            (room_number, room_type, price, status, description, image)
            VALUES (%s, %s, %s, 'Available', %s, %s)
        """, (
            data["room_number"],
            data["room_type"],
            data["price"],
            data.get("description", ""),
            data.get("image"),
        ))
        room_id = cursor.lastrowid

    return jsonify({"message": "Room created", "room_id": room_id}), 201


@rooms_bp.put("/api/rooms/<int:room_id>")
def update_room(room_id):
    data = request.get_json(silent=True) or {}

    with db_cursor() as (_, cursor):
        cursor.execute("""
            UPDATE rooms
            SET room_number = %s,
                room_type = %s,
                price = %s,
                status = %s,
                description = %s,
                image = %s
            WHERE room_id = %s
        """, (
            data.get("room_number"),
            data.get("room_type"),
            data.get("price"),
            data.get("status"),
            data.get("description", ""),
            data.get("image"),
            room_id,
        ))

        if cursor.rowcount == 0:
            return jsonify({"error": "Room not found"}), 404

    return jsonify({"message": "Room updated"})


@rooms_bp.delete("/api/rooms/<int:room_id>")
def delete_room(room_id):
    with db_cursor(dictionary=True) as (_, cursor):
        cursor.execute("""
            SELECT status FROM rooms WHERE room_id = %s
        """, (room_id,))
        room = cursor.fetchone()

        if not room:
            return jsonify({"error": "Room not found"}), 404

        if room["status"] == "Booked":
            return jsonify({"error": "Booked rooms cannot be deleted"}), 400

        cursor.execute("DELETE FROM rooms WHERE room_id = %s", (room_id,))

    return jsonify({"message": "Room deleted"})
