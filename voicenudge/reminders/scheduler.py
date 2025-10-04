# voicenudge/reminders/scheduler.py
import logging
from datetime import datetime, timezone
from flask_apscheduler import APScheduler
from flask_mail import Message
from voicenudge.extensions import db, mail
from voicenudge.models import Reminder, Task, TaskHistory, User

# Silence chatty APScheduler INFO messages in dev
logging.getLogger("apscheduler").setLevel(logging.WARNING)

scheduler = APScheduler()

def send_email(app, to, subject, body):
    """Send email via Flask-Mail, with robust logging."""
    try:
        sender = app.config.get("MAIL_DEFAULT_SENDER")  # use your .env default
        msg = Message(subject=subject, sender=sender, recipients=[to], body=body)
        mail.send(msg)
        print(f"✅ Sent email to {to} • subject='{subject}'")
        return True
    except Exception as e:
        print(f"❌ Email send failed to {to}: {e}")
        return False

def check_reminders(app):
    """Check for due reminders and send emails."""
    with app.app_context():
        # Use timezone-aware UTC for consistency
        now = datetime.now(timezone.utc)
        print(f"⏰ Checking reminders at {now.isoformat()}")

        # If your DB columns are naive UTC, drop tzinfo by using .replace(tzinfo=None) on 'now'
        # now = datetime.utcnow()

        due_reminders = Reminder.query.filter(
            Reminder.remind_at <= now,  # or <= datetime.utcnow() if using naive
            Reminder.sent == False
        ).all()

        print(f"📋 Found {len(due_reminders)} due reminder(s)")

        for r in due_reminders:
            task = Task.query.get(r.task_id)
            user = User.query.get(r.user_id)

            if not task or not user or not user.email:
                # Mark as sent to avoid reprocessing broken rows
                r.sent = True
                continue

            subject = f"[VoiceNudge] Reminder: {task.title or task.text}"
            body = (
                f"Hi {user.name or ''},\n\n"
                f"This is your reminder for:\n"
                f"- {task.title or task.text}\n"
                f"Due at (UTC): {task.due_at}\n\n"
                f"— VoiceNudge"
            )

            ok = send_email(app, user.email, subject, body)
            if ok:
                r.sent = True
                # Optional history audit
                try:
                    db.session.add(TaskHistory(
                        user_id=user.id,
                        task_id=task.id,
                        text=getattr(task, "text", None),
                        title=getattr(task, "title", None),
                        due_at=getattr(task, "due_at", None),
                        category=getattr(task, "category", None),
                        priority=getattr(task, "priority", None),
                    ))
                except Exception as hist_err:
                    print(f"⚠️ Could not write TaskHistory: {hist_err}")

        db.session.commit()

def init_scheduler(app):
    """Initialize and start APScheduler with a resilient interval job."""
    if not scheduler.running:
        scheduler.init_app(app)
        scheduler.add_job(
            id="reminder_job",
            func=lambda: check_reminders(app),
            trigger="interval",
            minutes=1,
            # ✔ prevent small delays from skipping the run
            misfire_grace_time=60,
            # ✔ if multiple runs pile up, merge them into one run
            coalesce=True,
            # ✔ ensure only one instance runs at a time
            max_instances=1,
        )
        scheduler.start()
        print("✅ Reminder scheduler started")
