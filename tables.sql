CREATE DATABASE hospital_db;
USE hospital_db;
CREATE TABLE patient (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    age INT,
    gender VARCHAR(10),
    contact VARCHAR(15),
    address VARCHAR(100)
);


CREATE TABLE ward (
    ward_id INT AUTO_INCREMENT PRIMARY KEY,
    ward_type VARCHAR(30),
    room_number INT,
    bed_number INT,
    cost_per_day DECIMAL(10,2)
);

CREATE TABLE admission (
    admission_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT,
    ward_id INT,
    admission_date DATE,
    discharge_date DATE,

    FOREIGN KEY (patient_id) REFERENCES patient(patient_id)
        ON DELETE CASCADE,
    FOREIGN KEY (ward_id) REFERENCES ward(ward_id)
        ON DELETE CASCADE
);

CREATE TABLE doctor (
    doctor_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    specialization VARCHAR(50),
    contact VARCHAR(15),
    experience_years INT
);

CREATE TABLE department (
    department_id INT AUTO_INCREMENT PRIMARY KEY,
    department_name VARCHAR(50),
    floor_number INT
);

CREATE TABLE appointment (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT,
    doctor_id INT,
    appointment_date DATETIME,
    status VARCHAR(20),

    FOREIGN KEY (patient_id) REFERENCES patient(patient_id)
        ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctor(doctor_id)
        ON DELETE CASCADE
);


CREATE TABLE operation (
    operation_id INT AUTO_INCREMENT PRIMARY KEY,
    patient_id INT,
    doctor_id INT,
    ot_id INT,
    operation_date DATE,
    operation_type VARCHAR(50),

    FOREIGN KEY (patient_id) REFERENCES patient(patient_id)
        ON DELETE CASCADE,
    FOREIGN KEY (doctor_id) REFERENCES doctor(doctor_id)
        ON DELETE CASCADE,
    FOREIGN KEY (ot_id) REFERENCES operation_theatre(ot_id)
        ON DELETE CASCADE
);
INSERT INTO patient (name, age, gender, contact, address)
VALUES ('Rahul Sharma', 25, 'Male', '9876543210', 'Mumbai');
INSERT INTO doctor (name, specialization, contact, experience_years)
VALUES ('Dr. Mehta', 'Cardiology', '9123456789', 10);

SELECT * FROM patient;
SELECT * FROM doctor;


desc admission;

ALTER TABLE admission
ADD COLUMN is_icu BOOLEAN DEFAULT FALSE;
ALTER TABLE admission
ADD COLUMN is_operation_required BOOLEAN DEFAULT FALSE;
ALTER TABLE admission
ADD COLUMN expected_discharge DATE;

ALTER TABLE icu
ADD COLUMN daily_cost DECIMAL(10,2);
ALTER TABLE icu
ADD COLUMN icu_start_date DATE;
ALTER TABLE icu
ADD COLUMN icu_end_date DATE;
ALTER TABLE icu
ADD COLUMN admission_id INT;
ALTER TABLE icu
ADD CONSTRAINT fk_icu_admission
FOREIGN KEY (admission_id)
REFERENCES admission(admission_id);



CREATE TABLE billing (
    bill_id INT AUTO_INCREMENT PRIMARY KEY,
    admission_id INT NOT NULL,
    ward_charges DECIMAL(10,2),
    icu_charges DECIMAL(10,2),
    operation_charges DECIMAL(10,2),
    total_amount DECIMAL(10,2),
    bill_date DATE,
    payment_status VARCHAR(20),
    CONSTRAINT fk_billing_admission
        FOREIGN KEY (admission_id)
        REFERENCES admission(admission_id)
        ON DELETE CASCADE
);

CREATE TABLE operation (
    operation_id INT AUTO_INCREMENT PRIMARY KEY,
    admission_id INT NOT NULL,
    operation_name VARCHAR(100),
    operation_date DATE,
    surgeon_name VARCHAR(100),
    operation_cost DECIMAL(10,2),
    CONSTRAINT fk_operation_admission
        FOREIGN KEY (admission_id)
        REFERENCES admission(admission_id)
        ON DELETE CASCADE
);


SELECT
    a.admission_id,
    p.name AS patient_name,

    -- Ward calculation
    DATEDIFF(CURRENT_DATE, a.admission_date) AS ward_days,
    w.cost_per_day,
    DATEDIFF(CURRENT_DATE, a.admission_date) * w.cost_per_day AS ward_charges,

    -- ICU calculation
    IFNULL(SUM(
        DATEDIFF(
            IFNULL(i.icu_end_date, CURRENT_DATE),
            i.icu_start_date
        ) * i.daily_cost
    ), 0) AS icu_charges,

    -- Operation calculation
    IFNULL(SUM(o.operation_cost), 0) AS operation_charges

FROM admission a
JOIN patient p ON a.patient_id = p.patient_id
JOIN ward w ON a.ward_id = w.ward_id
LEFT JOIN icu i ON a.admission_id = i.admission_id
LEFT JOIN operation o ON a.admission_id = o.admission_id
WHERE a.admission_id = 1
GROUP BY a.admission_id;


INSERT INTO billing (
    admission_id,
    ward_charges,
    icu_charges,
    operation_charges,
    total_amount,
    bill_date,
    payment_status
)
SELECT
    a.admission_id,

    DATEDIFF(CURRENT_DATE, a.admission_date) * w.cost_per_day,

    IFNULL(SUM(
        DATEDIFF(
            IFNULL(i.icu_end_date, CURRENT_DATE),
            i.icu_start_date
        ) * i.daily_cost
    ), 0),

    IFNULL(SUM(o.operation_cost), 0),

    (
        DATEDIFF(CURRENT_DATE, a.admission_date) * w.cost_per_day
        +
        IFNULL(SUM(
            DATEDIFF(
                IFNULL(i.icu_end_date, CURRENT_DATE),
                i.icu_start_date
            ) * i.daily_cost
        ), 0)
        +
        IFNULL(SUM(o.operation_cost), 0)
    ),

    CURRENT_DATE,
    'UNPAID'

FROM admission a
JOIN ward w ON a.ward_id = w.ward_id
LEFT JOIN icu i ON a.admission_id = i.admission_id
LEFT JOIN operation o ON a.admission_id = o.admission_id
WHERE a.admission_id = 1
GROUP BY a.admission_id;

CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL
);



SELECT * FROM billing;

SELECT password_hash, username, role FROM users;
SELECT user_id, username,password_hash, role FROM users;




INSERT INTO users (username, password_hash, role)
VALUES (
    'admin',
    SHA2('admin123', 256),
    'admin'
);


