"""Shared OpenAI judge request handling for evaluation rechecks."""

from __future__ import annotations

from dataclasses import dataclass
import os
import time
from typing import Callable

import requests


@dataclass(frozen=True)
class RecheckApiConfig:
    model: str = "gpt-5-nano"
    timeout: float = 60.0
    attempts: int = 3
    reasoning_effort: str = "minimal"


class JudgeRequestError(RuntimeError):
    def __init__(self, message: str, *, attempts: int, retryable: bool) -> None:
        super().__init__(message)
        self.attempts = attempts
        self.retryable = retryable


def _positive_float(name: str, default: str) -> float:
    value = float(os.getenv(name, default))
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return value


def _positive_int(name: str, default: str) -> int:
    value = int(os.getenv(name, default))
    if value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def config_from_env() -> RecheckApiConfig:
    return RecheckApiConfig(
        model=os.getenv("RECHECK_JUDGE_MODEL", "gpt-5-nano"),
        timeout=_positive_float("RECHECK_API_TIMEOUT", "60"),
        attempts=_positive_int("RECHECK_API_RETRIES", "3"),
        reasoning_effort=os.getenv("RECHECK_REASONING_EFFORT", "minimal"),
    )


def build_payload(config: RecheckApiConfig, gold_answer: str, model_response: str) -> dict:
    payload = {
        "model": config.model,
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
    }
    if config.model.startswith("gpt-5"):
        payload["reasoning_effort"] = config.reasoning_effort
    return payload


def _headers(api_url: str, api_key: str) -> dict[str, str]:
    if "api.openai.com" in api_url or api_url.rstrip("/").endswith("/chat/completions"):
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    return {"api-key": api_key, "Content-Type": "application/json"}


def request_judgement(
    api_url: str,
    api_key: str,
    gold_answer: str,
    model_response: str,
    *,
    config: RecheckApiConfig | None = None,
    post: Callable = requests.post,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    config = config or config_from_env()
    payload = build_payload(config, gold_answer, model_response)
    headers = _headers(api_url, api_key)
    last_error = "unknown API failure"

    for attempt in range(1, config.attempts + 1):
        retryable = False
        try:
            response = post(
                api_url,
                headers=headers,
                json=payload,
                timeout=config.timeout,
            )
            status = response.status_code
            if status == 429 or 500 <= status <= 599:
                retryable = True
                last_error = f"HTTP {status}"
            else:
                try:
                    response.raise_for_status()
                except requests.exceptions.HTTPError as exc:
                    raise JudgeRequestError(
                        f"permanent judge API failure on attempt {attempt}: HTTP {status}",
                        attempts=attempt,
                        retryable=False,
                    ) from exc
                try:
                    return response.json()["choices"][0]["message"]["content"]
                except (KeyError, IndexError, TypeError, ValueError) as exc:
                    raise JudgeRequestError(
                        f"invalid judge API response on attempt {attempt}: {exc}",
                        attempts=attempt,
                        retryable=False,
                    ) from exc
        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as exc:
            retryable = True
            last_error = f"{type(exc).__name__}: {exc}"

        if retryable and attempt < config.attempts:
            sleep(2 ** (attempt - 1))
            continue
        raise JudgeRequestError(
            f"judge API failed after {attempt} attempt(s): {last_error}",
            attempts=attempt,
            retryable=retryable,
        )

    raise AssertionError("unreachable")
