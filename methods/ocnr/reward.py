"""Original R-Zero parsing/BLEU + paper Eq.20 uncertainty + Eq.17 OCNR.

No Validity-RZero, Terra, semantic judge, taxonomy, or previous treatments.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from mathruler.grader import extract_boxed_content

from methods.ocnr.bleu import cluster_share_per_problem


def solver_scores(rows, num_services, port_base):
    root = Path(os.environ["OCNR_REWARD_DIR"])
    root.mkdir(parents=True, exist_ok=True)
    indices = [list(range(i, len(rows), num_services)) for i in range(num_services)]

    def fetch(shard):
        ids = indices[shard]
        if not ids:
            return []
        path = root / f"request-{uuid.uuid4().hex}.json"
        output = path.with_name(path.stem + "_results.json")
        path.write_text(json.dumps([rows[i] for i in ids]))
        session = requests.Session()
        session.trust_env = False
        try:
            response = session.get(f"http://127.0.0.1:{port_base + shard}/hello",
                                   params={"name": str(path)}, timeout=14400)
            response.raise_for_status()
            result = json.loads(output.read_text())
            if len(result) != len(ids):
                raise ValueError("Solver result count mismatch")
            return list(zip(ids, result))
        finally:
            session.close()
            path.unlink(missing_ok=True)
            output.unlink(missing_ok=True)

    ordered = [None] * len(rows)
    with ThreadPoolExecutor(max_workers=num_services) as pool:
        for shard in pool.map(fetch, range(num_services)):
            for index, row in shard:
                ordered[index] = row
    return ordered


def compute_score(predicts, ground_truths, num_services=1, port_base=5200,
                  novelty_port=5202, novelty_coefficient=0.3,
                  uncertainty_scale=2.0, **_):
    if os.getenv("VALIDITY_RZERO_ENABLED", "0") != "0":
        raise RuntimeError("OCNR must run on the pure R-Zero path")
    parsed = []
    for predict in predicts:
        questions = re.findall(r"<question>(.*?)</question>", predict, re.DOTALL)
        answer = extract_boxed_content(predict)
        # Retain upstream reward parsing (answer used only as a nonempty marker).
        parsed.append({"question": questions[-1].strip(), "answer": answer[-1].strip()}
                      if questions and answer else {"question": "", "answer": ""})
    results = solver_scores(parsed, num_services, port_base)
    texts = [row["question"] for row in results]
    penalty = cluster_share_per_problem(texts, distance_threshold=0.5) if len(texts) > 1 else [1.0] * len(texts)
    novelty = [0.0] * len(results)
    distance = [0.0] * len(results)
    valid = [i for i, row in enumerate(results) if row["question"] and row["score"] >= 0]
    if novelty_coefficient and valid:
        session = requests.Session()
        session.trust_env = False
        try:
            response = session.post(f"http://127.0.0.1:{novelty_port}/novelty",
                                    json={"questions": [texts[i] for i in valid]}, timeout=14400)
            response.raise_for_status()
            values = response.json()
        finally:
            session.close()
        if len(values["novelty"]) != len(valid):
            raise ValueError("novelty count mismatch")
        for position, index in enumerate(valid):
            novelty[index] = float(values["novelty"][position])
            distance[index] = float(values["distance_squared"][position])
    scores, audit = [], []
    for i, row in enumerate(results):
        frontier = uncertainty_scale * min(row["score"], 1 - row["score"]) if row["question"] else -1.0
        base = frontier - penalty[i]
        bonus = novelty_coefficient * novelty[i]
        scores.append({"overall": base + bonus, "format": float(bool(row["question"])),
                       "accuracy": penalty[i], "base_reward": base, "frontier_reward": frontier,
                       "novelty": novelty[i], "novelty_bonus": bonus, "sd_distance_squared": distance[i]})
        audit.append({"question": texts[i], "solver_score": row["score"], **scores[-1]})
    path = Path(os.environ["OCNR_REWARD_DIR"]) / f"reward-{uuid.uuid4().hex}.json"
    path.write_text(json.dumps(audit, ensure_ascii=False))
    return scores
