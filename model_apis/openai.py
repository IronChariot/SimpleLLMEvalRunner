from openai import OpenAI

client = OpenAI()

# Function to create a chat completion using OpenAI's API
def chat_completion(model, user_message, temperature=0.0, max_tokens=1024, system_prompt=""):
    messages = []
    if system_prompt != "":
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})
    chat_completion = client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens
    )
    text_response = chat_completion.choices[0].message.content
    return text_response