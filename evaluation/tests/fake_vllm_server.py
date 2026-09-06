"""CPU HTTP fixture, installed as a fake vllm module only inside test directories."""

import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--port", type=int)
parser.add_argument("--api-key")
parser.add_argument("--served-model-name")
args, _ = parser.parse_known_args()
Path(os.environ["TEST_SERVER_PID"]).write_text(str(os.getpid()))


class Handler(BaseHTTPRequestHandler):
    def reply(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def authorized(self):
        if self.headers.get("Authorization") != "Bearer " + args.api_key:
            self.reply(401, {})
            return False
        return True

    def do_GET(self):
        if self.authorized():
            self.reply(200, {"data": [{"id": args.served_model_name}]})

    def do_POST(self):
        if not self.authorized():
            return
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        assert body["model"] == args.served_model_name
        assert body["chat_template_kwargs"] == {"enable_thinking": False}
        assert body["max_tokens"] == 32
        assert "reasoning_effort" not in body
        if os.getenv("TEST_SERVER_FAILURE"):
            self.reply(500, {})
        else:
            self.reply(200, {"choices": [{"message": {"content": "Yes"}, "finish_reason": "stop"}]})


HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
