"""
Validation functions for AI Medical Chatbot
"""
import re
from typing import Tuple, Optional, List

def validate_email(email: str) -> Tuple[bool, str]:
    if not email:
        return False, "Email is required"
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
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
        'heart attack', 'stroke', 'chest pain', 'can\'t breathe',
        'difficulty breathing', 'severe pain', 'unconscious'
    ]
    found = []
    text_lower = text.lower()
    for keyword in emergency_keywords:
        if keyword in text_lower:
            found.append(keyword)
    return len(found) > 0, found
