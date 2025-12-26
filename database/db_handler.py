"""
Database handler for AI Medical Chatbot
"""
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta
import json
from .models import db, User, ChatHistory, UserAnalytics

class DatabaseHandler:
    """Handles database operations for the medical chatbot"""
    
    @staticmethod
    def create_user(username, email, password_hash):
        """Create a new user"""
        try:
            user = User(
                username=username,
                email=email,
                password_hash=password_hash
            )
            db.session.add(user)
            db.session.commit()
            return user
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_user_by_username(username):
        """Get user by username"""
        return User.query.filter_by(username=username).first()
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email"""
        return User.query.filter_by(email=email).first()
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user by ID"""
        return User.query.get(user_id)
    
    @staticmethod
    def save_chat_history(user_id, user_query, bot_response, intent=None, entities=None, confidence=None, processing_time=None):  # ADD processing_time
        """Save chat history"""
        try:
            entities_json = json.dumps(entities) if entities else None
            
            chat = ChatHistory(
                user_id=user_id,
                user_query=user_query,
                bot_response=bot_response,
                intent=intent,
                entities=entities_json,
                confidence=confidence,
                processing_time=processing_time,  
                timestamp=datetime.utcnow()
            )
            
            db.session.add(chat)
            db.session.commit()
            
            # Update analytics
            DatabaseHandler.update_user_analytics(user_id, intent)
            
            return chat
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def update_user_analytics(user_id, intent):
        """Update user analytics"""
        try:
            today = datetime.utcnow().date()
            analytics = UserAnalytics.query.filter_by(
                user_id=user_id,
                date=today
            ).first()
            
            if not analytics:
                analytics = UserAnalytics(
                    user_id=user_id,
                    date=today,
                    total_chats=0,
                    avg_confidence=0.0,
                    common_intents='{}'
                )
                db.session.add(analytics)
            
            analytics.total_chats += 1
            
            # Update intents
            if intent:
                intents_dict = json.loads(analytics.common_intents) if analytics.common_intents else {}
                intents_dict[intent] = intents_dict.get(intent, 0) + 1
                analytics.common_intents = json.dumps(intents_dict)
            
            db.session.commit()
            return analytics
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_chat_history(user_id, limit=50, offset=0):
        """Get chat history for a user"""
        return ChatHistory.query.filter_by(user_id=user_id)\
            .order_by(ChatHistory.timestamp.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()
    
    @staticmethod
    def get_recent_chats(user_id, hours=24):
        """Get recent chats within specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return ChatHistory.query.filter(
            ChatHistory.user_id == user_id,
            ChatHistory.timestamp >= cutoff_time
        ).order_by(ChatHistory.timestamp.desc()).all()
    
    @staticmethod
    def delete_chat_history(record_id, user_id):
        """Delete a chat record"""
        try:
            record = ChatHistory.query.get(record_id)
            if record and record.user_id == user_id:
                db.session.delete(record)
                db.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_user_analytics(user_id, days=30):
        """Get user analytics for specified days"""
        cutoff_date = datetime.utcnow().date() - timedelta(days=days)
        
        analytics = UserAnalytics.query.filter(
            UserAnalytics.user_id == user_id,
            UserAnalytics.date >= cutoff_date
        ).order_by(UserAnalytics.date.desc()).all()
        
        return analytics
    
    @staticmethod
    def get_chat_statistics(user_id):
        """Get chat statistics for a user"""
        total_chats = ChatHistory.query.filter_by(user_id=user_id).count()
        
        if total_chats > 0:
            avg_confidence = db.session.query(
                db.func.avg(ChatHistory.confidence)
            ).filter_by(user_id=user_id).scalar() or 0.0
            
            # Get most common intent
            most_common = db.session.query(
                ChatHistory.intent,
                db.func.count(ChatHistory.intent).label('count')
            ).filter_by(user_id=user_id)\
             .group_by(ChatHistory.intent)\
             .order_by(db.desc('count'))\
             .first()
            
            most_common_intent = most_common[0] if most_common else None
            
            return {
                'total_chats': total_chats,
                'avg_confidence': round(avg_confidence * 100, 2),
                'most_common_intent': most_common_intent
            }
        
        return {
            'total_chats': 0,
            'avg_confidence': 0,
            'most_common_intent': None
        }
    
    @staticmethod
    def export_chat_history_csv(user_id):
        """Export chat history as CSV data"""
        import csv
        import io
        
        chats = ChatHistory.query.filter_by(user_id=user_id)\
            .order_by(ChatHistory.timestamp.desc())\
            .all()
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Timestamp', 'User Query', 'Bot Response', 'Intent', 'Confidence', 'Entities'])
        
        # Write data
        for chat in chats:
            writer.writerow([
                chat.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                chat.user_query,
                chat.bot_response,
                chat.intent or '',
                f"{chat.confidence * 100:.1f}%" if chat.confidence else '',
                chat.entities or ''
            ])
        
        output.seek(0)
        return output.getvalue()
    
    @staticmethod
    def cleanup_old_records(days_to_keep=90):
        """Clean up old chat records"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Delete old chat history
            old_chats = ChatHistory.query.filter(
                ChatHistory.timestamp < cutoff_date
            ).delete()
            
            # Delete old analytics
            old_analytics = UserAnalytics.query.filter(
                UserAnalytics.date < cutoff_date.date()
            ).delete()
            
            db.session.commit()
            
            return {
                'deleted_chats': old_chats,
                'deleted_analytics': old_analytics
            }
        except SQLAlchemyError as e:
            db.session.rollback()
            raise e