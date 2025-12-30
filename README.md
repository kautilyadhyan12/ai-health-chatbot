This project uses GPU-intensive models. 
 Due to hardware limitations on 
free cloud platforms, live deployment is not provided.

A complete video demonstration and system walkthrough 
is available below.

demo: https://youtu.be/7PrF-3ah_5o 

 ai-health-chatbot
 AI Medical Chatbot powered by LLaMA-3 8B + Retrieval-Augmented Generation (RAG)
 
Setup Guide: python:3.10

Hardware:8GB RAM,GPU

Create Virtual Environment: 1)python3.10 -m venv venv
2)venv\Scripts\activate

Install Dependencies:pip install -r requirements.txt

Run Setup: python setup.py
Download AI Model: python download_model.py

or  Download from: https://huggingface.co/bartowski/Meta-Llama-3-8B-Instruct-GGUF  and place in models folder

Check GPU: python -c "import torch; print('CUDA Available:', torch.cuda.is_available())"
Check GPU Support for LLaMA: python -c "from llama_cpp import Llama; print('LLaMA backend loaded')"

start application: python app.py

