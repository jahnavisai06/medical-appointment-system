import threading
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail as SendGridMail
import os

def _send_async_email(to, subject, body):
    try:
        message = SendGridMail(
            from_email=os.getenv('MAIL_USERNAME'),
            to_emails=to,
            subject=subject,
            plain_text_content=body
        )
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(f"Email sent to {to}, status: {response.status_code}")
    except Exception as e:
        print(f"Email failed: {e}")

def send_email(to, subject, body):
    thread = threading.Thread(target=_send_async_email, args=(to, subject, body))
    thread.start()

def send_appointment_confirmed(patient_email, patient_name, doctor_name, date, time):
    send_email(
        to=patient_email,
        subject="Appointment Confirmed - MedApp",
        body=f"""Dear {patient_name},

Your appointment has been confirmed!

Doctor: {doctor_name}
Date: {date}
Time: {time}

Please arrive 10 minutes early.

Regards,
MedApp Team"""
    )

def send_appointment_cancelled(patient_email, patient_name, doctor_name, date, time):
    send_email(
        to=patient_email,
        subject="Appointment Cancelled - MedApp",
        body=f"""Dear {patient_name},

Your appointment has been cancelled.

Doctor: {doctor_name}
Date: {date}
Time: {time}

Please book a new appointment at your convenience.

Regards,
MedApp Team"""
    )

def send_report_published(patient_email, patient_name, doctor_name):
    send_email(
        to=patient_email,
        subject="Your Genetic Report is Ready - MedApp",
        body=f"""Dear {patient_name},

Your genetic analysis report has been published by {doctor_name}.

Please login to MedApp and go to My Appointments to view your report.

Regards,
MedApp Team"""
    )

def send_appointment_reminder(patient_email, patient_name, doctor_name, date, time):
    send_email(
        to=patient_email,
        subject="Appointment Reminder - MedApp",
        body=f"""Dear {patient_name},

This is a reminder that you have an appointment tomorrow!

Doctor: {doctor_name}
Date: {date}
Time: {time}

Please arrive 10 minutes early.

Regards,
MedApp Team"""
    )