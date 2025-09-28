from datetime import datetime
from voicenudge.extensions import db

class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    due_at = db.Column(db.DateTime, nullable=True)
    category = db.Column(db.String(50))
    priority = db.Column(db.String(20))
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TaskHistory(db.Model):
    __tablename__ = "task_history"
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer)
    text = db.Column(db.Text, nullable=False)    
    title = db.Column(db.String(255), nullable=False)
    due_at = db.Column(db.DateTime, nullable=True) 
    category = db.Column(db.String(50))
    priority = db.Column(db.String(20))
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
