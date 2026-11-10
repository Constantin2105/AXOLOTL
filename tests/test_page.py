import re

import pytest

from conftest import ROOT
from htmltree import norm, old, parse, read

THREE = "assets/vendor/three.r128.v1.min.js"
SECTIONS = ["intro", "probleme", "ailleurs", "axolotl", "produit", "avantage", "marche", "feuille-de-route", "investir"]
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
    # Vercel hosting + review of Nov 9: early-detection claim sourced, MedGemma fine-tuning stated
    "Un cancer du sein repéré tôt",
    "Un modèle médical de pointe, déjà entraîné",
    # Roadmap of Nov 10: step 1 (MedGemma evaluation + fine-tuning) is in progress
    "Lecture de mammographies sur MedGemma",
)
CONTACT = "contact@valyon.co"


@pytest.fixture(scope="module")
def new():
    return parse(read("index.html"))


@pytest.fixture(scope="module")
def before():
    return parse(old("index.html"))


def test_all_old_text_kept(new, before):
    full = new.text()
    missing = []
    old_form = set(before.find("form", name="investisseurs").texts())
    for region in (before.find("main"), before.find("footer")):
        for piece in region.texts():
            if piece in old_form:
                continue
            piece = norm(piece)
            if len(piece) < 3 or piece.startswith(REPLACED + CORRECTED):
                continue
            if piece not in full:
                missing.append(piece)
    assert not missing, missing


def test_contact_by_email_not_form(new):
    assert new.find("form") is None          # no form backend on Vercel: submissions would be lost
    invest = new.find(id="investir")
    mail = [a.attrs["href"] for a in invest.find_all("a") if a.attrs.get("href", "").startswith("mailto:")]
    assert mail and mail[0].startswith("mailto:" + CONTACT + "?subject=")
    assert CONTACT in invest.text() and CONTACT in new.find("footer").text()


def test_team_on_home(new):
    text = new.find(id="investir").text()
    for name in ("Jean-Baptiste Carmel Togninou Adikin", "Yelian Constantin Zounmevo"):
        assert name in text
    assert text.count("Co-fondateur et co-gérant") == 2


def test_head(new, before):
    assert new.find("title").text() == "Axolotl — L'IA qui repère le cancer du sein à temps"
    for name in ("description", "og:description"):
        meta = new.find("meta", name=name) or new.find("meta", property=name)
        assert "mammographie" in meta.attrs["content"], name
    assert new.find("meta", name="theme-color").attrs["content"] == "#ffffff"
    assert THREE in [s.attrs.get("src") for s in new.find_all("script")]
    assert "Bricolage" not in read("index.html")


@pytest.mark.parametrize("page", ["index.html", "en.html", "404.html", "mentions-legales.html", "confidentialite.html"])
def test_no_third_party_requests(page):
    """Fonts and three.js are served from our own host: no visitor IP goes to Google or Cloudflare."""
    root = parse(read(page))
    for n in root.iter():
        if n.tag in ("link", "script", "img") and n.attrs.get("rel") != "alternate":
            ref = n.attrs.get("href") or n.attrs.get("src") or ""
            assert not ref.startswith(("http:", "https:", "//")), (page, ref)


def test_fonts_self_hosted():
    css = read("assets/site.v3.css")
    files = re.findall(r"url\(\"?(fonts/[^)\"]+)\"?\)", css)
    assert len(files) == 3
    for f in files:
        assert (ROOT / "assets" / f).stat().st_size > 10_000, f
    assert "Inter Tight" in css and "IBM Plex Mono" in css


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
    counts = [n.attrs["data-count"] for n in new.find_all(cls="num-figure") if "data-count" in n.attrs]
    assert counts == ["1.15", "2.1", "44", "3"]
    assert new.find("canvas", id="scan") is not None
    road = new.find("ol", cls="road")
    assert road.find("li", cls="now") is not None


def test_no_fake_controls(new):
    top = new.find("header", cls="top")
    assert "FR" not in top.text().split()
    assert new.find("input", type="search") is None


def test_reveal_states_require_js_class():
    css = re.sub(r"/\*.*?\*/", "", read("assets/site.v3.css"), flags=re.S)
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
        assert r.endswith(".svg") or re.search(r"\.v\d+\.", r), r


def test_ui_script_runs_before_three(new):
    srcs = [s.attrs.get("src") for s in new.find_all("script") if s.attrs.get("src")]
    assert srcs.index("assets/site.v3.js") < srcs.index(THREE) < srcs.index("assets/axolotl.v1.js")


def test_viewer_survives_missing_roundrect():
    js = read("assets/site.v3.js")
    assert "c.roundRect(" not in js          # every rounded rect goes through the fallback helper
    assert "finally" in js and "viewer.classList.add('done')" in js


def test_gl_canvas_sized_by_renderer():
    css = re.sub(r"/\*.*?\*/", "", read("assets/site.v3.css"), flags=re.S)
    rule = re.search(r"#gl\s*\{([^}]*)\}", css).group(1)
    assert "100vh" not in rule and "100vw" not in rule
    assert "setSize(innerWidth, innerHeight, false)" not in read("assets/axolotl.v1.js")


def test_desktop_hero_stage_starts_after_copy():
    css = read("assets/site.v3.css")
    rule = re.search(r"\.hero-stage \{ position: absolute;([^}]*)\}", css).group(1)
    assert "left: calc(var(--gutter) + var(--rail-space) + 540px)" in rule and "width" not in rule


LEGAL = {"mentions-legales.html": "Mentions légales", "confidentialite.html": "Politique de confidentialité"}


def test_no_unearned_validation_claim(new):
    text = new.text()
    assert "Validé sur des examens locaux" not in text
    assert not re.search(r"\bvalidée?s?\b sur", text)


def test_roadmap_matches_real_state(new, en):
    # Step 1 (prototype: MedGemma evaluation + fine-tuning) is in progress; the pilot is only in preparation
    steps = new.find("ol", cls="road").find_all("li")
    first, second = next(steps), next(steps)
    assert "now" in first.classes and first.find("span", cls="when").text() == "Étape 1, en cours"
    assert "fine-tuning" in first.text() and "mammographies publiques" in first.text()
    assert second.find("span", cls="when").text() == "Étape 2, en préparation"
    assert "autorisation de l'APDP" in second.text() and "comité d'éthique" in second.text()
    en_steps = en.find("ol", cls="road").find_all("li")
    e1, e2 = next(en_steps), next(en_steps)
    assert "now" in e1.classes and e1.find("span", cls="when").text() == "Step 1, in progress"
    assert e2.find("span", cls="when").text() == "Step 2, in preparation"
    assert "APDP authorisation and ethics approval" in e2.text()


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
    assert "assets/site.v3.css" in [l.attrs.get("href", "").lstrip("/") for l in root.find_all("link")]
    assert root.find("script") is None     # plain text pages: no WebGL scene, no tracking


def test_legal_pages_linked(new):
    foot = [a.attrs.get("href") for a in new.find("footer").find_all("a")]
    for page in LEGAL:
        assert page in foot, page
    near_form = [a.attrs.get("href") for a in new.find(id="investir").find_all("a")]
    assert "confidentialite.html" in near_form


def test_privacy_names_real_processors():
    text = parse(read("confidentialite.html")).text()
    for who in ("Vercel", "Zoho"):
        assert who in text, who
    for gone in ("Netlify", "Google Fonts", "cdnjs", "Cloudflare", "formulaire"):
        assert gone not in text, gone
    mentions = parse(read("mentions-legales.html")).text()
    assert "Vercel Inc." in mentions and "Netlify" not in mentions


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


def test_legal_contact_and_ifu_filled():
    for page in LEGAL:
        html = read(page)
        assert 'class="todo"' not in html, page
        assert 'href="mailto:contact@valyon.co"' in html, page
        for private in ("0202011938915", "0202213829108", "gmail.com", "+229"):
            assert private not in html, (page, private)
    assert "3202660487413" in parse(read("mentions-legales.html")).text()


def test_cards_numbered_in_order(new):
    nums = [n.text() for n in new.find("div", cls="sections").find_all("p", cls="num")]
    assert nums == [f"{i:02d}" for i in range(1, len(nums) + 1)]
    menu = [a.attrs["href"] for a in new.find("nav", id="menu").find("ol").find_all("a")]
    assert menu == ["#" + s for s in SECTIONS]


def test_evidence_section(new):
    sec = new.find(id="ailleurs")
    text = sec.text()
    assert "MASAI" in text and "+29 %" in text and "−44 %" in text
    assert "un seul pays" in text
    assert "n'est pas spécialisé en mammographie" in text and "fine-tuning" in text
    hrefs = [a.attrs.get("href", "") for a in new.find_all("a")]
    for ref in ("https://doi.org/10.1016/S2589-7500(24)00267-X", "https://doi.org/10.1016/S0140-6736(25)02464-X",
                "https://www.ajol.info/index.php/jaim/article/view/239787"):
        assert ref in hrefs, ref
    assert "plusieurs programmes de dépistage suédois" not in text   # no source found for this claim


def test_needs_block(new):
    needs = new.find(id="besoins")
    items = [li.text() for li in needs.find_all("li")]
    assert len(items) == 4
    for word in ("calcul", "données", "radiologues", "financement"):
        assert any(word in i for i in items), word
    assert CONTACT in needs.text()


def test_footnotes_numbered_in_reading_order(new):
    sups = [a.attrs["href"] for a in new.find_all("a") if a.attrs.get("href", "").startswith("#src-")]
    first_seen = list(dict.fromkeys(sups))
    assert first_seen == [f"#src-{i}" for i in range(1, len(first_seen) + 1)]
    for ref in first_seen:
        assert new.find(id=ref[1:]) is not None, ref


def test_early_detection_claim_sourced(new):
    lede = new.find(id="probleme").find("p", cls="lede")
    assert "99 %" in lede.text() and lede.find("sup") is not None


def test_preprint_flagged(new):
    assert "prépublication non relue par des pairs" in new.find(id="axolotl").text()


# ---------- Review of Nov 9, evening ----------

def test_market_claims_match_evidence(new):
    text = new.find(id="marche").text()
    assert "progresse dans toute la sous-région" not in text
    assert "passe aujourd'hui par les campagnes et les centres d'imagerie privés" in text
    assert "concentrent la lecture sur quelques semaines" in text


def test_axolotl_studied_for_regeneration(new):
    text = new.find(id="axolotl").text()
    assert "pour sa régénération" in text and "sans encore comprendre pourquoi" in text
    assert "si rares que" not in text


def test_no_euro(new):
    text = new.text()
    assert not re.search(r"euros?", text.lower())
    assert "chaque franc investi" in text


def test_benin_paragraph_closes_on_need(new):
    text = new.find(id="ailleurs").text()
    assert "radiologues spécialisés en sein manquent" in text
    src = new.find(id="src-9")
    assert src is not None and src.find("a").attrs["href"].startswith("https://www.lunduniversity.lu.se/")


def test_relative_survival_contrast(new):
    lede = new.find(id="probleme").find("p", cls="lede").text()
    assert "survie relative" in lede and "32 %" in lede


def test_health_data_promise_in_future(new):
    text = new.find(id="avantage").text()
    assert "seront chiffrées" in text and "sont chiffrées" not in text


def test_adikin_background(new):
    assert "IRISA" in new.find(id="investir").text()


# ---------- English version ----------

@pytest.fixture(scope="module")
def en():
    return parse(read("en.html"))


ACCENTED_OK = {"Hernström", "Médicale", "Accessibilité", "l'imagerie", "prise", "Bénin", "Afr", "Imag", "Méd"}


def test_english_page_structure(en, new):
    assert en.find("html").attrs["lang"] == "en"
    assert [n.attrs["id"] for n in en.iter() if "data-sec" in n.attrs] == SECTIONS
    rail = [a.attrs["data-for"] for a in en.find("ul", cls="rail").find_all("a")]
    assert rail == SECTIONS
    assert en.find("form") is None
    mail = [a.attrs["href"] for a in en.find(id="investir").find_all("a") if a.attrs.get("href", "").startswith("mailto:")]
    assert mail and mail[0].startswith("mailto:" + CONTACT + "?subject=")
    assert [s.attrs.get("src") for s in en.find_all("script") if s.attrs.get("src")] == \
           [s.attrs.get("src") for s in new.find_all("script") if s.attrs.get("src")]
    assert en.find("button", id="menu-toggle").attrs.get("data-close-label") == "Close"


def test_english_page_is_in_english(en):
    text = en.text()
    for fr in ("Le problème", "mammographie", "radiologues", "Nous ", " les ", " des ", "Écrire"):
        assert fr not in text, fr
    for must in ("MASAI", "fine-tun", "Benin", "breast cancer", "contact@valyon.co", "IRISA"):
        assert must in text, must


def test_language_links(en, new):
    def alts(root):
        return {l.attrs["hreflang"]: l.attrs["href"] for l in root.find_all("link", rel="alternate")}
    for root in (new, en):
        assert alts(root) == {"fr": "https://axolotl.valyon.co/", "en": "https://axolotl.valyon.co/en",
                              "x-default": "https://axolotl.valyon.co/"}
    assert new.find("a", cls="lang").attrs["href"] == "/en"
    assert en.find("a", cls="lang").attrs["href"] == "/"


def test_menu_label_translatable():
    js = read("assets/site.v3.js")
    assert "dataset.closeLabel" in js and "dataset.openLabel" in js


def test_footnote_click_highlights_source():
    js, css = read("assets/site.v3.js"), read("assets/site.v3.css")
    assert 'sup a[href^="#src-"]' in js and "is-cited" in js and "src-back" in js
    assert "Retour au texte" in js and "Back to text" in js
    assert ".sources li:target" in css and ".sources li.is-cited" in css    # works without JS too
    assert "animation: none !important" in css               # reduced motion: static highlight


# ---------- Review of Nov 10 ----------

def test_no_false_no_data_claim(new, en):
    assert "ne collecte aucune donnée" not in new.text()
    assert "Ce site n'a pas de formulaire" in new.find(id="investir").text()
    assert "collects no data" not in en.text()
    assert "This site has no form" in en.find(id="investir").text()


def test_survival_sentence_subject(new, en):
    lede = new.find(id="probleme").find("p", cls="lede").text()
    assert "S'il est repéré tard, quand il s'est déjà propagé à distance, la survie tombe à 32 %" in lede
    assert "If it is found late, once it has spread to distant organs, survival falls to 32%" in \
        en.find(id="probleme").find("p", cls="lede").text()


@pytest.mark.parametrize("page", ["index.html", "en.html"])
def test_workload_figure_cites_masai_paper(page):
    html = read(page)
    # shortage claim -> Lund release [9], 44 % figure -> Lancet Digital Health [6]
    assert re.search(r'manquent,<sup><a href="#src-9"[^>]*>9</a></sup> elle a réduit de 44&nbsp;% leur travail de lecture\.<sup><a href="#src-6"', html) or \
           re.search(r'short supply,<sup><a href="#src-9"[^>]*>9</a></sup> it cut their reading work by 44%\.<sup><a href="#src-6"', html), page
