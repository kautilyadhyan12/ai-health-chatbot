from llama_cpp import Llama

print("Testing GPU offload...")

llm = Llama(
    model_path="models/Meta-Llama-3-8B-Instruct.Q2_K.gguf",
    n_gpu_layers=14,    
    n_ctx=2048,
    n_threads=8,
    verbose=True
)

print("Model loaded")
print(llm("I feel dizzy and weak")["choices"][0]["text"])
