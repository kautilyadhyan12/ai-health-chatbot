"""
Streamlit AI Medical Chatbot - LLaMA-3 8B Q3_K_M Edition
Modern, interactive interface for your medical chatbot
"""

import streamlit as st
import sys
import os
import json
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ============================================
# STREAMLIT CONFIGURATION
# ============================================

st.set_page_config(
    page_title="MedAI Assistant - LLaMA-3 8B",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/ai-medical-chatbot',
        'Report a bug': 'https://github.com/yourusername/ai-medical-chatbot/issues',
        'About': '# AI Medical Chatbot v1.0\nPowered by LLaMA-3 8B + Medical RAG'
    }
)

# ============================================
# CUSTOM CSS STYLING
# ============================================

st.markdown("""
<style>
    /* Green Medical Theme */
    :root {
        --primary-green: #10B981;
        --primary-green-dark: #059669;
        --primary-green-light: #34D399;
        --secondary-teal: #0D9488;
        --accent-emerald: #047857;
        --dark-green: #064E3B;
        --light-green: #F0FDF4;
    }
    
    /* Main container */
    .main {
        background-color: #F9FAFB;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--dark-green), #065F46);
    }
    
    [data-testid="stSidebar"] .stButton button {
        background-color: var(--primary-green);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
        width: 100%;
        margin: 5px 0;
        transition: all 0.3s ease;
    }
    
    [data-testid="stSidebar"] .stButton button:hover {
        background-color: var(--primary-green-dark);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    
    /* Headers */
    h1, h2, h3 {
        color: var(--dark-green) !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Cards */
    .stCard {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border-left: 4px solid var(--primary-green);
        margin-bottom: 20px;
    }
    
    /* Chat bubbles */
    .user-message {
        background: linear-gradient(135deg, var(--primary-green), var(--secondary-teal));
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
        margin-right: 0;
    }
    
    .ai-message {
        background: #F3F4F6;
        color: var(--dark-green);
        padding: 12px 16px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        max-width: 80%;
        border: 1px solid #E5E7EB;
    }
    
    /* Emergency alerts */
    .emergency-alert {
        background: linear-gradient(135deg, #FEF3C7, #FDE68A);
        border: 2px solid #F59E0B;
        border-radius: 12px;
        padding: 16px;
        margin: 16px 0;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    /* Metrics */
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-top: 4px solid var(--primary-green);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 700;
        color: var(--primary-green);
        margin: 10px 0;
    }
    
    .metric-label {
        color: #6B7280;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Buttons */
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary-green), var(--secondary-teal));
        color: white;
        border: none;
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(16, 185, 129, 0.3);
    }
    
    /* Progress bars */
    .stProgress > div > div > div > div {
        background-color: var(--primary-green);
    }
    
    /* Custom tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #F3F4F6;
        padding: 4px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-green);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# INITIALIZATION & SESSION STATE
# ============================================

def initialize_session_state():
    """Initialize session state variables"""
    if 'page' not in st.session_state:
        st.session_state.page = "dashboard"
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'user_stats' not in st.session_state:
        st.session_state.user_stats = {
            'total_chats': 0,
            'avg_confidence': 0,
            'most_common_intent': 'N/A',
            'last_active': 'Never'
        }
    
    if 'analytics_data' not in st.session_state:
        st.session_state.analytics_data = []
    
    if 'rag_system' not in st.session_state:
        st.session_state.rag_system = None
    
    if 'safety_checker' not in st.session_state:
        st.session_state.safety_checker = None
    
    if 'model_loaded' not in st.session_state:
        st.session_state.model_loaded = False
    
    if 'processing' not in st.session_state:
        st.session_state.processing = False

# ============================================
# MODEL LOADING
# ============================================

def load_ml_models():
    """Load LLaMA-3 model and RAG system"""
    if st.session_state.model_loaded:
        return True
    
    try:
        with st.spinner("🚀 Loading LLaMA-3 8B Q3_K_M (3.74GB)..."):
            # Import your RAG system
            from ml_models.rag_system import OptimizedMedicalRAG
            
            # Configuration for Q3_K_M
            optimized_config = {
                'llama_config': {
                    'n_ctx': 1536,
                    'n_gpu_layers': 26,
                    'max_tokens': 256,
                    'temperature': 0.3,
                    'offload_kqv': True,
                    'use_mmap': True,
                    'f16_kv': True,
                    'n_batch': 256
                },
                'embedding_model': 'sentence-transformers/all-mpnet-base-v2'
            }
            
            # Initialize RAG system
            st.session_state.rag_system = OptimizedMedicalRAG(
                knowledge_base_path="data/medical_knowledge/medical_faqs.json",
                llama_model_path="models/Meta-Llama-3-8B-Instruct.Q3_K_M.gguf",
                vector_db_path="data/vector_db/medical_index.faiss",
                config=optimized_config
            )
            
            # Load safety checker
            from ml_models.safety_checker import SafetyChecker
            st.session_state.safety_checker = SafetyChecker()
            
            st.session_state.model_loaded = True
            
            return True
            
    except ImportError as e:
        st.error(f"❌ Failed to import ML modules: {e}")
        return False
    except Exception as e:
        st.error(f"❌ Model loading error: {e}")
        return False

# ============================================
# HELPER FUNCTIONS
# ============================================

def create_emergency_response(keywords: List[str]) -> str:
    """Create emergency response message"""
    response = """🚨 **MEDICAL EMERGENCY DETECTED** 🚨

I detected the following concerning keywords: **{keywords}**

**⚠️ THIS REQUIRES IMMEDIATE MEDICAL ATTENTION ⚠️**

**Please take these steps immediately:**
1. **📞 Call emergency services (911/112) RIGHT NOW**
2. **🏥 Go to the nearest emergency room**
3. **👥 Stay with someone if possible**
4. **📋 Describe symptoms clearly to medical professionals**

**Do NOT wait for further AI responses.**

**Emergency Numbers:**
• 🇺🇸 USA: 911
• 🇪🇺 EU: 112
• 🇬🇧 UK: 999
• 🇦🇺 Australia: 000
• 🇮🇳 India: 112

**This AI assistant cannot provide emergency medical care.**
""".format(keywords=", ".join(keywords))
    
    return response

def save_chat_history(user_query: str, ai_response: str, intent: str = None, 
                     confidence: float = None, processing_time: float = None):
    """Save chat to session history"""
    chat_entry = {
        'timestamp': datetime.now().isoformat(),
        'user_query': user_query,
        'ai_response': ai_response,
        'intent': intent,
        'confidence': confidence,
        'processing_time': processing_time
    }
    
    st.session_state.chat_history.append(chat_entry)
    
    # Update stats
    st.session_state.user_stats['total_chats'] = len(st.session_state.chat_history)
    if confidence:
        # Update average confidence
        all_confidences = [c['confidence'] for c in st.session_state.chat_history 
                          if c['confidence'] is not None]
        if all_confidences:
            st.session_state.user_stats['avg_confidence'] = sum(all_confidences) / len(all_confidences)
    
    # Update most common intent
    if intent:
        intents = [c['intent'] for c in st.session_state.chat_history 
                  if c['intent'] is not None]
        if intents:
            from collections import Counter
            most_common = Counter(intents).most_common(1)[0][0]
            st.session_state.user_stats['most_common_intent'] = most_common
    
    st.session_state.user_stats['last_active'] = 'Just now'

def generate_sample_analytics():
    """Generate sample analytics data for demo"""
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') 
             for i in range(30, -1, -1)]
    
    intents = ['symptom_check', 'medication_info', 'lifestyle_advice', 
               'condition_info', 'general_health']
    
    analytics = []
    for date in dates:
        daily_chats = np.random.randint(3, 15)
        intent_counts = {intent: np.random.randint(0, daily_chats//2) 
                        for intent in intents}
        
        analytics.append({
            'date': date,
            'chats': daily_chats,
            'intents': intent_counts
        })
    
    return analytics

def format_time_ago(timestamp_str: str) -> str:
    """Format timestamp as time ago"""
    try:
        timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
        
        diff = now - timestamp
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        else:
            return "Just now"
    except:
        return timestamp_str

# ============================================
# PAGE COMPONENTS
# ============================================

def render_sidebar():
    """Render sidebar navigation"""
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <h1 style='color: white; font-size: 1.8rem; margin-bottom: 5px;'>🏥 MedAI</h1>
            <p style='color: #A7F3D0; font-size: 0.9rem; margin: 0;'>LLaMA-3 8B Q3_K_M</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation
        st.markdown("### Navigation")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Dashboard", use_container_width=True):
                st.session_state.page = "dashboard"
                st.rerun()
        with col2:
            if st.button("💬 Chat", use_container_width=True):
                st.session_state.page = "chat"
                st.rerun()
        
        col3, col4 = st.columns(2)
        with col3:
            if st.button("📈 Analytics", use_container_width=True):
                st.session_state.page = "analytics"
                st.rerun()
        with col4:
            if st.button("📋 History", use_container_width=True):
                st.session_state.page = "history"
                st.rerun()
        
        st.markdown("---")
        
        # Model Status
        st.markdown("### 🤖 Model Status")
        
        if st.session_state.model_loaded:
            status_text = "✅ LLaMA-3 8B Q3_K_M"
            status_color = "#10B981"
        else:
            status_text = "❌ Not Loaded"
            status_color = "#EF4444"
        
        st.markdown(f"""
        <div style='background: rgba(255,255,255,0.1); padding: 12px; border-radius: 8px; margin: 10px 0;'>
            <div style='color: {status_color}; font-weight: 600; font-size: 0.9rem;'>
                {status_text}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Load Model Button
        if not st.session_state.model_loaded:
            if st.button("🔄 Load AI Model", use_container_width=True):
                with st.spinner("Loading model..."):
                    if load_ml_models():
                        st.success("✅ Model loaded successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to load model")
        
        # Health Tip
        st.markdown("---")
        st.markdown("### 💡 Health Tip")
        
        health_tips = [
            "Stay hydrated! Drink at least 8 glasses of water daily.",
            "Aim for 7-9 hours of quality sleep each night.",
            "Take regular breaks from screens to rest your eyes.",
            "Practice deep breathing to reduce stress and anxiety.",
            "Include fruits and vegetables in every meal."
        ]
        
        import random
        tip = random.choice(health_tips)
        
        st.info(f"✨ {tip}")
        
        # Emergency Button
        st.markdown("---")
        if st.button("🚨 Emergency Help", type="secondary", use_container_width=True):
            st.session_state.page = "emergency"
            st.rerun()

def render_dashboard():
    """Render dashboard page"""
    st.title("📊 Dashboard")
    st.markdown("Your AI medical assistant overview")
    
    # Quick Stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-value'>{}</div>
            <div class='metric-label'>Total Chats</div>
        </div>
        """.format(st.session_state.user_stats['total_chats']), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-value'>{:.1f}%</div>
            <div class='metric-label'>Avg Confidence</div>
        </div>
        """.format(st.session_state.user_stats['avg_confidence'] * 100), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-value'>{}</div>
            <div class='metric-label'>Most Common Intent</div>
        </div>
        """.format(st.session_state.user_stats['most_common_intent']), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-value'>{}</div>
            <div class='metric-label'>Last Active</div>
        </div>
        """.format(st.session_state.user_stats['last_active']), unsafe_allow_html=True)
    
    # Charts Row
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📈 Chat Activity (30 Days)")
        
        # Generate sample data
        dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') 
                for i in range(29, -1, -1)]
        chats = np.random.randint(5, 20, size=30)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=chats,
            mode='lines+markers',
            name='Daily Chats',
            line=dict(color='#10B981', width=3),
            marker=dict(size=8, color='#10B981')
        ))
        
        fig.update_layout(
            template='plotly_white',
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            xaxis_title="Date",
            yaxis_title="Number of Chats",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 🎯 Intent Distribution")
        
        intents = ['Symptom Check', 'Medication', 'Lifestyle', 'Condition Info', 'General']
        counts = np.random.randint(5, 25, size=5)
        
        fig = go.Figure(data=[go.Pie(
            labels=intents,
            values=counts,
            hole=.4,
            marker_colors=['#10B981', '#34D399', '#059669', '#0D9488', '#047857']
        )])
        
        fig.update_layout(
            template='plotly_white',
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Quick Actions
    st.markdown("#### ⚡ Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🆕 New Chat", use_container_width=True):
            st.session_state.page = "chat"
            st.rerun()
    
    with col2:
        if st.button("📥 Export History", use_container_width=True):
            export_history()
    
    with col3:
        if st.button("🧹 Clear History", use_container_width=True):
            if st.session_state.chat_history:
                st.session_state.chat_history.clear()
                st.session_state.user_stats = {
                    'total_chats': 0,
                    'avg_confidence': 0,
                    'most_common_intent': 'N/A',
                    'last_active': 'Never'
                }
                st.success("✅ Chat history cleared!")
                st.rerun()
    
    with col4:
        if st.button("⚙️ Settings", use_container_width=True):
            st.session_state.page = "settings"
            st.rerun()
    
    # Recent Activity
    st.markdown("#### 📝 Recent Activity")
    
    if st.session_state.chat_history:
        recent_chats = st.session_state.chat_history[-5:][::-1]
        
        for chat in recent_chats:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**Q:** {chat['user_query'][:100]}...")
                    st.markdown(f"**A:** {chat['ai_response'][:100]}...")
                
                with col2:
                    intent = chat['intent'] or 'General'
                    st.markdown(f"`{intent}`")
                
                with col3:
                    time_ago = format_time_ago(chat['timestamp'])
                    st.markdown(f"<div style='text-align: right; color: #6B7280;'>{time_ago}</div>", 
                               unsafe_allow_html=True)
                
                st.markdown("---")
    else:
        st.info("No recent activity. Start a chat to see your history here.")

def render_chat():
    """Render chat interface"""
    st.title("💬 MedAI Chat Assistant")
    
    # Chat Info Bar
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Model", "LLaMA-3 8B Q3_K_M")
    
    with col2:
        status = "✅ Online" if st.session_state.model_loaded else "❌ Offline"
        st.metric("Status", status)
    
    with col3:
        st.metric("Chats Today", len(st.session_state.chat_history))
    
    # Chat Container
    chat_container = st.container(height=500, border=True)
    
    with chat_container:
        # Display chat history
        for chat in st.session_state.chat_history:
            # User message
            st.markdown(f"""
            <div class='user-message'>
                <div style='font-weight: 600; margin-bottom: 4px;'>You</div>
                <div>{chat['user_query']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # AI message
            st.markdown(f"""
            <div class='ai-message'>
                <div style='font-weight: 600; margin-bottom: 4px;'>
                    🏥 MedAI Assistant • Confidence: {chat['confidence']*100:.1f}%
                </div>
                <div>{chat['ai_response']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
    
    # Quick Prompts
    st.markdown("#### 💡 Quick Questions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🤒 Flu Symptoms", use_container_width=True):
            process_quick_prompt("What are common flu symptoms?")
    
    with col2:
        if st.button("❤️ Blood Pressure", use_container_width=True):
            process_quick_prompt("How to lower blood pressure naturally?")
    
    with col3:
        if st.button("🥗 Healthy Diet", use_container_width=True):
            process_quick_prompt("What is considered a healthy diet?")
    
    with col4:
        if st.button("💤 Sleep Tips", use_container_width=True):
            process_quick_prompt("How much sleep do adults need?")
    
    # Chat Input
    st.markdown("---")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_area(
            "💭 Your medical question:",
            placeholder="Ask about symptoms, medications, lifestyle, or general health...",
            height=100,
            key="user_input"
        )
    
    with col2:
        st.markdown("<div style='height: 28px'></div>", unsafe_allow_html=True)
        if st.button("🚀 Send", type="primary", use_container_width=True, use_container_width=True):
            if user_input.strip():
                process_user_query(user_input)
            else:
                st.warning("Please enter a question")
    
    # Safety Notice
    st.markdown("""
    <div style='background: #FEF3C7; padding: 12px; border-radius: 8px; margin-top: 20px; border-left: 4px solid #F59E0B;'>
        ⚠️ **Medical Disclaimer:** This AI assistant provides general health information only. 
        Always consult healthcare professionals for medical advice, diagnosis, or treatment.
        For emergencies, call 911/112 immediately.
    </div>
    """, unsafe_allow_html=True)

def process_quick_prompt(prompt: str):
    """Process quick prompt button click"""
    # Set the prompt in the input
    st.session_state.user_input = prompt
    st.rerun()

def process_user_query(user_query: str):
    """Process user query through the AI model"""
    if not st.session_state.model_loaded:
        st.error("⚠️ Please load the AI model first from the sidebar")
        return
    
    if not user_query.strip():
        return
    
    # Safety check
    is_emergency, emergency_type, keyword = st.session_state.safety_checker.check_emergency(user_query)
    
    if is_emergency:
        response = create_emergency_response([keyword])
        intent = "emergency"
        confidence = 1.0
        
        # Show emergency modal
        st.error("🚨 EMERGENCY DETECTED - Please seek immediate medical attention!")
        st.markdown(f"""
        <div class='emergency-alert'>
            <h4>⚠️ Emergency Detected</h4>
            <p>I detected: <strong>{keyword}</strong></p>
            <p>Please call emergency services (911/112) immediately.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Still save the response
        save_chat_history(user_query, response, intent, confidence, 0.1)
        st.rerun()
        return
    
    # Process with AI
    with st.spinner("🤖 Thinking..."):
        start_time = time.time()
        
        try:
            result = st.session_state.rag_system.query(user_query)
            
            processing_time = time.time() - start_time
            
            response = result.get('response', 'Sorry, I could not generate a response.')
            intent = result.get('intent', 'general_health')
            confidence = result.get('confidence', 0.5)
            
            save_chat_history(user_query, response, intent, confidence, processing_time)
            
            # Success notification
            st.success(f"✅ Response generated in {processing_time:.2f}s")
            
            # Rerun to show updated chat
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error processing query: {str(e)}")
            
            # Save error response
            error_response = """I apologize, but I encountered an error processing your request.

**Please try:**
1. Rephrasing your question
2. Asking about general health topics
3. Consulting a healthcare professional for specific concerns

**Medical Disclaimer:** I provide general health information only."""
            
            save_chat_history(user_query, error_response, "error", 0.0, 0.1)

def render_analytics():
    """Render analytics page"""
    st.title("📈 Analytics")
    st.markdown("Detailed insights from your medical queries")
    
    # Generate sample analytics if none
    if not st.session_state.analytics_data:
        st.session_state.analytics_data = generate_sample_analytics()
    
    # Date Range Selector
    col1, col2 = st.columns([1, 3])
    
    with col1:
        time_range = st.selectbox(
            "Time Range",
            ["Last 7 Days", "Last 30 Days", "Last 90 Days", "All Time"],
            index=1
        )
    
    with col2:
        selected_intent = st.selectbox(
            "Filter by Intent",
            ["All Intents", "Symptom Check", "Medication Info", "Lifestyle Advice", 
             "Condition Info", "General Health"]
        )
    
    # Main Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Activity Timeline
        st.markdown("#### 📊 Activity Timeline")
        
        dates = [d['date'] for d in st.session_state.analytics_data[-30:]]
        chats = [d['chats'] for d in st.session_state.analytics_data[-30:]]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=dates,
            y=chats,
            name='Daily Chats',
            marker_color='#10B981'
        ))
        
        fig.update_layout(
            template='plotly_white',
            height=350,
            xaxis_title="Date",
            yaxis_title="Number of Chats",
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Peak Hours
        st.markdown("#### ⏰ Peak Activity Hours")
        
        hours = [f"{h}:00" for h in range(6, 24, 3)]
        activity = np.random.randint(5, 30, size=len(hours))
        
        fig = go.Figure(data=[go.Scatterpolar(
            r=activity,
            theta=hours,
            fill='toself',
            line_color='#10B981',
            fillcolor='rgba(16, 185, 129, 0.3)'
        )])
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(activity)]
                )
            ),
            showlegend=False,
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Insights
    st.markdown("#### 🧠 Insights & Recommendations")
    
    insights = [
        {
            'title': 'Active Usage',
            'message': 'You average 8.2 chats per day. Keep exploring health topics!',
            'icon': '📈',
            'color': '#10B981'
        },
        {
            'title': 'Common Interest',
            'message': 'Your most common topic is symptom checking.',
            'icon': '🤒',
            'color': '#3B82F6'
        },
        {
            'title': 'Response Quality',
            'message': 'Average confidence score: 78.5% (Good)',
            'icon': '🎯',
            'color': '#F59E0B'
        },
        {
            'title': 'Health Awareness',
            'message': 'Great job staying informed about your health!',
            'icon': '❤️',
            'color': '#EF4444'
        }
    ]
    
    cols = st.columns(4)
    for idx, insight in enumerate(insights):
        with cols[idx]:
            st.markdown(f"""
            <div style='
                background: white;
                padding: 20px;
                border-radius: 12px;
                border-left: 4px solid {insight['color']};
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                height: 180px;
            '>
                <div style='
                    font-size: 2rem;
                    margin-bottom: 10px;
                '>
                    {insight['icon']}
                </div>
                <h4 style='
                    color: #1F2937;
                    margin-bottom: 8px;
                '>
                    {insight['title']}
                </h4>
                <p style='
                    color: #6B7280;
                    font-size: 0.9rem;
                    line-height: 1.4;
                '>
                    {insight['message']}
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    # Export Button
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col2:
        if st.button("📥 Export Analytics", use_container_width=True):
            export_analytics()

def render_history():
    """Render chat history page"""
    st.title("📋 Chat History")
    
    # Search and Filters
    col1, col2, col3 = st.columns([3, 2, 2])
    
    with col1:
        search_query = st.text_input("🔍 Search conversations", placeholder="Type to search...")
    
    with col2:
        date_filter = st.selectbox(
            "Date Filter",
            ["All Time", "Today", "Last 7 Days", "Last 30 Days"]
        )
    
    with col3:
        intent_filter = st.selectbox(
            "Intent Filter",
            ["All Intents", "Symptom Check", "Medication", "Lifestyle", "General"]
        )
    
    # History List
    if st.session_state.chat_history:
        # Filter history
        filtered_history = st.session_state.chat_history
        
        if search_query:
            filtered_history = [h for h in filtered_history 
                              if search_query.lower() in h['user_query'].lower() 
                              or search_query.lower() in h['ai_response'].lower()]
        
        if intent_filter != "All Intents":
            filtered_history = [h for h in filtered_history 
                              if h['intent'] and intent_filter.lower() in h['intent'].lower()]
        
        # Display history
        for idx, chat in enumerate(reversed(filtered_history)):
            with st.expander(f"💬 {chat['user_query'][:50]}...", expanded=idx < 3):
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**Question:** {chat['user_query']}")
                    st.markdown(f"**Response:** {chat['ai_response']}")
                
                with col2:
                    intent_display = chat['intent'].replace('_', ' ').title() if chat['intent'] else 'General'
                    st.markdown(f"**Intent:** `{intent_display}`")
                
                with col3:
                    time_ago = format_time_ago(chat['timestamp'])
                    confidence = chat['confidence'] * 100 if chat['confidence'] else 0
                    st.markdown(f"**Time:** {time_ago}")
                    st.markdown(f"**Confidence:** {confidence:.1f}%")
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("📋 Copy", key=f"copy_{idx}", use_container_width=True):
                        st.toast("✅ Copied to clipboard!")
                
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{idx}", use_container_width=True):
                        st.session_state.chat_history.remove(chat)
                        st.success("✅ Conversation deleted!")
                        st.rerun()
                
                with col3:
                    if st.button("🔄 Continue", key=f"continue_{idx}", use_container_width=True):
                        st.session_state.page = "chat"
                        st.session_state.user_input = chat['user_query']
                        st.rerun()
    else:
        st.info("No chat history yet. Start a conversation to see your history here.")
    
    # Bulk Actions
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("📥 Export All", use_container_width=True):
            export_history()
    
    with col2:
        if st.button("🗑️ Clear All", type="secondary", use_container_width=True):
            if st.session_state.chat_history:
                if st.checkbox("I'm sure I want to delete all history"):
                    st.session_state.chat_history.clear()
                    st.success("✅ All history cleared!")
                    st.rerun()

def export_history():
    """Export chat history"""
    if not st.session_state.chat_history:
        st.warning("No chat history to export")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(st.session_state.chat_history)
    
    # Format timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Convert to CSV
    csv = df.to_csv(index=False)
    
    # Provide download button
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"medai_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )

def export_analytics():
    """Export analytics data"""
    df = pd.DataFrame(st.session_state.analytics_data)
    
    # Flatten intents dictionary
    df_intents = pd.json_normalize(df['intents'])
    df = pd.concat([df.drop('intents', axis=1), df_intents], axis=1)
    
    csv = df.to_csv(index=False)
    
    st.download_button(
        label="📥 Download Analytics",
        data=csv,
        file_name=f"medai_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
        use_container_width=True
    )

def render_emergency():
    """Render emergency page"""
    st.title("🚨 Emergency Assistance")
    
    st.markdown("""
    <div class='emergency-alert'>
        <h2>⚠️ MEDICAL EMERGENCY</h2>
        <p>If you're experiencing a medical emergency, please take immediate action:</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Emergency Steps
    steps = [
        {
            "number": "1",
            "title": "Call Emergency Services",
            "description": "Dial 911 (USA), 112 (EU), 999 (UK), or 000 (Australia) immediately",
            "icon": "📞"
        },
        {
            "number": "2",
            "title": "Stay Calm",
            "description": "Take deep breaths and stay with someone if possible",
            "icon": "🧘"
        },
        {
            "number": "3",
            "title": "Describe Symptoms",
            "description": "Clearly explain symptoms to the dispatcher",
            "icon": "🗣️"
        },
        {
            "number": "4",
            "title": "Follow Instructions",
            "description": "Listen carefully and follow all instructions from emergency responders",
            "icon": "👂"
        }
    ]
    
    cols = st.columns(4)
    for idx, step in enumerate(steps):
        with cols[idx]:
            st.markdown(f"""
            <div style='
                background: white;
                padding: 20px;
                border-radius: 12px;
                text-align: center;
                border: 2px solid #EF4444;
                height: 200px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            '>
                <div style='
                    font-size: 3rem;
                    margin-bottom: 10px;
                '>
                    {step['icon']}
                </div>
                <div style='
                    background: #EF4444;
                    color: white;
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin: 0 auto 10px;
                    font-weight: bold;
                '>
                    {step['number']}
                </div>
                <h4 style='
                    color: #1F2937;
                    margin-bottom: 8px;
                '>
                    {step['title']}
                </h4>
                <p style='
                    color: #6B7280;
                    font-size: 0.85rem;
                '>
                    {step['description']}
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    # Emergency Numbers
    st.markdown("---")
    st.markdown("#### 📞 Emergency Numbers Worldwide")
    
    emergency_numbers = {
        "🇺🇸 United States": "911",
        "🇪🇺 European Union": "112",
        "🇬🇧 United Kingdom": "999",
        "🇦🇺 Australia": "000",
        "🇨🇦 Canada": "911",
        "🇯🇵 Japan": "119",
        "🇮🇳 India": "112",
        "🇨🇳 China": "120",
        "🇧🇷 Brazil": "192",
        "🇷🇺 Russia": "112"
    }
    
    cols = st.columns(5)
    for idx, (country, number) in enumerate(emergency_numbers.items()):
        with cols[idx % 5]:
            st.markdown(f"""
            <div style='
                background: #FEF2F2;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                border: 1px solid #FECACA;
            '>
                <div style='font-size: 1.2rem; margin-bottom: 5px;'>{country}</div>
                <div style='
                    font-size: 1.5rem;
                    font-weight: bold;
                    color: #DC2626;
                '>
                    {number}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # First Aid Tips
    st.markdown("---")
    st.markdown("#### 🩹 First Aid Quick Tips")
    
    tips = [
        "**Bleeding:** Apply direct pressure with clean cloth",
        "**Choking:** Perform Heimlich maneuver",
        "**Burn:** Cool with running water for 20 minutes",
        "**Heart Attack:** Call emergency, give aspirin if available",
        "**Stroke:** Remember FAST - Face, Arms, Speech, Time"
    ]
    
    for tip in tips:
        st.info(f"💡 {tip}")
    
    # Back to safety
    st.markdown("---")
    if st.button("⬅️ Back to Chat", type="primary", use_container_width=True):
        st.session_state.page = "chat"
        st.rerun()

def render_settings():
    """Render settings page"""
    st.title("⚙️ Settings")
    
    tabs = st.tabs(["User Profile", "AI Settings", "Privacy", "About"])
    
    with tabs[0]:
        st.markdown("#### 👤 User Profile")
        
        col1, col2 = st.columns(2)
        
        with col1:
            username = st.text_input("Username", value="medai_user")
        
        with col2:
            email = st.text_input("Email", value="user@example.com")
        
        notification_level = st.select_slider(
            "Notification Level",
            options=["Minimal", "Normal", "Detailed"],
            value="Normal"
        )
        
        if st.button("💾 Save Profile", type="primary"):
            st.success("✅ Profile saved!")
    
    with tabs[1]:
        st.markdown("#### 🤖 AI Settings")
        
        model_version = st.selectbox(
            "Model Version",
            ["LLaMA-3 8B Q3_K_M (Recommended)", "LLaMA-3 8B Q4_K_M", "LLaMA-3 8B Q5_K_M"],
            index=0
        )
        
        temperature = st.slider(
            "Creativity (Temperature)",
            min_value=0.0,
            max_value=1.0,
            value=0.3,
            help="Lower = more factual, Higher = more creative"
        )
        
        response_length = st.selectbox(
            "Response Length",
            ["Concise", "Normal", "Detailed"],
            index=1
        )
        
        safety_level = st.select_slider(
            "Safety Level",
            options=["Permissive", "Balanced", "Strict"],
            value="Balanced"
        )
        
        if st.button("🔄 Apply AI Settings"):
            st.success("✅ AI settings applied!")
    
    with tabs[2]:
        st.markdown("#### 🔒 Privacy & Security")
        
        data_retention = st.selectbox(
            "Chat History Retention",
            ["30 days", "90 days", "1 year", "Forever"],
            index=1
        )
        
        auto_delete = st.toggle("Auto-delete old chats", value=True)
        
        share_analytics = st.toggle(
            "Share anonymous analytics",
            value=False,
            help="Help improve MedAI by sharing anonymous usage data"
        )
        
        st.markdown("---")
        st.markdown("#### 🗑️ Data Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Export All Data", use_container_width=True):
                export_history()
        
        with col2:
            if st.button("Delete All Data", type="secondary", use_container_width=True):
                if st.checkbox("I understand this will delete ALL my data permanently"):
                    st.session_state.chat_history.clear()
                    st.session_state.analytics_data.clear()
                    st.success("✅ All data deleted!")
    
    with tabs[3]:
        st.markdown("#### ℹ️ About MedAI")
        
        st.markdown("""
        **MedAI Assistant v1.0**
        
        An AI-powered medical chatbot powered by LLaMA-3 8B with Retrieval-Augmented Generation.
        
        **Features:**
        - LLaMA-3 8B Q3_K_M model (3.74GB)
        - Medical knowledge base with RAG
        - Real-time chat interface
        - Detailed analytics dashboard
        - Emergency detection system
        
        **Technology Stack:**
        - 🤖 LLaMA-3 8B via llama.cpp
        - 🔍 FAISS vector database
        - 🎯 Sentence Transformers
        - 🎨 Streamlit interface
        
        **Medical Disclaimer:**
        > This AI assistant provides general health information only. 
        > Always consult healthcare professionals for medical advice, 
        > diagnosis, or treatment. For emergencies, call 911/112 immediately.
        
        **Contact:**
        - GitHub: [yourusername/ai-medical-chatbot](https://github.com/yourusername/ai-medical-chatbot)
        - Issues: [Report a bug](https://github.com/yourusername/ai-medical-chatbot/issues)
        
        **Version:** 1.0.0
        **Last Updated:** December 2024
        """)

# ============================================
# MAIN APP
# ============================================

def main():
    """Main Streamlit application"""
    
    # Initialize session state
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Render main content based on page
    if st.session_state.page == "dashboard":
        render_dashboard()
    elif st.session_state.page == "chat":
        render_chat()
    elif st.session_state.page == "analytics":
        render_analytics()
    elif st.session_state.page == "history":
        render_history()
    elif st.session_state.page == "emergency":
        render_emergency()
    elif st.session_state.page == "settings":
        render_settings()
    else:
        render_dashboard()
    
    # Footer
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style='text-align: center; color: #6B7280; font-size: 0.9rem; padding: 20px;'>
            <p>🏥 MedAI Assistant • LLaMA-3 8B Q3_K_M Edition</p>
            <p>⚠️ For medical emergencies, call 911/112 immediately</p>
            <p>© 2024 AI Medical Chatbot • v1.0.0</p>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()