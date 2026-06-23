from flask import Blueprint, request, redirect, render_template, session
from config import get_db_connection
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

bp = Blueprint('auth', __name__)

@bp.route('/')
def home():
    return render_template('index.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        security_answer = request.form['security_answer'].strip().lower()
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO patients (name, email, password, phone, security_answer) VALUES (%s, %s, %s, %s, %s)",
                      (name, email, hashed_password, phone, security_answer))
       
        connection.commit()
        cursor.close()
        connection.close()
        
        return redirect('/login')
    return render_template('register.html')
@bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        security_answer = request.form['security_answer'].strip().lower()
        new_password = request.form['new_password']

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT id, security_answer FROM patients WHERE email = %s", (email,))
        patient = cursor.fetchone()

        if not patient:
            cursor.close()
            connection.close()
            return render_template('forgot_password.html', error='No account found with that email.')

        if patient[1] != security_answer:
            cursor.close()
            connection.close()
            return render_template('forgot_password.html', error='Security answer is incorrect.')

        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        cursor.execute("UPDATE patients SET password = %s WHERE id = %s", (hashed_password, patient[0]))
        connection.commit()
        cursor.close()
        connection.close()

        return render_template('forgot_password.html', success='Password reset successful! You can now login.')

    return render_template('forgot_password.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        connection = get_db_connection()
        cursor = connection.cursor()

        if role == 'patient':
            cursor.execute("SELECT * FROM patients WHERE email = %s", (email,))
        elif role == 'doctor':
            cursor.execute("SELECT * FROM doctors WHERE email = %s", (email,))
        elif role == 'admin':
            cursor.execute("SELECT * FROM admin WHERE email = %s", (email,))

        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if role == 'admin':
             password_index = 2
        else:
             password_index = 3

        if user and bcrypt.check_password_hash(user[password_index], password):
            session.permanent = True
            session['user_id'] = user[0]
            session['role'] = role
            if role == 'patient':
                return redirect('/patient_dashboard')
            elif role == 'doctor':
                return redirect('/doctor_dashboard')
            elif role == 'admin':
                return redirect('/admin_dashboard')
        else:
            return render_template('login.html', error='Invalid credentials')

    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect('/login')