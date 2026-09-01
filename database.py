import os
from contextlib import contextmanager

import mysql.connector
from config import Config


@contextmanager
def db_cursor(dictionary=False):
    connection = mysql.connector.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME
    )

    cursor = connection.cursor(dictionary=dictionary)

    try:
        yield cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()
