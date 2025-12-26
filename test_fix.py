
"""
Test script to verify the ellipsis fix
"""
import sys
sys.path.append('.')

from config import Config
from ml_models.llama_model import OptimizedLLaMAModel

def main():
    print("🧪 Testing LLaMA-3 Q3_K_M ellipsis fix...")
    
    
    config = Config.get_optimized_llama_config()
    
    
    model = OptimizedLLaMAModel(
        model_path="models/Meta-Llama-3-8B-Instruct.Q3_K_M.gguf",
        config=config
    )
    
    if not model.model:
        print("❌ Model failed to load")
        return
    
    
    test_prompts = [
        "What are fever symptoms?",
        "How to lower blood pressure naturally?",
        "What is a healthy diet?",
        "Tell me about diabetes",
        "What are signs of dehydration?"
    ]
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n{'='*60}")
        print(f"TEST {i}: {prompt}")
        print(f"{'='*60}")
        
        response = model.generate_response(
            prompt=prompt,
            max_tokens=200,
            temperature=0.3
        )
        
        print(f"\nResponse ({len(response)} chars):")
        print(response[:300] + "..." if len(response) > 300 else response)
        
        # Check for ellipsis
        if response.count('...') > 3:
            print(f"⚠️ WARNING: Still has {response.count('...')} ellipsis")
        else:
            print("✅ No excessive ellipsis detected")
    
    print(f"\n{'='*60}")
    print("🎯 TEST COMPLETE")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()