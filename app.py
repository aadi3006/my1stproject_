from flask import Flask, render_template, request, redirect
import mysql.connector

app = Flask(__name__)

# Database Connection
conn = mysql.connector.connect(
    host="localhost",
    user="root",

    database="hospital_db"
)

cursor = conn.cursor()

# ------------------------------
# Dashboard Route
# ------------------------------
@app.route('/')
def dashboard():
    cursor.execute("SELECT COUNT(*) FROM patient")
    total_patients = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM doctor")
    total_doctors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM appointment")
    total_appointments = cursor.fetchone()[0]

    return render_template(
        "dashboard.html",
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_appointments=total_appointments
    )

# ------------------------------
# Add Patient Route
# ------------------------------
@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        contact = request.form['contact']
        address = request.form['address']

        cursor.execute(
            "INSERT INTO patient (name, age, gender, contact, address) VALUES (%s, %s, %s, %s, %s)",
            (name, age, gender, contact, address)
        )
        conn.commit()

        return redirect('/')

    return render_template('add_patient.html')

@app.route('/patients')
def view_patients():
    cursor.execute("SELECT * FROM patient")
    patients = cursor.fetchall()
    return render_template("view_patients.html", patients=patients)

@app.route('/delete_patient/<int:id>')
def delete_patient(id):
    cursor.execute("DELETE FROM patient WHERE patient_id = %s", (id,))
    conn.commit()
    return redirect('/patients')

@app.route('/edit_patient/<int:id>', methods=['GET', 'POST'])
def edit_patient(id):
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        contact = request.form['contact']
        address = request.form['address']

        cursor.execute("""
            UPDATE patient 
            SET name=%s, age=%s, gender=%s, contact=%s, address=%s
            WHERE patient_id=%s
        """, (name, age, gender, contact, address, id))

        conn.commit()
        return redirect('/patients')

    cursor.execute("SELECT * FROM patient WHERE patient_id=%s", (id,))
    patient = cursor.fetchone()
    return render_template("edit_patient.html", patient=patient)



if __name__ == '__main__':
    app.run(debug=True)
