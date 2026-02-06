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
       # <-- PUT YOUR MYSQL PASSWORD HERE
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
            SET name=%s, age=%s, gender=%s, contact=%s, address=%s
            WHERE patient_id=%s
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
# RUN APP
# --------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
