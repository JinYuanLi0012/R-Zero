"""Shared concurrency helpers for mathematical answer rechecks."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, MutableSequence

def recheck_concurrency() -> int:
    raw_value = os.getenv("RECHECK_CONCURRENCY", "32")
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"RECHECK_CONCURRENCY must be a positive integer; got {raw_value!r}"
        ) from exc
    if value <= 0:
        raise ValueError(
            f"RECHECK_CONCURRENCY must be a positive integer; got {raw_value!r}"
        )
    return value


def recheck_rows(
    rows: MutableSequence[dict],
    judge: Callable[[str, str], str],
    concurrency: int,
    description: str,
    *,
    show_progress: bool = True,
) -> None:
    """Recheck locally wrong rows and update scores only from the caller thread."""
    pending = [index for index, row in enumerate(rows) if float(row.get("score", 0)) < 0.5]
    if not pending:
        return

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = {
            executor.submit(judge, rows[index]["answer"], rows[index]["response"]): index
            for index in pending
        }
        completed = as_completed(futures)
        if show_progress:
            from tqdm import tqdm

            completed = tqdm(completed, total=len(futures), desc=description)
        for future in completed:
            index = futures[future]
            try:
                verdict = future.result()
            except Exception as exc:
                print(f"judge error on {description} row {index}: {exc}", flush=True)
                verdict = "No"
            if "yes" in str(verdict).lower():
                rows[index]["score"] = 1
