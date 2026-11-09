import re

import pytest

from conftest import ROOT
from htmltree import norm, old, parse, read

THREE = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"
SECTIONS = ["intro", "probleme", "axolotl", "produit", "avantage", "marche", "feuille-de-route", "investir"]
REPLACED = ("Régénération", "Un membre d'axolotl repousse cellule par cellule")
# Old sentences deliberately rewritten (Nov 2026): claims matched to the real state, mammography only
CORRECTED = (
    "Axolotl lit les mammographies, radiographies et scanners",
    "En Afrique, le cancer tue d'abord",
    "Pendant cette reconstruction, ses cellules",
    "Ci-contre, une patte de l'axolotl repousse",
    "Chez l'axolotl, une patte repousse",
    "Axolotl s'intègre au flux de travail",
    "L'image est envoyée au format DICOM",
    "Les modèles ouverts comme MedGemma",
    "Validé sur des examens locaux",
    "Une IA entraînée en Europe",
    "Axolotl fonctionne avec l'équipement",
    "Les examens sont chiffrés",
    "Le dépistage du cancer progresse",
    "Ministères, ONG et campagnes",
    "Étape 2, en cours",
    "L'IA qui repère le cancer à",
    "Un second regard sur chaque examen",
    "L'examen arrive",
    "Le modèle parcourt l'image",
    "Abonnement mensuel par site",
    "Tarif par examen",
    "Étude de performance avec",
    "Recrutement des hôpitaux et cliniques partenaires",
)


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
            if len(piece) < 3 or piece.startswith(REPLACED + CORRECTED):
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
    assert new.find("title").text() == "Axolotl — L'IA qui repère le cancer du sein à temps"
    for name in ("description", "og:description"):
        meta = new.find("meta", name=name) or new.find("meta", property=name)
        assert "mammographie" in meta.attrs["content"], name
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


def test_merci():
    new_html = read("merci.html")
    new_m, old_m = parse(new_html), parse(old("merci.html"))
    assert new_m.find("h1").text() == old_m.find("h1").text()
    old_ps = [p.text() for p in old_m.find("main").find_all("p")]
    full = new_m.text()
    for p in old_ps:
        assert p in full, p
    assert new_m.find("meta", name="robots").attrs["content"] == "noindex"
    assert "assets/site.v1.css" in [l.attrs.get("href", "").lstrip("/") for l in new_m.find_all("link")]
    assert "Bricolage" not in new_html
    assert "three" not in new_html


def test_ui_script_runs_before_three(new):
    srcs = [s.attrs.get("src") for s in new.find_all("script") if s.attrs.get("src")]
    assert srcs.index("assets/site.v1.js") < srcs.index(THREE) < srcs.index("assets/axolotl.v1.js")


def test_viewer_survives_missing_roundrect():
    js = read("assets/site.v1.js")
    assert "c.roundRect(" not in js          # every rounded rect goes through the fallback helper
    assert "finally" in js and "viewer.classList.add('done')" in js


def test_gl_canvas_sized_by_renderer():
    css = re.sub(r"/\*.*?\*/", "", read("assets/site.v1.css"), flags=re.S)
    rule = re.search(r"#gl\s*\{([^}]*)\}", css).group(1)
    assert "100vh" not in rule and "100vw" not in rule
    assert "setSize(innerWidth, innerHeight, false)" not in read("assets/axolotl.v1.js")


def test_desktop_hero_stage_starts_after_copy():
    css = read("assets/site.v1.css")
    rule = re.search(r"\.hero-stage \{ position: absolute;([^}]*)\}", css).group(1)
    assert "left: calc(var(--gutter) + var(--rail-space) + 540px)" in rule and "width" not in rule


LEGAL = {"mentions-legales.html": "Mentions légales", "confidentialite.html": "Politique de confidentialité"}


def test_no_unearned_validation_claim(new):
    text = new.text()
    assert "Validé sur des examens locaux" not in text
    assert not re.search(r"\bvalidée?s?\b sur", text)


def test_pilot_in_preparation(new):
    now = new.find("ol", cls="road").find("li", cls="now")
    assert now.find("span", cls="when").text() == "Étape 2, en préparation"
    assert "en cours" not in new.find("ol", cls="road").text()


def test_mammography_only(new):
    head = " ".join(m.attrs.get("content", "") for m in new.find_all("meta"))
    text = (new.find("title").text() + " " + head + " " + new.text()).lower()
    for word in ("radiographie", "scanner", "irm", "échographie", "imagerie clinique", "examen"):
        assert not re.search(r"\b" + word, text), word
    assert "mammographie" in new.find(id="intro").text()


def test_no_axolotl_cell_claim(new):
    text = new.find(id="axolotl").text()
    assert "cellule" not in text


@pytest.mark.parametrize("page,title", LEGAL.items())
def test_legal_page(page, title):
    html = read(page)
    root = parse(html)
    assert root.find("h1").text() == title
    text = root.text()
    assert "Code du numérique" in text
    assert "APDP" in text and "Autorité de protection des données à caractère personnel" in text
    assert "assets/site.v1.css" in [l.attrs.get("href", "").lstrip("/") for l in root.find_all("link")]
    assert root.find("script") is None     # plain text pages: no WebGL scene, no tracking


def test_legal_pages_linked(new):
    foot = [a.attrs.get("href") for a in new.find("footer").find_all("a")]
    for page in LEGAL:
        assert page in foot, page
    near_form = [a.attrs.get("href") for a in new.find(id="investir").find_all("a")]
    assert "confidentialite.html" in near_form


def test_privacy_names_real_processors():
    text = parse(read("confidentialite.html")).text()
    for who in ("Netlify", "Google Fonts", "cdnjs"):
        assert who in text, who


def test_legal_identity_from_registry():
    for page in LEGAL:
        text = parse(read(page)).text()
        assert "VALYON SARL" in text, page
        assert "RB/ABC/26 B 10694" in text, page
        assert "Abomey-Calavi" in text, page
        assert "forme juridique" not in text and "adresse à compléter" not in text, page
    mentions = parse(read("mentions-legales.html")).text()
    assert "100 000 FCFA" in mentions
    assert "Jean-Baptiste Carmel Togninou Adikin" in mentions and "Yelian Constantin Zounmevo" in mentions


def test_apdp_request_in_progress():
    for page in LEGAL:
        text = parse(read(page)).text()
        assert re.search(r"demande .{0,80}APDP.{0,40} est en cours", text), page
        assert "récépissé à compléter" not in text, page
