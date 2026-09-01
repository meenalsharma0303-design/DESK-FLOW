import os
from pathlib import Path

from dotenv import load_dotenv


# Get the directory where this config.py file is located
BASE_DIR = Path(__file__).resolve().parent

# Explicitly load .env from the project directory
ENV_FILE = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE)


class Config:

    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY")

    # Database
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_NAME = os.getenv("DB_NAME", "hotel")

    # Hotel
    HOTEL_NAME = os.getenv(
        "HOTEL_NAME",
        "DESK-FLOW Hotel"
    )

    HOTEL_ADDRESS = os.getenv(
        "HOTEL_ADDRESS",
        ""
    )

    HOTEL_PHONE = os.getenv(
        "HOTEL_PHONE",
        ""
    )

    HOTEL_EMAIL = os.getenv(
        "HOTEL_EMAIL",
        ""
    )

    # SMTP
    SMTP_HOST = os.getenv(
        "SMTP_HOST",
        "smtp.gmail.com"
    )

    SMTP_PORT = int(
        os.getenv("SMTP_PORT", "587")
    )

    SMTP_USER = os.getenv(
        "SMTP_USER",
        ""
    )

    SMTP_PASSWORD = os.getenv(
        "SMTP_PASSWORD",
        ""
    )

    SMTP_USE_TLS = (
        os.getenv(
            "SMTP_USE_TLS",
            "true"
        ).lower() == "true"
    )