"""Explicit, credential-independent Qwen3 recheck client for a local vLLM server."""

import json
import os
import re
from urllib.parse import urlsplit

import requests

DEFAULT_MODEL = "Qwen/Qwen3-32B"
PROMPT_VERSION = "math-recheck-local-v1"


def local_backend():
    backend = os.getenv("RECHECK_BACKEND", "api")
    if backend not in ("api", "local"):
        raise ValueError("RECHECK_BACKEND must be api or local")
    return backend == "local"


def judge_metadata():
    """Stable resume identity: exclude the ephemeral server port and access key."""
    max_tokens = int(os.getenv("RECHECK_MAX_COMPLETION_TOKENS", "32"))
    if max_tokens <= 0:
        raise ValueError("RECHECK_MAX_COMPLETION_TOKENS must be positive")
    return {
        "backend": "local",
        "model": os.getenv("RECHECK_LOCAL_MODEL", DEFAULT_MODEL),
        "revision": os.getenv("RECHECK_LOCAL_REVISION") or None,
        "prompt_version": PROMPT_VERSION,
        "enable_thinking": False,
        "temperature": 0.0,
        "max_tokens": max_tokens,
    }


def parse_verdict(content):
    # Non-thinking Qwen templates may emit an empty think block. Never inspect
    # reasoning prose for a substring such as "yes".
    if not isinstance(content, str):
        raise ValueError("Local judge returned no text verdict")
    text = re.sub(r"^\s*<think>\s*</think>\s*", "", content).strip()
    match = re.fullmatch(r"(yes|no)[.!]?", text, flags=re.IGNORECASE)
    if not match:
        raise ValueError("Local judge must return exactly Yes or No")
    return match.group(1).capitalize()


class LocalJudge:
    def __init__(self):
        self.metadata = judge_metadata()
        base = os.getenv("RECHECK_LOCAL_BASE_URL", "http://127.0.0.1:8000/v1").rstrip("/")
        url = urlsplit(base)
        if (url.scheme != "http" or url.hostname not in ("127.0.0.1", "localhost", "::1")
                or url.username or url.password or url.query or url.fragment or url.path != "/v1"):
            raise ValueError("RECHECK_LOCAL_BASE_URL must be a loopback http URL ending in /v1")
        self.url = base + "/chat/completions"
        self.served_model = os.getenv("RECHECK_LOCAL_SERVED_MODEL", self.metadata["model"])
        self.timeout = float(os.getenv("RECHECK_LOCAL_TIMEOUT", "120"))
        if not 0 < self.timeout < float("inf"):
            raise ValueError("RECHECK_LOCAL_TIMEOUT must be finite and positive")
        self.headers = {"Content-Type": "application/json"}
        # Deliberately never load OPENAI_API_KEY, OPENAI_BASE_URL or tokens.json.
        key = os.getenv("RECHECK_LOCAL_API_KEY")
        if key:
            self.headers["Authorization"] = "Bearer " + key

    def __call__(self, answer, response):
        payload = {
            "model": self.served_model,
            "messages": [
                {"role": "system", "content": "You are a math answer checker."},
                {"role": "user", "content": (
                    f"Hi, there is a model response: {response}\n\n"
                    f", and the ground truth answer is: {answer}\n\n"
                    ", please check whether the model response is correct or not, "
                    "and return the **only** Yes or No."
                )},
            ],
            "temperature": 0.0,
            "max_tokens": self.metadata["max_tokens"],
            "chat_template_kwargs": {"enable_thinking": False},
        }
        # Each worker owns its session; local requests must bypass proxy settings.
        with requests.Session() as session:
            session.trust_env = False
            try:
                result = session.post(self.url, headers=self.headers, json=payload,
                                      timeout=self.timeout, allow_redirects=False)
            except requests.RequestException:
                raise RuntimeError("Local judge connection failed or timed out") from None
        if result.status_code != 200:
            raise RuntimeError(f"Local judge HTTP status {result.status_code}")
        try:
            choice = result.json()["choices"][0]
            if choice.get("finish_reason") != "stop":
                raise ValueError("Local judge response was truncated or did not finish normally")
            return parse_verdict(choice["message"]["content"])
        except (KeyError, IndexError, TypeError, json.JSONDecodeError):
            raise ValueError("Local judge returned a malformed completion") from None
