
"""
Setup script for AI Medical Chatbot
Fixes all issues and initializes the project with LLaMA-3 + RAG
"""

import os
import sys
import shutil
import subprocess

def create_directories():
    """Create all required directories"""
    directories = [
        'data/medical_knowledge',
        'data/vector_db',
        'models',
        'uploads',
        'model_cache',
        'utils'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def fix_safety_checker():
    """Fix the safety checker filename"""
    old_path = 'ml_models/saftey_checker.py'
    new_path = 'ml_models/safety_checker.py'
    
    if os.path.exists(old_path) and not os.path.exists(new_path):
        shutil.move(old_path, new_path)
        print(f"✅ Renamed {old_path} to {new_path}")
    elif os.path.exists(new_path):
        print(f"✅ Safety checker already exists at {new_path}")
    else:
        print(f"⚠️ Safety checker not found, creating placeholder")
        # Create minimal safety checker
        safety_content = '''import re

class SafetyChecker:
    def __init__(self):
        self.emergency_keywords = [
            'heart attack', 'stroke', 'suicide', 'severe pain',
            'bleeding heavily', 'can\\'t breathe', 'unconscious',
            'chest pain', 'shortness of breath', 'sudden paralysis'
        ]
    
    def check_emergency(self, text):
        text_lower = text.lower()
        for keyword in self.emergency_keywords:
            if keyword in text_lower:
                return True, "EMERGENCY_DETECTED", keyword
        return False, "SAFE", ""
    
    def validate_query(self, text):
        if len(text) < 3:
            return False, "Query too short"
        if len(text) > 500:
            return False, "Query too long"
        return True, "Valid query"
'''
        with open(new_path, 'w') as f:
            f.write(safety_content)

def create_utils_files():
    """Create utils files"""
    # Create helpers.py
    helpers_content = '''"""
Helper functions for AI Medical Chatbot
"""
import re
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import json

def format_timestamp(timestamp: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    return timestamp.strftime(format_str)

def sanitize_input(text: str, max_length: int = 1000) -> str:
    if not text:
        return ""
    text = text.strip()[:max_length]
    text = re.sub(r'[<>"\'`;\\\\]', '', text)
    text = re.sub(r'\\s+', ' ', text)
    return text

def calculate_confidence_score(similarity: float, has_entities: bool = False) -> float:
    confidence = similarity * 0.7
    if has_entities:
        confidence += 0.2
    return min(confidence, 1.0)

def generate_session_id() -> str:
    return str(uuid.uuid4())
'''
    
    with open('utils/helpers.py', 'w') as f:
        f.write(helpers_content)
    
    # Create validators.py
    validators_content = '''"""
Validation functions for AI Medical Chatbot
"""
import re
from typing import Tuple, Optional, List

def validate_email(email: str) -> Tuple[bool, str]:
    if not email:
        return False, "Email is required"
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False, "Invalid email"
    return True, "Valid email"

def validate_password(password: str) -> Tuple[bool, str]:
    if not password:
        return False, "Password is required"
    if len(password) < 6:
        return False, "Password too short"
    return True, "Valid password"

def contains_emergency_keywords(text: str) -> Tuple[bool, List[str]]:
    emergency_keywords = [
        'heart attack', 'stroke', 'chest pain', 'can\\'t breathe',
        'difficulty breathing', 'severe pain', 'unconscious'
    ]
    found = []
    text_lower = text.lower()
    for keyword in emergency_keywords:
        if keyword in text_lower:
            found.append(keyword)
    return len(found) > 0, found
'''
    
    with open('utils/validators.py', 'w') as f:
        f.write(validators_content)
    
    
    init_content = '''"""
Utilities package for AI Medical Chatbot
"""
from .helpers import *
from .validators import *

__all__ = [
    'format_timestamp',
    'sanitize_input',
    'calculate_confidence_score',
    'generate_session_id',
    'validate_email',
    'validate_password',
    'contains_emergency_keywords'
]
'''
    
    with open('utils/__init__.py', 'w') as f:
        f.write(init_content)
    
    print("✅ Created utils files")

def create_env_file():
    """Create .env file if not exists"""
    if not os.path.exists('.env'):
        env_content = '''SECRET_KEY=your-super-secret-key-change-this-in-production-2024
DATABASE_URL=sqlite:///medical_chatbot.db
DEBUG=True
FLASK_ENV=development
FLASK_APP=app.py
MODEL_PATH=./ml_models
UPLOAD_FOLDER=./uploads
SESSION_TYPE=filesystem
KNOWLEDGE_BASE_PATH=data/medical_knowledge/medical_faqs.json
VECTOR_DB_PATH=data/vector_db/medical_index.faiss
EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2
# LLAMA_MODEL_PATH=models/llama-3-8b-q4_k_m.gguf  # Uncomment after downloading
'''
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file")
    else:
        print("✅ .env file already exists")

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        print("⚠️ Please install manually: pip install -r requirements.txt")

def main():
    print("🔧 Setting up AI Medical Chatbot with LLaMA-3 + RAG...\n")
    
    try:
        fix_safety_checker()
        create_directories()
        create_utils_files()
        create_env_file()
        install_dependencies()
        
        print("\n" + "="*60)
        print("🎉 Setup complete!")
        print("="*60)
        print("\n📋 Next steps:")
        print("1. Download LLaMA-3 model:")
        print("   - Option A: Run 'python download_models.py'")
        print("   - Option B: Download manually from HuggingFace")
        print("   - Recommended: Meta-Llama-3-8B-Instruct.Q4_K_M.gguf")
        print("2. Update LLAMA_MODEL_PATH in .env file")
        print("3. Start the application: python app.py")
        print("4. Open browser: http://localhost:5000")
        print("\n⚠️ IMPORTANT:")
        print("- Change SECRET_KEY in .env for production!")
        print("- The first run will download embedding models (~400MB)")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()