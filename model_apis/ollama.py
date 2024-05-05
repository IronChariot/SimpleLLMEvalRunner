# ollama runs on localhost:11434
# Expects a request like this curl:
# http://localhost:11434/api/generate -d '{ "model": "llama2-uncensored", "prompt": "What is water made of?" }

import requests
import json

# Function to create a chat completion using ollama
def chat_completion(model, user_message, temperature=0.0, max_tokens=1024, system_prompt=""):
    url = "http://localhost:11434/api/generate"
    headers = {
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "prompt": user_message,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens
        }
    }

    # Add system prompt if provided
    if system_prompt != "":
        data["system"] = system_prompt
    
    response = requests.post(url, headers=headers, data=json.dumps(data))

    text_response = ""
    if response.status_code == 200:
        text_response = response.json()["text"]
    else:
        text_response = "Error: " + str(response.status_code)

    return text_response