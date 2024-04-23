import yaml
import os
import datetime
from model_apis import groq, openai, anthropic
from rich.console import Console
from rich.markdown import Markdown

console = Console()

# Dictionary to map API names to their corresponding module functions
api_functions = {
    "openai": openai.chat_completion,
    "groq": groq.chat_completion,
    "anthropic": anthropic.chat_completion
}

def run_test(model_name, temperature, max_tokens, api_name, prompt, system_prompt):
    # Get the chat_completion function based on the API name
    chat_completion_func = api_functions.get(api_name)
    
    if chat_completion_func:
        # Call the chat_completion function with the provided parameters (model, user_message, temperature, max_tokens, system_prompt if any)
        response = chat_completion_func(model_name, prompt, temperature, max_tokens, system_prompt)
        return response
    else:
        raise ValueError(f"Unsupported API: {api_name}")

def main():
    # Read the test definition JSON file
    with open("test_definition.yml") as file:
        test_definition_yml = yaml.safe_load(file)
        test_definition = test_definition_yml["test"]
    
    # Read the test cases JSON file
    with open("test_sets/test_sets.yml") as file:
        test_sets = yaml.safe_load(file)

    # Extract the test name from the test definition, create a folde for it in the results folder
    test_name = test_definition["test_name"]
    # If the test name has {date} or {time} in it, replace them with the current date and time
    if "{date}" in test_name or "{time}" in test_name:
        now = datetime.datetime.now()
        test_name = test_name.replace("{date}", now.strftime("%Y-%m-%d"))
        test_name = test_name.replace("{time}", now.strftime("%H-%M-%S"))

    test_folder = f"results/{test_name}"
    if not os.path.exists(test_folder):
        os.makedirs(test_folder)

    # Create a tabulated results csv file in the test results folder
    with open(f"{test_folder}/tabulated_results.csv", "w") as file:
        file.write("model,set_display_name,case_display_name,evaluation_type,evaluation_score\n")

    # Iterate over the models in the test definition
    for model in test_definition["models"]:
        # Extract the model_name for the model, and create a folder for it in the test results folder
        model_name = model["model_name"]
        model_folder = f"{test_folder}/{model_name}"
        if not os.path.exists(model_folder):
            os.makedirs(model_folder)

        # Extract the display_name, temperature, max_tokens, shots and api_name for the model
        display_name = model["display_name"]        
        temperature = model["temperature"]
        max_tokens = model["max_tokens"]
        api_name = model["api"]
        
        # Iterate over the test sets
        for test_set in test_sets["test_sets"]:
            set_name = test_set["set_name"]
            set_display_name = test_set["set_display_name"]
            set_prompt_folder = f"test_sets/test_cases/{set_name}"
            set_result_folder = f"{model_folder}/{set_name}"
            if not os.path.exists(set_result_folder):
                os.makedirs(set_result_folder)
            test_cases = test_set["test_cases"]
            for case in test_cases:
                case_id = case["name"]
                case_display_name = case["display_name"]
                case_evaluation = case["evaluation"]
                if "evaluation_matches" in case:
                    case_evaluation_matches = case["evaluation_matches"]
                case_system_prompt = case["system_prompt"]

                case_response_file = f"{set_result_folder}/{case_id}.md"
                prompt_file = f"{set_prompt_folder}/{case_id}.txt"
                
                # Read the prompt from the corresponding file
                with open(prompt_file) as file:
                    prompt = file.read()

                print(f"Running test case '{case_display_name}' in set '{set_display_name}' against the {display_name} model...")
            
                # Run the test for the current model and test case, and save the response to file
                response = run_test(model_name, temperature, max_tokens, api_name, prompt, case_system_prompt)
                with open(case_response_file, "w") as file:
                    file.write(response)

                # Evaluate response
                eval_score = 0
                if case_evaluation == "contains":
                    score = 0
                    for match in case_evaluation_matches:
                        if match.lower() in response.lower(): # Assuming matches can be case-insensitive
                            score += 1
                    eval_score = (score / len(case_evaluation_matches)) * 10
                elif case_evaluation == "exact":
                    if case_evaluation_matches[0].lower() == response.lower(): # Assuming matches can be case-insensitive
                        eval_score = 10
                else: # Manual evaluation, show the user the prompt and response, then ask them to input a number between 0 and 10
                    print("----------------------=====PROMPT=====----------------------")
                    md = Markdown(prompt)
                    console.print(md)
                    print("----------------------====RESPONSE====----------------------")
                    md = Markdown(response)
                    console.print(md)
                    # Use a loop to make sure we get a valid answer from the user, even if they put a number outside the range or a non-integer
                    while True:
                        try:
                            eval_score = int(input("Enter a score between 0 and 10 (see readme for guidance): "))
                            if 0 <= eval_score <= 10:
                                break
                            else:
                                print("Invalid input. Please enter a number between 0 and 10.")
                        except ValueError:
                            print("Invalid input. Please enter a number between 0 and 10.")

                # Write the evaluation score to the tabulated results csv file
                with open(f"{test_folder}/tabulated_results.csv", "a") as file:
                    file.write(f"{display_name},{set_display_name},{case_display_name},{case_evaluation},{eval_score}\n")

if __name__ == "__main__":
    main()