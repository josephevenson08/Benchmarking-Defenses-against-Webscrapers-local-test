"""Checks for measurement/time_models.py, using a stand-in for Ollama's HTTP API (no Ollama or model needed).

Run with: python -m unittest discover -s measurement/tests -t .
"""

import http.server
import json
import threading
import unittest

from measurement import time_models as tm

ITEMS = {
    "products": [{"product_id": "p1", "name": "Larkfield Studio Headphones", "price": "$89.99"}],
    "articles": [{"article_id": "a1", "title": "Caring for Cast Iron Cookware", "author": "Maya Okafor"}],
}
FIELDS = {
    "product": [{"key": "name", "label": "Name"}, {"key": "price", "label": "Price"}],
    "article": [{"key": "title", "label": "Title"}, {"key": "author", "label": "Author"}],
}
TAGS = {"models": [{"name": "tiny:1b", "model": "tiny:1b", "size": 806000000, "digest": "97558784bdc9" + "0" * 52,
                    "details": {"family": "gemma3", "parameter_size": "1B", "quantization_level": "Q4_K_M"}}]}
GENERATE = {"model": "tiny:1b", "response": '{"Name": "Larkfield Studio Headphones", "Price": "89.99"}', "done": True,
            "total_duration": 2_500_000_000, "load_duration": 500_000_000, "prompt_eval_count": 120,
            "prompt_eval_duration": 1_000_000_000, "eval_count": 30, "eval_duration": 1_000_000_000}


def serve_fake_ollama():
    requests_seen = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def _send(self, payload):
            body = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            self._send({"version": "0.0-test"} if self.path == "/api/version" else TAGS)

        def do_POST(self):
            requests_seen.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
            self._send(GENERATE)

        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}", requests_seen


class PromptAndTargetsTest(unittest.TestCase):
    def test_product_and_article_targets(self):
        labels, expected = tm.page_targets("/products/p1", ITEMS, FIELDS)
        self.assertEqual(labels, ["Name", "Price"])
        self.assertEqual(expected["Price"], "$89.99")
        labels, expected = tm.page_targets("/articles/a1", ITEMS, FIELDS)
        self.assertEqual(expected, {"Title": "Caring for Cast Iron Cookware", "Author": "Maya Okafor"})
        with self.assertRaises(ValueError):
            tm.page_targets("/", ITEMS, FIELDS)

    def test_prompt_holds_the_text_and_every_label(self):
        prompt = tm.build_prompt("  Name Larkfield  ", ["Name", "Price"])
        self.assertIn("Name Larkfield", prompt)
        self.assertIn("Name, Price", prompt)

    def test_values_found_is_case_insensitive_text_match(self):
        expected = {"Name": "Larkfield Studio Headphones", "Price": "$89.99"}
        self.assertEqual(tm.values_found('{"Name": "larkfield studio headphones", "Price": "89.99"}', expected), 1)
        self.assertEqual(tm.values_found("nothing", expected), 0)


class OllamaApiTest(unittest.TestCase):
    def setUp(self):
        self.server, self.url, self.seen = serve_fake_ollama()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def test_list_models_keeps_name_digest_and_details(self):
        [m] = tm.list_models(self.url)
        self.assertEqual((m["name"], m["parameter_size"], m["quantization"]), ("tiny:1b", "1B", "Q4_K_M"))
        self.assertTrue(m["digest"].startswith("97558784bdc9"))

    def test_generate_sends_temperature_0_and_the_reply_cap(self):
        data, wall = tm.generate(self.url, "tiny:1b", "prompt", 400, 10)
        self.assertEqual(self.seen[0]["options"], {"temperature": 0, "num_predict": 400})
        self.assertFalse(self.seen[0]["stream"])
        m = tm.measurement(data, wall, {"Name": "Larkfield Studio Headphones", "Price": "$89.99"})
        self.assertEqual((m["total_s"], m["load_s"], m["prompt_tokens"], m["reply_tokens"]), (2.5, 0.5, 120, 30))
        self.assertEqual((m["reply_tokens_per_s"], m["values_found"], m["values_expected"]), (30.0, 1, 2))

    def test_summary_averages_and_counts_errors(self):
        data, wall = tm.generate(self.url, "tiny:1b", "prompt", 400, 10)
        call = {"model": "tiny:1b", **tm.measurement(data, wall, {"Name": "Larkfield Studio Headphones"})}
        s = tm.summarize("tiny:1b", [call, call, {"model": "tiny:1b", "error": "timeout"}])
        self.assertEqual((s["calls"], s["errors"], s["mean_prompt_tokens"]), (3, 1, 120))
        self.assertEqual((s["values_found"], s["values_expected"]), (2, 2))


if __name__ == "__main__":
    unittest.main()
