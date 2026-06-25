from flask import Blueprint, request, redirect, render_template, session
from config import get_db_connection
from notifications import create_notification, get_notifications, get_unread_count, mark_as_read
from email_service import send_appointment_confirmed, send_appointment_cancelled, send_report_published
bp = Blueprint('doctor', __name__)

@bp.route('/doctor_dashboard')
def doctor_dashboard():
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect('/login')
    return render_template('doctor_dashboard.html')

@bp.route('/doctor_availability', methods=['GET', 'POST'])
def doctor_availability():
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect('/login')
    
    if request.method == 'POST':
        day_of_week = request.form['day_of_week']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        doctor_id = session['user_id']

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO doctor_availability (doctor_id, day_of_week, start_time, end_time) VALUES (%s, %s, %s, %s)",
                      (doctor_id, day_of_week, start_time, end_time))
        connection.commit()
        cursor.close()
        connection.close()
        return redirect('/doctor_availability')

    doctor_id = session['user_id']
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM doctor_availability WHERE doctor_id = %s", (doctor_id,))
    availability = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('doctor_availability.html', availability=availability)

@bp.route('/doctor_appointments')
def doctor_appointments():
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect('/login')
    
    doctor_id = session['user_id']
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
    SELECT appointments.id, patients.name, appointments.appointment_date,
           appointments.appointment_time, appointments.status, appointments.notes,
           appointments.genetic_analysis_required, genetic_reports.id, genetic_reports.status
    FROM appointments
    JOIN patients ON appointments.patient_id = patients.id
    LEFT JOIN genetic_reports ON genetic_reports.appointment_id = appointments.id
    WHERE appointments.doctor_id = %s
""", (doctor_id,))
    
    appointments = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('doctor_appointments.html', appointments=appointments)

@bp.route('/update_appointment/<int:appointment_id>', methods=['GET', 'POST'])
def update_appointment(appointment_id):
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect('/login')
    
    if request.method == 'POST':
        status = request.form['status']
        notes = request.form['notes']

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE appointments SET status = %s, notes = %s WHERE id = %s AND doctor_id = %s",
                      (status, notes, appointment_id, session['user_id']))
        connection.commit()

        # Notify patient
        cursor.execute("SELECT patient_id FROM appointments WHERE id = %s", (appointment_id,))
        appointment = cursor.fetchone()
        cursor.execute("SELECT name FROM doctors WHERE id = %s", (session['user_id'],))
        doctor = cursor.fetchone()
        # Get patient email and appointment details
        cursor.execute("SELECT name, email FROM patients WHERE id = %s", (appointment[0],))
        patient_details = cursor.fetchone()
        cursor.execute("SELECT appointment_date, appointment_time FROM appointments WHERE id = %s", (appointment_id,))
        appt_details = cursor.fetchone()

        if status == 'confirmed':
            create_notification(appointment[0], 'patient', f"Dr. {doctor[0]} has confirmed your appointment!", '/my_appointments')
            send_appointment_confirmed(patient_details[1], patient_details[0], doctor[0], appt_details[0], appt_details[1])
        elif status == 'cancelled':
            create_notification(appointment[0], 'patient', f"Dr. {doctor[0]} has cancelled your appointment.", '/my_appointments')
            send_appointment_cancelled(patient_details[1], patient_details[0], doctor[0], appt_details[0], appt_details[1])
        cursor.close()
        connection.close()
        return redirect('/doctor_appointments')

    return render_template('update_appointment.html')

@bp.route('/toggle_genetic/<int:appointment_id>')
def toggle_genetic(appointment_id):
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect('/login')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT genetic_analysis_required FROM appointments WHERE id = %s", (appointment_id,))
    appointment = cursor.fetchone()
    new_status = not appointment[0]
    cursor.execute("UPDATE appointments SET genetic_analysis_required = %s WHERE id = %s", (new_status, appointment_id))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect('/doctor_appointments')

@bp.route('/upload_genetic/<int:appointment_id>', methods=['GET', 'POST'])
def upload_genetic(appointment_id):
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect('/login')
    
    if request.method == 'POST':
        import os
        from pipeline import run_pipeline
        
        file = request.files['genetic_file']
        import os as os_module
        original_ext = os_module.path.splitext(file.filename)[1].lower()
        file_path = os.path.join('uploads', f'genetic_{appointment_id}{original_ext}')
        file.save(file_path)
        
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO genetic_reports (appointment_id, file_path, uploaded_by, status) VALUES (%s, %s, %s, 'pending')",
            (appointment_id, file_path, session['user_id'])
        )
        connection.commit()
        report_id = cursor.lastrowid
        cursor.close()
        connection.close()
        
        run_pipeline(file_path, report_id)

        # Notify patient
        cursor2 = connection2 = get_db_connection().cursor()
        connection2 = get_db_connection()
        cursor2 = connection2.cursor()
        cursor2.execute("SELECT patient_id FROM appointments WHERE id = %s", (appointment_id,))
        patient = cursor2.fetchone()
        create_notification(patient[0], 'patient', "Your genetic file has been uploaded and analyzed by the doctor!", '/my_appointments')
        cursor2.close()
        connection2.close()
        
        return redirect(f'/view_report/{report_id}')
    
    return render_template('upload_genetic.html', appointment_id=appointment_id)

@bp.route('/view_report/<int:report_id>', methods=['GET', 'POST'])
def view_report(report_id):
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect('/login')
    
    if request.method == 'POST':
        comments = request.form['comments']
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE genetic_reports SET status = 'published' WHERE id = %s", (report_id,))
        cursor.execute("UPDATE analysis_results SET comments = %s WHERE report_id = %s", (comments, report_id))
        connection.commit()

        # Notify patient
        # Notify patient
        cursor.execute("""
            SELECT appointments.patient_id, patients.name, patients.email, doctors.name
            FROM genetic_reports 
            JOIN appointments ON genetic_reports.appointment_id = appointments.id
            JOIN patients ON appointments.patient_id = patients.id
            JOIN doctors ON appointments.doctor_id = doctors.id
            WHERE genetic_reports.id = %s
        """, (report_id,))
        report_data = cursor.fetchone()
        create_notification(report_data[0], 'patient', "Your genetic analysis report has been published by the doctor!", '/my_appointments')
        send_report_published(report_data[2], report_data[1], report_data[3])
        cursor.close()
        connection.close()
        return redirect('/doctor_appointments')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM analysis_results WHERE report_id = %s", (report_id,))
    results = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('view_report.html', results=results, report_id=report_id)

@bp.route('/doctor_notifications')
def doctor_notifications():
    if 'user_id' not in session or session['role'] != 'doctor':
        return redirect('/login')
    
    mark_as_read(session['user_id'], 'doctor')
    notifs = get_notifications(session['user_id'], 'doctor')
    return render_template('notifications.html', notifications=notifs, role='doctor')