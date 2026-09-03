# DESKFLOW — Flask + MySQL Backend

This project connects the supplied DESKFLOW hotel frontend to a beginner-friendly Flask backend using MySQL Connector/Python.

## What is included

- Flask web server
- MySQL database
- `mysql-connector-python` for database access
- Staff authentication using Flask sessions and password hashing
- Room availability checking before booking
- Guest and booking storage
- Booking confirmation page
- Automatic PDF invoice generation with ReportLab
- Staff dashboard, bookings, guests, rooms and housekeeping pages
- `schema.sql` and `seed.sql` with 30 sample rooms and demo records
- Your original frontend styling is kept in `static/style.css`

## Project structure

```text
DESKFLOW_backend/
├── app.py
├── db.py
├── invoice_generator.py
├── requirements.txt
├── schema.sql
├── seed.sql
├── seed_admin.py
├── static/
│   └── style.css
├── templates/
│   ├── index.html
│   ├── rooms.html
│   ├── booking.html
│   ├── confirmation.html
│   ├── staff-login.html
│   ├── dashboard.html
│   ├── bookings.html
│   ├── guests.html
│   ├── rooms-management.html
│   ├── housekeeping.html
│   └── invoice.html
└── generated_invoices/
```

## 1. Install Python

Install Python 3.11+.

Check:

```bash
python --version
```

## 2. Install MySQL

Install MySQL Server and MySQL Workbench.

Remember the MySQL `root` password you created during installation.

## 3. Open the project

In Command Prompt / PowerShell:

```bash
cd path\to\DESKFLOW_backend
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

You should now see `(venv)` at the beginning of the terminal line.

## 4. Install Python packages

```bash
pip install -r requirements.txt
```

The important packages are:

- Flask — web framework
- mysql-connector-python — connects Python to MySQL
- ReportLab — creates PDF invoices
- Werkzeug — secure password hashing

## 5. Create the database

Open MySQL Workbench.

Open `schema.sql`, run the entire file.

This creates:

- `deskflow` database
- `staff_users`
- `rooms`
- `guests`
- `bookings`
- `housekeeping`

## 6. Add sample data

Open `seed.sql` in MySQL Workbench and run it.

It creates 30 rooms plus sample guests/bookings.

The demo staff login is:

```text
Email:    admin@deskflow.com
Password: admin123
```

## 7. Configure MySQL connection

Open `db.py`.

Change this line:

```python
password=os.getenv("DB_PASSWORD", "YOUR_MYSQL_PASSWORD"),
```

to your actual MySQL password if you are not using environment variables.

Example:

```python
password=os.getenv("DB_PASSWORD", "root123"),
```

For a college project this is easy to understand. In a real application, do not commit database passwords to GitHub.

## 8. Run the Flask application

With the virtual environment active:

```bash
python app.py
```

You should see something similar to:

```text
Running on http://127.0.0.1:5000
```

Open:

```text
http://127.0.0.1:5000/
```

Do NOT double-click the HTML files anymore. Flask must serve them.

## 9. Test the complete booking flow

1. Open Home.
2. Click `Book a stay`.
3. Select check-in and check-out dates.
4. Select a room.
5. Select number of guests.
6. Enter name, email and phone.
7. Click `Confirm my stay`.
8. Flask validates the dates and room.
9. The guest is inserted/updated in MySQL.
10. The booking is inserted into MySQL.
11. You are sent to the confirmation page.
12. Click `Download Invoice PDF`.
13. A PDF invoice is generated in `generated_invoices/`.

## 10. Test staff authentication

Go to:

```text
http://127.0.0.1:5000/staff-login.html
```

Use:

```text
admin@deskflow.com
admin123
```

After login you can open:

- Dashboard
- Bookings
- Guests
- Rooms
- Housekeeping

The management pages are protected by the `login_required` decorator. If a person is not logged in, Flask sends them back to the staff login page.

## 11. How the database works

The main relationship is:

```text
STAFF USERS
    |
    | authentication
    v

GUESTS 1 -------- many BOOKINGS many -------- 1 ROOMS
                         |
                         |
                         v
                  HOUSEKEEPING
```

A booking stores:

- guest
- room
- check-in
- check-out
- number of guests
- special requests
- total amount
- booking status

The backend calculates:

```text
number of nights = check-out - check-in

total = number of nights × room price
```

The user cannot simply send their own price from the browser because the server gets the room price from MySQL.

## 12. Important beginner files

### `app.py`

Contains the Flask routes and application logic.

For example:

```python
@app.route("/api/booking", methods=["POST"])
def create_booking():
```

handles a new booking.

### `db.py`

Contains the MySQL connection function:

```python
get_connection()
```

Every route obtains a connection, performs its SQL queries, then closes the cursor and connection.

### `invoice_generator.py`

Uses ReportLab to create the invoice PDF.

### `templates/`

Contains the frontend HTML pages served by Flask.

### `static/`

Contains CSS and other static frontend assets.

## 13. Why the frontend is now connected

The old booking page used a normal link:

```text
booking.html → confirmation.html
```

That did not save anything.

The new booking page sends a POST request:

```text
Browser
   ↓
POST /api/booking
   ↓
Flask
   ↓
Validate dates + room
   ↓
MySQL
   ↓
Create booking
   ↓
Confirmation page
   ↓
PDF invoice
```

The staff login similarly sends the email/password to Flask instead of directly opening the dashboard.

## 14. Common errors

### `ModuleNotFoundError: No module named 'mysql'`

Run:

```bash
pip install mysql-connector-python
```

### `ModuleNotFoundError: No module named 'flask'`

Run:

```bash
pip install Flask
```

### MySQL access denied

Check the username/password in `db.py`.

### Unknown database `deskflow`

Run `schema.sql` in MySQL Workbench.

### Page opens but CSS is missing

Make sure you start Flask with:

```bash
python app.py
```

and visit:

```text
http://127.0.0.1:5000/
```

Do not open `index.html` directly from File Explorer.

### `Address already in use`

Stop the other Flask/Python process or close the terminal running it.

## 15. Recommended order for your DBMS project

For a beginner, learn and demonstrate the project in this order:

1. MySQL database creation
2. Tables and primary/foreign keys
3. Insert sample data
4. Python MySQL connection
5. SELECT queries
6. Flask routes
7. HTML form → Flask POST
8. INSERT booking
9. Authentication/session
10. PDF invoice generation

This gives you a clear explanation for a DBMS viva.

## 16. Security note

This is intentionally beginner-friendly. For a production hotel system you would additionally add CSRF protection, stronger session configuration, role-based authorization, HTTPS, rate limiting, environment-based secrets and payment processing.
