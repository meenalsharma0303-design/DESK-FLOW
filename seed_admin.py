from werkzeug.security import generate_password_hash
from db import get_connection

conn=get_connection()
cur=conn.cursor()
cur.execute("""
UPDATE staff_users SET password_hash=%s WHERE email=%s
""",(generate_password_hash("admin123"),"admin@deskflow.com"))
conn.commit()
cur.close(); conn.close()
print("Admin password set. Login: admin@deskflow.com / admin123")
