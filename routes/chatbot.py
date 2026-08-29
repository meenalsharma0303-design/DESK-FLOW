from flask import Blueprint, jsonify, request
from database import db_cursor

chatbot_bp = Blueprint("chatbot", __name__)


def hotel_context():
    with db_cursor(dictionary=True) as (_, cursor):
        cursor.execute("""
            SELECT room_type, COUNT(*) AS total,
                   SUM(status = 'Available') AS available,
                   MIN(price) AS starting_price
            FROM rooms
            GROUP BY room_type
            ORDER BY room_type
        """)
        rooms = cursor.fetchall()

    return rooms


@chatbot_bp.post("/api/chatbot/message")
def chatbot_message():
    data = request.get_json(silent=True) or {}

    message = (data.get("message") or "").strip()
    customer_id = data.get("customer_id")

    if not message:
        return jsonify({"error": "Message is required"}), 400

    # Safe starter response. Replace this function with an AI provider
    # later; keep database/business operations on the Flask side.
    lower = message.lower()
    rooms = hotel_context()

    if "room" in lower or "available" in lower:
        if rooms:
            parts = []
            for r in rooms:
                parts.append(
                    f"{r['room_type']}: {int(r['available'])} available, "
                    f"from ₹{float(r['starting_price']):,.0f}"
                )
            response = "Current room availability: " + "; ".join(parts)
        else:
            response = "I could not find room information right now."
    elif "check-in" in lower or "check in" in lower:
        response = "Please use the hotel's published check-in policy on the website."
    else:
        response = (
            "Hello! I can help with room availability, room types and "
            "general hotel questions."
        )

    with db_cursor() as (_, cursor):
        cursor.execute("""
            INSERT INTO chatbot_messages
            (customer_id, user_message, bot_response)
            VALUES (%s, %s, %s)
        """, (customer_id, message, response))

    return jsonify({"message": response})


@chatbot_bp.get("/api/chatbot/history/<int:customer_id>")
def chatbot_history(customer_id):
    with db_cursor(dictionary=True) as (_, cursor):
        cursor.execute("""
            SELECT message_id, user_message, bot_response, created_at
            FROM chatbot_messages
            WHERE customer_id = %s
            ORDER BY created_at ASC
        """, (customer_id,))
        messages = cursor.fetchall()

    for m in messages:
        m["created_at"] = str(m["created_at"])

    return jsonify(messages)
