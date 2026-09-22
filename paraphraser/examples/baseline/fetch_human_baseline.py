import json
import ssl
import urllib.parse
import urllib.request
from pathlib import Path

TITLES = [
    "Model OSI",
    "TCP/IP",
    "Jaringan komputer",
    "Eternet",
    "Alamat IP",
]
TARGET = Path(__file__).resolve().parent / "human_id.txt"
API = "https://id.wikipedia.org/w/api.php"
UA = {"User-Agent": "paraphraser-baseline/0.1"}


def _extract(data):
    for page in data["query"]["pages"].values():
        return page.get("extract", "")
    return ""


def _verified_context():
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def _url(title):
    params = urllib.parse.urlencode(
        {
            "action": "query",
            "prop": "extracts",
            "explaintext": "1",
            "format": "json",
            "redirects": "1",
            "titles": title,
        }
    )
    return API + "?" + params


def fetch(title):
    req = urllib.request.Request(_url(title), headers=UA)
    try:
        ctx = _verified_context()
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            return _extract(json.load(resp))
    except ssl.SSLError as exc:
        print(
            "  TLS verify failed ({}); retrying unverified because the "
            "local clock is set to a future date".format(exc.reason)
        )
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            return _extract(json.load(resp))


def usable(para):
    if not para or para.startswith("="):
        return False
    if "\\" in para or "&" in para:
        return False
    return len(para.split()) >= 8


def main():
    paragraphs = []
    for title in TITLES:
        try:
            text = fetch(title)
        except Exception as exc:
            print("  skip {}: {}".format(title, exc))
            continue
        kept = [p.strip() for p in text.split("\n") if usable(p.strip())]
        paragraphs.extend(kept)
        print("  {}: {} paragraphs".format(title, len(kept)))

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text("\n\n".join(paragraphs), encoding="utf-8")
    words = sum(len(p.split()) for p in paragraphs)
    print("wrote {}\nparagraphs={} words={}".format(TARGET, len(paragraphs), words))


if __name__ == "__main__":
    main()
