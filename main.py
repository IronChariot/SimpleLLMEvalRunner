import yaml
import os
import time
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

rate_limits_per_minute = {
    "openai": 500,
    "groq": 30,
    "anthropic": 30
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

# Function to call the llama 3 70b model to judge whether an answer matches the expected answer
def judge_answer(question, answer, expected_answers):
    prompt = f"<question>{question}</question>"
    prompt += f"<expected_answers>{', '.join(expected_answers)}</expected_answers>"
    prompt += f"<given_answer>{answer}</given_answer>"
    prompt += f"Does the given answer match the expected answer, in the core details provided in the expected answer? Think it through, then respond with a yes or no inside a <response_correct></response_correct> tag."

    print(f"Prompt: {prompt}")

    chat_completion_func = api_functions.get("groq")
    response = chat_completion_func("llama3-70b-8192", prompt, temperature=0.0, max_tokens=1024, system_prompt="")

    print(f"Response from evaluator: {response}")
    print("--------------------------------------------------------------------")

    if "<response_correct>yes</response_correct>" in response:
        return True
    else:
        return False


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
                case_repeat = case["repeat"]
                if "evaluation_answers" in case:
                    case_evaluation_answers = case["evaluation_answers"]
                case_system_prompt = case["system_prompt"]
                prompt_file = f"{set_prompt_folder}/{case_id}.txt"
                
                # Read the prompt from the corresponding file
                with open(prompt_file) as file:
                    prompt = file.read()

                # if case_repeat wasn't specified, set it to 1
                # also if the model temperature is set to 0, set it to 1, no point in repeating a test case with a temperature of 0
                if case_repeat is None or case_repeat == 0 or temperature == 0:
                    case_repeat = 1

                # Make a note of the time now, so that we can obey rate limits
                time_now = time.time()
                requests_since_last_check = 0
                total_eval_score = 0
                print(f"Running test cases '{case_display_name}' in set '{set_display_name}' {case_repeat} times against the {display_name} model...")
                for i in range(case_repeat):
                    case_response_file = f"{set_result_folder}/{case_id} ({i+1}).md"

                    # Run the test for the current model and test case, and save the response to file
                    response = run_test(model_name, temperature, max_tokens, api_name, prompt, case_system_prompt)
                    requests_since_last_check += 1
                    with open(case_response_file, "w") as file:
                        file.write(response)

                    # If the first case_evaluation_answers starts with 'file:', evaluate the response against the contents of that file
                    if case_evaluation_answers is not None and case_evaluation_answers[0].startswith("file:"):
                        with open(f"{set_prompt_folder}/{case_evaluation_answers[0][5:]}") as file:
                            case_evaluation_answers = []
                            solution_text = file.read()
                            case_evaluation_answers.append(solution_text)

                    # Evaluate response
                    eval_score = 0
                    if case_evaluation == "contains" or case_evaluation == "contains_all" or case_evaluation == "contains_one":
                        score = 0
                        for match in case_evaluation_answers:
                            if match.lower() in response.lower(): # Assuming matches can be case-insensitive
                                score += 1
                        if case_evaluation == "contains":
                            eval_score = (score / len(case_evaluation_answers)) * 100
                        elif case_evaluation == "contains_all": # Either give a perfect score or 0
                            if score == len(case_evaluation_answers):
                                eval_score = 100
                            else:
                                eval_score = 0
                        elif case_evaluation == "contains_one": # Either give a perfect score or 0
                            if score > 0:
                                eval_score = 100
                            else:
                                eval_score = 0
                    elif case_evaluation == "exact":
                        if case_evaluation_answers[0].lower() == response.lower(): # Assuming matches can be case-insensitive
                            eval_score = 100
                    elif case_evaluation == "automatic":
                        response_judged_correct = judge_answer(prompt, response, case_evaluation_answers)
                        requests_since_last_check += 1
                        if response_judged_correct:
                            eval_score = 100
                        else:
                            eval_score = 0
                    else: # Manual evaluation, show the user the prompt and response, then ask them to input a number between 0 and 10
                        print("----------------------=====PROMPT=====----------------------")
                        md = Markdown(prompt)
                        console.print(md)
                        print("----------------------====SOLUTION====-----------------------")
                        for answer in case_evaluation_answers:
                            print(answer)
                        print("----------------------====RESPONSE====----------------------")
                        md = Markdown(response)
                        console.print(md)
                        # Use a loop to make sure we get a valid answer from the user, even if they put a number outside the range or a non-integer
                        while True:
                            try:
                                eval_score = int(input("Enter a score between 0 and 100 (see readme for guidance): "))
                                if 0 <= eval_score <= 100:
                                    break
                                else:
                                    print("Invalid input. Please enter a number between 0 and 10.")
                            except ValueError:
                                print("Invalid input. Please enter a number between 0 and 10.")

                    # Write the evaluation score to the tabulated results csv file
                    with open(f"{test_folder}/tabulated_results.csv", "a") as file:
                        file.write(f"{display_name},{set_display_name},{case_display_name},{case_evaluation},{eval_score}\n")

                    # Add the evaluation score to the total evaluation score
                    total_eval_score += eval_score

                    # If this was the last repeat for this test case, calculate the average evaluation score
                    if i == case_repeat - 1:
                        average_eval_score = total_eval_score / case_repeat
                        print(f"Average evaluation score for {case_display_name} ({display_name}): {average_eval_score:.2f}%")

                    # Check whether we're about to exceed the rate limit (as specified by the API)
                    if requests_since_last_check >= rate_limits_per_minute[api_name]:
                        time_since_last_check = time.time() - time_now
                        if time_since_last_check < 60:
                            print(f"Sleeping for {60 - time_since_last_check + 5} seconds to avoid rate limit errors ({i+1} / {case_repeat})...")
                            time.sleep(60 - time_since_last_check + 5) # Add 5 seconds to account for network latency etc
                        time_now = time.time()
                        requests_since_last_check = 0
                    
if __name__ == "__main__":
    main()