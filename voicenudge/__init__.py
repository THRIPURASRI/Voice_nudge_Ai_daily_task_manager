from flask import Flask
from voicenudge.extensions import db, migrate, jwt, mail
from voicenudge.auth.routes import auth_bp
from voicenudge.tasks.routes import tasks_bp
from voicenudge.history.routes import history_bp
from voicenudge.reminders.scheduler import init_scheduler   # ✅ use scheduler not routes


def create_app():
    app = Flask(__name__)
    app.config.from_object("voicenudge.config.Config")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)      # ✅ add JWT
    mail.init_app(app)     # ✅ add Mail

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
    app.register_blueprint(history_bp, url_prefix="/api/history")

    # Start reminder scheduler
    init_scheduler(app)    # ✅ add scheduler

    # Auto-create tables in dev
    with app.app_context():
        db.create_all()

    return app
