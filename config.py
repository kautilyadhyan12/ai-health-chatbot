"""
Configuration for AI Medical Chatbot - Optimized for Q3_K_M hybrid mode
SAFE FOR GTX 1650 4GB VRAM
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    
    # FLASK APPLICATION SETTINGS
    
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-super-secret-key-change-this-in-production-2024')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///medical_chatbot.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
   
    # LLaMA-3 8B Q3_K_M MODEL SETTINGS

    
    LLAMA_MODEL_PATH = os.getenv('LLAMA_MODEL_PATH', 'models/Meta-Llama-3-8B-Instruct.Q3_K_M.gguf')
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/all-mpnet-base-v2')
    
    
    LLAMA_CONTEXT_SIZE = int(os.getenv('LLAMA_CONTEXT_SIZE', 1536))  
    LLAMA_MAX_TOKENS = int(os.getenv('LLAMA_MAX_TOKENS', 256))      
    LLAMA_TEMPERATURE = float(os.getenv('LLAMA_TEMPERATURE', 0.3)) 
    LLAMA_TOP_P = float(os.getenv('LLAMA_TOP_P', 0.95))
    LLAMA_TOP_K = int(os.getenv('LLAMA_TOP_K', 40))
    LLAMA_REPEAT_PENALTY = float(os.getenv('LLAMA_REPEAT_PENALTY', 1.1))
    
   
    LLAMA_BATCH_SIZE = int(os.getenv('LLAMA_BATCH_SIZE', 256))
    LLAMA_N_GPU_LAYERS = int(os.getenv('LLAMA_N_GPU_LAYERS', 26))  
    
    
    LLAMA_OFFLOAD_KQV = os.getenv('LLAMA_OFFLOAD_KQV', 'True').lower() in ('true', '1', 't')
    LLAMA_USE_MMAP = os.getenv('LLAMA_USE_MMAP', 'True').lower() in ('true', '1', 't')
    LLAMA_F16_KV = os.getenv('LLAMA_F16_KV', 'True').lower() in ('true', '1', 't')
    
    
    # KNOWLEDGE BASE & VECTOR DATABASE
    
    VECTOR_DB_PATH = os.getenv('VECTOR_DB_PATH', 'data/vector_db/medical_index.faiss')
    KNOWLEDGE_BASE_PATH = os.getenv('KNOWLEDGE_BASE_PATH', 'data/medical_knowledge/medical_faqs.json')
    
    
    # SAFETY & CONTENT SETTINGS
   
    EMERGENCY_RESPONSE = os.getenv('EMERGENCY_RESPONSE', '⚠️ EMERGENCY DETECTED: Please seek immediate medical attention or call emergency services (911/112)!')
    DISCLAIMER = os.getenv('DISCLAIMER', 'Disclaimer: I am an AI assistant providing general health information. Always consult with healthcare professionals for medical advice, diagnosis, or treatment.')
    
    
    # APPLICATION SETTINGS
    
    DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    
    
    # SECURITY SETTINGS
    
    SESSION_COOKIE_SECURE = not DEBUG
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    
    # API SETTINGS
    
    API_RATE_LIMIT = os.getenv('API_RATE_LIMIT', '100 per day')
    
    @staticmethod
    def get_optimized_llama_config():
        """
        Get optimized LLaMA configuration for Q3_K_M hybrid mode.
        SAFE FOR GTX 1650 4GB VRAM
        """
        return {
            'n_gpu_layers': Config.LLAMA_N_GPU_LAYERS,  
            'n_ctx': Config.LLAMA_CONTEXT_SIZE,         
            'n_batch': Config.LLAMA_BATCH_SIZE,         
            'max_tokens': Config.LLAMA_MAX_TOKENS,      
            'temperature': Config.LLAMA_TEMPERATURE,    
            'top_p': Config.LLAMA_TOP_P,
            'top_k': Config.LLAMA_TOP_K,
            'repeat_penalty': Config.LLAMA_REPEAT_PENALTY,
            'offload_kqv': Config.LLAMA_OFFLOAD_KQV,
            'f16_kv': Config.LLAMA_F16_KV,
            'use_mmap': Config.LLAMA_USE_MMAP
        }
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        app.config.from_object(Config)
        
        # Create necessary directories
        directories = [
            'models',
            'data/vector_db',
            'data/medical_knowledge',
            app.config['UPLOAD_FOLDER']
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)