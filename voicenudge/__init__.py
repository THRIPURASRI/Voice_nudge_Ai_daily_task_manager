# voicenudge/__init__.py
from flask import Flask
import os
from voicenudge.extensions import db, migrate, jwt, mail
from voicenudge.auth.routes import auth_bp
from voicenudge.tasks.routes import tasks_bp
from voicenudge.history.routes import history_bp
from voicenudge.reminders.scheduler import init_scheduler


def create_app():
    app = Flask(__name__)
    app.config.from_object("voicenudge.config.Config")

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)

    # Blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
    app.register_blueprint(history_bp, url_prefix="/api/history")

    # ✅ Start the scheduler only in the active process (avoids double start)
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        with app.app_context():
            init_scheduler(app)

    # (Optional in dev) auto-create tables
    # with app.app_context():
    #     db.create_all()

    return app
