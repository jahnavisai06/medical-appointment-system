from flask import Blueprint, request, redirect, render_template, session
from config import get_db_connection

bp = Blueprint('admin', __name__)

@bp.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect('/login')
    return render_template('admin_dashboard.html')

@bp.route('/admin_doctors')
def admin_doctors():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect('/login')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM doctors")
    doctors = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('admin_doctors.html', doctors=doctors)

@bp.route('/toggle_doctor/<int:doctor_id>')
def toggle_doctor(doctor_id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect('/login')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT is_active FROM doctors WHERE id = %s", (doctor_id,))
    doctor = cursor.fetchone()
    new_status = not doctor[0]
    cursor.execute("UPDATE doctors SET is_active = %s WHERE id = %s", (new_status, doctor_id))
    connection.commit()
    cursor.close()
    connection.close()
    return redirect('/admin_doctors')

@bp.route('/admin_patients')
def admin_patients():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect('/login')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM patients")
    patients = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('admin_patients.html', patients=patients)

@bp.route('/admin_appointments')
def admin_appointments():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect('/login')
    
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT appointments.id, patients.name, doctors.name,
               appointments.appointment_date, appointments.appointment_time,
               appointments.status
        FROM appointments
        JOIN patients ON appointments.patient_id = patients.id
        JOIN doctors ON appointments.doctor_id = doctors.id
    """)
    appointments = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('admin_appointments.html', appointments=appointments)

@bp.route('/add_doctor', methods=['GET', 'POST'])
def add_doctor():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect('/login')
    
    if request.method == 'POST':
        from flask_bcrypt import Bcrypt
        bcrypt = Bcrypt()
        
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        specialization = request.form['specialization']
        bio = request.form['bio']
        consultation_fee = request.form['consultation_fee']
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO doctors (name, email, password, specialization, bio, consultation_fee, is_active) VALUES (%s, %s, %s, %s, %s, %s, TRUE)",
                      (name, email, hashed_password, specialization, bio, consultation_fee))
        connection.commit()
        cursor.close()
        connection.close()
        
        return redirect('/admin_doctors')
    
    return render_template('add_doctor.html')