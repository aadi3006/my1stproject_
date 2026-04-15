# ============================================================
# Hospital Management System - Flask Web Application
# ============================================================
# This is the main backend file. It handles all web routes,
# database operations, and user authentication.
# ============================================================

# --- IMPORTS ---
# Flask: the main web framework we use to build this app
from flask import Flask, render_template, request, redirect, url_for, session, abort

# Werkzeug: helps us securely store and check passwords (hashing)
from werkzeug.security import generate_password_hash, check_password_hash

# mysql.connector: lets Python talk to our MySQL database
import mysql.connector
from mysql.connector import pooling  # pooling = reusing DB connections efficiently

# functools.wraps: needed to build custom decorators properly
from functools import wraps

# date: used to get today's date for billing and appointments
from datetime import date


# --- FLASK APP SETUP ---
app = Flask(__name__)  # Create the Flask app instance

# Secret key is used to sign and protect session cookies (login data)
app.secret_key = "super_secret_key_change_later"


# --------------------------------------------------
# DATABASE CONNECTION POOL
# --------------------------------------------------
# These are the credentials to connect to our local MySQL database
db_config = {
    "host": "localhost",      # DB is running on this machine
    "user": "root",           # MySQL username
    "password": "",           # MySQL password (empty for local dev)
    "database": "hospital_db" # The database we want to use
}

# A connection pool lets multiple users share DB connections efficiently.
# Instead of opening a new connection every time, we reuse from a pool of 5.
try:
    connection_pool = pooling.MySQLConnectionPool(
        pool_name="hospital_pool",
        pool_size=5,      # Max 5 connections in the pool
        **db_config       # Unpack the config dictionary as arguments
    )
except mysql.connector.Error:
    # If the pool fails (e.g., DB is offline), fall back to None
    connection_pool = None


def get_db():
    """Get a DB connection — from the pool if available, or a fresh one."""
    if connection_pool:
        return connection_pool.get_connection()  # Grab from pool
    else:
        return mysql.connector.connect(**db_config)  # Fallback: direct connect


# --------------------------------------------------
# CREATE DEFAULT ADMIN IF NOT EXISTS
# --------------------------------------------------
def create_default_admin():
    """Automatically create a default admin account on first run."""
    conn = get_db()
    cursor = conn.cursor(dictionary=True)  # dictionary=True → rows returned as dicts

    # Check if admin user already exists in the DB
    cursor.execute("SELECT * FROM users WHERE username=%s", ("admin",))
    user = cursor.fetchone()

    if not user:
        # If no admin found, hash the password and insert into DB
        hashed_password = generate_password_hash("admin2006")
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s,%s,%s)",
            ("admin", hashed_password, "admin")
        )
        conn.commit()  # Save changes to DB

    cursor.close()
    conn.close()


# Run this function once when the app starts
create_default_admin()


# --------------------------------------------------
# LOGIN REQUIRED DECORATOR
# --------------------------------------------------
# A decorator is a function that wraps another function.
# @login_required → if user is NOT logged in, redirect them to /login
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user_id' not in session:  # Check if user session exists
            return redirect(url_for('login'))  # Redirect to login page
        return f(*args, **kwargs)  # If logged in, run the original route
    return wrap


# --------------------------------------------------
# ROLE REQUIRED DECORATOR
# --------------------------------------------------
# Works like login_required but also checks the user's ROLE.
# Example: @role_required(['admin']) → only admin can access this route.
def role_required(allowed_roles):
    """Restrict a route to specific user roles (e.g., 'admin')."""
    def decorator(f):
        @wraps(f)
        def wrap(*args, **kwargs):
            if session.get('role') not in allowed_roles:
                # User doesn't have permission → send back to dashboard
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return wrap
    return decorator


# --------------------------------------------------
# CONTEXT PROCESSOR — inject global data into all templates
# --------------------------------------------------
# This automatically sends 'date_today' to every HTML template.
# So any template can display today's date without us passing it manually.
@app.context_processor
def inject_globals():
    return {
        'date_today': date.today().isoformat()  # e.g., "2026-04-15"
    }


# --------------------------------------------------
# AUTH ROUTES — Login, Logout, Register
# --------------------------------------------------

# @app.route → tells Flask which URL triggers this function
# methods=['GET', 'POST'] → this route handles both page load (GET) and form submit (POST)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # User submitted the login form — grab the values
        username = request.form.get('username')
        password = request.form.get('password')

        # Look up the user in the database
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, username, password_hash, role FROM users WHERE username=%s",
            (username,) 
        )
        user = cursor.fetchone()  # Get one matching user row
        cursor.close()
        conn.close()

        # Check if user exists AND if entered password matches the stored hash
        if user and check_password_hash(user['password_hash'], password):
            # Store user info in session (like a login "token" in the browser)
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))  # Go to dashboard on success

        # If login fails, show the form again with an error message
        return render_template('auth/login.html', error="Invalid username or password")

    # If it's a GET request, just show the login page
    return render_template('auth/login.html')


@app.route('/logout')
def logout():
    session.clear()  # Remove all session data (effectively logs out)
    return redirect(url_for('login'))  # Redirect to login page


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = 'viewer'  # Public registration always gets 'viewer' role (not admin)

        # Hash the password before storing it (never store plain passwords!)
        password_hash = generate_password_hash(password)

        # Insert new user into the database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s,%s,%s)",
            (username, password_hash, role)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('login'))  # After registering, send to login

    # GET request → just show the register form
    return render_template('auth/register.html')


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
@app.route('/')           # Root URL '/'
@login_required           # Must be logged in to see this page
def dashboard():
    conn = get_db()
    cursor = conn.cursor()

    # COUNT(*) = count all rows in that table
    cursor.execute("SELECT COUNT(*) FROM patient")
    total_patients = cursor.fetchone()[0]  # [0] = first column of first row

    cursor.execute("SELECT COUNT(*) FROM doctor")
    total_doctors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM appointment")
    total_appointments = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    # render_template → send data to the HTML file to display
    return render_template(
        "dashboard.html",
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_appointments=total_appointments,
        current_page='dashboard'   # Used to highlight the active link in sidebar
    )


# --------------------------------------------------
# PATIENT MODULE
# --------------------------------------------------

# Add a new patient — only admin can do this
@app.route('/add_patient', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])  # Only admin role can access
def add_patient():
    if request.method == 'POST':
        # Get form data and insert a new patient row into the DB
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO patient (name, age, gender, contact, address) VALUES (%s,%s,%s,%s,%s)",
            (
                request.form['name'],
                request.form['age'],
                request.form['gender'],
                request.form['contact'],
                request.form['address']
            )
        )
        conn.commit()  # Commit = save to DB permanently
        cursor.close()
        conn.close()
        return redirect(url_for('view_patients'))  # Go to patient list after adding

    # GET request → show the blank add-patient form
    return render_template('add_patient.html', current_page='patients')


# View all patients — any logged-in user can see this
@app.route('/patients')
@login_required
def view_patients():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patient")   # Get all rows from patient table
    patients = cursor.fetchall()              # fetchall() = get all results as a list
    cursor.close()
    conn.close()
    return render_template("view_patients.html", patients=patients, current_page='patients')


# Delete a patient by their ID — admin only
# <int:id> in the URL captures a number, e.g. /delete_patient/5 → id=5
@app.route('/delete_patient/<int:id>')
@login_required
@role_required(['admin'])
def delete_patient(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM patient WHERE patient_id=%s", (id,))  # Delete by ID
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('view_patients'))


# Edit an existing patient's details — admin only
@app.route('/edit_patient/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def edit_patient(id):
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Update the patient row with new form values
        cursor.execute("""
                       UPDATE patient
                       SET name=%s,
                           age=%s,
                           gender=%s,
                           contact=%s,
                           address=%s
                       WHERE patient_id = %s
                       """, (
                           request.form['name'],
                           request.form['age'],
                           request.form['gender'],
                           request.form['contact'],
                           request.form['address'],
                           id  # The patient we're updating
                       ))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('view_patients'))

    # GET → fetch existing patient data and pre-fill the edit form
    cursor.execute("SELECT * FROM patient WHERE patient_id=%s", (id,))
    patient = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template("edit_patient.html", patient=patient, current_page='patients')


# --------------------------------------------------
# DOCTOR MODULE
# --------------------------------------------------

# Add a new doctor — admin only
@app.route('/add_doctor', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def add_doctor():
    if request.method == 'POST':
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO doctor (name, specialization, contact, experience_years) VALUES (%s,%s,%s,%s)",
            (
                request.form['name'],
                request.form['specialization'],
                request.form['contact'],
                request.form['experience']
            )
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('view_doctors'))

    return render_template('add_doctor.html', current_page='doctors')


# View all doctors — any logged-in user
@app.route('/doctors')
@login_required
def view_doctors():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doctor")
    doctors = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("view_doctors.html", doctors=doctors, current_page='doctors')


# Delete a doctor by ID — admin only
@app.route('/delete_doctor/<int:id>')
@login_required
@role_required(['admin'])
def delete_doctor(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM doctor WHERE doctor_id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('view_doctors'))


# Edit an existing doctor's information — admin only
@app.route('/edit_doctor/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def edit_doctor(id):
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Update the doctor record in the DB
        cursor.execute("""
                       UPDATE doctor
                       SET name=%s,
                           specialization=%s,
                           contact=%s,
                           experience_years=%s
                       WHERE doctor_id = %s
                       """, (
                           request.form['name'],
                           request.form['specialization'],
                           request.form['contact'],
                           request.form['experience'],
                           id
                       ))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('view_doctors'))

    # GET → load current doctor data into the edit form
    cursor.execute("SELECT * FROM doctor WHERE doctor_id=%s", (id,))
    doctor = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template("edit_doctor.html", doctor=doctor, current_page='doctors')


# --------------------------------------------------
# APPOINTMENT MODULE
# --------------------------------------------------

# Schedule a new appointment — admin only
@app.route('/add_appointment', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def add_appointment():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Insert a new appointment row linking a patient and a doctor
        cursor.execute(
            "INSERT INTO appointment (patient_id, doctor_id, appointment_date, status) VALUES (%s,%s,%s,%s)",
            (
                request.form['patient_id'],
                request.form['doctor_id'],
                request.form['appointment_date'],
                request.form.get('status', 'Scheduled')  # Default status = 'Scheduled'
            )
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('view_appointments'))

    # GET → fetch patient and doctor lists to show in dropdowns
    cursor.execute("SELECT patient_id, name FROM patient ORDER BY name")
    patients = cursor.fetchall()

    cursor.execute("SELECT doctor_id, name, specialization FROM doctor ORDER BY name")
    doctors = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('add_appointment.html', patients=patients, doctors=doctors, current_page='appointments')


# View all appointments — any logged-in user
@app.route('/appointments')
@login_required
def view_appointments():
    conn = get_db()
    cursor = conn.cursor()
    # JOIN combines data from multiple tables into one result
    # Here we join appointment with patient and doctor tables to get names
    cursor.execute("""
                   SELECT a.appointment_id,
                          p.name as patient_name,
                          d.name as doctor_name,
                          a.appointment_date,
                          a.status
                   FROM appointment a
                            JOIN patient p ON a.patient_id = p.patient_id
                            JOIN doctor d ON a.doctor_id = d.doctor_id
                   ORDER BY a.appointment_date DESC
                   """)
    appointments = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("view_appointments.html", appointments=appointments, current_page='appointments')


# Delete an appointment by ID — admin only
@app.route('/delete_appointment/<int:id>')
@login_required
@role_required(['admin'])
def delete_appointment(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM appointment WHERE appointment_id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('view_appointments'))


# --------------------------------------------------
# ADMISSION MODULE
# --------------------------------------------------

# Admit a patient to a ward — admin only
@app.route('/add_admission', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def add_admission():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Checkboxes return a value only if checked; if unchecked, .get() returns None
        is_icu = 1 if request.form.get('is_icu') else 0
        is_operation = 1 if request.form.get('is_operation_required') else 0

        # Insert the admission record into the DB
        cursor.execute(
            """INSERT INTO admission
               (patient_id, ward_id, admission_date, expected_discharge, is_icu, is_operation_required)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (
                request.form['patient_id'],
                request.form['ward_id'],
                request.form['admission_date'],
                request.form['expected_discharge'],
                is_icu,
                is_operation
            )
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('view_admissions'))

    # GET → load patients and ward types for dropdowns
    cursor.execute("SELECT patient_id, name FROM patient ORDER BY name")
    patients = cursor.fetchall()

    # GROUP BY ward_type → group wards by type (e.g., General, ICU, Private)
    # MIN() → pick one representative ward_id and cost for each type
    cursor.execute("""
                   SELECT MIN(ward_id) as ward_id, ward_type, MIN(cost_per_day) as cost
                   FROM ward
                   GROUP BY ward_type
                   ORDER BY ward_type
                   """)
    wards = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('add_admission.html', patients=patients, wards=wards, current_page='admissions')


# View all admissions (regular + ICU) — any logged-in user
@app.route('/admissions')
@login_required
def view_admissions():
    conn = get_db()
    cursor = conn.cursor()

    # Get regular ward admissions with patient name and ward type
    cursor.execute("""
                   SELECT a.admission_id,
                          p.name as patient_name,
                          w.ward_type,
                          a.admission_date,
                          a.expected_discharge,
                          a.is_icu,
                          a.is_operation_required
                   FROM admission a
                            JOIN patient p ON a.patient_id = p.patient_id
                            LEFT JOIN ward w ON a.ward_id = w.ward_id
                   ORDER BY a.admission_date DESC
                   """)
    admissions = cursor.fetchall()

    # Also get ICU-specific admission details
    cursor.execute("""
                   SELECT i.icu_id,
                          p.name as patient_name,
                          i.bed_number,
                          i.icu_start_date,
                          i.icu_end_date,
                          i.daily_cost
                   FROM icu i
                            JOIN admission a ON i.admission_id = a.admission_id
                            JOIN patient p ON a.patient_id = p.patient_id
                   ORDER BY i.icu_start_date DESC
                   """)
    icu_admissions = cursor.fetchall()

    cursor.close()
    conn.close()
    # Pass both regular and ICU admissions to the template
    return render_template("view_admissions.html", admissions=admissions, icu_admissions=icu_admissions, current_page='admissions')


# Delete an admission record — admin only
@app.route('/delete_admission/<int:id>')
@login_required
@role_required(['admin'])
def delete_admission(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM admission WHERE admission_id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('view_admissions'))


# --------------------------------------------------
# ICU MODULE
# --------------------------------------------------

# Add ICU details for an existing admission — admin only
@app.route('/add_icu', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def add_icu():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Insert ICU record; icu_end_date can be None (patient still in ICU)
        cursor.execute(
            "INSERT INTO icu (admission_id, icu_start_date, icu_end_date, bed_number, daily_cost) VALUES (%s,%s,%s,%s,%s)",
            (
                request.form['admission_id'],
                request.form['icu_start_date'],
                request.form.get('icu_end_date') if request.form.get('icu_end_date') else None,
                request.form['bed_number'],
                request.form.get('daily_cost', 2500.00)  # Default daily cost = 2500
            )
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('view_admissions'))

    # GET → only show admissions that are flagged as ICU (is_icu = 1)
    cursor.execute("""
                   SELECT a.admission_id, p.name, a.admission_date
                   FROM admission a
                            JOIN patient p ON a.patient_id = p.patient_id
                   WHERE a.is_icu = 1
                   ORDER BY a.admission_date DESC
                   """)
    admissions = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('icu/add_icu.html', admissions=admissions, current_page='admissions')


# --------------------------------------------------
# BILLING MODULE
# --------------------------------------------------

# Generate a bill for an admission — admin only
@app.route('/billing', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def billing():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Read each charge from the form; default to 0 if not provided
        ward_charges = float(request.form.get('ward_charges', 0))
        icu_charges = float(request.form.get('icu_charges', 0))
        operation_charges = float(request.form.get('operation_charges', 0))

        # Total is the sum of all three charge categories
        total_amount = ward_charges + icu_charges + operation_charges

        # Insert the bill into the billing table
        cursor.execute(
            """INSERT INTO billing
               (admission_id, ward_charges, icu_charges, operation_charges, total_amount, bill_date, payment_status)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (
                request.form['admission_id'],
                ward_charges,
                icu_charges,
                operation_charges,
                total_amount,
                request.form.get('bill_date', date.today()),   # Default to today
                request.form.get('payment_status', 'Unpaid')   # Default = 'Unpaid'
            )
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('view_bills'))

    # GET → load admissions dropdown so admin can pick which one to bill
    cursor.execute("""
                   SELECT a.admission_id, p.name, a.admission_date
                   FROM admission a
                            JOIN patient p ON a.patient_id = p.patient_id
                   ORDER BY a.admission_date DESC
                   """)
    admissions = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template('billing.html', admissions=admissions, current_page='billing')


# View all generated bills — any logged-in user
@app.route('/bills')
@login_required
def view_bills():
    conn = get_db()
    # dictionary=True → each row returned as a dict (e.g., row['patient_name'])
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
                   SELECT b.bill_id,
                          p.name as patient_name,
                          b.ward_charges,
                          b.icu_charges,
                          b.operation_charges,
                          b.total_amount,
                          b.bill_date,
                          b.payment_status
                   FROM billing b
                            JOIN admission a ON b.admission_id = a.admission_id
                            JOIN patient p ON a.patient_id = p.patient_id
                   ORDER BY b.bill_date DESC
                   """)
    bills = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("view_bills.html", bills=bills, current_page='bills')


# Delete a bill by ID — admin only
@app.route('/delete_bill/<int:id>')
@login_required
@role_required(['admin'])
def delete_bill(id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM billing WHERE bill_id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('view_bills'))


# --------------------------------------------------
# DATABASE EXPLORER (Admin Only)
# --------------------------------------------------
# This section lets the admin browse the raw database tables directly.

@app.route('/db_explorer')
@login_required
@role_required(['admin'])  # Only admin can use this tool
def db_explorer():
    """Show all tables in the database as clickable cards."""
    conn = get_db()
    cursor = conn.cursor()

    # SHOW TABLES → returns a list of all table names in the DB
    cursor.execute("SHOW TABLES")
    table_names = [row[0] for row in cursor.fetchall()]

    # For each table, count how many rows it has
    tables = []
    for name in table_names:
        cursor.execute(f"SELECT COUNT(*) FROM `{name}`")
        count = cursor.fetchone()[0]
        tables.append({'name': name, 'row_count': count})

    cursor.close()
    conn.close()
    return render_template('db_explorer.html', tables=tables, current_page='db_explorer')


# View all rows of a specific table — admin only
@app.route('/db_explorer/<table_name>')
@login_required
@role_required(['admin'])
def db_table_view(table_name):
    """Show all rows of a specific table with column headers."""
    conn = get_db()
    cursor = conn.cursor()

    # Security check: make sure the requested table actually exists
    # This prevents SQL injection via the URL parameter
    cursor.execute("SHOW TABLES")
    valid_tables = [row[0] for row in cursor.fetchall()]

    if table_name not in valid_tables:
        # If unknown table name, redirect back to explorer safely
        cursor.close()
        conn.close()
        return redirect(url_for('db_explorer'))

    # SHOW COLUMNS → returns column metadata; we only need the name (row[0])
    cursor.execute(f"SHOW COLUMNS FROM `{table_name}`")
    columns = [row[0] for row in cursor.fetchall()]

    # Get all rows from the selected table
    cursor.execute(f"SELECT * FROM `{table_name}`")
    rows = cursor.fetchall()
    row_count = len(rows)

    cursor.close()
    conn.close()

    # Send table name, column headers, and data rows to the template
    return render_template(
        'db_table_view.html',
        table_name=table_name,
        columns=columns,
        rows=rows,
        row_count=row_count,
        current_page='db_explorer'
    )


# --------------------------------------------------
# TEST/DEBUG ROUTE
# --------------------------------------------------
# A quick test route to check if ward data is loading from the DB.
# Useful during development — not meant for production use.
@app.route('/test_wards')
def test_wards():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT ward_id, ward_type, room_number, bed_number, cost_per_day FROM ward LIMIT 10")
    wards = cursor.fetchall()
    cursor.close()
    conn.close()

    # Return raw HTML directly (no template needed for a quick debug view)
    output = f"<h1>Ward Data Test</h1><p>Found {len(wards)} wards</p><ul>"
    for w in wards:
        output += f"<li>ID: {w[0]}, Type: {w[1]}, Room: {w[2]}, Bed: {w[3]}, Cost: ${w[4]}</li>"
    output += "</ul>"
    return output


# --------------------------------------------------
# RUN APP
# --------------------------------------------------
# This block only runs when you start the file directly (python app.py)
# debug=True → auto-reload on code changes + shows detailed errors
# port=5002 → app runs at http://localhost:5002

if __name__ == '__main__':
    app.run(debug=True, port=5002)