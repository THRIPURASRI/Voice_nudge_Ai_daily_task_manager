from datetime import datetime
from flask_apscheduler import APScheduler
from flask import current_app
from voicenudge.extensions import db, mail
from voicenudge.models import Reminder, Task, TaskHistory, User
from flask_mail import Message

# Initialize APScheduler
scheduler = APScheduler()


def send_email(to, subject, body):
    """Helper to send email via Flask-Mail."""
    msg = Message(subject=subject, recipients=[to], body=body)
    mail.send(msg)


def check_reminders():
    """Job that checks for due reminders and sends emails to users."""
    with current_app.app_context():
        now = datetime.utcnow()
        due_reminders = Reminder.query.filter(
            Reminder.remind_at <= now, Reminder.sent == False
        ).all()

        for r in due_reminders:
            task = Task.query.get(r.task_id)
            user = User.query.get(r.user_id)

            # If task or user missing → mark as sent
            if not task or not user:
                r.sent = True
                continue

            subject = f"[VoiceNudge] Reminder: {task.title or task.text}"
            body = (
                f"Hi {user.name},\n\n"
                f"This is your reminder for task:\n"
                f"- {task.title or task.text}\n"
                f"Due at: {task.due_at}\n\n"
                f"— VoiceNudge"
            )

            try:
                send_email(user.email, subject, body)

                # Mark reminder as sent
                r.sent = True

                # Save to task history
                history = TaskHistory(
                    user_id=user.id,
                    task_id=task.id,
                    text=task.text,
                    title=task.title,
                    due_at=task.due_at,
                    category=task.category,
                    priority=task.priority,
                )
                db.session.add(history)

            except Exception as e:
                current_app.logger.error(f"Reminder email failed: {e}")

        db.session.commit()


def init_scheduler(app):
    """Initialize APScheduler with the reminder job."""
    if not scheduler.running:
        scheduler.init_app(app)
        scheduler.add_job(
            id="reminder_job",
            func=check_reminders,
            trigger="interval",
            minutes=1  # check every 1 minute
        )
        scheduler.start()
