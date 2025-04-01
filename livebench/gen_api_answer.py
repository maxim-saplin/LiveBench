"""Generate answers with GPT-4

Usage:
python3 gen_api_answer.py --model gpt-3.5-turbo
"""

import argparse
import json
import os
import time
import concurrent.futures
import glob
import shortuuid
import tqdm
import random
import datetime
import string

from livebench.common import (
    LIVE_BENCH_RELEASES,
    reorg_answer_file,
    get_categories_tasks,
    load_questions,
    load_questions_jsonl,
    LIVE_BENCH_DATA_SUPER_PATH,
    filter_questions
)
from livebench.model.completions import chat_completion_openai

from livebench.model import Model, get_model


def get_answer(
    question: dict,
    model: Model,
    num_choices: int,
    max_tokens: int,
    answer_file: str,
    api_dict: dict | None = None,
    stream: bool = False,
    force_temperature: float | None = None,
    randomize_prompt: bool = False,
    add_noise: bool = False
):
    """
    Perform inference for a single question.

    Args:
        question: At minimum, a dictionary with a key 'turns' that maps to a list of messages in the conversation, the last of which should ask the question.
        model: The API name for the model (e.g. gpt-4o-mini or claude-3-5-sonnet-20240620)
        num_choices: The number of model outputs to generate for each question
        max_tokens: The maximum number of tokens for each model response
        answer_file: The path to the file in which to write answers
        api_dict: A dictionary specifying the base API URL and key for model requests
        stream: Whether to stream the model's response
        force_temperature: Override the temperature setting
        randomize_prompt: Whether to add a randomized header to the prompt
        add_noise: Whether to simulate typos by replacing letters with 1% probability
    """
    assert (
        force_temperature is not None and "required_temperature" in question.keys()
    ) is False
    
    if force_temperature is not None:
        temperature = args.force_temperature
    elif "required_temperature" in question.keys():
        temperature = question["required_temperature"]
    else:
        temperature = 0
    
    # Pre-generate random prefix if needed (outside the loop so it's consistent across choices)
    random_prefix = ""
    if randomize_prompt:
        # Generate random name with letter-digit-letter-digit pattern
        letters = 'abcdefgh'
        digits = '12345678'
        name = random.choice(letters) + random.choice(digits) + random.choice(letters) + random.choice(digits)
        now = datetime.datetime.now()
        datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")
        random_prefix = f"Hello {name}, {datetime_str}\n\n"

    choices = []
    total_num_tokens = 0
    for i in range(num_choices):
        conv = model.adapter.get_default_conv_template(model.api_name)

        # Create a modified_question object to track changes if we're applying any modifications
        modified_question = None
        if randomize_prompt or add_noise:
            modified_question = dict(question)
            modified_question["turns"] = list(question["turns"])

        turns = []
        for j in range(len(question["turns"])):
            prompt_text = question["turns"][j]
            modified_prompt = prompt_text
            modifications_applied = False
            
            # Apply randomization only to the first turn
            if randomize_prompt and j == 0:
                modified_prompt = random_prefix + modified_prompt
                modifications_applied = True
            
            # Apply noise with 1% probability for each letter
            if add_noise:
                noisy_text = ""
                for char in modified_prompt:
                    if char.isalpha() and random.random() < 0.01:  # 1% chance to replace a letter with another random letter
                        if char.isupper():
                            noisy_text += random.choice(string.ascii_uppercase)
                        else:
                            noisy_text += random.choice(string.ascii_lowercase)
                    else:
                        noisy_text += char
                
                # Only consider it modified if at least one character changed
                if noisy_text != modified_prompt:
                    modified_prompt = noisy_text
                    modifications_applied = True
            
            # Store the modified turn for future reference
            if modified_question is not None and modifications_applied:
                modified_question["turns"][j] = modified_prompt
            
            # Use the modified prompt for the actual API call
            conv.append_message(conv.roles[0], modified_prompt)
            conv.append_message(conv.roles[1], None)

            if api_dict is not None:
                output, num_tokens = chat_completion_openai(
                    model, conv, temperature, max_tokens, api_dict=api_dict, stream=stream
                )
            else:
                assert model.api_function is not None
                output, num_tokens = model.api_function(
                    model, conv, temperature, max_tokens, api_dict=api_dict
                )

            conv.update_last_message(output)
            turns.append(output)
            total_num_tokens += num_tokens

        choices.append({"index": i, "turns": turns})

    # Dump answers
    ans = {
        "question_id": question["question_id"],
        "answer_id": shortuuid.uuid(),
        "model_id": model.display_name,
        "choices": choices,
        "tstamp": time.time(),
        "total_output_tokens": total_num_tokens,
    }

    os.makedirs(os.path.dirname(answer_file), exist_ok=True)
    with open(answer_file, "a") as fout:
        fout.write(json.dumps(ans) + "\n")
    
    # If we applied modifications (randomize_prompt or add_noise), save the modified question
    if modified_question is not None:
        # Create a path for the questions file based on the answer file
        questions_file = answer_file.replace(".jsonl", "_QUESTIONS.jsonlx") # use jsonlx in order to to confuse with model results
        
        # Save information about modifications
        modification_data = {
            "question_id": question["question_id"],
            "model_id": model.display_name,
            "original_turns": question["turns"],
            "modified_turns": modified_question["turns"],
            "randomize_prompt_applied": randomize_prompt,
            "add_noise_applied": add_noise,
            "random_prefix": random_prefix if randomize_prompt else "",
            "tstamp": time.time(),
        }
        
        # Save the modified question
        with open(questions_file, "a") as fout:
            fout.write(json.dumps(modification_data) + "\n")


def run_questions(
    parallel,
    questions: list[dict],
    model: Model,
    num_choices: int,
    max_tokens: int,
    answer_file: str,
    api_dict: dict | None,
    stream: bool,
    force_temperature: float | None,
    randomize_prompt: bool = False,
    add_noise: bool = False
):
    """
    Perform inference on a list of questions. Output answers to answer_file.

    Args:
        questions: The list of questions.
        model: The API name for the model (e.g. gpt-4o-mini or claude-3-5-sonnet-20240620)
        num_choices: The number of model outputs to generate for each question
        max_tokens: The maximum number of tokens for each model response
        answer_file: The path to the file in which to write answers
        parallel: The number of workers to use to make concurrent API requests
        api_dict: A dictionary specifying the base API URL and key for model requests
        stream: Whether to stream the model's response
        force_temperature: Override the temperature setting
        randomize_prompt: Whether to add a randomized header to the prompt
        add_noise: Whether to simulate typos by replacing letters with 1% probability
    """
    if randomize_prompt:
        questions_file = answer_file.replace(".jsonl", "_QUESTIONS.jsonlx") # use jsonlx in order to to confuse with model results
        # Initialize the questions file (create or truncate)
        os.makedirs(os.path.dirname(questions_file), exist_ok=True)
        
        # Only initialize if not resuming or retrying failures
        if not args.resume and not args.retry_failures:
            with open(questions_file, "w") as f:
                pass  # Just create an empty file

    if parallel == 1:
        for question in tqdm.tqdm(questions):
            get_answer(
                question,
                model,
                num_choices,
                max_tokens,
                answer_file,
                api_dict=api_dict,
                stream=stream,
                force_temperature=force_temperature,
                randomize_prompt=randomize_prompt,
                add_noise=add_noise
            )
        if len(questions) > 0:
            reorg_answer_file(answer_file)
    else:

        with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = []
            for question in questions:
                future = executor.submit(
                    get_answer,
                    question,
                    model,
                    num_choices,
                    max_tokens,
                    answer_file,
                    api_dict=api_dict,
                    stream=stream,
                    force_temperature=force_temperature,
                    randomize_prompt=randomize_prompt,
                    add_noise=add_noise
                )
                futures.append(future)

            for future in tqdm.tqdm(
                concurrent.futures.as_completed(futures), total=len(futures)
            ):
                future.result()
        if len(questions) > 0:
            reorg_answer_file(answer_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate benchmark question answers using an API-based model"
    )
    parser.add_argument(
        "--bench-name",
        type=str,
        default="live_bench",
        help="The name of the benchmark question set. Defaults to 'live_bench', or all tasks in the benchmark. Specify e.g. live_bench/reasoning/web_of_lies_v2 to generate only for that task.",
    )
    parser.add_argument(
        "--api-base",
        type=str,
        default=None,
        help="If provided, will be used as the base of an openai API request, along with the environment variable LIVEBENCH_API_KEY",
    )
    parser.add_argument("--model", type=str, default="gpt-3.5-turbo")
    parser.add_argument(
        "--num-choices",
        type=int,
        default=1,
        help="How many completion choices to generate.",
    )
    parser.add_argument(
        "--force-temperature", type=float, help="Forcibly set a sampling temperature."
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="The maximum number of new generated tokens.",
    )
    parser.add_argument(
        "--question-begin",
        type=int,
        help="A debug option. The begin index of questions.",
    )
    parser.add_argument(
        "--question-end", type=int, help="A debug option. The end index of questions."
    )
    parser.add_argument(
        "--parallel", type=int, default=1, help="The number of concurrent API calls."
    )
    parser.add_argument(
        "--question-source",
        type=str,
        default="huggingface",
        help="The source of the questions. 'huggingface' will draw questions from huggingface. 'jsonl' will gather local jsonl files at data/{bench_name}/**/question.jsonl to permit tweaking or writing custom questions.",
    )
    parser.add_argument(
        "--livebench-release-option",
        type=str,
        default=max(LIVE_BENCH_RELEASES),
        choices=sorted(LIVE_BENCH_RELEASES),
        help="Livebench release to use. Provide a single date option. Will handle excluding deprecated questions for selected release.",
    )
    parser.add_argument(
        "--question-id",
        type=str,
        default=None,
        nargs="+",
        help="A list of question ids to generate answers for.",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=False,
        help="Do not generate answers for questions that have already been generated, unless they were errors and --retry-failures is set."
    )
    parser.add_argument(
        "--model-display-name",
        type=str,
        default=None,
        help="Optional display name of the model. If not provided, will be inferred from --model.",
    )
    parser.add_argument(
        "--retry-failures",
        action="store_true",
        default=False,
        help="Retry generating answers for questions that have failed in the past.",
    )
    parser.add_argument(
        "--stream",
        action="store_true",
        default=False,
        help="Stream responses, for models that support streaming"
    )
    parser.add_argument(
        "--randomize-prompt",
        action="store_true",
        default=False,
        help="Add a randomized header to each prompt (Hello {name}, {datetime})"
    )
    parser.add_argument(
        "--add-noise",
        action="store_true",
        default=False,
        help="Simulate typos by replacing letters with 1% probability"
    )
    args = parser.parse_args()

    model = get_model(args.model)

    if args.model_display_name is not None:
        model_dict = model.__dict__
        model_dict["display_name"] = args.model_display_name
        model = type(model)(**model_dict)

    if args.livebench_release_option not in LIVE_BENCH_RELEASES:
        raise ValueError(f"Bad release {args.livebench_release_option}.")

    release_set = set(
        [r for r in LIVE_BENCH_RELEASES if r <= args.livebench_release_option]
    )

    if args.api_base is not None:
        # use manually-specified model API

        api_key = os.environ.get("LIVEBENCH_API_KEY", "EMPTY")

        api_dict = {
            "api_key": api_key,
            "api_base": args.api_base,
        }
    else:
        api_dict = None

    if args.question_source == "huggingface":
        categories, tasks = get_categories_tasks(args.bench_name)

        for category_name, task_names in tasks.items():
            for task_name in task_names:
                questions = load_questions(
                    categories[category_name],
                    release_set,
                    args.livebench_release_option,
                    task_name,
                    args.question_id
                )

                questions = questions[args.question_begin:args.question_end]

                task_full_name = (
                    f"{LIVE_BENCH_DATA_SUPER_PATH}/{category_name}/{task_name}"
                )
                answer_file = (
                    f"data/{task_full_name}/model_answer/{model.display_name}.jsonl"
                )

                questions = filter_questions(questions, answer_file, args.resume, args.retry_failures)

                print(f"Questions from {task_full_name}")
                print(f"Output to {answer_file}")

                run_questions(
                    parallel=args.parallel,
                    questions=questions,
                    model=model,
                    num_choices=args.num_choices,
                    max_tokens=args.max_tokens,
                    answer_file=answer_file,
                    api_dict=api_dict,
                    stream=args.stream,
                    force_temperature=args.force_temperature,
                    randomize_prompt=args.randomize_prompt,
                    add_noise=args.add_noise
                )

    elif args.question_source == "jsonl":
        # use locally-provided questions

        list_of_question_files = []
        original_question_file = f"data/{args.bench_name}/question.jsonl"
        if os.path.exists(original_question_file):
            # if one specific file for bench_name exists, use it (e.g. if bench_name = live_bench/math/AMPS_Hard)
            list_of_question_files = [original_question_file]
        else:
            # gather all question files for bench_name (e.g. if bench_name = live_bench/math)
            list_of_question_files = glob.glob(
                f"data/{args.bench_name}/**/question.jsonl", recursive=True
            )

        for question_file in list_of_question_files:
            print(question_file)
            questions = load_questions_jsonl(
                question_file, release_set, args.livebench_release_option, args.question_id
            )
            
            questions = questions[args.question_begin:args.question_end]

            bench_name = os.path.dirname(question_file).replace("data/", "")
            answer_file = f"data/{bench_name}/model_answer/{model.display_name}.jsonl"

            questions = filter_questions(questions, answer_file, args.resume, args.retry_failures)
                    
            print(f"Questions from {question_file}")
            print(f"Output to {answer_file}")

            run_questions(
                parallel=args.parallel,
                questions=questions,
                model=model,
                num_choices=args.num_choices,
                max_tokens=args.max_tokens,
                answer_file=answer_file,
                api_dict=api_dict,
                stream=args.stream,
                force_temperature=args.force_temperature,
                randomize_prompt=args.randomize_prompt,
                add_noise=args.add_noise
            )

    else:
        raise ValueError(f"Bad question source {args.question_source}.")
