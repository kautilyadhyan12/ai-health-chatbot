"""
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
    text = re.sub(r'[<>"'`;\\]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text

def calculate_confidence_score(similarity: float, has_entities: bool = False) -> float:
    confidence = similarity * 0.7
    if has_entities:
        confidence += 0.2
    return min(confidence, 1.0)

def generate_session_id() -> str:
    return str(uuid.uuid4())
