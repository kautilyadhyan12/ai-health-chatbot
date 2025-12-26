from llama_cpp import Llama

llm = Llama(
    model_path="models/Meta-Llama-3-8B-Instruct.Q2_K.gguf",
    n_gpu_layers=14,   
    n_ctx=1024,
    n_batch=512,
    verbose=True
)

out = llm("Explain dizziness in simple terms.", max_tokens=100)
print(out["choices"][0]["text"])
