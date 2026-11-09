import json

from conftest import ROOT


def load():
    return json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))


def test_private_folders_not_deployed():
    ignored = (ROOT / ".vercelignore").read_text(encoding="utf-8").split()
    for path in ("tools", "docs", "tests"):
        assert path in ignored or path + "/" in ignored, path


def test_security_and_cache_headers():
    heads = {h["source"]: {x["key"]: x["value"] for x in h["headers"]} for h in load()["headers"]}
    site = heads["/(.*)"]
    assert site["X-Frame-Options"] == "DENY"
    assert site["X-Content-Type-Options"] == "nosniff"
    assert site["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "camera=()" in site["Permissions-Policy"]
    assert heads["/assets/(.*)"]["Cache-Control"] == "public, max-age=31536000, immutable"


def test_netlify_leftovers_removed():
    assert not (ROOT / "netlify.toml").exists()
    assert not (ROOT / "merci.html").exists()
