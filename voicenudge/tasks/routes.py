from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from voicenudge.extensions import db
from voicenudge.models import Task, TaskHistory
from voicenudge.nlp.utils import parse_task
from voicenudge.ml.model_service import predict_category, predict_priority
from voicenudge.speech.whisper_stt import transcribe_audio
from voicenudge.models import Reminder
from datetime import datetime, timedelta, timezone


tasks_bp = Blueprint("tasks", __name__)

def convert_ist_to_utc(ist_datetime_str):
    """Convert ISO 8601 datetime string from IST to UTC."""
    try:
        ist_offset = timedelta(hours=5, minutes=30)
        ist = timezone(ist_offset)
        ist_dt = datetime.fromisoformat(ist_datetime_str)
        ist_dt = ist_dt.replace(tzinfo=ist)
        utc_dt = ist_dt.astimezone(timezone.utc)
        return utc_dt
    except Exception:
        return None
# -------------------------
# Ingest task via text
# -------------------------

@tasks_bp.route("/ingest_text", methods=["POST"])
@jwt_required()
def ingest_text():
    uid = int(get_jwt_identity())
    data = request.get_json()
    text = data.get("text", "")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    parsed = parse_task(text)
    category = predict_category(text)
    priority = predict_priority(text)

    task = Task(
        user_id=uid,
        text=text,
        title=parsed["title"],
        due_at=parsed["due_at"],   # may be None
        category=category,
        priority=priority,
        original_text=None
    )
    db.session.add(task)
    db.session.commit()

    response = {
        "id": task.id,
        "title": task.title,
        "due_at": str(task.due_at) if task.due_at else None,
        "category": task.category,
        "priority": task.priority,
    }

    if not task.due_at:
        response["note"] = "No due date detected. Please set one."

    return jsonify(response), 201


# -------------------------
# Ingest task via voice
# -------------------------
@tasks_bp.route("/voice_ingest", methods=["POST"])
@jwt_required()
def voice_ingest():
    uid = int(get_jwt_identity())

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    path = f"/tmp/{file.filename}"
    file.save(path)

    raw_text = transcribe_audio(path, translate=False)       # native
    translated_text = transcribe_audio(path, translate=True) # English

    parsed = parse_task(translated_text)
    category = predict_category(translated_text)
    priority = predict_priority(translated_text)

    task = Task(
        user_id=uid,
        text=translated_text,
        original_text=raw_text,
        title=parsed["title"],
        due_at=parsed["due_at"],   # may be None
        category=category,
        priority=priority,
    )
    db.session.add(task)
    db.session.commit()

    response = {
        "id": task.id,
        "title": task.title,
        "due_at": str(task.due_at) if task.due_at else None,
        "category": task.category,
        "priority": task.priority,
        "transcribed_text": translated_text,
        "original_text": raw_text
    }

    if not task.due_at:
        response["note"] = "No due date detected. Please set one."

    return jsonify(response), 201

@tasks_bp.route("/<int:task_id>/set_due", methods=["PATCH"])
@jwt_required()
def set_due(task_id):
    from datetime import datetime, timedelta, timezone

    uid = int(get_jwt_identity())
    task = Task.query.filter_by(id=task_id, user_id=uid).first_or_404()

    data = request.get_json()
    new_due = data.get("due_at")
    if not new_due:
        return jsonify({"error": "due_at required (ISO 8601 format)"}), 400

    try:
        # ✅ Parse IST datetime string (from frontend or Postman)
        ist_offset = timedelta(hours=5, minutes=30)
        ist_tz = timezone(ist_offset)
        due_time_ist = datetime.fromisoformat(new_due)
        due_time_ist = due_time_ist.replace(tzinfo=ist_tz)

        # ✅ Convert IST → UTC for consistent database scheduling
        due_time_utc = due_time_ist.astimezone(timezone.utc)

    except ValueError:
        return jsonify({"error": "Invalid ISO datetime format"}), 400

    # ✅ Update task due time in UTC
    task.due_at = due_time_utc

    # ✅ Automatically create reminder 5 minutes before due time
    remind_time_utc = due_time_utc - timedelta(minutes=5)
    reminder = Reminder(task_id=task.id, user_id=uid, remind_at=remind_time_utc)
    db.session.add(reminder)
    db.session.commit()

    # ✅ Convert back to IST just for displaying in response
    due_time_ist_display = due_time_utc.astimezone(ist_tz)
    remind_time_ist_display = remind_time_utc.astimezone(ist_tz)

    return jsonify({
        "message": f"Task {task.id} due date updated",
        "due_at_utc": due_time_utc.isoformat(),
        "remind_at_utc": remind_time_utc.isoformat(),
        "due_at_ist": due_time_ist_display.strftime("%Y-%m-%d %H:%M:%S"),
        "remind_at_ist": remind_time_ist_display.strftime("%Y-%m-%d %H:%M:%S")
    }), 200

# -------------------------
# List tasks (per user)
# -------------------------
@tasks_bp.route("/", methods=["GET"])
@jwt_required()
def list_tasks():
    uid = int(get_jwt_identity())
    tasks = Task.query.filter_by(user_id=uid).all()
    return jsonify([
        {
            "id": t.id,
            "title": t.title,
            "due_at": str(t.due_at),
            "category": t.category,
            "priority": t.priority,
            "status": t.status,
            "text": t.text,
            "original_text": t.original_text
        } for t in tasks
    ])


# -------------------------
# Complete a task (moves to history)
# -------------------------
@tasks_bp.route("/<int:task_id>/complete", methods=["PATCH"])
@jwt_required()
def complete_task(task_id):
    uid = int(get_jwt_identity())
    task = Task.query.filter_by(id=task_id, user_id=uid).first_or_404()

    history = TaskHistory(
        user_id=uid,
        task_id=task.id,
        text=task.text,
        title=task.title,
        due_at=task.due_at,
        category=task.category,
        priority=task.priority
    )

    db.session.add(history)
    db.session.delete(task)
    db.session.commit()

    return jsonify({"message": f"Task {task_id} completed and moved to history"})
