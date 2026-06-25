from flask import Flask, session
from app.routes import auth, patient, doctor, admin
from notifications import get_unread_count
from datetime import timedelta
from dotenv import load_dotenv
import os

load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Ensure uploads folder exists
    os.makedirs('uploads', exist_ok=True)
    
    app.secret_key = os.getenv('SECRET_KEY')
    app.permanent_session_lifetime = timedelta(minutes=30)
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(patient.bp)
    app.register_blueprint(doctor.bp)
    app.register_blueprint(admin.bp)

    @app.context_processor
    def inject_notifications():
        if 'user_id' in session and 'role' in session:
            count = get_unread_count(session['user_id'], session['role'])
            return {'unread_count': count}
        return {'unread_count': 0}

    return app