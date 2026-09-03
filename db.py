import os
import mysql.connector
from mysql.connector import Error

def get_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "akgec"),
            database=os.getenv("DB_NAME", "deskflow")
        )
    except Error as e:
        raise RuntimeError(f"Could not connect to MySQL: {e}")
