from __future__ import annotations

import unittest
from unittest.mock import Mock
import sys
import types

# Keep this unit test independent of the training environment's third-party
# packages. Production already depends on requests; here a tiny API-compatible
# module is sufficient because every HTTP call is mocked.
fake_requests = types.ModuleType("requests")


class Timeout(Exception):
    pass


class ConnectionError(Exception):
    pass


class HTTPError(Exception):
    def __init__(self, message: str, response=None) -> None:
        super().__init__(message)
        self.response = response


fake_requests.Timeout = Timeout
fake_requests.ConnectionError = ConnectionError
fake_requests.HTTPError = HTTPError
fake_requests.exceptions = types.SimpleNamespace(
    Timeout=Timeout,
    ConnectionError=ConnectionError,
    HTTPError=HTTPError,
)
fake_requests.post = Mock()
sys.modules.setdefault("requests", fake_requests)

from evaluation import recheck_api
from evaluation.recheck_api import JudgeRequestError, RecheckApiConfig, request_judgement


class FakeResponse:
    def __init__(self, status_code: int, content: str = "Yes") -> None:
        self.status_code = status_code
        self._content = content

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            response = Mock(status_code=self.status_code)
            raise recheck_api.requests.exceptions.HTTPError(
                f"HTTP {self.status_code}", response=response
            )

    def json(self) -> dict:
        return {"choices": [{"message": {"content": self._content}}]}


def config(attempts: int = 3) -> RecheckApiConfig:
    return RecheckApiConfig(timeout=60, attempts=attempts, reasoning_effort="minimal")


class RecheckApiTests(unittest.TestCase):
    def test_success_uses_timeout_and_minimal_reasoning(self) -> None:
        post = Mock(return_value=FakeResponse(200, "Yes"))
        result = request_judgement(
            "https://api.openai.com/v1/chat/completions",
            "secret",
            "42",
            "\\boxed{42}",
            config=config(),
            post=post,
            sleep=Mock(),
        )
        self.assertEqual(result, "Yes")
        self.assertEqual(post.call_args.kwargs["timeout"], 60)
        self.assertEqual(post.call_args.kwargs["json"]["reasoning_effort"], "minimal")

    def test_timeout_then_success_retries_once(self) -> None:
        post = Mock(
            side_effect=[recheck_api.requests.exceptions.Timeout("slow"), FakeResponse(200)]
        )
        sleep = Mock()
        self.assertEqual(
            request_judgement("url", "key", "a", "b", config=config(), post=post, sleep=sleep),
            "Yes",
        )
        self.assertEqual(post.call_count, 2)
        sleep.assert_called_once_with(1)

    def test_429_and_5xx_are_retried(self) -> None:
        post = Mock(side_effect=[FakeResponse(429), FakeResponse(503), FakeResponse(200)])
        sleep = Mock()
        self.assertEqual(
            request_judgement("url", "key", "a", "b", config=config(), post=post, sleep=sleep),
            "Yes",
        )
        self.assertEqual(post.call_count, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 2])

    def test_permanent_400_is_not_retried(self) -> None:
        post = Mock(return_value=FakeResponse(400))
        sleep = Mock()
        with self.assertRaises(JudgeRequestError) as caught:
            request_judgement("url", "key", "a", "b", config=config(), post=post, sleep=sleep)
        self.assertFalse(caught.exception.retryable)
        self.assertEqual(caught.exception.attempts, 1)
        self.assertEqual(post.call_count, 1)
        sleep.assert_not_called()

    def test_retry_exhaustion_is_explicit(self) -> None:
        post = Mock(side_effect=recheck_api.requests.exceptions.ConnectionError("offline"))
        sleep = Mock()
        with self.assertRaisesRegex(JudgeRequestError, "failed after 3 attempt") as caught:
            request_judgement("url", "key", "a", "b", config=config(), post=post, sleep=sleep)
        self.assertTrue(caught.exception.retryable)
        self.assertEqual(caught.exception.attempts, 3)
        self.assertEqual(post.call_count, 3)
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 2])


if __name__ == "__main__":
    unittest.main()
