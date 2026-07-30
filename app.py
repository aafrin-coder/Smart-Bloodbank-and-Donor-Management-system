from flask import Flask, render_template, request, redirect, session
import sqlite3

from flask import send_file
from openpyxl import Workbook
from reportlab.platypus import SimpleDocTemplate, Table


app = Flask(__name__)

app.secret_key = "bloodbank_secret_key"


# Database Connection
def get_db_connection():
    conn = sqlite3.connect("bloodbank.db")
    conn.row_factory = sqlite3.Row
    return conn

# Login Page
@app.route('/')
def login():
    return render_template("login.html")

# Login Authentication
@app.route('/login', methods=['POST'])
def check_login():

    username = request.form['username']
    password = request.form['password']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM admin WHERE username=? AND password=?",
        (username, password)
    )

    admin = cursor.fetchone()
    conn.close()

    if admin:
        session["logged_in"] = True
        return redirect('/dashboard')
    else:
        return render_template(
            "login.html",
            error="Invalid Username or Password"
        )

# Dashboard

@app.route('/dashboard')
def dashboard():

    if "logged_in" not in session:
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

# ---------------- Logout ----------------

@app.route('/logout')
def logout():

    session.clear()

    return redirect("/")


#Run Application

if __name__ == "__main__":
    app.run(debug=True)