import anthropic
import time

# Function to create a chat completion using Anthropic's API
def chat_completion(model, user_message, temperature=0.0, max_tokens=1024, system_prompt=""):
    messages = [{"role": "user", "content": user_message}]

    chat_completion = None
    while True:
        try:
            chat_completion = anthropic.Anthropic().messages.create(
                system=system_prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages
            )
        except Exception as e:
            if e.response.status_code == 529:
                chat_completion = None
                print("API is Overloaded. Waiting 30 seconds before retrying.")
                time.sleep(30)
            else:
                raise

        if chat_completion is not None:
            break

    text_response = chat_completion.content[0].text
    return text_response