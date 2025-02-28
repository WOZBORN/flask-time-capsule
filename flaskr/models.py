from datetime import datetime
import uuid

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


from flaskr import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    capsules = db.relationship('Capsule', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Capsule(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    unlock_date = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=False)
    access_code = db.Column(db.String(10), unique=True)
    items = db.relationship('CapsuleItem', backref='capsule', lazy=True, cascade="all, delete-orphan")


class CapsuleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # 'text', 'file', 'image', 'audio'
    content = db.Column(db.Text)  # For text items or file paths
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    capsule_id = db.Column(db.String(36), db.ForeignKey('capsule.id'), nullable=False)
    file_path = db.Column(db.String(255))  # For file uploads
    file_name = db.Column(db.String(255))  # Original filename