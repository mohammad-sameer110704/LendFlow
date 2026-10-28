from flask import Flask, request, render_template, redirect, url_for
import mysql.connector


# =========================================================
# FLASK APPLICATION
# =========================================================

app = Flask(__name__)


# =========================================================
# MYSQL DATABASE CONFIGURATION
# =========================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "lendflow"
}


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():

    return mysql.connector.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"]
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():
    return """
    <h1>LendFlow Flask Application Running</h1>
    <h2>Admin</h2>
    <a href="/admin/signup">Admin Signup</a><br>
    <a href="/admin/login">Admin Login</a><br>
    <h2>Borrower</h2>
    <a href="/loan">Borrower Signup</a><br>
    <a href="/barrower/login">Borrower Login</a><br>
    <h2>Payments</h2>
    <a href="/payments">Make Payment</a><br>
    <h2>Search</h2>
    <a href="/search_barrower">Search Borrower</a>
    """


# =========================================================
# ADMIN SIGNUP
# =========================================================

@app.route("/admin/signup", methods=["GET", "POST"])
def admin_signup():
    if request.method == "GET":
        return render_template("admin_signup.html")

    name = request.form.get("name")
    phno = request.form.get("phno")
    adhaar = request.form.get("adhaar")
    password = request.form.get("password")

    if not name or not phno or not adhaar or not password:
        return "Name, phno, adhaar and password are required", 400

    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT phno FROM admin WHERE phno = %s", (phno,))
    result = cursor.fetchone()

    if result:
        return "Phone number already registered", 409

    # Insert admin
    cursor.execute("INSERT INTO admin (name, phno, adhaar, password) VALUES (%s, %s, %s, %s)", (name, phno, adhaar, password))
    connection.commit()
    cursor.close()
    connection.close()

    return "Admin registration successful", 201
       

# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "GET":
        return render_template("admin_login.html")

    phno = request.form.get("phno")
    password = request.form.get("password")

    if not phno or not password:
        return "phno and password are required", 400

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM admin WHERE phno = %s", (phno,))
    admin = cursor.fetchone()

    if not admin:
        return "phno not found", 404

    stored_password = admin["password"]

    if password != stored_password:
        return "Incorrect password", 401

    cursor.close()
    connection.close()
    return "Admin login successful"

# =========================================================
# Loan Creation
# =========================================================

@app.route("/loan", methods=["GET", "POST"])
def loan_creation():

    if request.method == "GET":
        return render_template("borrower_signup.html")

    name = request.form.get("name")
    phno = request.form.get("phno")
    adhaar = request.form.get("adhaar")
    amount = request.form.get("amount")

    if not all([name, phno, adhaar, amount]):
        return "All fields are required", 400

    # Currently using Aadhaar as the password
    password = adhaar

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)


    # Check whether the borrower already exists
    cursor.execute("SELECT * FROM loan WHERE phno = %s",(phno,))
    borrower = cursor.fetchone()

    if borrower:
        return "Borrower already exists", 409

    # Insert loan details
    cursor.execute("INSERT INTO loan (name, phno, adhaar, amount) VALUES (%s, %s, %s, %s)", (name, phno, adhaar, amount))
    connection.commit()
    cursor.close()
    connection.close()

    return "Loan created successfully", 201

# =========================================================
# Barrower LOGIN
# =========================================================

@app.route("/barrower/login", methods=["GET", "POST"])
def barrower_login():
    if request.method == "GET":
        return render_template("borrower_login.html")

    phno = request.form.get("phno")
    password = request.form.get("password")

    if not phno or not password:
        return "phno and password are required", 400

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM loan WHERE phno = %s", (phno,))
    borrower = cursor.fetchone()

    if not borrower:
        return "phno not found", 404

    stored_password = borrower["password"]

    if password != stored_password:
        return "Incorrect password", 401
    cursor.close()
    connection.close()
    return redirect(f"/change_password/{borrower['phno']}")

# =========================================================
# Change Password
# =========================================================

@app.route("/change_password/<int:phno>", methods=["GET", "POST"])
def change_password(phno):
    if request.method == "GET":
        return render_template("change_password.html", phno=phno)

    new_password = request.form.get("new_password")
    confirm_password = request.form.get("confirm_password")

    if not new_password or not confirm_password:
        return "Both password fields are required", 400

    if new_password != confirm_password:
        return "Passwords do not match", 400

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    # Update password and mark as changed
    cursor.execute("UPDATE barrower SET password = %s,WHERE phno = %s", (new_password, phno))
    connection.commit()
    cursor.close()
    connection.close()

    return "Password changed successfully. Please login again."

# =========================================================
# Payments
# =========================================================

@app.route("/payments", methods=["GET", "POST"])
def payments():
    if request.method == "GET":
        return render_template("payment.html")

    phno = request.form.get("phno")
    amount = request.form.get("amount")

    if not all([phno, amount]):
        return "All fields are required", 400

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM loan WHERE phno = %s", (phno,))
    loan = cursor.fetchone()

    if not loan:
        cursor.close()
        connection.close()
        return "Loan not found", 404

    # Insert payment
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT name,adhaar FROM loan WHERE phno = %s", (phno,))
    data=cursor.fetchone()
    name=data["name"]
    adhaar=data["adhaar"]
    cursor.execute("INSERT INTO payments (phno, amount,name,adhaar) VALUES (%s, %s)", (phno, amount,name,adhaar))
    connection.commit()
    cursor.close()
    connection.close()

    return "Payment saved successfully", 201

# =========================================================
# Search barrower by adhaar
# =========================================================

@app.route("/search_barrower", methods=["GET", "POST"])
def search_barrower():
    if request.method == "GET":
            return render_template("search.html")

    adhaar = request.form.get("adhaar")

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM loan WHERE adhaar = %s", (adhaar,))
    data = cursor.fetchall()
    cursor.close()
    connection.close()

    if data:
        return f"Found {len(data)} record(s)"
    return "records not found"

# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )