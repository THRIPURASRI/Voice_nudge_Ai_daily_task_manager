from flask import Blueprint, request, jsonify
from voicenudge.extensions import db
from voicenudge.models import Task, TaskHistory
from voicenudge.nlp.utils import parse_task
from voicenudge.ml.model_service import predict_category, predict_priority
from voicenudge.speech.whisper_stt import transcribe_audio

tasks_bp = Blueprint("tasks", __name__)

@tasks_bp.route("/ingest_text", methods=["POST"])
def ingest_text():
    data = request.get_json()
    text = data.get("text", "")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    parsed = parse_task(text)
    category = predict_category(text)
    priority = predict_priority(text)

    task = Task(
        text=text,
        title=parsed["title"],
        due_at=parsed["due_at"],
        category=category,
        priority=priority,
    )
    db.session.add(task)
    db.session.commit()

    return jsonify({
        "id": task.id,
        "title": task.title,
        "due_at": str(task.due_at),
        "category": task.category,
        "priority": task.priority
    })


@tasks_bp.route("/voice_ingest", methods=["POST"])
def voice_ingest():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    path = f"/tmp/{file.filename}"
    file.save(path)

    text = transcribe_audio(path)
    parsed = parse_task(text)
    category = predict_category(text)
    priority = predict_priority(text)

    task = Task(
        text=text,
        title=parsed["title"],
        due_at=parsed["due_at"],
        category=category,
        priority=priority,
    )
    db.session.add(task)
    db.session.commit()

    return jsonify({
        "id": task.id,
        "title": task.title,
        "due_at": str(task.due_at),
        "category": task.category,
        "priority": task.priority,
        "transcribed_text": text
    })


# -------------------------
# List all tasks
# -------------------------
@tasks_bp.route("/", methods=["GET"])
def list_tasks():
    tasks = Task.query.all()
    return jsonify([
        {
            "id": t.id,
            "title": t.title,
            "due_at": str(t.due_at),
            "category": t.category,
            "priority": t.priority,
            "status": t.status
        } for t in tasks
    ])


# -------------------------
# Mark task as completed (moves to history)
# -------------------------
@tasks_bp.route("/<int:task_id>/complete", methods=["PATCH"])
def complete_task(task_id):
    task = Task.query.get_or_404(task_id)

    history = TaskHistory(
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
