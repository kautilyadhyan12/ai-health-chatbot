
import sys
sys.path.append('.')

from ml_models.rag_system import OptimizedMedicalRAG
from config import Config

def debug_rag():
    print("🔍 DEBUGGING RAG SYSTEM...")
    
    
    config = {
        'llama_config': Config.get_optimized_llama_config(),
        'embedding_model': 'sentence-transformers/all-mpnet-base-v2'
    }
    
    print("1. Testing LLaMA model directly...")
    from ml_models.llama_model import OptimizedLLaMAModel
    
    
    llama_model = OptimizedLLaMAModel(
        model_path="models/Meta-Llama-3-8B-Instruct.Q3_K_M.gguf",
        config=config['llama_config']
    )
    
    if not llama_model.model:
        print("❌ LLaMA model failed to load!")
        return
    
    print("✅ LLaMA model loaded")
    
    # Test direct generation
    print("\n2. Testing direct LLaMA generation...")
    direct_response = llama_model.generate_response(
        prompt="What are fever symptoms?",
        temperature=0.3,
        max_tokens=200
    )
    
    print(f"Direct LLaMA Response:\n{direct_response}")
    print(f"Length: {len(direct_response)} chars")
    
    
    print("\n3. Testing RAG system...")
    rag = OptimizedMedicalRAG(
        knowledge_base_path="data/medical_knowledge/medical_faqs.json",
        llama_model_path="models/Meta-Llama-3-8B-Instruct.Q3_K_M.gguf",
        vector_db_path="data/vector_db/medical_index.faiss",
        config=config
    )
    
    print(f"LLaMA model in RAG: {'✅ Loaded' if rag.llama_model else '❌ Not loaded'}")
    
    # Test RAG query
    print("\n4. Testing RAG query...")
    result = rag.query("What are fever symptoms?")
    
    print(f"Response type: {type(result.get('response', 'No response'))}")
    print(f"Model used: {result.get('model', 'unknown')}")
    print(f"Response preview: {result.get('response', '')[:200]}...")
    
    
    response = result.get('response', '')
    if "Based on the provided information" in response:
        print("\n⚠️ PROBLEM DETECTED: Using fallback response!")
        print("The LLaMA model is not being called properly.")
    else:
        print("\n✅ SUCCESS: Using LLaMA-generated response!")
    
    return rag, result

if __name__ == '__main__':
    debug_rag()