

from pathlib import Path

config_path = Path("config.py")

if not config_path.exists():
    print("ERROR: config.py not found")
    exit(1)

content = config_path.read_text(encoding="utf-8", errors="ignore")

updates = {
    "LLAMA_N_GPU_LAYERS": "LLAMA_N_GPU_LAYERS = 24",
    "LLAMA_BATCH_SIZE": "LLAMA_BATCH_SIZE = 384",
    "LLAMA_CONTEXT_SIZE": "LLAMA_CONTEXT_SIZE = 2048",
    "LLAMA_MAX_TOKENS": "LLAMA_MAX_TOKENS = 384",
    "LLAMA_TEMPERATURE": "LLAMA_TEMPERATURE = 0.1",
}

lines = content.splitlines()
new_lines = []

for line in lines:
    replaced = False
    for key, value in updates.items():
        if line.strip().startswith(key):
            new_lines.append(value)
            replaced = True
            break
    if not replaced:
        new_lines.append(line)

config_path.write_text("\n".join(new_lines), encoding="utf-8")

print("CONFIG UPDATED SUCCESSFULLY")
print("GTX 1650 SAFE SETTINGS APPLIED")
