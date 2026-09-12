"""One dedicated GPU: online novelty service or post-Solver SD fitting."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np

from methods.ocnr.core import fit_prototype, seenness, write_json
from methods.ocnr.features import SolverFeatures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["fit", "serve"])
    parser.add_argument("--model", required=True)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--data", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--round", type=int)
    parser.add_argument("--port", type=int, default=5202)
    parser.add_argument("--run-id", default="")
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    state = json.loads(args.state.read_text()) if args.state else None
    if args.mode == "serve" and (state is None or state["solver_model"] != args.model):
        raise ValueError("online prototype must belong to this frozen Solver checkpoint")
    features = SolverFeatures(args.model, config["embedding_batch_size"], config["embedding_max_length"])
    if args.mode == "fit":
        rows = json.loads(args.data.read_text())
        x, extraction = features.extract([row["question"] for row in rows])
        labels = [row["sd_label"] for row in rows]
        w, metrics = fit_prototype(
            x, labels, state["prototype"] if state else None, tau=config["tau"],
            learning_rate=config["sd_learning_rate"], steps=config["sd_steps"], ema_rate=config["ema_rate"]
        )
        # Preserve features for cheap diagnostics; no synthetic claims of held-out accuracy.
        np.savez_compressed(args.output.with_suffix(".features.npz"), embeddings=x, labels=labels)
        write_json(args.output, {"version": 1, "round": args.round, "solver_model": args.model,
                               "tau": config["tau"], "prototype": w.tolist(),
                               "extraction": extraction, "training_diagnostics": metrics})
        print(json.dumps({"extraction": extraction, "sd": metrics}), flush=True)
        if metrics["novelty_std"] < 1e-6:
            print("[OCNR] Near-constant novelty. Recorded as-is; no automatic normalization or retuning.", flush=True)
        return

    from flask import Flask, jsonify, request
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify(status="ok", pid=os.getpid(), run_id=args.run_id,
                       solver_model=args.model, sd_round=state["round"])

    @app.post("/novelty")
    def novelty():
        questions = request.get_json()["questions"]
        x, extraction = features.extract(questions)
        p, distance = seenness(x, state["prototype"], state["tau"])
        return jsonify(novelty=(1 - p).tolist(), seen=p.tolist(), distance_squared=distance.tolist(),
                       extraction=extraction)

    app.run(host="127.0.0.1", port=args.port, threaded=False)


if __name__ == "__main__":
    main()
