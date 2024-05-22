# Simple LLM Eval Runner

This project was created to write and test new evals against arbitrary LLMs as easily as possible. The responses can be evaluated automatically if an eval has a set-in-stone expected output, or manually evaluated. Results will be stored in a separate folder tree with full responses of each eval for each model, as well as summaries of scores.

Made in Python with just a couple of JSON files to define the large language models you want to test and the evals you want to run. When you want to add a new model to test, either find the corresponding Python file to use an existing API, or create a new Python file in the model_apis directory for the new API you want to use, and add it to the models array in the test_definition.json file. When adding more evals, add them to the cases.json file, along a text file containing the actual prompt.

The code for actually calling the LLM APIs assumes that you have your API keys in the appropriate environment variable, as defined in the API's documentation.

# Evaluation Types

Current, in the test_sets.yml file, the "evaluation" for each eval can be either 'exact', 'contains', or 'manual'. All string comparison evaluations are case insensitive.
- 'exact' means the LLM's response must be exactly the single string given in the evaluation_answers array. 
- 'contains' means that the LLM's response must contain the strings given in the evaluation_answers array, and is scored for each correct answer.
- 'contains_all' means that the LLM's response must contain all strings given in the evaluation_answers array, and only gets a score if all answers were present.
- 'automatic' uses a model (currently Llama 3 70B through Groq for a good mix of speed, quality and cost) to compare the given response to the reference answers, and give a full score if its finds that they match (this is not perfectly reliable).
- 'manual' means that the user is presented with the prompt, the answer(s) listed in the evaluation_answers array, and the LLM's response, and must put in an evaluation score between 0 and 100.

# Evaluation Ratings

Evaluation metric is a score from 0 to 100. For exact match or 'contains all' evaluations, this will only be 0 and 100. For automatic model-based evaluation, the model will be asked if the provided answer matches the provided correct answer, giving a boolean answer, which will be translated to 0 or 100. For manual evaluation, use your own judgement, but here is some guidance (mostly for myself):
- 0: Complete and utter failure to do anything remotely like correct reasoning or a correct answer
- 1-40: Shows some level of understanding of the problem, but fails to correctly reason about it
- 41-60: Gets it about equal parts right and wrong
- 61-90: Gets the reasoning/recall mostly right, and may get the answer completely right, but some of the reasoning is flawed or missing
- 91-100: Perfect reasoning/recall leading to a correct answer

# Difficulty Ratings:

## Context length: 0-10
The difficulty rating is measured on a logarithmic scale, with 7 being 10,000,000 tokens, 6 being 1,000,000 tokens, etc. Not all numbers will be used in practice, at least until we reach models which can process much longer context lengths.

## Reasoning depth: 0-10
The difficulty rating is based on the directness of the connection between a clue given in the context, and the answer. 
- 0: For something where the answer is directly in the context (essentially just retrieval, not reasoning).
    - Context: Bob is in Paris.
    - Question: Which city is Bob in?
- 1: For something where the answer is directly related to a clue in the context
    - Context: Bob is at the Eiffel tower.
    - Question: Which city is Bob in?
- 2: For something where the answer is related to two clues in the context, or the clue given in the context leads to a new conclusion which itself leads to the answer
    - Context: The animal spat at the passerby while being shorn.
    - Question: What animal is likely to be the subject of the above sentence?
    
    - Context: The mother of the lead singer of the band 'Queen' was very proud.
    - Question: What is the aforementioned mother's name?

If it's hard to get a true rating, just estimate it.

## Instruction Compliance: 0-10
The difficulty rating is based on the intricacies of the required output. Requiring no set format, and no other (non-format related) specific instructions while answering, would be a rating of 0. Half of difficulty should come from requiring a particular output format, adding 1-5 points depending on how detailed/strange the output format is. The other half of the rating comes from specific instructions, for example requiring the output to contain a certain word at the end of every sentence (e.g. the apple test), or asked to answer in a particular style. The exact number of points will probably end up being quite subjective, but as long as you're consistent across your evals, it's probably fine.

Example: asking for a direct answer without any discussion, CoT or any extraneous text at all would probably be a rating of 2 or 3 (one or two points of difficulty for a single answer format, one or two points of difficulty for following the instructions of not saying anything except for the answer).

## TODO
- [ ] Create a view of the results in more details, specifically a cross reference of how each model (down the left) do against each problem (across the top), as well as a view of the results where we should how well each model does in each of the difficulty categories.
- [ ] When doing manual evaluation, instead of giving a 0-100 score, you can instead start typing a follow-up question, in case you want to maybe double check the LLM's understanding of something in the eval, or the 'reasoning' for its answer. The response will then be displayed, at which point you can then give your rating or ask more questions. The follow-up questions and responses will be included in the record of the responses.
- [x] Allow a chosen LLM to evaluate a response, instead of having the user do it.

## Thanks

Inspired by babel.cloud's LLM-RGB evaluations, from which I will be nicking some of the test cases.
