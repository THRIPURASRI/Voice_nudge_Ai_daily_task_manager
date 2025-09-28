from flask import Blueprint, jsonify
from voicenudge.extensions import db
from voicenudge.models import TaskHistory

history_bp = Blueprint("history", __name__)


@history_bp.route("/", methods=["GET"])
def list_history():
    history = TaskHistory.query.all()
    return jsonify([
        {
            "id": h.id,
            "title": h.title,
            "due_at": str(h.due_at),
            "category": h.category,
            "priority": h.priority
        } for h in history
    ])


@history_bp.route("/clear", methods=["DELETE"])
def clear_history():
    TaskHistory.query.delete()
    db.session.commit()
    return jsonify({"message": "All history cleared"})
