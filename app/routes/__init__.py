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
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO patients (name, email, password, phone) VALUES (%s, %s, %s, %s)",
                      (name, email, hashed_password, phone))
        connection.commit()
        cursor.close()
        connection.close()
        
        return redirect('/login')
    
    return render_template('register.html')