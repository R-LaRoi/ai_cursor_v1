from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(100))
    location = db.Column(db.String(100))
    bio = db.Column(db.Text)
    avatar_color = db.Column(db.String(7))  # Hex color code
    avatar_url = db.Column(db.String(200))  # URL to uploaded avatar image
    streak = db.Column(db.Integer, default=0)  # Current streak of daily posts
    last_post_date = db.Column(db.Date)  # Date of last post
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    goals = db.relationship('Goal', backref='user', lazy=True)
    gratitudes = db.relationship('Gratitude', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def update_streak(self):
        today = datetime.utcnow().date()
        if self.last_post_date:
            yesterday = today - datetime.timedelta(days=1)
            if self.last_post_date == yesterday:
                self.streak += 1
            elif self.last_post_date != today:
                self.streak = 1
        else:
            self.streak = 1
        self.last_post_date = today

class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)

class Gratitude(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    likes = db.Column(db.Integer, default=0) 