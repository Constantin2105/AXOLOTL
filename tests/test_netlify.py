import tomllib

from conftest import ROOT


def load():
    return tomllib.loads((ROOT / "netlify.toml").read_text(encoding="utf-8"))


def test_private_folders_blocked():
    rules = {r["from"]: r for r in load().get("redirects", [])}
    for path in ("/tools/*", "/docs/*", "/tests/*"):
        r = rules[path]
        assert (r["to"], r["status"], r["force"]) == ("/404", 404, True), path


def test_headers_kept():
    heads = {h["for"]: h["values"] for h in load()["headers"]}
    assert heads["/*"]["X-Frame-Options"] == "DENY"
    assert heads["/assets/*"]["Cache-Control"] == "public, max-age=31536000, immutable"
