import sys
sys.path.append(".")

from ml_models.rag_system import OptimizedMedicalRAG
from config import Config

def main():
    print("🧪 Testing RAG system with fixed temperature...")
    
    
    config = {
        "llama_config": Config.get_optimized_llama_config(),
        "embedding_model": "sentence-transformers/all-mpnet-base-v2"
    }
    
    # Initialize RAG
    rag = OptimizedMedicalRAG(
        knowledge_base_path="data/medical_knowledge/medical_faqs.json",
        llama_model_path="models/Meta-Llama-3-8B-Instruct.Q3_K_M.gguf",
        vector_db_path="data/vector_db/medical_index.faiss",
        config=config
    )
    
    if not rag.llama_model:
        print("❌ LLaMA model not loaded")
        return
    
    # Test query
    test_query = "What are fever symptoms?"
    print(f"\n{'='*60}")
    print(f"TEST QUERY: {test_query}")
    print(f"{'='*60}")
    
    # Get response
    result = rag.query(test_query)
    
    print(f"\nRESPONSE:")
    print(result["response"])
    print(f"\nLength: {len(result['response'])} characters")
    print(f"Temperature used: {config['llama_config']['temperature']}")
    print(f"Model: {result.get('model', 'unknown')}")
    
    print(f"\n{'='*60}")
    print("🎯 TEST COMPLETE")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()