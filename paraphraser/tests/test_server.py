import json
import threading
import unittest
import urllib.request
from http.server import ThreadingHTTPServer

from paraphraser.ranker import Ranker
from paraphraser.server import ParaphraserHandler


def offline_ranker():
    r = Ranker.__new__(Ranker)
    r.model = None
    r.tok = None
    r.model_id = "test-offline"
    return r


class TestServerEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Bind to port 0 to get an OS-assigned free port
        cls.httpd = ThreadingHTTPServer(("127.0.0.1", 0), ParaphraserHandler)
        cls.httpd.ranker = offline_ranker()  # type: ignore[attr-defined]
        cls.port = cls.httpd.server_port
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        try:
            cls.httpd.shutdown()
        except Exception:
            pass
        finally:
            cls.httpd.server_close()

    def test_health_endpoint(self):
        req = urllib.request.Request(f"{self.base_url}/api/health")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["status"], "ok")
            self.assertIn("supported_languages", data)
            self.assertIn("en", data["supported_languages"])
            self.assertIn("id", data["supported_languages"])

    def test_metrics_endpoint(self):
        body = json.dumps({"text": "First sentence. Second sentence with many more words inside."}).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/metrics",
            data=body,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("metrics", data)
            self.assertEqual(data["metrics"]["sentences"], 2)

    def test_paraphrase_endpoint_indonesian(self):
        body = json.dumps({
            "text": "Model OSI membahas tujuh layer yang saling terhubung dengan gampang.",
            "lang": "id",
            "density": 0.5,
            "seed": 42,
            "is_tex": False
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/paraphrase",
            data=body,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("paraphrased", data)
            self.assertIn("metrics", data)
            self.assertIn("stats", data)
            self.assertIn("diff", data)

    def test_paraphrase_endpoint_english(self):
        body = json.dumps({
            "text": "This paper discusses network protocols and explains several important factors.",
            "lang": "en",
            "density": 0.5,
            "seed": 42,
            "is_tex": False
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/paraphrase",
            data=body,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("paraphrased", data)
            self.assertIn("after", data["metrics"])


if __name__ == "__main__":
    unittest.main()
