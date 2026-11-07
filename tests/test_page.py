import re

import pytest

from conftest import ROOT
from htmltree import norm, old, parse, read

THREE = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"
SECTIONS = ["intro", "probleme", "axolotl", "produit", "avantage", "marche", "feuille-de-route", "investir"]
REPLACED = ("Régénération", "Un membre d'axolotl repousse cellule par cellule")


@pytest.fixture(scope="module")
def new():
    return parse(read("index.html"))


@pytest.fixture(scope="module")
def before():
    return parse(old("index.html"))


def test_all_old_text_kept(new, before):
    full = new.text()
    missing = []
    for region in (before.find("main"), before.find("footer")):
        for piece in region.texts():
            piece = norm(piece)
            if len(piece) < 3 or piece.startswith(REPLACED):
                continue
            if piece not in full:
                missing.append(piece)
    assert not missing, missing


def _form(root):
    f = root.find("form", name="investisseurs")
    assert f is not None
    attrs = {k: f.attrs.get(k) for k in ("name", "method", "action", "data-netlify", "netlify-honeypot")}
    hidden = {n.attrs["name"]: n.attrs.get("value") for n in f.find_all("input", type="hidden")}
    fields = [n.attrs.get("name") for n in f.iter() if n.tag in ("input", "select", "textarea")]
    options = [norm(" ".join(o.texts())) for o in f.find_all("option")]
    required = sorted(n.attrs["name"] for n in f.iter() if n.tag in ("input", "select", "textarea") and "required" in n.attrs)
    return attrs, hidden, fields, options, required


def test_form_unchanged(new, before):
    assert _form(new) == _form(before)
    attrs, hidden, *_ = _form(new)
    assert attrs == {"name": "investisseurs", "method": "POST", "action": "/merci",
                     "data-netlify": "true", "netlify-honeypot": "bot-field"}
    assert hidden["subject"] == "Axolotl · nouveau contact investisseur (%{submissionId})"


def test_head(new, before):
    assert new.find("title").text() == before.find("title").text()
    assert new.find("meta", name="description").attrs["content"] == before.find("meta", name="description").attrs["content"]
    assert new.find("meta", name="theme-color").attrs["content"] == "#ffffff"
    assert THREE in [s.attrs.get("src") for s in new.find_all("script")]
    fonts = " ".join(l.attrs.get("href", "") for l in new.find_all("link"))
    assert "Inter+Tight" in fonts and "IBM+Plex+Mono" in fonts
    assert "Bricolage" not in read("index.html")


def test_sections_and_rail(new):
    for sid in SECTIONS:
        sec = new.find(id=sid)
        assert sec is not None and "data-sec" in sec.attrs, sid
    rail = new.find("ul", cls="rail")
    links = [(a.attrs["data-for"], a.attrs["href"]) for a in rail.find_all("a")]
    assert links == [(s, "#" + s) for s in SECTIONS]


def test_dom_contract(new):
    assert "no-js" in new.find("html").classes
    assert new.find("canvas", id="gl").attrs.get("aria-hidden") == "true"
    toggle = new.find("button", id="menu-toggle")
    assert toggle.attrs.get("aria-controls") == "menu" and toggle.attrs.get("aria-expanded") == "false"
    assert "hidden" in new.find("nav", id="menu").attrs
    hero = new.find(id="intro").find(cls="hero-stage")
    stage = new.find(id="axolotl").find(cls="regen-stage").find(cls="regen-sticky")
    assert "data-axolotl-stage" in stage.attrs
    for box in (hero, stage):
        img = box.find("img", cls="axo-poster")
        assert img.attrs["src"] == "assets/axolotl-poster.v1.webp" and img.attrs["alt"] == ""
    counts = [n.attrs.get("data-count") for n in new.find_all(cls="num-figure")]
    assert counts == ["1.15", "2.1", "44", "3"]
    assert new.find("canvas", id="scan") is not None
    road = new.find("ol", cls="road")
    assert road.find("li", cls="done") is not None and road.find("li", cls="now") is not None


def test_no_fake_controls(new):
    top = new.find("header", cls="top")
    assert "FR" not in top.text().split()
    assert new.find("input", type="search") is None


def test_reveal_states_require_js_class():
    css = re.sub(r"/\*.*?\*/", "", read("assets/site.v1.css"), flags=re.S)
    for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        if not re.search(r"\.reveal|\.stagger|#title", sel):
            continue
        hides = re.search(r"opacity\s*:\s*0(?![.\d])", body) or re.search(r"transform\s*:\s*translate", body)
        if hides:
            for s in sel.split(","):
                assert s.strip().startswith(".js "), s.strip()


def test_assets_versioned(new):
    refs = [n.attrs.get("src") or n.attrs.get("href") for n in new.iter() if n.tag in ("script", "link", "img", "a")]
    local = [r for r in refs if r and r.lstrip("/").startswith("assets/")]
    assert local
    for r in local:
        assert r.endswith(".svg") or ".v1." in r, r
