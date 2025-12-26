"""
PII (Personally Identifiable Information) Handler
Properly masks PII while preserving query semantics
"""
import re
from typing import Tuple, List, Optional
import hashlib

class PIIHandler:
    """Handle PII detection and masking"""
    
    def __init__(self):
        # PII patterns with better detection
        self.patterns = {
            'email': {
                'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'mask': '[EMAIL_{hash}]'
            },
            'phone': {
                'pattern': r'\b(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}\b',
                'mask': '[PHONE_{hash}]'
            },
            'ssn': {
                'pattern': r'\b\d{3}[-.]?\d{2}[-.]?\d{4}\b',
                'mask': '[SSN_{hash}]'
            },
            'credit_card': {
                'pattern': r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',
                'mask': '[CARD_{hash}]'
            }
        }
    
    def detect_and_mask(self, text: str) -> Tuple[str, List[str]]:
        """
        Detect and mask PII in text
        Returns: (masked_text, detected_types)
        """
        if not text:
            return text, []
        
        masked_text = text
        detected_types = []
        
        for pii_type, config in self.patterns.items():
            pattern = config['pattern']
            mask_template = config['mask']
            
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if matches:
                detected_types.append(pii_type)
                
                for match in matches:
                    pii_value = match.group()
                    
                    pii_hash = hashlib.md5(pii_value.encode()).hexdigest()[:8]
                    mask = mask_template.format(hash=pii_hash)
                    masked_text = masked_text.replace(pii_value, mask)
        
        return masked_text, detected_types
    
    def contains_pii(self, text: str) -> Tuple[bool, List[str]]:
        """Check if text contains PII without masking"""
        detected_types = []
        
        for pii_type, config in self.patterns.items():
            if re.search(config['pattern'], text, re.IGNORECASE):
                detected_types.append(pii_type)
        
        return len(detected_types) > 0, detected_types

# Singleton instance
pii_handler = PIIHandler()