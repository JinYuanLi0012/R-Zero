import argparse
import json
import os
from pathlib import Path
import random
import requests
from tqdm import tqdm

DEFAULT_DATASETS = ["math", "gsm8k", "amc", "minerva", "olympiad", "aime2024", "aime2025"]


def load_openai_key(token_file: Path):
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key
    try:
        return json.loads(token_file.read_text()).get("openai")
    except Exception:
        return None


def judge_model_response(api_url, api_key, gold_answer, model_response):
    payload = {
        "model": os.getenv("RECHECK_JUDGE_MODEL", "gpt-4o"),
        "messages": [
            {"role": "system", "content": "You are a math answer checker."},
            {
                "role": "user",
                "content": (
                    f"Hi, there is a model response: {model_response}\n\n"
                    f", and the ground truth answer is: {gold_answer}\n\n"
                    "please check whether the model response is correct or not, "
                    "and return the **only** Yes or No."
                ),
            },
        ],
        "temperature": 0.1,
    }
    if "api.openai.com" in api_url or api_url.rstrip("/").endswith("/chat/completions"):
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    else:
        headers = {"api-key": api_key, "Content-Type": "application/json"}
    response = requests.post(api_url, headers=headers, json=payload, timeout=20)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def load_completed(output_file: Path):
    completed = set()
    if not output_file.exists():
        return completed
    for line in output_file.read_text().splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        model = item.get("model")
        dataset = item.get("dataset")
        if model and dataset:
            completed.add((model, dataset))
    return completed


def model_eval_dir(storage_path: Path, model: str):
    return storage_path / "evaluation" / model.replace("/", "_")


def recheck_dataset(storage_path, model, dataset, api_url, api_key):
    result_file = model_eval_dir(storage_path, model) / f"results_{dataset}.json"
    if not result_file.exists():
        raise FileNotFoundError(result_file)
    results = json.loads(result_file.read_text())
    rows = results[:-1]
    if api_url and api_key:
        for row in tqdm(rows, desc=f"{dataset}"):
            if float(row.get("score", 0)) < 0.5:
                try:
                    verdict = judge_model_response(api_url, api_key, row["answer"], row["response"])
                except Exception as exc:
                    print(f"judge error on {model} {dataset}: {exc}", flush=True)
                    verdict = "No"
                if "yes" in verdict.lower():
                    row["score"] = 1
    else:
        print("No API key configured; using local raw scores.", flush=True)
    return round(sum(float(row.get("score", 0)) for row in rows) / len(rows) * 100, 2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models_file", required=True)
    parser.add_argument("--output_file", required=True)
    parser.add_argument("--datasets", default=",".join(DEFAULT_DATASETS))
    parser.add_argument("--token_file", default="tokens.json")
    parser.add_argument("--dry_run", action="store_true")
    args = parser.parse_args()

    storage_env = os.getenv("STORAGE_PATH")
    if not storage_env:
        raise RuntimeError("STORAGE_PATH is not set; source env_rzero.sh first")
    storage_path = Path(storage_env)
    output_file = Path(args.output_file)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    models = [line.strip() for line in Path(args.models_file).read_text().splitlines() if line.strip()]
    datasets = [x.strip() for x in args.datasets.split(",") if x.strip()]
    completed = load_completed(output_file)

    api_key = load_openai_key(Path(args.token_file))
    api_url = None
    if api_key:
        api_base = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        api_url = f"{api_base}/chat/completions"

    total = len(models) * len(datasets)
    pending = [(model, dataset) for model in models for dataset in datasets if (model, dataset) not in completed]
    print(f"completed before start: {len(completed)}/{total}", flush=True)
    print(f"pending: {len(pending)}/{total}", flush=True)
    for model, dataset in pending:
        print(f"PENDING: {model} {dataset}", flush=True)
    if args.dry_run:
        return
    for model in models:
        for dataset in datasets:
            if (model, dataset) in completed:
                print(f"SKIP done: {model} {dataset}", flush=True)
                continue
            print(f"RUN: {model} {dataset}", flush=True)
            score = recheck_dataset(storage_path, model, dataset, api_url, api_key)
            record = {"model": model, "dataset": dataset, "score": score}
            with output_file.open("a") as f:
                json.dump(record, f)
                f.write("\n")
            completed.add((model, dataset))
            print(f"DONE: {model} {dataset} {score}", flush=True)
    print(f"completed after finish: {len(completed)}/{total}", flush=True)


if __name__ == "__main__":
    main()
