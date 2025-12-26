"""
Retrieval-Augmented Generation System optimized for LLaMA-3 8B
FAST VERSION: Optimized for GTX 1650 4GB VRAM
"""
import faiss
import numpy as np
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from .llama_model import OptimizedLLaMAModel
from .embeddings import EmbeddingGenerator

class OptimizedMedicalRAG:
    def __init__(self, 
                 knowledge_base_path: str = "data/medical_knowledge/medical_faqs.json",
                 llama_model_path: str = None,
                 vector_db_path: str = "data/vector_db/medical_index.faiss",
                 config: Dict[str, Any] = None):
        
        self.knowledge_base_path = knowledge_base_path
        self.vector_db_path = vector_db_path
        self.config = config or {}
        
        print("=" * 50)
        print("🚀 Initializing Optimized Medical RAG System")
        print("=" * 50)
        
        
        print("📥 Loading embedding model...")
        self.embedding_generator = EmbeddingGenerator(
            model_name=self.config.get('embedding_model', 'sentence-transformers/all-mpnet-base-v2')
        )
        
        
        self.knowledge_base = []
        self.text_chunks = []
        self.index = None
        
        self.load_knowledge_base(knowledge_base_path)
        
        # Initialize LLaMA model
        self.llama_model = None
        if llama_model_path and os.path.exists(llama_model_path):
            try:
                print("📥 Loading LLaMA-3 8B...")
                self.llama_model = OptimizedLLaMAModel(
                    model_path=llama_model_path,
                    config=self.config.get('llama_config', {})
                )
            except Exception as e:
                print(f"⚠️ Could not load LLaMA model: {e}")
                print("Running in retrieval-only mode")
        else:
            print(f"⚠️ LLaMA model not found at: {llama_model_path}")
            print("Running in retrieval-only mode")
        
        print("=" * 50)
        print("✅ RAG System Initialized")
        print(f"   • Model: {'LLaMA-3 8B' if self.llama_model else 'Retrieval Only'}")
        print(f"   • Embeddings: {self.embedding_generator.model_name}")
        print(f"   • Knowledge Base: {len(self.knowledge_base)} entries")
        print("=" * 50)
    
    def load_knowledge_base(self, path: str):
        """Load and process medical knowledge base"""
        print(f"📚 Loading knowledge base from: {path}")
        
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.knowledge_base = data.get("medical_faqs", [])
                
                print(f"✅ Loaded {len(self.knowledge_base)} medical entries")
                self._create_text_chunks()
                self._build_vector_index()
                
            except Exception as e:
                print(f"❌ Error loading knowledge base: {e}")
                self._create_fallback_knowledge_base()
        else:
            print("⚠️ Knowledge base not found, creating sample data")
            self._create_fallback_knowledge_base()
    
    def _create_text_chunks(self):
        """Create optimized text chunks for retrieval"""
        self.text_chunks = []
        
        for entry in self.knowledge_base:
            # Create multiple chunk variations for better retrieval
            chunks = [
                
                f"Question: {entry['question']}\nAnswer: {entry['answer']}\nCategory: {entry.get('category', 'general')}",
                
                
                f"Medical Question: {entry['question']}\nRelated Information: {entry['answer'][:200]}...",
                
                
                f"Topic: {entry.get('category', 'general').replace('_', ' ').title()}\n{entry['question']}\n{entry['answer'][:150]}...",
                
                
                f"Keywords: {self._extract_keywords(entry['question'])}\n{entry['answer'][:100]}"
            ]
            self.text_chunks.extend(chunks)
        
        print(f"📝 Created {len(self.text_chunks)} text chunks")
    
    def _extract_keywords(self, text: str) -> str:
        """Extract keywords from text"""
        # Simple keyword extraction
        stop_words = {'what', 'are', 'how', 'to', 'is', 'the', 'a', 'an', 'of', 'for', 'with'}
        words = text.lower().split()
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        return ', '.join(set(keywords[:5]))
    
    def _create_fallback_knowledge_base(self):
        """Create fallback knowledge base"""
        print("🔄 Creating fallback knowledge base...")
        
        self.knowledge_base = [
            {
                "question": "What are common flu symptoms?",
                "answer": "Common flu symptoms include fever, cough, sore throat, runny or stuffy nose, body aches, headache, chills, and fatigue. Symptoms usually come on suddenly.",
                "category": "infectious_diseases",
                "severity": "moderate"
            },
            {
                "question": "How to manage high blood pressure naturally?",
                "answer": "Natural ways to manage blood pressure include: regular exercise (30 minutes daily), reducing sodium intake, eating potassium-rich foods, limiting alcohol, managing stress, maintaining healthy weight, and quitting smoking.",
                "category": "chronic_conditions",
                "severity": "serious"
            },
            {
                "question": "What is considered a healthy diet?",
                "answer": "A healthy diet includes: fruits and vegetables (5+ servings daily), whole grains, lean proteins, healthy fats, and limits processed foods, added sugars, and saturated fats. Stay hydrated with water.",
                "category": "nutrition",
                "severity": "low"
            },
            {
                "question": "How much sleep do adults need?",
                "answer": "Most adults need 7-9 hours of quality sleep per night. Maintain consistent sleep schedule, create comfortable sleep environment, avoid screens before bed, and limit caffeine.",
                "category": "lifestyle",
                "severity": "low"
            },
            {
                "question": "What are signs of dehydration?",
                "answer": "Signs include: thirst, dry mouth, fatigue, dizziness, dark yellow urine, decreased urination, dry skin, and headache. Severe dehydration requires immediate medical attention.",
                "category": "emergency",
                "severity": "moderate"
            }
        ]
        
        
        os.makedirs(os.path.dirname(self.knowledge_base_path), exist_ok=True)
        with open(self.knowledge_base_path, 'w', encoding='utf-8') as f:
            json.dump({
                "medical_faqs": self.knowledge_base,
                "last_updated": datetime.now().isoformat(),
                "version": "1.0.0",
                "model": "LLaMA-3 8B Optimized"
            }, f, indent=2, ensure_ascii=False)
        
        self._create_text_chunks()
        print(f"✅ Created fallback knowledge base with {len(self.knowledge_base)} entries")
    
    def _build_vector_index(self):
        """Build FAISS vector index with optimizations"""
        if not self.text_chunks:
            print("⚠️ No text chunks to index")
            return
        
        print(f"🔨 Building FAISS index with {len(self.text_chunks)} chunks...")
        
        try:
            # Generate embeddings with progress
            embeddings = self.embedding_generator.get_embeddings(
                self.text_chunks,
                batch_size=16,  
                show_progress_bar=True
            )
            
            dimension = embeddings.shape[1]
            print(f"📐 Embedding dimension: {dimension}")
            
            # Use IndexFlatIP for cosine similarity 
            self.index = faiss.IndexFlatIP(dimension)
            
           
            faiss.normalize_L2(embeddings)
            self.index.add(embeddings.astype('float32'))
            
            # Save index
            os.makedirs(os.path.dirname(self.vector_db_path), exist_ok=True)
            faiss.write_index(self.index, self.vector_db_path)
            
            print(f"✅ FAISS index built and saved to: {self.vector_db_path}")
            print(f"   • Vectors: {self.index.ntotal}")
            print(f"   • Dimension: {dimension}")
            
        except Exception as e:
            print(f"❌ Error building vector index: {e}")
            self.index = None
    
    def retrieve_relevant_info(self, query: str, k: int = 3, similarity_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Retrieve relevant information with optimizations"""
        if self.index is None or not self.text_chunks:
            print("⚠️ Index not available")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.embedding_generator.get_single_embedding(query)
            query_embedding = query_embedding.reshape(1, -1)
            
           
            faiss.normalize_L2(query_embedding)
            
            
            k_search = min(k * 3, len(self.text_chunks))  
            distances, indices = self.index.search(
                query_embedding.astype('float32'),
                k_search
            )
            
            
            results = []
            seen_questions = set()
            
            for idx, distance in zip(indices[0], distances[0]):
                if idx < len(self.text_chunks) and distance >= similarity_threshold:
                    chunk = self.text_chunks[idx]
                    
                    # Find corresponding knowledge base entry
                    for entry in self.knowledge_base:
                        if entry['question'] in chunk and entry['question'] not in seen_questions:
                            results.append({
                                'question': entry['question'],
                                'answer': entry['answer'],
                                'category': entry.get('category', 'general'),
                                'severity': entry.get('severity', 'unknown'),
                                'similarity': float(distance),
                                'source': 'knowledge_base'
                            })
                            seen_questions.add(entry['question'])
                            break
                
                if len(results) >= k:
                    break
            
            # Sort by similarity
            results.sort(key=lambda x: x['similarity'], reverse=True)
            
            return results
            
        except Exception as e:
            print(f"❌ Error retrieving information: {e}")
            return []
    
    def generate_rag_response(self, query: str, retrieved_info: List[Dict[str, Any]] = None) -> str:
        """Generate response using RAG with LLaMA-3 - OPTIMIZED FOR SPEED"""
        # Prepare context
        context = ""
        if retrieved_info and len(retrieved_info) > 0:
            context = "Here is some relevant medical information:\n\n"
            for i, info in enumerate(retrieved_info[:2]): 
                context += f"{i+1}. **{info['question']}**\n"
                context += f"   {info['answer'][:200]}...\n\n"
        
        # ============================================
        #  PROMPT FOR SPEED 
        # ============================================
        prompt = f"""Question: {query}

Medical Context:
{context}

Provide a clear, concise medical answer. Include safety disclaimer."""
        
        
        if self.llama_model:
            try:
                response = self.llama_model.generate_response(
                    prompt=prompt,
                    max_tokens=250, 
                    temperature=0.3,  
                    top_p=0.95,
                    top_k=40,
                    repeat_penalty=1.1
                )
                
                return response
                
            except Exception as e:
                print(f"❌ LLaMA generation error: {e}")
                return self._generate_fallback_response(query, retrieved_info)
        else:
            return self._generate_fallback_response(query, retrieved_info)
    
    def _generate_fallback_response(self, query: str, retrieved_info: List[Dict[str, Any]] = None) -> str:
        """Generate fallback response without LLaMA"""
        response = f"I understand you're asking about: **{query}**\n\n"
        
        if retrieved_info and len(retrieved_info) > 0:
            response += "Here's some relevant information:\n\n"
            for info in retrieved_info[:3]:
                response += f"**• {info['question']}**\n"
                response += f"  {info['answer'][:200]}...\n\n"
        else:
            response += "This appears to be a health-related question. "
            response += "For accurate information, please consult with a healthcare professional.\n\n"
        
        response += "**General Health Tips:**\n"
        response += "• Stay hydrated and get adequate rest\n"
        response += "• Eat a balanced diet with plenty of fruits and vegetables\n"
        response += "• Exercise regularly as appropriate\n"
        response += "• Manage stress through relaxation techniques\n"
        response += "• Get regular health check-ups\n\n"
        
        response += "**⚠️ Medical Disclaimer:** I am an AI assistant providing general health information only. "
        response += "Always consult with qualified healthcare professionals for medical advice, diagnosis, or treatment."
        
        return response
    
    def query(self, user_query: str) -> Dict[str, Any]:
        """
        Complete RAG pipeline optimized for Q3_K_M
        
        Args:
            user_query: User's query
            
        Returns:
            Dictionary with response and metadata
        """
        start_time = datetime.now()
        
        # Retrieve relevant information
        retrieved_info = self.retrieve_relevant_info(user_query, k=3)
        
       
        response = self.generate_rag_response(user_query, retrieved_info)
        
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        
        confidence = self._calculate_confidence(retrieved_info, response)
        
        
        intent = self._determine_intent(user_query)
        
        return {
            'response': response,
            'retrieved_info': retrieved_info,
            'confidence': confidence,
            'intent': intent,
            'processing_time': processing_time,
            'timestamp': datetime.now().isoformat(),
            'model': 'LLaMA-3 8B' if self.llama_model else 'fallback',
            'optimized': True
        }
    
    def _calculate_confidence(self, retrieved_info: List[Dict], response: str) -> float:
        """Calculate confidence score"""
        if not retrieved_info:
            return 0.3  
        
        
        avg_similarity = sum(info['similarity'] for info in retrieved_info) / len(retrieved_info)
        
        
        response_length = len(response.split())
        length_boost = min(response_length / 100, 0.2)  
        
        # Check for safety keywords
        safety_keywords = ['consult', 'professional', 'doctor', 'advice', 'disclaimer']
        has_safety = any(keyword in response.lower() for keyword in safety_keywords)
        safety_boost = 0.1 if has_safety else 0
        
        confidence = avg_similarity * 0.7 + length_boost + safety_boost
        return min(confidence, 1.0)
    
    def _determine_intent(self, query: str) -> str:
        """Determine user intent"""
        query_lower = query.lower()
        
        intent_patterns = {
            'symptom_check': ['symptom', 'pain', 'hurt', 'ache', 'fever', 'headache', 'cough', 'sore', 'feel'],
            'medication_info': ['medicine', 'medication', 'drug', 'pill', 'dose', 'prescription', 'side effect'],
            'condition_info': ['disease', 'condition', 'illness', 'diagnosis', 'what is', 'what are', 'cause of'],
            'lifestyle_advice': ['diet', 'exercise', 'sleep', 'healthy', 'nutrition', 'weight', 'fitness', 'lifestyle'],
            'prevention': ['prevent', 'avoid', 'reduce risk', 'protection', 'vaccine'],
            'emergency': ['emergency', 'urgent', '911', 'heart attack', 'stroke', 'severe', 'bleeding', 'can\'t breathe']
        }
        
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                if pattern in query_lower:
                    return intent
        
        return 'general_health'
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            'llama_loaded': self.llama_model is not None,
            'embedding_model': self.embedding_generator.model_name,
            'knowledge_base_entries': len(self.knowledge_base),
            'vector_index_loaded': self.index is not None,
            'text_chunks': len(self.text_chunks),
            'optimization': 'Q3_K_M (3.74GB) - GTX 1650 4GB Optimized'
        }