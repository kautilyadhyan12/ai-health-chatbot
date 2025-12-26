
"""
Reset database and add test data
"""
import os
import sys
sys.path.append('.')

from app import app, db
from database.models import User, ChatHistory, UserAnalytics
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

with app.app_context():
    print("🔧 Resetting database...")
    
    
    db.drop_all()
    print("✅ Dropped all tables")
    
    
    db.create_all()
    print("✅ Created all tables")
    
    # Create test user
    test_user = User(
        username='testuser',
        email='test@medai.com',
        password_hash=generate_password_hash('test123'),
        created_at=datetime.utcnow()
    )
    db.session.add(test_user)
    
    # Create admin user
    admin_user = User(
        username='admin',
        email='admin@medai.com',
        password_hash=generate_password_hash('admin123'),
        created_at=datetime.utcnow()
    )
    db.session.add(admin_user)
    
    db.session.commit()
    print(f"✅ Created users: testuser (id={test_user.id}), admin (id={admin_user.id})")
    
    # Add test chat history
    test_chats = [
        {
            'user_id': test_user.id,
            'user_query': 'What are flu symptoms?',
            'bot_response': 'Flu symptoms include fever, cough, sore throat...',
            'intent': 'symptom_check',
            'confidence': 0.85,
            'processing_time': 1.5,
            'timestamp': datetime.utcnow() - timedelta(hours=1)
        },
        {
            'user_id': test_user.id,
            'user_query': 'How to lower blood pressure?',
            'bot_response': 'Lower blood pressure by exercising, reducing salt...',
            'intent': 'condition_info',
            'confidence': 0.92,
            'processing_time': 2.1,
            'timestamp': datetime.utcnow() - timedelta(minutes=30)
        },
        {
            'user_id': test_user.id,
            'user_query': 'Healthy diet tips?',
            'bot_response': 'A healthy diet includes fruits, vegetables...',
            'intent': 'lifestyle_advice',
            'confidence': 0.78,
            'processing_time': 1.8,
            'timestamp': datetime.utcnow() - timedelta(minutes=15)
        }
    ]
    
    for chat_data in test_chats:
        chat = ChatHistory(**chat_data)
        db.session.add(chat)
    
    db.session.commit()
    print(f"✅ Added {len(test_chats)} test chat records")
    
    # Verify
    total_chats = ChatHistory.query.count()
    user_chats = ChatHistory.query.filter_by(user_id=test_user.id).count()
    
    print("\n" + "="*60)
    print("📊 DATABASE VERIFICATION:")
    print("="*60)
    print(f"Total users: {User.query.count()}")
    print(f"Total chats: {total_chats}")
    print(f"Chats for testuser (id={test_user.id}): {user_chats}")
    
    # Show all chats
    chats = ChatHistory.query.all()
    for chat in chats:
        print(f"  - ID:{chat.id} User:{chat.user_id} Intent:{chat.intent} Conf:{chat.confidence}")
    
    print("="*60)
    print("✅ Database reset complete!")
    print("Login with: username='testuser', password='test123'")