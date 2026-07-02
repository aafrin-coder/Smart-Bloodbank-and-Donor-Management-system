import sqlite3

connection = sqlite3.connect("bloodbank.db")

cursor = connection.cursor()

# Admin Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS admin(
    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT 
)
""")

# Donor Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS donor(
    donor_id INTEGER PRIMARY KEY AUTOINCREMENT,
    donor_name TEXT NOT NULL,
    age INTEGER,
    gender TEXT,
    blood_group TEXT,
    phone TEXT,
    email TEXT,
    address TEXT,
    last_donation TEXT
)
""")

# Recipient Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS recipient(
    recipient_id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipient_name TEXT,
    age INTEGER,
    gender TEXT,
    blood_group TEXT,
    phone TEXT,
    hospital TEXT
)
""")

# Blood Stock Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS blood_stock(
    stock_id INTEGER PRIMARY KEY AUTOINCREMENT,
    blood_group TEXT,
    units INTEGER
)
""")

# Blood Request Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS blood_request(
    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_name TEXT,
    blood_group TEXT,
    units INTEGER,
    hospital TEXT,
    status TEXT
)
""")

cursor.execute("""
INSERT INTO admin(username,password)
SELECT 'admin','admin123'
WHERE NOT EXISTS(
SELECT 1 FROM admin WHERE username='admin'
)
""")

connection.commit()
connection.close()

print("Database created successfully.")