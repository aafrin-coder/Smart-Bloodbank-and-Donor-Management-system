from flask import Flask, render_template, request, redirect, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

from flask import send_file
from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Table

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

app.secret_key = "smart_blood_bank_secret_key"

EMAIL_ADDRESS = "smartbloodbank2026@gmail.com"
EMAIL_PASSWORD = "zoxd waye bpmo ptty"


# Database Connection
def get_db_connection():
    conn = sqlite3.connect("bloodbank.db")
    conn.row_factory = sqlite3.Row
    return conn

def send_welcome_email(receiver_email, full_name):

    subject = "Welcome to Smart Blood Bank"

    body = f"""
Dear {full_name},

Thank you for registering with Smart Blood Bank Management System.

Your account has been created successfully.

You can now log in and:
• Register as a donor
• Request blood
• View your profile

Thank you for helping save lives.

Regards,
Smart Blood Bank Team
"""

    msg = MIMEMultipart()

    msg["From"] = EMAIL_ADDRESS
    msg["To"] = receiver_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("Email Error:", e)

#home page

@app.route('/')
def home():

    conn = get_db_connection()

    total_donors = conn.execute(
        "SELECT COUNT(*) FROM donor"
    ).fetchone()[0]

    total_stock = conn.execute(
        "SELECT SUM(units) FROM blood_stock"
    ).fetchone()[0] or 0

    total_requests = conn.execute(
        "SELECT COUNT(*) FROM blood_request"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "home.html",
        total_donors=total_donors,
        total_stock=total_stock,
        total_requests=total_requests
    )

#login page

@app.route('/login')
def login():
    return render_template("login.html")

@app.route('/login', methods=['POST'])
def check_login():

    username = request.form['username']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM admin WHERE username=?",
        (username,)
    )

    admin = cursor.fetchone()
    conn.close()

    if admin and check_password_hash(admin["password"], password):
        session.clear()
        session["admin_id"] = admin["admin_id"]
        session["admin_name"] = admin["username"]

        return redirect("/dashboard")

    return render_template(
        "login.html",
        error="Invalid Admin Username or Password"
    )

# Register page

@app.route('/register')
def register():
    return render_template("register.html")

@app.route('/register', methods=['POST'])
def save_register():

    full_name = request.form['full_name']
    username = request.form['username']
    email = request.form['email']
    phone = request.form['phone']
    blood_group = request.form['blood_group']
    password = request.form['password']
    confirm_password = request.form['confirm_password']

    if password != confirm_password:

        return render_template(
            "register.html",
            error="Passwords do not match"
        )

    conn = get_db_connection()

    existing = conn.execute(
        "SELECT * FROM users WHERE username=? OR email=?",
        (username, email)
    ).fetchone()

    if existing:

        conn.close()

        return render_template(
            "register.html",
            error="Username or Email already exists"
        )

    hashed_password = generate_password_hash(password)

    conn.execute("""

    INSERT INTO users
    (full_name,username,email,phone,blood_group,password)

    VALUES(?,?,?,?,?,?)

    """,

    (

    full_name,
    username,
    email,
    phone,
    blood_group,
    hashed_password

    ))

    conn.commit()
    conn.close()

    send_welcome_email(email,full_name)

    return redirect("/user_login")

# User login
@app.route('/user_login')
def user_login():

    return render_template("user_login.html")

@app.route('/user_login', methods=['POST'])
def check_user_login():

    email = request.form['email']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE email=?",
        (email,)
    )

    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user["password"], password):
        session.clear()
        session["user_id"] = user["user_id"]
        session["user_name"] = user["full_name"]

        return redirect("/user_dashboard")

    return render_template(
        "user_login.html",
        error="Invalid Email or Password"
    )


# User dashboard

@app.route('/user_dashboard')
def user_dashboard():

    if "user_id" not in session:
        return redirect("/user_login")

    conn = get_db_connection()

    user = conn.execute(
        "SELECT * FROM users WHERE user_id=?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    return render_template(
        "user_dashboard.html",
        user=user
    )

# Profile 

@app.route('/profile')
def profile():

    if "user_id" not in session:
        return redirect("/user_login")

    conn = get_db_connection()

    user = conn.execute(
        "SELECT * FROM users WHERE user_id=?",
        (session["user_id"],)
    ).fetchone()

    conn.close()

    return render_template(
        "user_profile.html",
        user=user
    )

@app.route('/update_profile', methods=['POST'])
def update_profile():

    if "user_id" not in session:
        return redirect("/user_login")

    full_name = request.form['full_name']
    email = request.form['email']
    phone = request.form['phone']
    blood_group = request.form['blood_group']

    conn = get_db_connection()

    conn.execute("""

    UPDATE users

    SET

    full_name=?,
    email=?,
    phone=?,
    blood_group=?

    WHERE user_id=?

    """,

    (

    full_name,
    email,
    phone,
    blood_group,
    session["user_id"]

    ))

    conn.commit()

    conn.close()

    return redirect("/profile")

# Dashboard

@app.route('/dashboard')
def dashboard():

    if "admin_id" not in session:
        return redirect("/")

    conn = get_db_connection()

    total_donors = conn.execute(
        "SELECT COUNT(*) FROM donor"
    ).fetchone()[0]

    total_recipients = conn.execute(
        "SELECT COUNT(*) FROM recipient"
    ).fetchone()[0]

    total_requests = conn.execute(
        "SELECT COUNT(*) FROM blood_request"
    ).fetchone()[0]

    total_stock = conn.execute(
        "SELECT COUNT(*) FROM blood_stock"
    ).fetchone()[0]


    blood_stock = conn.execute("""
    SELECT
         blood_group,
         SUM(units) AS units,

        CASE
            WHEN SUM(units) < 5 THEN 'Low Stock'
            ELSE 'Available'
        END AS status

    FROM blood_stock

    GROUP BY blood_group
    """).fetchall()


    conn.close()

    return render_template(
        "dashboard.html",
        total_donors=total_donors,
        total_recipients=total_recipients,
        total_requests=total_requests,
        total_stock=total_stock,
        blood_stock=blood_stock
    )

# donor page

@app.route('/donor')
def donor():

    return render_template("donor.html")

#add_donor

@app.route('/add_donor', methods=['POST'])
def add_donor():

    donor_name = request.form['donor_name']
    age = request.form['age']
    gender = request.form['gender']
    blood_group = request.form['blood_group']
    phone = request.form['phone']
    email = request.form['email']
    address = request.form['address']
    last_donation = request.form['last_donation']

    conn = get_db_connection()

    conn.execute("""
        INSERT INTO donor
        (donor_name,age,gender,blood_group,phone,email,address,last_donation)

        VALUES(?,?,?,?,?,?,?,?)
    """,

    (
        donor_name,
        age,
        gender,
        blood_group,
        phone,
        email,
        address,
        last_donation
    ))

    conn.commit()
    conn.close()

    return redirect('/view_donors')

#view_donor

@app.route('/view_donors')
def view_donors():

    conn = get_db_connection()

    donors = conn.execute(
        "SELECT * FROM donor"
    ).fetchall()

    conn.close()

    return render_template(
        "view_donors.html",
        donors=donors
    )

# Search Donors

@app.route('/search_donor')
def search_donor():

    keyword = request.args.get('keyword')

    conn = get_db_connection()

    donors = conn.execute("""

    SELECT * FROM donor

    WHERE donor_name LIKE ?

    OR blood_group LIKE ?

    OR phone LIKE ?

    """,

    (

    '%' + keyword + '%',

    '%' + keyword + '%',

    '%' + keyword + '%'

    )).fetchall()

    conn.close()

    return render_template(
        "view_donors.html",
        donors=donors
    )

# Edit Donor
@app.route('/edit_donor/<int:id>')
def edit_donor(id):

    conn = get_db_connection()

    donor = conn.execute(
        "SELECT * FROM donor WHERE donor_id=?",
        (id,)
    ).fetchone()

    conn.close()

    return render_template(
        "edit_donor.html",
        donor=donor
    )


# Update Donor
@app.route('/update_donor/<int:id>', methods=['POST'])
def update_donor(id):

    conn = get_db_connection()

    conn.execute("""
    UPDATE donor
    SET donor_name=?,
        age=?,
        gender=?,
        blood_group=?,
        phone=?,
        email=?,
        address=?,
        last_donation=?
    WHERE donor_id=?
    """,

    (
        request.form['donor_name'],
        request.form['age'],
        request.form['gender'],
        request.form['blood_group'],
        request.form['phone'],
        request.form['email'],
        request.form['address'],
        request.form['last_donation'],
        id
    ))

    conn.commit()
    conn.close()

    return redirect('/view_donors')


# Delete Donor
@app.route('/delete_donor/<int:id>')
def delete_donor(id):

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM donor WHERE donor_id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect('/view_donors')

# Blood Stock Page
@app.route('/blood_stock')
def blood_stock():

    conn = get_db_connection()

    stock = conn.execute(
        "SELECT * FROM blood_stock"
    ).fetchall()

    conn.close()

    return render_template(
        "blood_stock.html",
        stock=stock
    )


# Add Blood Stock
@app.route('/add_stock', methods=['POST'])
def add_stock():

    blood_group = request.form['blood_group']
    units = request.form['units']

    conn = get_db_connection()

    conn.execute(
        """
        INSERT INTO blood_stock
        (blood_group, units)
        VALUES (?,?)
        """,
        (blood_group, units)
    )

    conn.commit()
    conn.close()

    return redirect('/blood_stock')


# ---------------- Recipient Page ----------------

@app.route('/recipient')
def recipient():
    return render_template("recipient.html")


# ---------------- Add Recipient ----------------

@app.route('/add_recipient', methods=['POST'])
def add_recipient():

    recipient_name = request.form['recipient_name']
    age = request.form['age']
    gender = request.form['gender']
    blood_group = request.form['blood_group']
    phone = request.form['phone']
    hospital = request.form['hospital']

    conn = get_db_connection()

    conn.execute("""
    INSERT INTO recipient
    (recipient_name,age,gender,blood_group,phone,hospital)

    VALUES(?,?,?,?,?,?)
    """,

    (
        recipient_name,
        age,
        gender,
        blood_group,
        phone,
        hospital
    ))

    conn.commit()
    conn.close()

    return redirect('/view_recipients')


# ---------------- View Recipients ----------------

@app.route('/view_recipients')
def view_recipients():

    conn = get_db_connection()

    recipients = conn.execute(
        "SELECT * FROM recipient"
    ).fetchall()

    conn.close()

    return render_template(
        "view_recipients.html",
        recipients=recipients
    )

# ---------------- Search Recipients ----------------

@app.route('/search_recipient')
def search_recipient():

    keyword = request.args.get('keyword')

    conn = get_db_connection()

    recipients = conn.execute("""

    SELECT * FROM recipient

    WHERE recipient_name LIKE ?

    OR blood_group LIKE ?

    OR phone LIKE ?

    """,

    (

    '%' + keyword + '%',

    '%' + keyword + '%',

    '%' + keyword + '%'

    )).fetchall()

    conn.close()

    return render_template(
        "view_recipients.html",
        recipients=recipients
    )



# ---------------- Blood Request Page ----------------

@app.route('/blood_request')
def blood_request():
    return render_template("blood_request.html")


# ---------------- Add Blood Request ----------------

@app.route('/add_request', methods=['POST'])
def add_request():

    patient_name = request.form['patient_name']
    blood_group = request.form['blood_group']
    units = request.form['units']
    hospital = request.form['hospital']

    conn = get_db_connection()

    conn.execute("""
    INSERT INTO blood_request
    (patient_name, blood_group, units, hospital, status)

    VALUES (?, ?, ?, ?, ?)
    """,

    (
        patient_name,
        blood_group,
        units,
        hospital,
        "Pending"
    ))

    conn.commit()
    conn.close()

    return redirect('/view_requests')


# ---------------- View Blood Requests ----------------

@app.route('/view_requests')
def view_requests():

    conn = get_db_connection()

    requests = conn.execute(
        "SELECT * FROM blood_request"
    ).fetchall()

    conn.close()

    return render_template(
        "view_requests.html",
        requests=requests
    )


# ---------------- Reports ----------------

@app.route('/reports')
def reports():

    conn = get_db_connection()

    total_donors = conn.execute(
        "SELECT COUNT(*) FROM donor"
    ).fetchone()[0]

    total_recipients = conn.execute(
        "SELECT COUNT(*) FROM recipient"
    ).fetchone()[0]

    total_stock = conn.execute(
        "SELECT COUNT(*) FROM blood_stock"
    ).fetchone()[0]

    total_requests = conn.execute(
        "SELECT COUNT(*) FROM blood_request"
    ).fetchone()[0]

    conn.close()

    return render_template(
        "reports.html",
        total_donors=total_donors,
        total_recipients=total_recipients,
        total_stock=total_stock,
        total_requests=total_requests
    )


# ---------------- Export Donors to Excel ----------------

@app.route('/export_excel')
def export_excel():

    conn = get_db_connection()

    donors = conn.execute(
        "SELECT * FROM donor"
    ).fetchall()

    conn.close()

    wb = Workbook()

    ws = wb.active

    ws.title = "Donors"

    ws.append([
        "ID",
        "Name",
        "Age",
        "Gender",
        "Blood Group",
        "Phone",
        "Email",
        "Address",
        "Last Donation"
    ])

    for donor in donors:

        ws.append([
            donor["donor_id"],
            donor["donor_name"],
            donor["age"],
            donor["gender"],
            donor["blood_group"],
            donor["phone"],
            donor["email"],
            donor["address"],
            donor["last_donation"]
        ])

    file_name = "donor_report.xlsx"

    wb.save(file_name)

    return send_file(file_name, as_attachment=True)



# ---------------- Export Donors to PDF ----------------

@app.route('/export_pdf')
def export_pdf():

    conn = get_db_connection()

    donors = conn.execute(
        "SELECT * FROM donor"
    ).fetchall()

    conn.close()

    file_name = "donor_report.pdf"

    pdf = SimpleDocTemplate(file_name)

    data = [[
        "ID",
        "Name",
        "Blood Group",
        "Phone"
    ]]

    for donor in donors:

        data.append([
            donor["donor_id"],
            donor["donor_name"],
            donor["blood_group"],
            donor["phone"]
        ])

    table = Table(data)

    pdf.build([table])

    return send_file(file_name, as_attachment=True)


# blood_compatibility 

@app.route('/blood_compatibility')
def compatibility():

    return render_template(
        "blood_compatibility.html"
    )


@app.route('/blood_compatibility', methods=['POST'])
def check_compatibility():

    blood = request.form['blood_group']

    compatibility = {

        "A+": "A+, A-, O+, O-",

        "A-": "A-, O-",

        "B+": "B+, B-, O+, O-",

        "B-": "B-, O-",

        "AB+": "All Blood Groups",

        "AB-": "AB-, A-, B-, O-",

        "O+": "O+, O-",

        "O-": "O-"

    }

    return render_template(

        "blood_compatibility.html",

        compatible=compatibility[blood]

    )

# Admin logout

@app.route('/admin_logout')
def admin_logout():

    session.clear()

    return redirect("/")

# ---------------- Logout ----------------

@app.route('/logout')
def logout():

    session.clear()

    return redirect("/")



#Run Application

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)