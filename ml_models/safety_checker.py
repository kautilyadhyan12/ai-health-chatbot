import re
from transformers import pipeline

class SafetyChecker:
    def __init__(self):
        # Emergency keywords
        self.emergency_keywords = [
            'heart attack', 'stroke', 'suicide', 'severe pain',
            'bleeding heavily', 'can\'t breathe', 'unconscious',
            'chest pain', 'shortness of breath', 'sudden paralysis',
            'choking', 'overdose', 'poisoning', 'seizure'
        ]
        
        # High-risk symptoms
        self.high_risk_symptoms = [
            'severe headache', 'high fever', 'seizure',
            'broken bone', 'deep cut', 'poisoning',
            'difficulty breathing', 'chest pressure', 'paralysis'
        ]
        
       
        try:
            self.toxicity_classifier = pipeline(
                "text-classification", 
                model="unitary/toxic-bert",
                device=-1 
            )
        except:
            self.toxicity_classifier = None
    
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
        # Check length
        if len(text) < 3:
            return False, "Query too short. Please provide more details."
        
        if len(text) > 500:
            return False, "Query too long. Please keep it under 500 characters."
        
        # Check for inappropriate content
        inappropriate_patterns = [
            r'\b(diagnose me|prescribe me|cure me|treat me)\b',
            r'\b(suicide|kill myself|end my life|self-harm)\b',
            r'\b(overdose|poison|illegal drugs|abuse)\b',
            r'\b(hack|exploit|virus|malware)\b'
        ]
        
        for pattern in inappropriate_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return False, "This query contains inappropriate requests. Please consult a healthcare professional directly."
        
        # Check toxicity (optional)
        if self.toxicity_classifier:
            try:
                result = self.toxicity_classifier(text[:512])[0]
                if result['label'] == 'toxic' and result['score'] > 0.8:
                    return False, "This query appears to be inappropriate."
            except:
                pass
        
        return True, "Valid query"
    
    def contains_pii(self, text):
        """Check for Personally Identifiable Information"""
        patterns = {
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'phone': r'\b(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b',
            'ssn': r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b',
            'credit_card': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'
        }
        
        found_pii = []
        for pii_type, pattern in patterns.items():
            if re.search(pattern, text):
                found_pii.append(pii_type)
        
        return len(found_pii) > 0, found_pii