import json
from mathruler.grader import extract_boxed_content, grade_answer
import openai
import requests
from tqdm import tqdm
import random
import argparse
import os

parser = argparse.ArgumentParser()
parser.add_argument("--model_name", type=str, default="Qwen/Qwen2.5-7B-Instruct")
args = parser.parse_args()

STORAGE_PATH = os.getenv("STORAGE_PATH")
FINAL_RESULTS_FILE = os.getenv("FINAL_RESULTS_FILE", "final_results.jsonl")
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
    try:
        gold_answer = answer
        model_response = response
        example = {
            "model": "gpt-4o",
            "messages": [
                {"role": "system", "content": "You are a math answer checker."},
                {"role": "user", "content": f"Hi, there is a model response: {model_response}\n\n, and the ground truth answer is: {gold_answer}\n\n, please check whether the model response is correct or not, and return the **only** Yes or No."}
            ],
            "temperature": 0.1
        }
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
new_results = []
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

        if api_urls and api_keys:
            for i in tqdm(range(len(results)-1)):
                    if results[i]['score'] < 0.5:
                        gpt_check = process_example(results[i]['answer'],results[i]['response'])
                        if "yes" in gpt_check.lower():
                            results[i]['score']=1
        else:
            print("No API urls configured; skipping GPT recheck and using local scores.")
        new_results.append({
            'model': model_name,
            'dataset': dataset,
            'score': round(sum([result['score'] for result in results[:-1]])/len(results[:-1])*100, 2)
        })
        print(new_results)
        with open(FINAL_RESULTS_FILE, 'a') as f:
            json.dump({
                'model': model_name,
                'dataset': dataset,
                'score': round(sum([result['score'] for result in results[:-1]])/len(results[:-1])*100, 2)
            }, f)
            f.write('\n')




