from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from voicenudge.extensions import db
from voicenudge.models import Task, TaskHistory

history_bp = Blueprint("history", __name__)


# -------------------------
# List history (completed + archived)
# -------------------------
@history_bp.route("/", methods=["GET"])
@jwt_required()
def list_history():
    uid = int(get_jwt_identity())

    # 1. Completed tasks still in tasks table
    completed_tasks = Task.query.filter_by(user_id=uid, status="completed").all()

    # 2. Archived history entries
    archived = TaskHistory.query.filter_by(user_id=uid).all()

    results = []

    for t in completed_tasks:
        results.append({
            "id": t.id,
            "title": t.title,
            "due_at": str(t.due_at),
            "category": t.category,
            "priority": t.priority,
            "status": "completed",
            "source": "tasks"
        })

    for h in archived:
        results.append({
            "id": h.id,
            "title": h.title,
            "due_at": str(h.due_at),
            "category": h.category,
            "priority": h.priority,
            "status": "archived",
            "completed_at": str(h.completed_at),
            "source": "history"
        })

    return jsonify(results)


# -------------------------
# Clear history (archive only, not tasks)
# -------------------------
@history_bp.route("/clear", methods=["DELETE"])
@jwt_required()
def clear_history():
    uid = int(get_jwt_identity())
    TaskHistory.query.filter_by(user_id=uid).delete()
    db.session.commit()
    return jsonify({"message": "Your archived history cleared (completed tasks remain)"})
