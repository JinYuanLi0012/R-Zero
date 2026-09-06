import json
import requests
import random
import argparse
import os

try:
    from evaluation.local_judge import LocalJudge, local_backend
    from evaluation.recheck_common import recheck_concurrency, recheck_rows
except ModuleNotFoundError:  # Support `python evaluation/results_recheck.py`.
    from local_judge import LocalJudge, local_backend
    from recheck_common import recheck_concurrency, recheck_rows

STORAGE_PATH = os.getenv("STORAGE_PATH")
FINAL_RESULTS_FILE = os.getenv("FINAL_RESULTS_FILE", "final_results.jsonl")
RECHECK_JUDGE_MODEL = os.getenv("RECHECK_JUDGE_MODEL", "gpt-4o")
RECHECK_REASONING_EFFORT = os.getenv("RECHECK_REASONING_EFFORT")
RECHECK_MAX_COMPLETION_TOKENS = int(os.getenv("RECHECK_MAX_COMPLETION_TOKENS", "8"))
api_urls = []
api_keys = []

IS_LOCAL = local_backend()
openai_key = None if IS_LOCAL else os.getenv("OPENAI_API_KEY")
if not IS_LOCAL and not openai_key:
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
    try:
        gold_answer = answer
        model_response = response
        example = {
            "model": RECHECK_JUDGE_MODEL,
            "messages": [
                {"role": "system", "content": "You are a math answer checker."},
                {"role": "user", "content": f"Hi, there is a model response: {model_response}\n\n, and the ground truth answer is: {gold_answer}\n\n, please check whether the model response is correct or not, and return the **only** Yes or No."}
            ],
        }
        if RECHECK_JUDGE_MODEL.startswith("gpt-5"):
            example["max_completion_tokens"] = RECHECK_MAX_COMPLETION_TOKENS
            if RECHECK_REASONING_EFFORT:
                example["reasoning_effort"] = RECHECK_REASONING_EFFORT
        else:
            example["temperature"] = 0.1
        api_index = random.randint(0, len(api_urls)-1)
        api_url = api_urls[api_index]
        api_key = api_keys[api_index]
        if "api.openai.com" in api_url or api_url.rstrip('/').endswith('/chat/completions'):
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        else:
            headers = {"api-key": api_key, "Content-Type": "application/json"}
        response = requests.post(api_url, headers=headers, json=example, timeout=20)
        response.raise_for_status()
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        print(e)
        return "No"
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, default="Qwen/Qwen2.5-7B-Instruct")
    parser.add_argument("--datasets", default=os.getenv("EVAL_TASKS", "math,gsm8k,amc,minerva,olympiad,aime2024,aime2025"))
    args = parser.parse_args()
    local_judge = LocalJudge() if IS_LOCAL else None
    concurrency = recheck_concurrency()

    new_results = []
    print(f"Recheck judge: {local_judge.metadata if IS_LOCAL else RECHECK_JUDGE_MODEL}")
    print(f"Recheck concurrency: {concurrency}")
    if RECHECK_REASONING_EFFORT and not IS_LOCAL:
        print(f"Recheck reasoning effort: {RECHECK_REASONING_EFFORT}")
    for model_name in [args.model_name]:
        for dataset in args.datasets.split(","):
            with open(f'{STORAGE_PATH}/evaluation/{model_name.replace("/","_")}/results_{dataset}.json', 'r') as f:
                results = json.load(f)

            rows = results[:-1]
            if local_judge or (api_urls and api_keys):
                recheck_rows(
                    rows,
                    local_judge or process_example,
                    concurrency,
                    f"{model_name} {dataset}",
                    strict=IS_LOCAL,
                )
            else:
                print("No API urls configured; skipping GPT recheck and using local scores.")
            score = round(sum(result['score'] for result in rows) / len(rows) * 100, 2)
            new_results.append({
                'model': model_name,
                'dataset': dataset,
                'score': score,
            })
            print(new_results)
            with open(FINAL_RESULTS_FILE, 'a') as f:
                json.dump({
                    'model': model_name,
                    'dataset': dataset,
                    'score': score,
                    **({'recheck': local_judge.metadata} if IS_LOCAL else {}),
                }, f)
                f.write('\n')


if __name__ == "__main__":
    main()
