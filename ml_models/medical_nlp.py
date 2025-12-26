import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sentence_transformers import SentenceTransformer
import spacy
import warnings
warnings.filterwarnings('ignore')

class MedicalNLP:
    def __init__(self):
        self.fallback_mode = False
        self.tokenizer = None
        self.model = None
        self.sentence_model = None
        self.nlp = None
        
        try:
            
            self.clinical_bert_model = "emilyalsentzer/Bio_ClinicalBERT"
            self.tokenizer = AutoTokenizer.from_pretrained(self.clinical_bert_model)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.clinical_bert_model, 
                num_labels=5
            )
            
            # Sentence transformer for embeddings
            self.sentence_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
            
           
            self.nlp = self._load_spacy_model()
            
        except Exception as e:
            print(f"⚠️ MedicalNLP initialization error: {e}")
            self.fallback_mode = True
    
    def _load_spacy_model(self):
        """Load spaCy model with fallback"""
        try:
           
            return spacy.load("en_core_sci_sm")
        except:
            try:
                
                return spacy.load("en_core_web_sm")
            except:
                try:
                    
                    import subprocess
                    import sys
                    subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
                    return spacy.load("en_core_web_sm")
                except:
                    print("⚠️ spaCy model loading failed")
                    return None
    
    def get_embeddings(self, text):
        """Convert text to embeddings"""
        if self.fallback_mode or self.sentence_model is None:
            
            return [0] * 384
        return self.sentence_model.encode(text)
    
    def extract_medical_entities(self, text):
        """Extract medical terms from query"""
        if self.fallback_mode or self.nlp is None:
            return []
        
        try:
            doc = self.nlp(text)
            entities = [(ent.text, ent.label_) for ent in doc.ents]
            return entities
        except:
            return []
    
    def classify_intent(self, text):
        """Classify user intent with improved logic"""
        if self.fallback_mode:
            return self._classify_intent_fallback(text)
        
        try:
            
            text_lower = text.lower()
            
            if any(word in text_lower for word in ['symptom', 'pain', 'hurt', 'ache', 'fever', 'headache']):
                return "symptom_check"
            elif any(word in text_lower for word in ['medicine', 'medication', 'drug', 'pill', 'dose', 'prescription']):
                return "medication_info"
            elif any(word in text_lower for word in ['diet', 'exercise', 'sleep', 'lifestyle', 'healthy', 'nutrition']):
                return "lifestyle_advice"
            elif any(word in text_lower for word in ['disease', 'condition', 'illness', 'diagnosis', 'treatment']):
                return "condition_info"
            else:
                return "general_health"
        except:
            return "general_health"
    
    def _classify_intent_fallback(self, text):
        """Fallback intent classification when models fail"""
        text_lower = text.lower()
        
        
        medical_keywords = {
            'symptom_check': ['pain', 'hurt', 'ache', 'fever', 'cough', 'headache'],
            'medication_info': ['medicine', 'drug', 'pill', 'dose', 'prescription'],
            'lifestyle_advice': ['diet', 'exercise', 'sleep', 'healthy', 'nutrition'],
            'condition_info': ['disease', 'condition', 'illness', 'diagnosis']
        }
        
        for intent, keywords in medical_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return intent
        
        return "general_health"