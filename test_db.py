from database import db_cursor

try:
    with db_cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()

    print("Database connection successful!")
    print("Result:", result)

except Exception as e:
    print("Database connection failed!")
    print("Error:", e)