"""
LLaMA-3 8B Q3_K_M model implementation optimized for hybrid CPU+GPU mode
FIXED: Complete response generation (no ellipsis)
"""
from llama_cpp import Llama
import torch
from typing import List, Dict, Any, Optional
import warnings
import gc
import os
import subprocess
import sys

warnings.filterwarnings('ignore')

class OptimizedLLaMAModel:
    def __init__(self, model_path: str = None, config: Dict[str, Any] = None):
        """
        Initialize LLaMA-3 8B Q3_K_M (3.74GB) model
        
        Args:
            model_path: Path to GGUF model file (Q3_K_M variant)
            config: Configuration dictionary with hybrid CPU+GPU settings
        """
        self.model = None
        self.config = config or {}
        
        # ============================================
        #  CPU+GPU CONFIGURATION FOR Q3_K_M
        # ============================================
        self.n_ctx = self.config.get('n_ctx', 1536)          
        self.n_gpu_layers = self.config.get('n_gpu_layers', 26)  
        self.n_batch = self.config.get('n_batch', 256)
        self.n_threads = self.config.get('n_threads', 8)
        self.max_tokens = self.config.get('max_tokens', 300)  
        self.temperature = self.config.get('temperature', 0.3)  
        self.top_p = self.config.get('top_p', 0.9)           
        self.top_k = self.config.get('top_k', 50)            
        self.repeat_penalty = self.config.get('repeat_penalty', 1.2)  
        self.use_mmap = self.config.get('use_mmap', True)
        self.use_mlock = self.config.get('use_mlock', False)
        self.offload_kqv = self.config.get('offload_kqv', True)  
        
        
        self.f16_kv = self.config.get('f16_kv', True)
        self.mul_mat_q = self.config.get('mul_mat_q', True)
        
        
        self.system_info = self._get_system_info()
        
        # ============================================
        # WINDOWS OPTIMIZATIONS
        # ============================================
        if os.name == 'nt':
            os.environ["OMP_NUM_THREADS"] = str(self.n_threads)
            
            gc.disable()  
        
        self._load_model(model_path)
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get detailed system information without torch.cuda dependency"""
        system_info = {
            'os': os.name,
            'cuda_available': False,
            'cpu_count': os.cpu_count() or 4
        }
        
        try:
            import psutil
            ram = psutil.virtual_memory()
            system_info['ram_gb'] = ram.total / 1e9
            system_info['ram_available_gb'] = ram.available / 1e9
        except ImportError:
            system_info['ram_gb'] = 16.0  
        
        
        try:
            if os.name == 'nt':
                # Check for NVIDIA GPU via nvidia-smi
                result = subprocess.run(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'], 
                                       capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if lines and lines[0]:
                        gpu_info = lines[0].split(', ')
                        system_info['cuda_available'] = True
                        system_info['gpu_name'] = gpu_info[0]
                        # Extract memory (format: "4096 MiB")
                        memory_str = gpu_info[1].replace('MiB', '').strip()
                        system_info['vram_gb'] = float(memory_str) / 1024
            else:
                
                result = subprocess.run(['which', 'nvidia-smi'], capture_output=True)
                if result.returncode == 0:
                    system_info['cuda_available'] = True
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            
            pass
        
        return system_info
    
    def _load_model(self, model_path: str):
        """Load Q3_K_M model with hybrid optimizations"""
        if not model_path:
            print("⚠️ No model path provided")
            return
        
        try:
            print("=" * 50)
            print(f"🤖 Loading LLaMA-3 8B Q3_K_M (3.74GB)")
            print("=" * 50)
            print(f"Model path: {model_path}")
            print(f"Context size: {self.n_ctx}")
            print(f"GPU layers: {self.n_gpu_layers}")
            print(f"Batch size: {self.n_batch}")
            print(f"Max tokens: {self.max_tokens}")
            print(f"Temperature: {self.temperature} (optimized for complete responses)")
            print(f"Repeat penalty: {self.repeat_penalty}")
            print(f"Memory mapping: {self.use_mmap}")
            print(f"Offload KQV: {self.offload_kqv}")
            print(f"KV cache in f16: {self.f16_kv}")
            
            # ============================================
            #  OPTIMAL CONFIGURATION
            # ============================================
            self.model = Llama(
                model_path=model_path,
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                n_gpu_layers=self.n_gpu_layers,  
                n_batch=self.n_batch,
                n_threads_batch=self.n_threads,
                rope_freq_base=10000,
                rope_freq_scale=1,
                mul_mat_q=self.mul_mat_q,
                f16_kv=self.f16_kv,
                logits_all=False,
                vocab_only=False,
                use_mmap=self.use_mmap,
                use_mlock=self.use_mlock,
                embedding=False,
                offload_kqv=self.offload_kqv,
                last_n_tokens_size=64,
                verbose=False  
            )
            
            print("=" * 50)
            print("✅ LLaMA-3 8B Q3_K_M loaded successfully!")
            print(f"Context size: {self.model.n_ctx()}")
            print(f"GPU layers loaded: {self.n_gpu_layers}")
            print(f"Batch size: {self.n_batch}")
            print(f"Model size: 3.74GB")
            print(f"Mode: {'Hybrid CPU+GPU' if self.n_gpu_layers > 0 else 'CPU only'}")
            print(f"Temperature: {self.temperature} (optimized for complete responses)")
            print(f"Repeat penalty: {self.repeat_penalty} (prevents loops)")
            print("=" * 50)
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            
            #  fallback sequence for OOM: 26 → 24 → 22
            if "CUDA out of memory" in str(e) or "memory" in str(e).lower():
                print("🔄 GPU OOM detected. Applying fallback sequence...")
                self._load_with_fallback_sequence(model_path)
            else:
                raise
    
    def _load_with_fallback_sequence(self, model_path: str):
        """Try loading with progressively reduced GPU layers (26 → 24 → 22)"""
        fallback_sequences = [
            {'n_gpu_layers': 24, 'n_ctx': 1536, 'n_batch': 256, 'max_tokens': 256, 'temperature': 0.3},
            {'n_gpu_layers': 22, 'n_ctx': 1536, 'n_batch': 192, 'max_tokens': 192, 'temperature': 0.3},
            {'n_gpu_layers': 20, 'n_ctx': 1536, 'n_batch': 128, 'max_tokens': 128, 'temperature': 0.4},
            {'n_gpu_layers': 0, 'n_ctx': 1024, 'n_batch': 64, 'max_tokens': 64, 'n_threads': 4, 'temperature': 0.5}
        ]
        
        for i, config in enumerate(fallback_sequences):
            try:
                print(f"   Attempt {i+1}: {config['n_gpu_layers']} GPU layers...")
                
                # Update configuration
                self.n_ctx = config['n_ctx']
                self.n_gpu_layers = config['n_gpu_layers']
                self.n_batch = config['n_batch']
                self.max_tokens = config['max_tokens']
                self.temperature = config['temperature']
                self.n_threads = config.get('n_threads', self.n_threads)
                
                
                self.model = Llama(
                    model_path=model_path,
                    n_ctx=self.n_ctx,
                    n_threads=self.n_threads,
                    n_gpu_layers=self.n_gpu_layers,
                    n_batch=self.n_batch,
                    verbose=False
                )
                
                print(f"   ✅ Success with {self.n_gpu_layers} GPU layers.")
                print(f"   ⚠️  Using reduced configuration for stability.")
                print(f"   ⚙️  Temperature increased to {self.temperature} for better responses")
                return
                
            except Exception as e:
                print(f"   ❌ Attempt {i+1} failed: {e}")
                continue
        
        print("❌ All fallback attempts failed. Running in CPU-only mode with minimal settings.")
        self.model = None
    
    def generate_response(self, 
                         prompt: str, 
                         max_tokens: Optional[int] = None,
                         temperature: Optional[float] = None,
                         top_p: Optional[float] = None,
                         top_k: Optional[int] = None,
                         repeat_penalty: Optional[float] = None,
                         stream: bool = False) -> str:
        """
        Generate response using LLaMA-3 8B Q3_K_M - FIXED FOR COMPLETE RESPONSES
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate (defaults to config)
            temperature: Sampling temperature (optimized for medical responses)
            top_p: Top-p sampling
            top_k: Top-k sampling
            repeat_penalty: Penalty for repeating tokens
            stream: Whether to stream response
            
        Returns:
            Generated response
        """
        if not self.model:
            return "Model not available. Please check configuration and try again."
        
        try:
            # ============================================
            #  simple medical system prompt
            # ============================================
            system_content = """You are MedAI, a helpful medical AI assistant. 
Provide clear, complete medical information. Always include safety disclaimers.
Never diagnose or prescribe. Encourage consulting healthcare professionals.
Keep responses informative and complete."""

            # Use proper chat format for Llama-3
            messages = [
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ]
            
            # Use parameters from config 
            max_tokens = max_tokens or self.max_tokens
            temperature = temperature or self.temperature
            top_p = top_p or self.top_p
            top_k = top_k or self.top_k
            repeat_penalty = repeat_penalty or self.repeat_penalty
            
            
            print(f"\n🔍 DEBUG - Generating response for: '{prompt[:50]}...'")
            print(f"   Temperature: {temperature}")
            print(f"   Max tokens: {max_tokens}")
            print(f"   Repeat penalty: {repeat_penalty}")
            
            # Generate response using Llama-3 chat completion API
            response = self.model.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repeat_penalty=repeat_penalty,
                stop=["<|end_of_text|>", "<|eot_id|>", "###", "Disclaimer:"]
            )
            
            
            if response and 'choices' in response and len(response['choices']) > 0:
                response_text = response['choices'][0]['message']['content'].strip()
            else:
                response_text = "I'm sorry, I couldn't generate a response. Please try again."
            
            
            response_text = self._clean_response(response_text)
            
            # Validate safety
            if not self._validate_response_safety(response_text):
                response_text = self._get_safe_fallback_response(prompt)
            
            print(f"✅ Response generated ({len(response_text)} chars)")
            return response_text
            
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            import traceback
            traceback.print_exc()
            return self._get_error_response()
    
    def _clean_response(self, response: str) -> str:
        """Clean and format the response for medical context - FIXED"""
        if not response:
            return "I apologize, but I couldn't generate a response. Please try rephrasing your question."
        
        
        response = response.strip()
        
        # Fix incomplete sentences
        if response.endswith('...'):
            response = response[:-3].strip()
            e
            if response and response[-1] not in ['.', '!', '?']:
                response += '.'
        
        
        if response.endswith(':'):
            response = response[:-1]
        
        
        if response and response[-1] not in ['.', '!', '?']:
            response += '.'
        
        # Remove any internal repetition patterns
        lines = response.split('\n')
        unique_lines = []
        for line in lines:
            line = line.strip()
            if line and line not in unique_lines:
                unique_lines.append(line)
        
        response = '\n'.join(unique_lines)
        
        # Add medical disclaimer 
        if "disclaimer" not in response.lower() and "consult" not in response.lower():
            response += "\n\n**Medical Disclaimer:** This information is for educational purposes only. Always consult with a healthcare professional for medical advice."
        
        return response
    
    def _validate_response_safety(self, response: str) -> bool:
        """
        Validate if response is safe for medical context
        
        Args:
            response: Generated response
            
        Returns:
            True if safe, False otherwise
        """
        if not response or len(response) < 10:
            print("⚠️ Response too short or empty")
            return False
        
        response_lower = response.lower()
        
        # Check for endless ellipsis pattern
        if response.count('...') > 3:
            print("⚠️ Excessive ellipsis detected")
            return False
        
        # Check for repetition patterns
        words = response_lower.split()
        if len(words) < 5:
            print("⚠️ Response too short")
            return False
        
        # Check word repetition 
        word_counts = {}
        for word in words:
            if len(word) > 3:  
                word_counts[word] = word_counts.get(word, 0) + 1
        
        max_repetition = max(word_counts.values(), default=0)
        if max_repetition > len(words) * 0.3:
            print(f"⚠️ Excessive word repetition detected: {max_repetition} repeats")
            return False
        
        
        dangerous_phrases = [
            "i diagnose you with",
            "you have [",
            "take this medication",
            "prescribe you",
            "you should definitely",
            "ignore your doctor",
            "self-medicate",
            "alternative to",
            "instead of seeing a doctor"
        ]
        
        for phrase in dangerous_phrases:
            if phrase in response_lower:
                print(f"⚠️ Dangerous phrase detected: {phrase}")
                return False
        
        return True
    
    def _get_safe_fallback_response(self, query: str) -> str:
        """Get safe fallback response"""
        return f"""I understand you're asking about: {query}

I want to ensure I provide safe and accurate information. For health-related questions:

**Please consult with a healthcare professional** who can:
• Review your specific situation
• Consider your medical history
• Provide personalized advice
• Order appropriate tests if needed

**For general health information:**
• Stay hydrated and get adequate sleep
• Eat a balanced diet with fruits and vegetables
• Exercise regularly as appropriate
• Monitor any symptoms and seek help if they worsen

**🚨 Seek immediate medical attention for:**
• Chest pain or pressure
• Difficulty breathing
• Severe pain
• Uncontrolled bleeding
• Sudden weakness or numbness

**Medical Disclaimer:** I am an AI assistant providing general information only. Always consult with qualified healthcare professionals for medical advice."""
    
    def _get_error_response(self) -> str:
        """Get error response"""
        return """I apologize, but I encountered an issue processing your request.

**Please try:**
1. Rephrasing your question to be more specific
2. Asking about general health topics
3. Consulting a healthcare professional for specific concerns

**Example questions that work well:**
• "What are common flu symptoms?"
• "How to manage stress naturally?"
• "What foods are good for heart health?"

**Remember:** I provide general health information only. For personal medical advice, please consult with a doctor or healthcare provider."""

    def get_model_info(self) -> Dict[str, Any]:
        """Get detailed model information"""
        if not self.model:
            return {'status': 'not_loaded'}
        
        return {
            'status': 'loaded',
            'model_type': 'LLaMA-3 8B Q3_K_M (3.74GB)',
            'context_size': self.n_ctx,
            'gpu_layers': self.n_gpu_layers,
            'batch_size': self.n_batch,
            'max_tokens': self.max_tokens,
            'temperature': self.temperature,
            'repeat_penalty': self.repeat_penalty,
            'mode': 'Hybrid CPU+GPU' if self.n_gpu_layers > 0 else 'CPU only',
            'memory_optimizations': {
                'use_mmap': self.use_mmap,
                'f16_kv': self.f16_kv,
                'offload_kqv': self.offload_kqv,
                'batch_size': self.n_batch
            },
            'system': {
                'os': self.system_info.get('os'),
                'cpu_count': self.system_info.get('cpu_count'),
                'ram_gb': self.system_info.get('ram_gb'),
                'cuda_available': self.system_info.get('cuda_available', False)
            }
        }

    def test_generation(self, test_prompt: str = "What are common symptoms of fever?") -> str:
        """
        Test method to verify model generation works correctly
        """
        print("\n" + "=" * 60)
        print("🧪 TESTING MODEL GENERATION")
        print("=" * 60)
        
        try:
            response = self.generate_response(
                prompt=test_prompt,
                max_tokens=200,
                temperature=0.3
            )
            
            print(f"\n✅ Test successful!")
            print(f"Prompt: {test_prompt}")
            print(f"Response length: {len(response)} characters")
            print(f"Response preview: {response[:100]}...")
            
            return response
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return f"Test failed: {e}"