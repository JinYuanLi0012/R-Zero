import argparse
import json
import os
from pathlib import Path
from tqdm import tqdm

from recheck_api import JudgeRequestError, config_from_env, request_judgement

DEFAULT_DATASETS = ["math", "gsm8k", "amc", "minerva", "olympiad", "aime2024", "aime2025"]


def load_openai_key(token_file: Path):
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key
    try:
        return json.loads(token_file.read_text()).get("openai")
    except Exception:
        return None


RECHECK_CONFIG = config_from_env()


def judge_model_response(api_url, api_key, gold_answer, model_response):
    return request_judgement(
        api_url,
        api_key,
        gold_answer,
        model_response,
        config=RECHECK_CONFIG,
    )


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
    judge_failures = 0
    if api_url and api_key:
        for row in tqdm(rows, desc=f"{dataset}"):
            if float(row.get("score", 0)) < 0.5:
                try:
                    verdict = judge_model_response(api_url, api_key, row["answer"], row["response"])
                except JudgeRequestError as exc:
                    judge_failures += 1
                    print(
                        f"WARNING: judge API failed on {model} {dataset}; "
                        f"preserving local score: {exc}",
                        flush=True,
                    )
                    continue
                if "yes" in verdict.lower():
                    row["score"] = 1
    else:
        print("No API key configured; using local raw scores.", flush=True)
    return (
        round(sum(float(row.get("score", 0)) for row in rows) / len(rows) * 100, 2),
        judge_failures,
    )


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
    total_judge_failures = 0
    for model in models:
        for dataset in datasets:
            if (model, dataset) in completed:
                print(f"SKIP done: {model} {dataset}", flush=True)
                continue
            print(f"RUN: {model} {dataset}", flush=True)
            score, judge_failures = recheck_dataset(storage_path, model, dataset, api_url, api_key)
            total_judge_failures += judge_failures
            if judge_failures:
                print(
                    f"WARNING: {model} {dataset} had {judge_failures} judge API failure(s); "
                    "those rows kept their original local scores.",
                    flush=True,
                )
            record = {
                "model": model,
                "dataset": dataset,
                "score": score,
                "judge_failures": judge_failures,
            }
            with output_file.open("a") as f:
                json.dump(record, f)
                f.write("\n")
            completed.add((model, dataset))
            print(f"DONE: {model} {dataset} {score}", flush=True)
    print(f"completed after finish: {len(completed)}/{total}", flush=True)
    if total_judge_failures:
        print(
            f"WARNING: evaluation completed with {total_judge_failures} total judge API "
            "failure(s); original local scores were preserved for those rows.",
            flush=True,
        )


if __name__ == "__main__":
    main()
