from datetime import datetime
from flask import Flask, jsonify, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

# Connect to MySQL database
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",  # Replace with your MySQL password
    database="hospital_db"
)
cursor = db.cursor()

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Patient Management Routes
@app.route('/patients')
def patients():
    cursor.execute("SELECT * FROM patients")
    patients = cursor.fetchall()
    return render_template('patients.html', patients=patients)

@app.route('/add_patient', methods=['POST'])
def add_patient():
    name = request.form['name']
    age = request.form['age']
    gender = request.form['gender']
    contact = request.form['contact']
    address = request.form['address']
    
    cursor.execute("INSERT INTO patients (name, age, gender, contact, address) VALUES (%s, %s, %s, %s, %s)", 
                   (name, age, gender, contact, address))
    db.commit()
    return redirect(url_for('patients'))

@app.route('/edit_patient/<int:patient_id>', methods=['GET', 'POST'])
def edit_patient(patient_id):
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        contact = request.form['contact']
        address = request.form['address']

        cursor.execute("UPDATE patients SET name=%s, age=%s, gender=%s, contact=%s, address=%s WHERE patient_id=%s",
                       (name, age, gender, contact, address, patient_id))
        db.commit()
        return redirect(url_for('patients'))

    cursor.execute("SELECT * FROM patients WHERE patient_id=%s", (patient_id,))
    patient = cursor.fetchone()
    return render_template('edit_patient.html', patient=patient)

@app.route('/delete_patient/<int:patient_id>')
def delete_patient(patient_id):
    cursor.execute("DELETE FROM patients WHERE patient_id=%s", (patient_id,))
    db.commit()
    return redirect(url_for('patients'))

# Doctor Management (similar to Patient Management)
@app.route('/doctors')
def doctors():
    cursor.execute("SELECT * FROM doctors")
    doctors = cursor.fetchall()
    return render_template('doctors.html', doctors=doctors)

@app.route('/add_doctor', methods=['POST'])
def add_doctor():
    name = request.form['name']
    specialization = request.form['specialization']
    contact = request.form['contact']

    cursor.execute("INSERT INTO doctors (name, specialization, contact) VALUES (%s, %s, %s)", 
                   (name, specialization, contact))
    db.commit()
    return redirect(url_for('doctors'))

@app.route('/edit_doctor/<int:doctor_id>', methods=['GET', 'POST'])
def edit_doctor(doctor_id):
    # If it's a POST request, update the doctor info
    if request.method == 'POST':
        name = request.form['name']
        specialization = request.form['specialization']
        contact = request.form['contact']
        cursor.execute("""
            UPDATE doctors 
            SET name=%s, specialization=%s, contact=%s 
            WHERE doctor_id=%s
        """, (name, specialization, contact, doctor_id))
        db.commit()
        return redirect(url_for('doctors'))
    cursor.execute("SELECT * FROM doctors WHERE doctor_id=%s", (doctor_id,))
    doctor = cursor.fetchone()

    return render_template('edit_doctor.html', doctor=doctor)


@app.route('/delete_doctor/<int:doctor_id>')
def delete_doctor(doctor_id):
    cursor.execute("DELETE FROM doctors WHERE doctor_id=%s", (doctor_id,))
    db.commit()
    return redirect(url_for('doctors'))



# Appointment Management (using stored procedure)

@app.route('/appointments')
def appointments():
    # Fetching existing appointments
    cursor.execute(""" 
        SELECT 
            a.appointment_id, 
            p.name AS patient_name, 
            d.name AS doctor_name, 
            a.appointment_date, 
            a.reason 
        FROM 
            appointments a 
        JOIN 
            patients p ON a.patient_id = p.patient_id 
        JOIN 
            doctors d ON a.doctor_id = d.doctor_id
    """)
    appointments = cursor.fetchall()

    # Fetching patients
    cursor.execute("SELECT patient_id, name FROM patients")
    patients = cursor.fetchall()

    # Fetching doctors
    cursor.execute("SELECT doctor_id, name FROM doctors")
    doctors = cursor.fetchall()

    # Render the appointments page with patients and doctors
    return render_template('appointments.html', appointments=appointments, patients=patients, doctors=doctors)

@app.route('/schedule_appointment', methods=['POST'])
def schedule_appointment():
    patient_id = request.form['patient_id']
    doctor_id = request.form['doctor_id']
    date = request.form['appointment_date']  # Date in 'YYYY-MM-DD' format
    time = request.form['appointment_time']  # Time in 'HH:MM' format
    appointment_date = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
    print(appointment_date)
    reason = request.form['reason']
    appointment_date = appointment_date.strftime('%Y-%m-%d %H:%M:%S')
    print("String datetime for insertion:", appointment_date)  # Debug print

    cursor.callproc('ScheduleAppointment', [patient_id, doctor_id, appointment_date, reason])
    db.commit()
    return redirect(url_for('appointments'))

@app.route('/edit_appointment/<int:appointment_id>', methods=['GET', 'POST'])
def edit_appointment(appointment_id):
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        doctor_id = request.form['doctor_id']
        appointment_date = request.form['appointment_date']
        reason = request.form['reason']
        cursor.execute("""
            UPDATE appointments 
            SET patient_id = %s, doctor_id = %s, appointment_date = %s, reason = %s 
            WHERE appointment_id = %s
        """, (patient_id, doctor_id, appointment_date, reason, appointment_id))
        db.commit()
        return redirect(url_for('appointments'))
    # Fetch current appointment details for editing
    cursor.execute("""
        SELECT a.appointment_id, a.patient_id, a.doctor_id, a.appointment_date, a.reason, p.name, d.name
        FROM appointments a 
        JOIN patients p ON a.patient_id = p.patient_id 
        JOIN doctors d ON a.doctor_id = d.doctor_id 
        WHERE a.appointment_id = %s
    """, (appointment_id,))
    appointment = cursor.fetchone()
    # Fetch all patients and doctors for dropdowns
    cursor.execute("SELECT * FROM patients")
    patients = cursor.fetchall()
    cursor.execute("SELECT * FROM doctors")
    doctors = cursor.fetchall()

    return render_template('edit_appointment.html', appointment=appointment, patients=patients, doctors=doctors)

@app.route('/delete_appointment/<int:appointment_id>')
def delete_appointment(appointment_id):
    cursor.execute("DELETE FROM appointments WHERE appointment_id = %s", (appointment_id,))
    db.commit()
    return redirect(url_for('appointments'))


# Billing Management (optional)
@app.route('/billing')
def billing():
    cursor.execute("SELECT * FROM billing")
    billing = cursor.fetchall()
    return render_template('billing.html', billing=billing)

@app.route('/edit_billing/<int:billing_id>', methods=['GET', 'POST'])
def edit_billing(billing_id):
    if request.method == 'POST':
        appointment_id = request.form['appointment_id']
        amount = request.form['amount']
        payment_status = request.form['payment_status']
        billing_date = request.form['billing_date']

        cursor.execute("""
            UPDATE billing 
            SET appointment_id = %s, amount = %s, payment_status = %s, billing_date = %s 
            WHERE billing_id = %s
        """, (appointment_id, amount, payment_status, billing_date, billing_id))
        db.commit()
        return redirect(url_for('billing'))

    # Fetch current billing details for editing
    cursor.execute("SELECT * FROM billing WHERE billing_id = %s", (billing_id,))
    bill = cursor.fetchone()

    # Fetch the associated appointment details
    cursor.execute("SELECT appointment_id, billing_date FROM billing WHERE billing_id = %s", (billing_id,))
    appointment_details = cursor.fetchone()

    return render_template('edit_billing.html', bill=bill, appointment_details=appointment_details)


@app.route('/delete_billing/<int:billing_id>', methods=['GET'])
def delete_billing(billing_id):
    cursor.execute("DELETE FROM billing WHERE billing_id = %s", (billing_id,))
    db.commit()
    return redirect(url_for('billing'))
    

# @app.route('/reports')
# def reports():
#     # Fetch total patients
#     cursor.execute("SELECT COUNT(*) FROM patients")
#     total_patients = cursor.fetchone()[0]
#     print("Total Patients:", total_patients)  # Debugging

#     # Fetch total doctors
#     cursor.execute("SELECT COUNT(*) FROM doctors")
#     total_doctors = cursor.fetchone()[0]
#     print("Total Doctors:", total_doctors)  # Debugging

#     # Fetch total appointments
#     cursor.execute("SELECT COUNT(*) FROM appointments")
#     total_appointments = cursor.fetchone()[0]
#     print("Total Appointments:", total_appointments)  # Debugging

#     # Fetch most popular doctor (by number of appointments)
#     cursor.execute("""
#         SELECT d.name, COUNT(*) AS appointment_count 
#         FROM doctors d 
#         JOIN appointments a ON d.doctor_id = a.doctor_id 
#         GROUP BY d.doctor_id 
#         ORDER BY appointment_count DESC 
#         LIMIT 1
#     """)
#     popular_doctor = cursor.fetchone()
#     print("Most Popular Doctor:", popular_doctor)  # Debugging

#     # Fetch total billing amount and unpaid bills
#     cursor.execute("SELECT SUM(amount) FROM billing")
#     total_billing = cursor.fetchone()[0] or 0  # Handle NULL case
#     print("Total Billing:", total_billing)

#     cursor.execute("SELECT COUNT(*) FROM billing WHERE payment_status = 'Unpaid'")
#     unpaid_bills = cursor.fetchone()[0]
#     print("Unpaid Bills:", unpaid_bills)

#     # Fetch upcoming appointments
#     cursor.execute("""
#         SELECT 
#             a.appointment_id, p.name AS patient_name, d.name AS doctor_name, 
#             a.appointment_date, a.reason 
#         FROM appointments a 
#         JOIN patients p ON a.patient_id = p.patient_id 
#         JOIN doctors d ON a.doctor_id = d.doctor_id 
#         WHERE a.appointment_date BETWEEN CURDATE() AND DATE_ADD(CURDATE(), INTERVAL 7 DAY)
#     """)
#     upcoming_appointments = cursor.fetchall()
#     print("Upcoming Appointments:", upcoming_appointments)

#     return render_template(
#         'reports.html',
#         total_patients=total_patients,
#         total_doctors=total_doctors,
#         total_appointments=total_appointments,
#         popular_doctor=popular_doctor,
#         total_billing=total_billing,
#         unpaid_bills=unpaid_bills,
#         upcoming_appointments=upcoming_appointments
#     )

@app.route('/reports')
def reports_page():
    data=reports_api()
    return render_template('reports.html',data=data) 

@app.route('/api/reports')
def reports_api():
     # Query total number of patients
    cursor.execute("SELECT COUNT(*) FROM patients")
    total_patients = cursor.fetchone()[0]

    # Query total number of doctors
    cursor.execute("SELECT COUNT(*) FROM doctors")
    total_doctors = cursor.fetchone()[0]

    # Query total number of appointments
    cursor.execute("SELECT COUNT(*) FROM appointments")
    total_appointments = cursor.fetchone()[0]

    # Query the most popular doctor based on appointment count
    cursor.execute("""
        SELECT doctors.name
        FROM appointments
        JOIN doctors ON appointments.doctor_id = doctors.doctor_id
        GROUP BY doctors.name
        ORDER BY COUNT(appointments.appointment_id) DESC
        LIMIT 1
    """)
    popular_doctor = cursor.fetchone()

    # Query total revenue from paid bills
    cursor.execute("SELECT SUM(amount) FROM billing WHERE payment_status = 'Paid'")
    total_billing = cursor.fetchone()[0] or 0

    # Query unpaid bills count
    cursor.execute("SELECT COUNT(*) FROM billing WHERE payment_status = 'Unpaid'")
    unpaid_bills = cursor.fetchone()[0]

    # Query upcoming appointments
    cursor.execute("""
        SELECT appointments.appointment_id, patients.name, doctors.name, 
               appointments.appointment_date, appointments.reason, billing.payment_status
        FROM appointments
        JOIN patients ON appointments.patient_id = patients.patient_id
        JOIN doctors ON appointments.doctor_id = doctors.doctor_id
        LEFT JOIN billing ON appointments.appointment_id = billing.appointment_id
        WHERE appointments.appointment_date > NOW()
        ORDER BY appointments.appointment_date ASC
        LIMIT 10
    """)
    upcoming_appointments = cursor.fetchall()

    # connection.close()

    # Prepare data for rendering
    data = {
        'totalPatients': total_patients,
        'totalDoctors': total_doctors,
        'totalAppointments': total_appointments,
        'popularDoctor': popular_doctor[0] if popular_doctor else None,
        'totalRevenue': total_billing,
        'pendingPayments': unpaid_bills,
        'appointments': [{
            'appointment_id': app[0],
            'patient_name': app[1],
            'doctor_name': app[2],
            'appointment_date': app[3],
            'reason': app[4],
            'payment_status': app[5]
        } for app in upcoming_appointments]
    }
    return data




if __name__ == "__main__":
    app.run(debug=True)
