from flask_mail import Mail, Message
from flask import current_app
import threading

mail = Mail()

def _send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
            print(f"Email sent to {msg.recipients}")
        except Exception as e:
            print(f"Email failed: {e}")

def send_email(to, subject, body):
    app = current_app._get_current_object()
    msg = Message(
        subject=subject,
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[to]
    )
    msg.body = body
    thread = threading.Thread(target=_send_async_email, args=(app, msg))
    thread.start()