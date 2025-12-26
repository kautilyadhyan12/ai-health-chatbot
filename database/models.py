from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    chat_history = db.relationship('ChatHistory', backref='user', lazy=True)
    analytics = db.relationship('UserAnalytics', backref='user', lazy=True)

class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user_query = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    intent = db.Column(db.String(50))
    entities = db.Column(db.Text)  
    confidence = db.Column(db.Float)
    processing_time = db.Column(db.Float)  
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_query': self.user_query,
            'bot_response': self.bot_response,
            'timestamp': self.timestamp.isoformat(),
            'intent': self.intent,
            'confidence': self.confidence,
            'processing_time': self.processing_time  
        }

class UserAnalytics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow, nullable=False)
    total_chats = db.Column(db.Integer, default=0, nullable=False)
    avg_confidence = db.Column(db.Float, default=0.0, nullable=False)
    common_intents = db.Column(db.Text, default='{}')  
    
    def update_intents(self, intent):
        intents_dict = json.loads(self.common_intents) if self.common_intents else {}
        intents_dict[intent] = intents_dict.get(intent, 0) + 1
        self.common_intents = json.dumps(intents_dict)