from flask import Flask
from config import Config

from routes.public import public_bp
from routes.booking import booking_bp
from routes.rooms import rooms_bp
from routes.guests import guests_bp
from routes.staff import staff_bp
from routes.chatbot import chatbot_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.register_blueprint(public_bp)
    app.register_blueprint(booking_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(guests_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(chatbot_bp)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)