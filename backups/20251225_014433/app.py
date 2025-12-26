"""
AI Medical Chatbot - Main Application
Optimized for LLaMA-3 8B Q3_K_S (3.2GB) on 4GB VRAM systems
"""

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import json
import csv
import io
import os
import sys
import traceback
import re
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')
from sqlalchemy import text  # For SQLAlchemy 2.x compatibility

from config import Config
from database.models import db, User, ChatHistory, UserAnalytics

from flask_socketio import SocketIO, emit, join_room
import json

# ============================================
# Initialize Flask Application
# ============================================

app = Flask(__name__)
app.config.from_object(Config)
Config.init_app(app)

# Initialize database
db.init_app(app)

# Initialize SocketIO for real-time updates with better configuration
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='threading',
    ping_timeout=60,
    ping_interval=25,
    logger=True,
    engineio_logger=False,
    always_connect=True
)
print("✅ Real-time Socket.IO initialized with improved configuration")

# Initialize Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

print("=" * 70)
print("🚀 AI Medical Chatbot - LLaMA-3 8B Q3_K_S (3.2GB)")
print("=" * 70)
print("Optimized for: Windows 10, 16GB RAM, GTX 1650 4GB VRAM")
print("=" * 70)

# ============================================
# System Check and Memory Optimization
# ============================================

def check_system_resources():
    """Check system resources WITHOUT torch.cuda dependency"""
    print("\n🔍 Checking system resources...")
    
    try:
        import psutil
        
        # Check RAM only - DO NOT USE torch.cuda
        ram = psutil.virtual_memory()
        ram_gb = ram.total / 1e9
        ram_available_gb = ram.available / 1e9
        print(f"📊 System RAM: {ram_gb:.1f}GB (Available: {ram_available_gb:.1f}GB)")
        
        # Check disk space
        disk = psutil.disk_usage(os.path.dirname(os.path.abspath(__file__)))
        free_gb = disk.free / 1e9
        print(f"💾 Disk space: {free_gb:.1f}GB free")
        
        if free_gb < 5:
            print("⚠️  Warning: Low disk space (<5GB)")
        
        # DO NOT check CUDA with torch
        # Let llama.cpp handle GPU detection internally
        print(f"🎮 GPU detection: Letting llama.cpp handle GPU compatibility")
        
        return {
            'cuda_available': False,  # We don't know yet
            'vram_gb': 0,             # We'll find out when llama.cpp loads
            'ram_available_gb': ram_available_gb,
            'disk_free_gb': free_gb
        }
        
    except ImportError as e:
        print(f"⚠️  Could not check system resources: {e}")
        return {
            'cuda_available': False,
            'vram_gb': 0,
            'ram_available_gb': 8,  # Assume minimum
            'disk_free_gb': 10
        }

# Run system check
system_info = check_system_resources()

# ============================================
# ML Models Initialization - CORRECTED FOR Q3_K_M
# ============================================

ml_models_loaded = False
rag_system = None
safety_checker = None

print("\n📥 Loading ML models...")

try:
    # Import ML models
    from ml_models.rag_system import OptimizedMedicalRAG
    
    print("✅ OptimizedMedicalRAG module imported")
    
    # Get OPTIMIZED configuration for Q3_K_M (3.74GB)
    from config import Config
    
    optimized_config = {
        'llama_config': {
            'n_ctx': app.config['LLAMA_CONTEXT_SIZE'],      # Should be 1536
            'n_gpu_layers': app.config['LLAMA_N_GPU_LAYERS'], # Should be 26
            'max_tokens': app.config['LLAMA_MAX_TOKENS'],     # Should be 256
            'temperature': app.config['LLAMA_TEMPERATURE'],   # Should be 0.1
            'offload_kqv': True,   # Critical for hybrid mode
            'use_mmap': True,
            'f16_kv': True,
            'n_batch': app.config['LLAMA_BATCH_SIZE']  # Should be 256
        },
        'embedding_model': app.config['EMBEDDING_MODEL']
    }
    
    # Initialize RAG System with Q3_K_M optimizations
    print(f"🔧 Configuring for Q3_K_M model (3.74GB)...")
    print(f"   • Context size: {app.config['LLAMA_CONTEXT_SIZE']}")
    print(f"   • GPU layers: {app.config['LLAMA_N_GPU_LAYERS']}")
    print(f"   • Max tokens: {app.config['LLAMA_MAX_TOKENS']}")
    print(f"   • Batch size: {app.config['LLAMA_BATCH_SIZE']}")
    print(f"   • Temperature: {app.config['LLAMA_TEMPERATURE']}")
    
    rag_system = OptimizedMedicalRAG(
        
        knowledge_base_path=app.config.get('KNOWLEDGE_BASE_PATH', 'data/medical_knowledge/medical_faqs.json'),
        llama_model_path=app.config.get('LLAMA_MODEL_PATH'),
        vector_db_path=app.config.get('VECTOR_DB_PATH', 'data/vector_db/medical_index.faiss'),
        config=optimized_config
    )
    print(f"\n🔍 APP DEBUG: RAG system initialized")
    print(f"🔍 APP DEBUG: LLaMA model loaded: {'✅ YES' if rag_system.llama_model else '❌ NO'}")
    print(f"🔍 APP DEBUG: RAG class: {rag_system.__class__.__name__}")
    
    print("✅ Medical RAG System initialized")
    
    
    # ============================================
    # 🚀 PRE-WARM MODEL FOR FASTER FIRST RESPONSE
    # ============================================
    if rag_system.llama_model:
        try:
                print("🔥 Pre-warming LLaMA model...")
                # Send a tiny query to load model into GPU memory
                warmup_response = rag_system.llama_model.generate_response(
                    prompt="Hello",
                    max_tokens=10,
                    temperature=0.1
                )
                print("✅ Model pre-warmed - first response will be faster")
        except Exception as e:
                print(f"⚠️ Pre-warm failed: {e}")
    
    # Initialize Safety Checker
    try:
        from ml_models.safety_checker import SafetyChecker
        safety_checker = SafetyChecker()
        print("✅ Safety Checker loaded")
    except ImportError:
        print("⚠️  Using fallback safety checker")
        safety_checker = None
    
    ml_models_loaded = True
    
    # Print model information
    print("\n📊 Model Information:")
    print(f"   • Model: LLaMA-3 8B Q3_K_M (3.74GB)")
    print(f"   • Status: {'✅ Loaded' if rag_system.llama_model else '❌ Not available'}")
    print(f"   • Embeddings: {rag_system.embedding_generator.model_name}")
    print(f"   • Knowledge Base: {len(rag_system.knowledge_base)} entries")
    
except ImportError as e:
    print(f"❌ Failed to import ML modules: {e}")
    traceback.print_exc()
except Exception as e:
    print(f"❌ ML initialization error: {e}")
    traceback.print_exc()

# ============================================
# Fallback Classes (if ML models fail)
# ============================================

if not safety_checker:
    print("⚠️  Creating fallback Safety Checker")
    
    class FallbackSafetyChecker:
        def __init__(self):
            self.emergency_keywords = [
                'heart attack', 'stroke', 'suicide', 'severe pain',
                'bleeding heavily', 'can\'t breathe', 'unconscious',
                'chest pain', 'shortness of breath', 'sudden paralysis',
                'choking', 'overdose', 'poisoning', 'seizure',
                'broken bone', 'deep cut', 'difficulty breathing',
                'chest pressure', 'paralysis', 'dying', 'emergency'
            ]
            
            self.high_risk_symptoms = [
                'severe headache', 'high fever', 'seizure',
                'broken bone', 'deep cut', 'poisoning',
                'difficulty breathing', 'chest pressure'
            ]
        
        def check_emergency(self, text):
            """Check for emergency situations"""
            text_lower = text.lower()
            
            for keyword in self.emergency_keywords:
                if keyword in text_lower:
                    return True, "EMERGENCY_DETECTED", keyword
            
            for symptom in self.high_risk_symptoms:
                if symptom in text_lower:
                    return True, "HIGH_RISK_SYMPTOM", symptom
            
            return False, "SAFE", ""
        
        def validate_query(self, text):
            """Validate if query is appropriate"""
            if len(text) < 3:
                return False, "Query too short. Please provide more details."
            
            if len(text) > 1000:
                return False, "Query too long. Please keep it under 1000 characters."
            
            # Check for inappropriate content
            inappropriate_patterns = [
                r'\b(diagnose me|prescribe me|cure me|treat me)\b',
                r'\b(suicide|kill myself|end my life|self-harm)\b',
                r'\b(overdose|poison|illegal drugs|abuse)\b',
            ]
            
            for pattern in inappropriate_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return False, "This query contains inappropriate requests. Please consult a healthcare professional directly."
            
            return True, "Valid query"
        
        def contains_pii(self, text):
            """Check for Personally Identifiable Information"""
            patterns = {
                'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'phone': r'\b(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b',
                'ssn': r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b',
            }
            
            found_pii = []
            for pii_type, pattern in patterns.items():
                if re.search(pattern, text):
                    found_pii.append(pii_type)
            
            return len(found_pii) > 0, found_pii
    
    safety_checker = FallbackSafetyChecker()

if not rag_system:
    print("⚠️  Creating fallback RAG System")
    
    class FallbackMedicalRAG:
        def __init__(self):
            self.knowledge_base = [
                {
                    "question": "What are common flu symptoms?",
                    "answer": "Common flu symptoms include fever, cough, sore throat, body aches, headache, chills, and fatigue. Symptoms usually come on suddenly.",
                    "category": "infectious_diseases",
                    "severity": "moderate"
                },
                {
                    "question": "How to manage high blood pressure?",
                    "answer": "High blood pressure can be managed through lifestyle changes: regular exercise, healthy diet low in sodium, weight management, limited alcohol, no smoking, stress reduction, and prescribed medications if needed.",
                    "category": "chronic_conditions",
                    "severity": "serious"
                }
            ]
            
            print("✅ Fallback RAG System created")
        
        def query(self, user_query):
            """Simple query response"""
            response = f"I understand you're asking about: {user_query}\n\n"
            response += "I'm your AI medical assistant. For accurate medical information, please consult with a healthcare professional.\n\n"
            response += "**General Health Tips:**\n"
            response += "• Stay hydrated and get enough rest\n"
            response += "• Eat a balanced diet with fruits and vegetables\n"
            response += "• Exercise regularly\n"
            response += "• Get regular health check-ups\n\n"
            response += "**⚠️ Important:** I provide general information only. Always consult healthcare professionals for medical advice."
            
            return {
                'response': response,
                'confidence': 0.5,
                'intent': 'general_health',
                'timestamp': datetime.now().isoformat(),
                'model': 'fallback',
                'processing_time': 0.1
            }
    
    rag_system = FallbackMedicalRAG()

# ============================================
# Flask-Login User Loader
# ============================================

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))

# ============================================
# Database Initialization
# ============================================

with app.app_context():
    try:
        # Drop all tables if exists and recreate (for development)
        if app.config['DEBUG']:
            #db.drop_all()
            pass
        db.create_all()
        print("✅ Database tables created")
        
        # Create admin user if not exists - FIXED: Read from env
        admin = User.query.filter_by(username='admin').first()  
        if not admin:
            admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
            admin = User(
                username='admin',
                email='admin@medai.com',
                password_hash=generate_password_hash(admin_password)
            )
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Created admin user (username: admin)")
            print(f"⚠️  Admin password set from environment variable")
    except Exception as e:
        print(f"❌ Database initialization error: {e}")

# ============================================
# Helper Functions
# ============================================

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input"""
    if not text:
        return ""
    
    text = text.strip()[:max_length]
    text = re.sub(r'[<>"\']', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text

def contains_pii(text: str):
    """
    Check if text contains Personally Identifiable Information (PII)
    Returns: (has_pii, pii_types, sanitized_text)
    """
    import re
    
    pii_patterns = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b',
        'ssn': r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b',
        'credit_card': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
    }
    
    sanitized = text
    found_pii = []
    
    for pii_type, pattern in pii_patterns.items():
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            found_pii.append(pii_type)
            # Mask the PII instead of removing entire query
            if pii_type == 'email':
                sanitized = sanitized.replace(match.group(), '[EMAIL]')
            elif pii_type == 'phone':
                sanitized = sanitized.replace(match.group(), '[PHONE]')
            elif pii_type == 'ssn':
                sanitized = sanitized.replace(match.group(), '[SSN]')
            elif pii_type == 'credit_card':
                sanitized = sanitized.replace(match.group(), '[CREDIT_CARD]')
    
    return len(found_pii) > 0, found_pii, sanitized

def generate_session_id() -> str:
    """Generate unique session ID"""
    import uuid
    return f"session-{str(uuid.uuid4())[:8]}"

def log_activity(user_id: int, action: str, details: str = ""):
    """Log user activity"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [USER:{user_id}] {action} - {details}")
    except:
        pass

def format_response_time(seconds: float) -> str:
    """Format response time for display"""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        return f"{seconds/60:.1f}min"

def create_emergency_response(keywords: List[str]) -> str:
    """Create emergency response"""
    response = "🚨 **MEDICAL EMERGENCY DETECTED** 🚨\n\n"
    response += f"I detected mentions of: {', '.join(keywords)}\n\n"
    response += "**THIS REQUIRES IMMEDIATE MEDICAL ATTENTION**\n\n"
    response += "**Please take these steps immediately:**\n"
    response += "1. 📞 **Call emergency services** (911/112) RIGHT NOW\n"
    response += "2. 🏥 **Go to the nearest emergency room**\n"
    response += "3. 👥 **Stay with someone** if possible\n"
    response += "4. 📋 **Describe your symptoms clearly** to medical professionals\n\n"
    response += "**Do NOT wait for further AI responses.**\n"
    response += "This AI assistant cannot provide emergency medical care.\n\n"
    response += "**Emergency Numbers:**\n"
    response += "• USA: 911\n• UK: 999\n• EU: 112\n• Australia: 000\n• India: 112\n\n"
    response += "Stay calm and follow the instructions of emergency responders."
    
    return response

def save_chat_to_history(user_id: int, user_query: str, bot_response: str, 
                         intent: str = None, confidence: float = None, 
                         entities: List[Dict] = None, processing_time: float = None) -> ChatHistory:
    """Save chat to database history AND broadcast real-time update"""
    try:
        print(f"🔴 DEBUG SAVE: user_id={user_id}, query='{user_query[:50]}...'")
        print(f"🔴 DEBUG SAVE: intent={intent}, confidence={confidence}")
        
        chat_record = ChatHistory(
            user_id=user_id,
            user_query=user_query[:500],
            bot_response=bot_response[:2000],
            intent=intent,
            entities=json.dumps(entities) if entities else None,
            confidence=confidence,
            processing_time=processing_time,
            timestamp=datetime.utcnow()
        )
        
        db.session.add(chat_record)
        
        # Update user analytics
        update_user_analytics(user_id, intent)
        
        db.session.commit()
        
        # ✅ VERIFY SAVE WORKED
        saved_id = chat_record.id
        verify = ChatHistory.query.get(saved_id)
        print(f"✅ DEBUG SAVE: Record saved with ID={saved_id}, exists={verify is not None}")
        
        # ✅ BROADCAST REAL-TIME UPDATE
        try:
            stats = get_user_statistics(user_id)
            print(f"📡 DEBUG SAVE: Broadcasting stats: {stats}")
            socketio.emit('dashboard_update', {
                'user_id': user_id,
                'stats': stats
            }, room=f'user_{user_id}')
            print(f"📡 Real-time update sent for user {user_id}")
        except Exception as e:
            print(f"⚠️ Could not send real-time update: {e}")
        
        return chat_record
        
    except Exception as e:
        print(f"❌ Error saving chat history: {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return None

def update_user_analytics(user_id: int, intent: str = None):
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
        
        if intent:
            try:
                intents_dict = json.loads(analytics.common_intents) if analytics.common_intents else {}
            except (json.JSONDecodeError, TypeError):
                intents_dict = {}
            
            intents_dict[intent] = intents_dict.get(intent, 0) + 1
            analytics.common_intents = json.dumps(intents_dict)
        
        db.session.commit()
        return analytics
        
    except Exception as e:
        print(f"❌ Error updating analytics: {e}")
        db.session.rollback()
        return None

# ↓ ADD AFTER THE ABOVE FUNCTION ↓
def get_user_statistics(user_id):
    """Get current statistics for a user"""
    print(f"🔍 DEBUG STATS: Called for user_id={user_id}")
    
    # DEBUG: Check all users and chats
    all_users = User.query.all()
    print(f"🔍 DEBUG: All users in DB: {[{'id': u.id, 'name': u.username} for u in all_users]}")
    
    all_chats = ChatHistory.query.all()
    print(f"🔍 DEBUG: All chats in DB: {len(all_chats)} total")
    
    # Total chats for this user
    total_chats = ChatHistory.query.filter_by(user_id=user_id).count()
    print(f"🔍 DEBUG: total_chats for user {user_id} = {total_chats}")
    
    # Check some actual records
    user_chats = ChatHistory.query.filter_by(user_id=user_id).all()
    print(f"🔍 DEBUG: Found {len(user_chats)} chat records for user {user_id}")
    for i, chat in enumerate(user_chats[:3]):  # Show first 3
        print(f"   Chat {i+1}: ID={chat.id}, Intent={chat.intent}, Confidence={chat.confidence}")
    
    # Average confidence
    avg_conf_result = db.session.query(db.func.avg(ChatHistory.confidence)).filter_by(user_id=user_id).scalar()
    print(f"🔍 DEBUG: avg_conf_result raw = {avg_conf_result}")
    avg_confidence = round((avg_conf_result or 0) * 100, 1)
    
    # Most common intent (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    most_common = db.session.query(
        ChatHistory.intent,
        db.func.count(ChatHistory.intent).label('count')
    ).filter(
        ChatHistory.user_id == user_id,
        ChatHistory.timestamp >= thirty_days_ago
    ).group_by(ChatHistory.intent).order_by(db.desc('count')).first()
    
    most_common_intent = most_common[0].replace('_', ' ').upper() if most_common else 'N/A'
    print(f"🔍 DEBUG: most_common_intent = {most_common_intent}")
    
    # Last active time
    last_chat = ChatHistory.query.filter_by(user_id=user_id).order_by(ChatHistory.timestamp.desc()).first()
    if last_chat:
        print(f"🔍 DEBUG: Last chat timestamp = {last_chat.timestamp}")
        time_diff = (datetime.utcnow() - last_chat.timestamp).seconds
        if time_diff < 60:
            last_active = 'Just now'
        elif time_diff < 3600:
            last_active = f'{time_diff//60} min ago'
        else:
            last_active = last_chat.timestamp.strftime('%H:%M')
    else:
        last_active = 'Never'
    
    result = {
        'total_chats': total_chats,
        'avg_confidence': avg_confidence,
        'most_common_intent': most_common_intent,
        'last_active': last_active
    }
    
    print(f"🔍 DEBUG STATS: Returning {result}")
    return result

def generate_insights(daily_stats: List[Dict], most_common_intent: str) -> List[Dict]:
    """Generate insights from analytics data"""
    insights = []
    
    if not daily_stats:
        insights.append({
            'type': 'info',
            'title': 'No Data Yet',
            'message': 'Start chatting to see insights about your health queries.',
            'icon': 'fas fa-chart-line'
        })
        return insights
    
    # Calculate average daily chats
    avg_daily_chats = sum(day['chats'] for day in daily_stats) / len(daily_stats)
    
    if avg_daily_chats > 5:
        insights.append({
            'type': 'success',
            'title': 'Active User',
            'message': f'You average {avg_daily_chats:.1f} chats per day. Keep exploring health topics!',
            'icon': 'fas fa-user-check'
        })
    
    # Most common intent insight
    if most_common_intent:
        intent_display = most_common_intent.replace('_', ' ').title()
        insights.append({
            'type': 'info',
            'title': 'Primary Interest',
            'message': f'Your most common topic is: {intent_display}',
            'icon': 'fas fa-tags'
        })
    
    # Peak activity insight
    max_chats_day = max(daily_stats, key=lambda x: x['chats'])
    if max_chats_day['chats'] > 10:
        insights.append({
            'type': 'warning',
            'title': 'High Activity Day',
            'message': f'You had {max_chats_day["chats"]} chats on {max_chats_day["date"][:10]}',
            'icon': 'fas fa-calendar-day'
        })
    
    return insights

# ============================================
# Application Routes
# ============================================

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'GET':
        return render_template('register.html')
    
    # Handle POST request
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # Validation
        if not username or not email or not password:
            return jsonify({'error': 'All fields are required', 'success': False}), 400
        
        if len(username) < 3:
            return jsonify({'error': 'Username must be at least 3 characters', 'success': False}), 400
        
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters', 'success': False}), 400
        
        # Simple email validation
        if '@' not in email or '.' not in email:
            return jsonify({'error': 'Please enter a valid email address', 'success': False}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists', 'success': False}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered', 'success': False}), 400
        
        # Create new user
        hashed_password = generate_password_hash(password)
        new_user = User(
            username=username,
            email=email,
            password_hash=hashed_password,
            created_at=datetime.utcnow()
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        log_activity(new_user.id, "REGISTER", f"New user: {username}")
        
        return jsonify({
            'message': 'Registration successful! Please login.',
            'success': True,
            'redirect': '/login'
        }), 201
        
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return jsonify({'error': 'Registration failed. Please try again.', 'success': False}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'GET':
        return render_template('login.html')
    
    # Handle POST request
    try:
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Find user
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            
            log_activity(user.id, "LOGIN", "Successful login")
            
            return jsonify({
                'message': 'Login successful',
                'success': True,
                'redirect': '/dashboard',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email
                }
            }), 200
        
        log_activity(0, "LOGIN_FAILED", f"Failed login attempt for: {username}")
        return jsonify({'error': 'Invalid username or password', 'success': False}), 401
        
    except Exception as e:
        print(f"❌ Login error: {e}")
        return jsonify({'error': 'Login failed. Please try again.', 'success': False}), 500

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    # Pre-load user statistics
    stats = get_user_statistics(current_user.id)
    
    return render_template('dashboard.html', 
                         username=current_user.username,
                         user_stats=stats)  # Pass stats to template

@app.route('/chat')
@login_required
def chat_page():
    """Chat interface page"""
    return render_template('chat.html', username=current_user.username)

@app.route('/analytics')
@login_required
def analytics_page():
    """Analytics page"""
    return render_template('analytics.html', username=current_user.username)

@app.route('/history')
@login_required
def history_page():
    """Chat history page"""
    return render_template('history.html', username=current_user.username)

# ============================================
# API Routes
# ============================================

@app.route('/api/user')
@login_required
def get_current_user():
    """Get current user information"""
    try:
        total_chats = ChatHistory.query.filter_by(user_id=current_user.id).count()
        
        return jsonify({
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email,
            'created_at': current_user.created_at.isoformat() if current_user.created_at else None,
            'total_chats': total_chats,
            'success': True
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    """Main chat endpoint - Optimized for Q3_K_S"""
    print(f"\n=== API CHAT CALLED ===")
    print(f"Using rag_system from app: {rag_system.__class__.__name__}")
    start_time = datetime.now()
    
    try:
        data = request.json
        user_query = data.get('message', '').strip()
        session_id = data.get('session_id', generate_session_id())
        
        if not user_query:
            return jsonify({'error': 'Empty message', 'success': False}), 400
        
        # Sanitize input
        user_query = sanitize_input(user_query, max_length=1000)
        
        # Check for emergency
        is_emergency, emergency_type, keyword = safety_checker.check_emergency(user_query)
        if is_emergency:
            processing_time = (datetime.now() - start_time).total_seconds()
            emergency_response = create_emergency_response([keyword])
            
            # Save emergency chat
            save_chat_to_history(
                user_id=current_user.id,
                user_query=user_query,
                bot_response=emergency_response,
                intent='emergency',
                confidence=1.0,
                entities=[{'type': 'emergency', 'keyword': keyword}],
                processing_time=processing_time
            )
            
            return jsonify({
                'response': emergency_response,
                'emergency': True,
                'intent': 'emergency',
                'confidence': 1.0,
                'processing_time': processing_time,
                'session_id': session_id,
                'success': True
            })
        
        # Validate query
        is_valid, validation_msg = safety_checker.validate_query(user_query)
        if not is_valid:
            return jsonify({'error': validation_msg, 'success': False}), 400
        
        # Check for PII - FIXED: Now masks instead of replacing entire query
        has_pii, pii_types, sanitized_query = contains_pii(user_query)
        if has_pii:
            print(f"⚠️ PII detected in query: {pii_types}")
            user_query = sanitized_query  # Use masked version
            log_activity(current_user.id, "PII_DETECTED", f"Types: {pii_types}")
        
        # Process with RAG system
        print(f"\n🔍 CHAT DEBUG: Calling RAG for: {user_query}")
        print(f"🔍 CHAT DEBUG: RAG has LLaMA: {rag_system.llama_model is not None}")
        
        rag_start = datetime.now()
        result = rag_system.query(user_query)
        rag_time = (datetime.now() - rag_start).total_seconds()
        
        print(f"🔍 CHAT DEBUG: Got response from: {result.get('model', 'unknown')}")
        print(f"🔍 CHAT DEBUG: Response preview: {result.get('response', '')[:200]}...")
        
        # Extract results
        response = result.get('response', '')
        intent = result.get('intent', 'general_health')
        confidence = result.get('confidence', 0.5)
        retrieved_info = result.get('retrieved_info', [])
        total_time = (datetime.now() - start_time).total_seconds()
        
        # Save to database
        chat_record = save_chat_to_history(
            user_id=current_user.id,
            user_query=user_query,
            bot_response=response,
            intent=intent,
            confidence=confidence,
            entities=retrieved_info,
            processing_time=total_time
        )
        
        log_activity(current_user.id, "CHAT", 
                    f"Query: {user_query[:50]}... | Time: {total_time:.2f}s | Intent: {intent}")
        
        return jsonify({
            'response': response,
            'intent': intent,
            'confidence': confidence,
            'processing_time': total_time,
            'rag_time': rag_time,
            'retrieved_info': retrieved_info[:3],
            'session_id': session_id,
            'chat_id': chat_record.id if chat_record else None,
            'model': result.get('model', 'unknown'),
            'optimized': result.get('optimized', False),
            'success': True
        })
        
    except Exception as e:
        print(f"❌ Chat error: {e}")
        traceback.print_exc()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Save error to history
        error_response = """I apologize, but I encountered an error processing your request.

Please try:
1. Rephrasing your question
2. Asking about general health topics
3. Consulting a healthcare professional for specific concerns

**Medical Disclaimer:** I provide general health information only. For personal medical advice, please consult with a doctor."""
        
        save_chat_to_history(
            user_id=current_user.id,
            user_query=user_query if 'user_query' in locals() else 'Error',
            bot_response=error_response,
            intent='error',
            confidence=0.0,
            processing_time=processing_time
        )
        
        return jsonify({
            'error': 'Sorry, I encountered an error. Please try again.',
            'success': False,
            'processing_time': processing_time
        }), 500

@app.route('/api/history')
@login_required
def get_history():
    """Get chat history with pagination"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '').strip()
        
        # Build query
        query = ChatHistory.query.filter_by(user_id=current_user.id)
        
        # Apply search filter
        if search:
            query = query.filter(
                (ChatHistory.user_query.contains(search)) |
                (ChatHistory.bot_response.contains(search))
            )
        
        # Get paginated results
        history = query.order_by(ChatHistory.timestamp.desc()).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        # Format response
        history_list = []
        for record in history.items:
            history_list.append({
                'id': record.id,
                'user_query': record.user_query,
                'bot_response': record.bot_response,
                'timestamp': record.timestamp.isoformat(),
                'intent': record.intent,
                'confidence': record.confidence,
                'processing_time': record.processing_time,
                'entities': json.loads(record.entities) if record.entities else []
            })
        
        return jsonify({
            'history': history_list,
            'pagination': {
                'page': history.page,
                'per_page': history.per_page,
                'total_pages': history.pages,
                'total_records': history.total,
                'has_next': history.has_next,
                'has_prev': history.has_prev
            },
            'success': True
        })
        
    except Exception as e:
        print(f"❌ History error: {e}")
        return jsonify({'error': 'Failed to load history', 'success': False}), 500

@app.route('/api/debug_stats')
@login_required
def debug_stats():
    """Debug endpoint to see raw statistics"""
    from database.models import ChatHistory, User
    
    # Get current user
    print(f"🔴 DEBUG: Current user = {current_user.id} - {current_user.username}")
    
    # Get all chats for this user
    user_chats = ChatHistory.query.filter_by(user_id=current_user.id).all()
    
    result = {
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'email': current_user.email
        },
        'database_counts': {
            'total_users': User.query.count(),
            'total_chats_all': ChatHistory.query.count(),
            'user_chats': len(user_chats)
        },
        'user_chats_detail': [
            {
                'id': chat.id,
                'query': chat.user_query[:50] + '...',
                'intent': chat.intent,
                'confidence': chat.confidence,
                'timestamp': chat.timestamp.isoformat() if chat.timestamp else None
            }
            for chat in user_chats[:10]  # First 10
        ],
        'stats': get_user_statistics(current_user.id)
    }
    
    return jsonify(result)

@app.route('/api/analytics')
@login_required
def get_analytics():
    """Get user analytics"""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Calculate date range
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        # Get analytics data
        analytics = UserAnalytics.query.filter(
            UserAnalytics.user_id == current_user.id,
            UserAnalytics.date >= start_date,
            UserAnalytics.date <= end_date
        ).order_by(UserAnalytics.date.desc()).all()
        
        # Get chat statistics
        total_chats = ChatHistory.query.filter_by(user_id=current_user.id).count()
        
        avg_confidence_result = db.session.query(
            db.func.avg(ChatHistory.confidence)
        ).filter_by(user_id=current_user.id).scalar()
        
        avg_confidence = round((avg_confidence_result or 0) * 100, 2)
        
        # Get most common intent
        most_common = db.session.query(
            ChatHistory.intent,
            db.func.count(ChatHistory.intent).label('count')
        ).filter_by(user_id=current_user.id)\
         .group_by(ChatHistory.intent)\
         .order_by(db.desc('count'))\
         .first()
        
        most_common_intent = most_common[0] if most_common else None
        
        # Format daily stats
        daily_stats = []
        for a in analytics:
            daily_stats.append({
                'date': a.date.isoformat(),
                'chats': a.total_chats,
                'intents': json.loads(a.common_intents) if a.common_intents else {}
            })
        
        # Calculate insights
        insights = generate_insights(daily_stats, most_common_intent)
        
        return jsonify({
            'summary': {
                'total_chats': total_chats,
                'avg_confidence': avg_confidence,
                'most_common_intent': most_common_intent,
                'active_days': len(daily_stats),
                'period_days': days
            },
            'daily_stats': daily_stats,
            'insights': insights,
            'success': True
        })
        
    except Exception as e:
        print(f"❌ Analytics error: {e}")
        return jsonify({'error': 'Failed to load analytics', 'success': False}), 500
    
@app.route('/api/dashboard/stats')
@login_required
def get_dashboard_stats():
    """Get dashboard statistics for immediate load"""
    try:
        stats = get_user_statistics(current_user.id)
        
        # Get recent chats for activity chart
        recent_chats = ChatHistory.query.filter_by(
            user_id=current_user.id
        ).order_by(ChatHistory.timestamp.desc()).limit(50).all()
        
        # Format chart data
        activity_data = []
        for i, chat in enumerate(recent_chats[:7][::-1]):  # Last 7 chats
            activity_data.append({
                'date': chat.timestamp.strftime('%m-%d'),
                'chats': i + 1  # Simple count for demo
            })
        
        return jsonify({
            'stats': stats,
            'activity': activity_data,
            'timestamp': datetime.now().isoformat(),
            'success': True
        })
        
    except Exception as e:
        print(f"❌ Dashboard stats error: {e}")
        return jsonify({'error': 'Failed to load dashboard stats', 'success': False}), 500

@app.route('/api/chart_data')
@login_required
def get_chart_data():
    """Get chart data for dashboard"""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Calculate date range
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        # Get analytics data
        analytics = UserAnalytics.query.filter(
            UserAnalytics.user_id == current_user.id,
            UserAnalytics.date >= start_date,
            UserAnalytics.date <= end_date
        ).order_by(UserAnalytics.date.asc()).all()
        
        # Format chart data
        daily_stats = []
        for a in analytics[-7:]:  # Last 7 days for activity chart
            daily_stats.append({
                'date': a.date.isoformat(),
                'chats': a.total_chats,
                'intents': json.loads(a.common_intents) if a.common_intents else {}
            })
        
        # Get intent distribution
        intent_counts = {}
        for a in analytics:
            intents = json.loads(a.common_intents) if a.common_intents else {}
            for intent, count in intents.items():
                intent_counts[intent] = intent_counts.get(intent, 0) + count
        
        return jsonify({
            'activity_data': {
                'labels': [day['date'][5:10] for day in daily_stats],  # MM-DD format
                'data': [day['chats'] for day in daily_stats]
            },
            'intent_data': {
                'labels': [intent.replace('_', ' ').title() for intent in intent_counts.keys()],
                'data': list(intent_counts.values()),
                'colors': ['#667eea', '#f093fb', '#4facfe', '#43e97b', '#fa709a']
            },
            'success': True
        })
        
    except Exception as e:
        print(f"❌ Chart data error: {e}")
        return jsonify({'error': 'Failed to load chart data', 'success': False}), 500

@app.route('/api/download_history')
@login_required
def download_history():
    """Download chat history as CSV"""
    try:
        # Get all history for user
        history = ChatHistory.query.filter_by(user_id=current_user.id)\
            .order_by(ChatHistory.timestamp.desc())\
            .all()
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'Timestamp', 'User Query', 'AI Response', 
            'Intent', 'Confidence', 'Processing Time (s)'
        ])
        
        # Write data
        for record in history:
            writer.writerow([
                record.id,
                record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                record.user_query[:200],
                record.bot_response[:200],
                record.intent or 'N/A',
                f"{record.confidence * 100:.1f}%" if record.confidence else 'N/A',
                f"{record.processing_time:.2f}" if record.processing_time else 'N/A'
            ])
        
        output.seek(0)
        
        # Create filename
        filename = f"medai_history_{current_user.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        log_activity(current_user.id, "DOWNLOAD_HISTORY", filename)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        print(f"❌ Download error: {e}")
        return jsonify({'error': 'Failed to download history'}), 500

@app.route('/api/delete_history/<int:record_id>', methods=['DELETE'])
@login_required
def delete_history_record(record_id):
    """Delete a specific chat record"""
    try:
        record = ChatHistory.query.get(record_id)
        
        if not record:
            return jsonify({'error': 'Record not found', 'success': False}), 404
        
        if record.user_id != current_user.id:
            return jsonify({'error': 'Unauthorized', 'success': False}), 403
        
        db.session.delete(record)
        db.session.commit()
        
        log_activity(current_user.id, "DELETE_HISTORY", f"Record ID: {record_id}")
        
        return jsonify({
            'message': 'Record deleted successfully',
            'success': True
        }), 200
        
    except Exception as e:
        print(f"❌ Delete error: {e}")
        return jsonify({'error': 'Failed to delete record', 'success': False}), 500

@app.route('/api/clear_history', methods=['DELETE'])
@login_required
def clear_all_history():
    """Clear all chat history for user"""
    try:
        # Get confirmation from request
        data = request.json if request.is_json else {}
        confirm = data.get('confirm', False)
        
        if not confirm:
            return jsonify({
                'error': 'Confirmation required. Send {"confirm": true} to clear all history.',
                'success': False
            }), 400
        
        # Delete all user's chat history
        deleted_count = ChatHistory.query.filter_by(user_id=current_user.id).delete()
        
        # Reset analytics
        UserAnalytics.query.filter_by(user_id=current_user.id).delete()
        
        db.session.commit()
        
        log_activity(current_user.id, "CLEAR_ALL_HISTORY", f"Deleted {deleted_count} records")
        
        return jsonify({
            'message': f'Successfully deleted {deleted_count} chat records',
            'deleted_count': deleted_count,
            'success': True
        }), 200
        
    except Exception as e:
        print(f"❌ Clear history error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to clear history', 'success': False}), 500

@app.route('/api/system/status')
def system_status():
    """Get system status - FIXED: Safe attribute checking"""
    try:
        # Get model info if available - FIXED: Safe attribute check
        model_info = {}
        if (rag_system and 
            hasattr(rag_system, 'llama_model') and 
            rag_system.llama_model and
            hasattr(rag_system.llama_model, 'get_model_info')):
            
            model_info = rag_system.llama_model.get_model_info()
        
        # Get batch size from config
        batch_size = app.config.get('LLAMA_BATCH_SIZE', 384)
        
        return jsonify({
            'status': 'online',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0',
            'optimization': 'Q3_K_S (3.2GB)',
            'system': {
                'cuda_available': system_info.get('cuda_available', False),
                'vram_gb': system_info.get('vram_gb', 0),
                'ram_available_gb': system_info.get('ram_available_gb', 0),
            },
            'models': {
                'llama_loaded': ml_models_loaded and rag_system.llama_model is not None,
                'embedding_model': app.config['EMBEDDING_MODEL'],
                'context_size': app.config['LLAMA_CONTEXT_SIZE'],
                'gpu_layers': app.config['LLAMA_N_GPU_LAYERS'],
                'batch_size': batch_size,  # FIXED: Include batch size
                **model_info
            },
            'database': 'connected',
            'success': True
        })
    except Exception as e:
        return jsonify({'status': 'error', 'error': str(e), 'success': False}), 500

# ============================================
# SOCKET.IO EVENT HANDLERS
# ============================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection for real-time updates"""
    try:
        if current_user.is_authenticated:
            # Join a room specific to this user for private updates
            join_room(f'user_{current_user.id}')
            print(f"📡 Client connected for user {current_user.id}")
            
            # Send immediate stats on connection
            stats = get_user_statistics(current_user.id)
            emit('dashboard_update', {
                'user_id': current_user.id,
                'stats': stats,
                'type': 'initial_load'
            }, room=f'user_{current_user.id}')
    except Exception as e:
        print(f"⚠️ SocketIO connect error: {e}")

@app.route('/api/system/health')
def health_check():
    """Health check endpoint - FIXED: SQLAlchemy 2.x compatibility"""
    try:
        # FIXED: Use text() for SQLAlchemy 2.x compatibility
        from sqlalchemy import text
        db.session.execute(text('SELECT 1'))
        
        # Check ML models
        model_status = 'loaded' if ml_models_loaded else 'fallback'
        if rag_system and hasattr(rag_system, 'llama_model'):
            model_status = 'llama_loaded' if rag_system.llama_model else 'fallback'
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'checks': {
                'database': 'ok',
                'models': model_status,
                'memory': 'ok'
            }
        })
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    log_activity(current_user.id, "LOGOUT", "User logged out")
    logout_user()
    return redirect(url_for('index'))

# ============================================
# Error Handlers
# ============================================

@app.errorhandler(404)
def not_found_error(error):
    """404 Error Handler"""
    return jsonify({
        'error': 'Page not found',
        'message': 'The requested page does not exist.',
        'success': False
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500 Error Handler"""
    print(f"❌ Internal server error: {error}")
    return jsonify({
        'error': 'Internal server error',
        'message': 'Something went wrong on our end. Please try again later.',
        'success': False
    }), 500

@app.errorhandler(401)
def unauthorized_error(error):
    """401 Error Handler"""
    return jsonify({
        'error': 'Unauthorized',
        'message': 'Please log in to access this page.',
        'success': False,
        'redirect': '/login'
    }), 401

@app.errorhandler(413)
def request_entity_too_large(error):
    """413 Error Handler"""
    return jsonify({
        'error': 'File too large',
        'message': 'The uploaded file exceeds the maximum allowed size.',
        'success': False
    }), 413

# ============================================
# Application Entry Point - CORRECTED
# ============================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🏥 AI Medical Chatbot Ready! - Q3_K_M OPTIMIZED")
    print("="*70)
    print(f"📁 Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print(f"🔐 Debug Mode: {app.config['DEBUG']}")
    print(f"🤖 ML Models: {'✅ LLaMA-3 8B Q3_K_M (3.74GB)' if ml_models_loaded else '⚠️ Fallback Mode'}")
    print(f"📡 Real-time dashboard: ENABLED (Socket.IO)")
    
    if ml_models_loaded:
        print(f"   • Context: {app.config['LLAMA_CONTEXT_SIZE']} tokens")
        print(f"   • GPU Layers: {app.config['LLAMA_N_GPU_LAYERS']}")
        print(f"   • Batch Size: {app.config['LLAMA_BATCH_SIZE']}")
        print(f"   • Max Tokens: {app.config['LLAMA_MAX_TOKENS']}")
        print(f"   • Embeddings: {app.config['EMBEDDING_MODEL']}")
    
    print(f"💻 System: Hybrid CPU+GPU mode (26 layers on GPU)")
    print(f"📊 Available RAM: {system_info.get('ram_available_gb', 0):.1f}GB")
    
    print("="*70)
    print("🌐 Server running at: http://localhost:5000")
    print("📡 Real-time dashboard: http://localhost:5000/dashboard")
    print("📊 System Status: http://localhost:5000/api/system/status")
    print("❤️  Health Check: http://localhost:5000/api/system/health")
    print("="*70 + "\n")
    
    # Create necessary directories
    for directory in ['uploads', 'data/vector_db', 'data/medical_knowledge', 'models']:
        os.makedirs(directory, exist_ok=True)
    
    # Run application WITH SOCKET.IO
    try:
        socketio.run(
            app,
            debug=app.config['DEBUG'],
            host='0.0.0.0',
            port=5000,
            allow_unsafe_werkzeug=True,
            use_reloader=False  # Important for memory management
        )
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("   1. Check if port 5000 is available")
        print("   2. Run as administrator")
        print("   3. Check firewall settings")
        sys.exit(1)