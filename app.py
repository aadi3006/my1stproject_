from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from functools import wraps
from datetime import date

app = Flask(__name__)
app.secret_key = "super_secret_key_change_later"

# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",  # <-- PUT YOUR MYSQL PASSWORD HERE
    database="hospital_db"
)


# --------------------------------------------------
# CREATE DEFAULT ADMIN IF NOT EXISTS
# --------------------------------------------------
def create_default_admin():
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username=%s", ("admin",))
    user = cursor.fetchone()

    if not user:
        hashed_password = generate_password_hash("admin2006")
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s,%s,%s)",
            ("admin", hashed_password, "admin")
        )
        conn.commit()

    cursor.close()


create_default_admin()


# --------------------------------------------------
# LOGIN REQUIRED DECORATOR
# --------------------------------------------------
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return wrap


# --------------------------------------------------
# AUTH ROUTES
# --------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT user_id, username, password_hash, role FROM users WHERE username=%s",
            (username,)
        )
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('dashboard'))

        return render_template('auth/login.html', error="Invalid username or password")

    return render_template('auth/login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        password_hash = generate_password_hash(password)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s,%s,%s)",
            (username, password_hash, role)
        )
        conn.commit()
        cursor.close()

        return redirect(url_for('login'))

    return render_template('auth/register.html')


# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
@app.route('/')
@login_required
def dashboard():
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM patient")
    total_patients = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM doctor")
    total_doctors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM appointment")
    total_appointments = cursor.fetchone()[0]

    cursor.close()

    return render_template(
        "dashboard.html",
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_appointments=total_appointments
    )


# --------------------------------------------------
# PATIENT MODULE
# --------------------------------------------------
@app.route('/add_patient', methods=['GET', 'POST'])
@login_required
def add_patient():
    if request.method == 'POST':
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
        conn.commit()
        cursor.close()
        return redirect('/patients')

    return render_template('add_patient.html')


@app.route('/patients')
@login_required
def view_patients():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patient")
    patients = cursor.fetchall()
    cursor.close()
    return render_template("view_patients.html", patients=patients)


@app.route('/delete_patient/<int:id>')
@login_required
def delete_patient(id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM patient WHERE patient_id=%s", (id,))
    conn.commit()
    cursor.close()
    return redirect('/patients')


@app.route('/edit_patient/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    cursor = conn.cursor()

    if request.method == 'POST':
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
                           id
                       ))
        conn.commit()
        cursor.close()
        return redirect('/patients')

    cursor.execute("SELECT * FROM patient WHERE patient_id=%s", (id,))
    patient = cursor.fetchone()
    cursor.close()
    return render_template("edit_patient.html", patient=patient)


# --------------------------------------------------
# DOCTOR MODULE
# --------------------------------------------------
@app.route('/add_doctor', methods=['GET', 'POST'])
@login_required
def add_doctor():
    if request.method == 'POST':
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO doctor (name, specialization, contact, email) VALUES (%s,%s,%s,%s)",
            (
                request.form['name'],
                request.form['specialization'],
                request.form['contact'],
                request.form['email']
            )
        )
        conn.commit()
        cursor.close()
        return redirect('/doctors')

    return render_template('add_doctor.html')


@app.route('/doctors')
@login_required
def view_doctors():
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM doctor")
    doctors = cursor.fetchall()
    cursor.close()
    return render_template("view_doctors.html", doctors=doctors)


@app.route('/delete_doctor/<int:id>')
@login_required
def delete_doctor(id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM doctor WHERE doctor_id=%s", (id,))
    conn.commit()
    cursor.close()
    return redirect('/doctors')


@app.route('/edit_doctor/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_doctor(id):
    cursor = conn.cursor()

    if request.method == 'POST':
        cursor.execute("""
                       UPDATE doctor
                       SET name=%s,
                           specialization=%s,
                           contact=%s,
                           email=%s
                       WHERE doctor_id = %s
                       """, (
                           request.form['name'],
                           request.form['specialization'],
                           request.form['contact'],
                           request.form['email'],
                           id
                       ))
        conn.commit()
        cursor.close()
        return redirect('/doctors')

    cursor.execute("SELECT * FROM doctor WHERE doctor_id=%s", (id,))
    doctor = cursor.fetchone()
    cursor.close()
    return render_template("edit_doctor.html", doctor=doctor)


# --------------------------------------------------
# APPOINTMENT MODULE
# --------------------------------------------------
@app.route('/add_appointment', methods=['GET', 'POST'])
@login_required
def add_appointment():
    cursor = conn.cursor()

    if request.method == 'POST':
        cursor.execute(
            "INSERT INTO appointment (patient_id, doctor_id, appointment_date, status) VALUES (%s,%s,%s,%s)",
            (
                request.form['patient_id'],
                request.form['doctor_id'],
                request.form['appointment_date'],
                request.form.get('status', 'Scheduled')
            )
        )
        conn.commit()
        cursor.close()
        return redirect('/appointments')

    # Fetch patients and doctors for dropdown
    cursor.execute("SELECT patient_id, name FROM patient ORDER BY name")
    patients = cursor.fetchall()

    cursor.execute("SELECT doctor_id, name, specialization FROM doctor ORDER BY name")
    doctors = cursor.fetchall()

    cursor.close()
    return render_template('add_appointment.html', patients=patients, doctors=doctors)


@app.route('/appointments')
@login_required
def view_appointments():
    cursor = conn.cursor()
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
    return render_template("view_appointments.html", appointments=appointments)


@app.route('/delete_appointment/<int:id>')
@login_required
def delete_appointment(id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM appointment WHERE appointment_id=%s", (id,))
    conn.commit()
    cursor.close()
    return redirect('/appointments')


# --------------------------------------------------
# ADMISSION MODULE
# --------------------------------------------------
@app.route('/add_admission', methods=['GET', 'POST'])
@login_required
def add_admission():
    cursor = conn.cursor()

    if request.method == 'POST':
        # Handle ICU and operation checkboxes
        is_icu = 1 if request.form.get('is_icu') else 0
        is_operation = 1 if request.form.get('is_operation_required') else 0

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
        return redirect('/admissions')

    # Fetch patients for dropdown
    cursor.execute("SELECT patient_id, name FROM patient ORDER BY name")
    patients = cursor.fetchall()

    # Get ward types with sample IDs
    cursor.execute("""
                   SELECT MIN(ward_id) as ward_id, ward_type, MIN(cost_per_day) as cost
                   FROM ward
                   GROUP BY ward_type
                   ORDER BY ward_type
                   """)
    wards = cursor.fetchall()

    cursor.close()
    return render_template('add_admission.html', patients=patients, wards=wards)


@app.route('/admissions')
@login_required
def view_admissions():
    cursor = conn.cursor()

    # Get regular admissions
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

    # Get ICU admissions - join through admission table
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
    return render_template("view_admissions.html", admissions=admissions, icu_admissions=icu_admissions)


@app.route('/delete_admission/<int:id>')
@login_required
def delete_admission(id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM admission WHERE admission_id=%s", (id,))
    conn.commit()
    cursor.close()
    return redirect('/admissions')


# --------------------------------------------------
# ICU MODULE
# --------------------------------------------------
@app.route('/add_icu', methods=['GET', 'POST'])
@login_required
def add_icu():
    cursor = conn.cursor()

    if request.method == 'POST':
        cursor.execute(
            "INSERT INTO icu (admission_id, icu_start_date, icu_end_date, bed_number, daily_cost) VALUES (%s,%s,%s,%s,%s)",
            (
                request.form['admission_id'],
                request.form['icu_start_date'],
                request.form.get('icu_end_date') if request.form.get('icu_end_date') else None,
                request.form['bed_number'],
                request.form.get('daily_cost', 2500.00)  # Default ICU cost
            )
        )
        conn.commit()
        cursor.close()
        return redirect('/admissions')

    # Fetch admissions with patient names for dropdown (only ICU admissions)
    cursor.execute("""
                   SELECT a.admission_id, p.name, a.admission_date
                   FROM admission a
                            JOIN patient p ON a.patient_id = p.patient_id
                   WHERE a.is_icu = 1
                   ORDER BY a.admission_date DESC
                   """)
    admissions = cursor.fetchall()

    cursor.close()
    return render_template('add_icu.html', admissions=admissions)


# --------------------------------------------------
# OPERATION MODULE
# --------------------------------------------------
@app.route('/add_operation', methods=['GET', 'POST'])
@login_required
def add_operation():
    cursor = conn.cursor()

    if request.method == 'POST':
        cursor.execute(
            "INSERT INTO operation (admission_id, operation_name, operation_date, surgeon_name, operation_cost) VALUES (%s,%s,%s,%s,%s)",
            (
                request.form['admission_id'],
                request.form['operation_name'],
                request.form['operation_date'],
                request.form['surgeon_name'],
                request.form['operation_cost']
            )
        )
        conn.commit()
        cursor.close()
        return redirect('/operations')

    # Fetch admissions that require operations
    cursor.execute("""
                   SELECT a.admission_id, p.name, a.admission_date
                   FROM admission a
                            JOIN patient p ON a.patient_id = p.patient_id
                   WHERE a.is_operation_required = 1
                   ORDER BY a.admission_date DESC
                   """)
    admissions = cursor.fetchall()

    cursor.close()
    return render_template('add_operation.html', admissions=admissions)


@app.route('/operations')
@login_required
def view_operations():
    cursor = conn.cursor()
    cursor.execute("""
                   SELECT o.operation_id,
                          p.name as patient_name,
                          o.operation_name,
                          o.operation_date,
                          o.surgeon_name,
                          o.operation_cost
                   FROM operation o
                            JOIN admission a ON o.admission_id = a.admission_id
                            JOIN patient p ON a.patient_id = p.patient_id
                   ORDER BY o.operation_date DESC
                   """)
    operations = cursor.fetchall()
    cursor.close()
    return render_template("view_operations.html", operations=operations)


@app.route('/delete_operation/<int:id>')
@login_required
def delete_operation(id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM operation WHERE operation_id=%s", (id,))
    conn.commit()
    cursor.close()
    return redirect('/operations')


# --------------------------------------------------
# BILLING MODULE
# --------------------------------------------------
@app.route('/billing', methods=['GET', 'POST'])
@login_required
def billing():
    cursor = conn.cursor()

    if request.method == 'POST':
        # Calculate total from individual charges
        ward_charges = float(request.form.get('ward_charges', 0))
        icu_charges = float(request.form.get('icu_charges', 0))
        operation_charges = float(request.form.get('operation_charges', 0))
        total_amount = ward_charges + icu_charges + operation_charges

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
                request.form.get('bill_date', date.today()),
                request.form.get('payment_status', 'Unpaid')
            )
        )
        conn.commit()
        cursor.close()
        return redirect('/bills')

    # Fetch admissions with patient names
    cursor.execute("""
                   SELECT a.admission_id, p.name, a.admission_date
                   FROM admission a
                            JOIN patient p ON a.patient_id = p.patient_id
                   ORDER BY a.admission_date DESC
                   """)
    admissions = cursor.fetchall()

    cursor.close()
    return render_template('billing.html', admissions=admissions)


@app.route('/bills')
@login_required
def view_bills():
    cursor = conn.cursor()
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
    return render_template("view_bills.html", bills=bills)


@app.route('/delete_bill/<int:id>')
@login_required
def delete_bill(id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM billing WHERE bill_id=%s", (id,))
    conn.commit()
    cursor.close()
    return redirect('/bills')


# --------------------------------------------------
# TEST/DEBUG ROUTE
# --------------------------------------------------
@app.route('/test_wards')
def test_wards():
    cursor = conn.cursor()
    cursor.execute("SELECT ward_id, ward_type, room_number, bed_number, cost_per_day FROM ward LIMIT 10")
    wards = cursor.fetchall()
    cursor.close()

    output = f"<h1>Ward Data Test</h1><p>Found {len(wards)} wards</p><ul>"
    for w in wards:
        output += f"<li>ID: {w[0]}, Type: {w[1]}, Room: {w[2]}, Bed: {w[3]}, Cost: ${w[4]}</li>"
    output += "</ul>"
    return output


# --------------------------------------------------
# RUN APP
# --------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)