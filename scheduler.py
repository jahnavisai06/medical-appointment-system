from apscheduler.schedulers.background import BackgroundScheduler
from config import get_db_connection
from notifications import create_notification
from email_service import send_appointment_reminder
from datetime import datetime, timedelta

def check_appointment_reminders():
    print("Checking appointment reminders...")
    connection = get_db_connection()
    cursor = connection.cursor()
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    
    cursor.execute("""
        SELECT appointments.id, appointments.patient_id, appointments.appointment_date,
               appointments.appointment_time, doctors.name
        FROM appointments
        JOIN doctors ON appointments.doctor_id = doctors.id
        WHERE appointments.appointment_date = %s
        AND appointments.status = 'confirmed'
    """, (tomorrow,))
    
    appointments = cursor.fetchall()
    
    for appointment in appointments:
        create_notification(
            appointment[1],
            'patient',
            f"Reminder: You have an appointment with {appointment[4]} tomorrow on {appointment[2]} at {appointment[3]}!",
            '/my_appointments'
        )
        # Get patient email
        conn2 = get_db_connection()
        cur2 = conn2.cursor()
        cur2.execute("SELECT name, email FROM patients WHERE id = %s", (appointment[1],))
        patient = cur2.fetchone()
        send_appointment_reminder(patient[1], patient[0], appointment[4], appointment[2], appointment[3])
        cur2.close()
        conn2.close()
        print(f"Reminder sent for appointment {appointment[0]}")
    
    cursor.close()
    connection.close()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_appointment_reminders, 'cron', hour=8, minute=0)
    scheduler.start()
    print("Scheduler started!")