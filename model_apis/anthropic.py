import anthropic

def chat_completion(model, user_message, temperature=0.0, max_tokens=1024, system_prompt=""):
    messages = [{"role": "user", "content": user_message}]

    chat_completion = anthropic.Anthropic().messages.create(
        system=system_prompt,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        messages=messages
    )

    text_response = chat_completion.content[0].text
    return text_response