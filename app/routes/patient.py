from flask import Blueprint, request, redirect, render_template, session
from config import get_db_connection
from notifications import create_notification, get_notifications, get_unread_count, mark_as_read

bp = Blueprint('patient', __name__)

@bp.route('/patient_dashboard')
def patient_dashboard():
    if 'user_id' not in session or session['role'] != 'patient':
        return redirect('/login')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM patients WHERE id = %s", (session['user_id'],))
    patient = cursor.fetchone()
    cursor.close()
    connection.close()
    
    return render_template('patient_dashboard.html', name=patient[0])

@bp.route('/search_doctors', methods=['GET', 'POST'])
def search_doctors():
    if 'user_id' not in session or session['role'] != 'patient':
        return redirect('/login')
    
    doctors = []
    if request.method == 'POST':
        specialization = request.form['specialization'].strip()
        doctor_name = request.form['doctor_name'].strip()
        connection = get_db_connection()
        cursor = connection.cursor()
        if doctor_name and specialization:
            cursor.execute("SELECT * FROM doctors WHERE name LIKE %s AND specialization LIKE %s AND is_active = TRUE",
                          (f'%{doctor_name}%', f'%{specialization}%'))
        elif doctor_name:
            cursor.execute("SELECT * FROM doctors WHERE name LIKE %s AND is_active = TRUE",
                          (f'%{doctor_name}%',))
        elif specialization:
            cursor.execute("SELECT * FROM doctors WHERE specialization LIKE %s AND is_active = TRUE",
                          (f'%{specialization}%',))
        else:
            cursor.execute("SELECT * FROM doctors WHERE is_active = TRUE")
        doctors = cursor.fetchall()
        cursor.close()
        connection.close()
    
    return render_template('search_doctors.html', doctors=doctors)

@bp.route('/book_appointment', methods=['GET', 'POST'])
def book_appointment():
    if 'user_id' not in session or session['role'] != 'patient':
        return redirect('/login')
    
    if request.method == 'POST':
        doctor_id = request.form['doctor_id']
        appointment_date = request.form['appointment_date']
        appointment_time = request.form['appointment_time']
        patient_id = session['user_id']

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM appointments WHERE doctor_id = %s AND appointment_date = %s AND appointment_time = %s",
                      (doctor_id, appointment_date, appointment_time))
        existing = cursor.fetchone()

        if existing:
            cursor.close()
            connection.close()
            return render_template('book_appointment.html', error='This slot is already booked! Please choose a different date or time.', doctor_id=doctor_id)

        cursor.execute("INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time) VALUES (%s, %s, %s, %s)",
                      (patient_id, doctor_id, appointment_date, appointment_time))
        connection.commit()

        # Notify doctor
        cursor.execute("SELECT name FROM patients WHERE id = %s", (patient_id,))
        patient = cursor.fetchone()
        create_notification(int(doctor_id), 'doctor', f"New appointment booked by {patient[0]} on {appointment_date} at {appointment_time}", '/doctor_appointments')

        # Send reminder if appointment is tomorrow
        from datetime import datetime, timedelta
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        if appointment_date == tomorrow:
            cursor.execute("SELECT name FROM doctors WHERE id = %s", (doctor_id,))
            doctor = cursor.fetchone()
            create_notification(int(patient_id), 'patient', f"Reminder: You have an appointment with {doctor[0]} tomorrow at {appointment_time}!", '/my_appointments')
            cursor.execute("SELECT name, email FROM patients WHERE id = %s", (patient_id,))
            patient_info = cursor.fetchone()
            from email_service import send_appointment_reminder
            send_appointment_reminder(patient_info[1], patient_info[0], doctor[0], appointment_date, appointment_time)

        cursor.close()
        connection.close()
        return redirect('/my_appointments')
    doctor_id = request.args.get('doctor_id', '')
    return render_template('book_appointment.html', doctor_id=doctor_id)

@bp.route('/my_appointments')
def my_appointments():
    if 'user_id' not in session or session['role'] != 'patient':
        return redirect('/login')
    
    patient_id = session['user_id']
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
    SELECT appointments.id, doctors.name, appointments.appointment_date, 
           appointments.appointment_time, appointments.status,
           genetic_reports.id
    FROM appointments 
    JOIN doctors ON appointments.doctor_id = doctors.id
    LEFT JOIN genetic_reports ON genetic_reports.appointment_id = appointments.id
    WHERE appointments.patient_id = %s
""", (patient_id,))
    appointments = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('my_appointments.html', appointments=appointments)

@bp.route('/cancel_appointment/<int:appointment_id>')
def cancel_appointment(appointment_id):
    if 'user_id' not in session or session['role'] != 'patient':
        return redirect('/login')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE appointments SET status = 'cancelled' WHERE id = %s AND patient_id = %s",
                  (appointment_id, session['user_id']))
    connection.commit()

    # Notify doctor
    cursor.execute("SELECT doctor_id, appointment_date, appointment_time FROM appointments WHERE id = %s", (appointment_id,))
    appointment = cursor.fetchone()
    cursor.execute("SELECT name FROM patients WHERE id = %s", (session['user_id'],))
    patient = cursor.fetchone()
    create_notification(appointment[0], 'doctor', f"{patient[0]} has cancelled the appointment on {appointment[1]} at {appointment[2]}.", '/doctor_appointments')
    cursor.close()
    connection.close()
    return redirect('/my_appointments')

@bp.route('/reschedule_appointment/<int:appointment_id>', methods=['GET', 'POST'])
def reschedule_appointment(appointment_id):
    if 'user_id' not in session or session['role'] != 'patient':
        return redirect('/login')
    
    if request.method == 'POST':
        new_date = request.form['appointment_date']
        new_time = request.form['appointment_time']
        
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE appointments SET appointment_date = %s, appointment_time = %s, status = 'pending' WHERE id = %s AND patient_id = %s",
                      (new_date, new_time, appointment_id, session['user_id']))
        connection.commit()

        # Notify doctor
        cursor.execute("SELECT doctor_id FROM appointments WHERE id = %s", (appointment_id,))
        appointment = cursor.fetchone()
        cursor.execute("SELECT name FROM patients WHERE id = %s", (session['user_id'],))
        patient = cursor.fetchone()
        create_notification(appointment[0], 'doctor', f"{patient[0]} has requested to reschedule their appointment to {new_date} at {new_time}. Please confirm.", '/doctor_appointments')
        cursor.close()
        connection.close()
        return redirect('/my_appointments')
    
    return render_template('reschedule_appointment.html')

@bp.route('/patient_report/<int:report_id>')
def patient_report(report_id):
    if 'user_id' not in session or session['role'] != 'patient':
        return redirect('/login')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM analysis_results WHERE report_id = %s", (report_id,))
    results = cursor.fetchall()
    cursor.execute("SELECT status FROM genetic_reports WHERE id = %s", (report_id,))
    report = cursor.fetchone()
    cursor.close()
    connection.close()
    
    if not report or report[0] != 'published':
        return render_template('patient_report.html', results=[], message='Report not published yet.')
    
    return render_template('patient_report.html', results=results, message=None)

@bp.route('/notifications')
def notifications():
    if 'user_id' not in session or session['role'] != 'patient':
        return redirect('/login')
    
    mark_as_read(session['user_id'], 'patient')
    notifs = get_notifications(session['user_id'], 'patient')
    return render_template('notifications.html', notifications=notifs, role='patient')