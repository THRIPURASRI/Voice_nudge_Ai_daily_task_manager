from flask import Flask
from voicenudge.extensions import db, migrate
from voicenudge.tasks.routes import tasks_bp
from voicenudge.history.routes import history_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object("voicenudge.config.Config")

    db.init_app(app)
    migrate.init_app(app, db)

    # ✅ make sure these are here
    app.register_blueprint(tasks_bp, url_prefix="/api/tasks")
    app.register_blueprint(history_bp, url_prefix="/api/history")

    return app
