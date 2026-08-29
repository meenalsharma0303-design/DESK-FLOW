import os
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv

from routes.public import public_bp
from routes.booking import booking_bp
from routes.staff import staff_bp
from routes.rooms import rooms_bp
from routes.guests import guests_bp
from routes.chatbot import chatbot_bp

load_dotenv()

app = Flask(
    __name__,
    template_folder="templates",
    static_folder="static",
)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "change-this-secret-key",
)

app.register_blueprint(public_bp)
app.register_blueprint(booking_bp)
app.register_blueprint(staff_bp)
app.register_blueprint(rooms_bp)
app.register_blueprint(guests_bp)
app.register_blueprint(chatbot_bp)


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "service": "DeskFlow Hotel backend"})


@app.errorhandler(404)
def not_found(error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found"}), 404
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Internal server error"}), 500
    return render_template("500.html"), 500


if __name__ == "__main__":
    app.run(debug=True)
