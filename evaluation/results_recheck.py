import json
from mathruler.grader import extract_boxed_content, grade_answer
import openai
from tqdm import tqdm
import random
import argparse
import os

from recheck_api import JudgeRequestError, config_from_env, request_judgement

parser = argparse.ArgumentParser()
parser.add_argument("--model_name", type=str, default="Qwen/Qwen2.5-7B-Instruct")
args = parser.parse_args()

STORAGE_PATH = os.getenv("STORAGE_PATH")
FINAL_RESULTS_FILE = os.getenv("FINAL_RESULTS_FILE", "final_results.jsonl")
RECHECK_CONFIG = config_from_env()
api_urls = []
api_keys = []

openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    try:
        with open('tokens.json', 'r') as f:
            openai_key = json.load(f).get('openai')
    except Exception:
        openai_key = None
if openai_key:
    api_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip('/')
    api_urls.append(f"{api_base}/chat/completions")
    api_keys.append(openai_key)

def process_example(answer, response):
    api_index = random.randint(0, len(api_urls)-1)
    return request_judgement(
        api_urls[api_index],
        api_keys[api_index],
        answer,
        response,
        config=RECHECK_CONFIG,
    )

new_results = []
total_judge_failures = 0
for model_name in [args.model_name]:
    for dataset in [
    "math",
    "gsm8k", 
    "amc",
    "minerva",
    "olympiad",
    "aime2024",
    "aime2025",
    ]:
        with open(f'{STORAGE_PATH}/evaluation/{model_name.replace("/","_")}/results_{dataset}.json', 'r') as f:
            results = json.load(f)

        dataset_judge_failures = 0
        if api_urls and api_keys:
            for i in tqdm(range(len(results)-1)):
                    if results[i]['score'] < 0.5:
                        try:
                            gpt_check = process_example(results[i]['answer'],results[i]['response'])
                        except JudgeRequestError as exc:
                            dataset_judge_failures += 1
                            print(
                                f"WARNING: judge API failed for {model_name} {dataset} row {i}; "
                                f"preserving local score: {exc}",
                                flush=True,
                            )
                            continue
                        if "yes" in gpt_check.lower():
                            results[i]['score']=1
        else:
            print("No API urls configured; skipping GPT recheck and using local scores.")
        total_judge_failures += dataset_judge_failures
        if dataset_judge_failures:
            print(
                f"WARNING: {model_name} {dataset} had {dataset_judge_failures} judge API "
                "failure(s); those rows kept their original local scores.",
                flush=True,
            )
        new_results.append({
            'model': model_name,
            'dataset': dataset,
            'score': round(sum([result['score'] for result in results[:-1]])/len(results[:-1])*100, 2),
            'judge_failures': dataset_judge_failures,
        })
        print(new_results)
        with open(FINAL_RESULTS_FILE, 'a') as f:
            json.dump({
                'model': model_name,
                'dataset': dataset,
                'score': round(sum([result['score'] for result in results[:-1]])/len(results[:-1])*100, 2),
                'judge_failures': dataset_judge_failures,
            }, f)
            f.write('\n')

if total_judge_failures:
    print(
        f"WARNING: evaluation completed with {total_judge_failures} total judge API "
        "failure(s); original local scores were preserved for those rows.",
        flush=True,
    )


