# Refonte Axolotl : plan de construction

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**But :** refaire la page investisseurs Axolotl dans le style MYDNA : fond blanc, cartes numérotées et un axolotl en particules détaillé et animé. Tout le contenu actuel et le formulaire Netlify sont conservés.

**Architecture :**
- **Site statique**, sans étape de build. `index.html` ne contient que le balisage.
- **Fichiers séparés :**
  - les styles dans `assets/site.v1.css` ;
  - l'interface dans `assets/site.v1.js` (menu, navigation latérale, révélations, compteurs, visionneuse, feuille de route) ;
  - la scène 3D dans `assets/axolotl.v1.js`.
- **Particules :** elles sont calculées hors ligne par `tools/bake.py`, à partir de l'illustration Gemini, dans `assets/axolotl.v1.bin`.
- **Repli :** une image fixe `assets/axolotl-poster.v1.webp` remplace la scène quand WebGL est indisponible ou que le mouvement est réduit.

**Tech Stack :** HTML/CSS/JS sans framework. three.js r128 (cdnjs). Python 3 (numpy, scipy, scikit-image, Pillow) pour les outils. pytest pour les tests. Netlify pour l'hébergement.

**Spec :** `docs/superpowers/specs/2026-11-07-refonte-axolotl-design.md` (à lire en entier avant toute tâche).

**Branche :** `refonte-particules`. Ne jamais commiter sur `main`. Pousser uniquement à la tâche 7, avec l'accord du porteur.

## Global Constraints

- **three.js :** exactement `https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js`. Aucune autre dépendance d'exécution.
- **Polices :** Google Fonts `Inter Tight` (300;400;500) et `IBM Plex Mono` (400;500). Bricolage Grotesque et IBM Plex Sans disparaissent.
- **Couleurs :**
  - fond `#ffffff`, encre `#111518`, texte secondaire `#62696d`, filets `#e4e7e9` ;
  - dégradé `#f27fa0` → `#d8479a` → `#8d55d8` → `#4f8fe0` ;
  - ambre `#f2a93b`, réservé au « signal ».
- **Animations :** courbe `cubic-bezier(.2,.8,.2,1)`, durées de 0,8 à 1,2 s.
- **Cache :** tout fichier sous `assets/` qui peut changer porte `.v1.` dans son nom (le cache y est `immutable`).
- **Poids :** `axolotl.v1.bin` ≤ 450 000 octets, poster ≤ 150 000 octets.
- **Formulaire Netlify :** à garder octet pour octet :
  - les attributs `name="investisseurs" method="POST" action="/merci" data-netlify="true" netlify-honeypot="bot-field"` ;
  - le champ caché `subject` = `Axolotl · nouveau contact investisseur (%{submissionId})` ;
  - les noms de champs `bot-field`, `nom`, `structure`, `profil`, `email`, `message`, et les 6 options de `profil`.
- **Mouvement réduit :** `prefers-reduced-motion: reduce` supprime tout mouvement et affiche le poster à la place de la scène.
- **Pas de faux éléments d'interface :** pas de sélecteur de langue, de recherche ni de son.
- **Exécution Python :** toujours `python -P` (jamais `-I`, qui masque numpy).

## Review Focus

1. **JS bloqué ou en échec :** tout le contenu doit rester visible. Les états cachés avant révélation n'existent que sous `html.js`. Test : `test_reveal_states_require_js_class` (tâche 3).
2. **Page rechargée au milieu du défilement** (le navigateur restaure la position) : la scène doit partir de l'état qui correspond à la position courante, pas de l'accueil. Vérifié à la tâche 5, étape 6.
3. **WebGL absent, three.js bloqué ou `axolotl.v1.bin` en 404 :** le poster s'affiche sans erreur non capturée en console. Vérifié à la tâche 5 avec `?nogl` et un nom de fichier cassé.
4. **Écran d'ordinateur bas** (1366×650) **et téléphone en paysage** : le titre et les boutons de l'accueil ne doivent jamais passer sous l'axolotl. Vérifié à la tâche 7.
5. **Navigation au clavier seul :**
   - le menu piège le focus, se ferme avec Échap et rend le focus au bouton ;
   - tout le formulaire est atteignable avec Tab.

   Vérifié à la tâche 4, étape 5.

---

## Structure des fichiers

| Fichier | Rôle |
|---|---|
| `tools/bake.py` | Image → `axolotl.v1.bin` (format AXL2), fonctions `bake`, `write_bin`, `read_bin` |
| `tools/poster.py` | `axolotl.v1.bin` → `axolotl-poster.v1.webp` |
| `tools/axolotl-reference.jpg` | Illustration Gemini (copiée de `~/Downloads/Gemini_Generated_Image_sq2p0bsq2p0bsq2p.jpg`) |
| `tools/requirements.txt` | `numpy`, `scipy`, `scikit-image`, `Pillow`, `pytest` |
| `assets/axolotl.v1.bin`, `assets/axolotl-poster.v1.webp` | Sorties des outils, commitées |
| `index.html` | Balisage seulement (head, en-tête, navigation latérale, menu, sections, pied de page) |
| `assets/site.v1.css` | Tous les styles, partagés avec `merci.html` |
| `assets/site.v1.js` | Interface hors scène 3D |
| `assets/axolotl.v1.js` | Scène three.js |
| `merci.html` | Page de remerciement restylée |
| `netlify.toml` | En-têtes existants + 404 forcées |
| `tests/test_bake.py`, `tests/test_poster.py`, `tests/test_page.py`, `tests/test_netlify.py` | Tests pytest |

---

### Task 1 : particules (format AXL2) avec filaments de branchies et pattes identifiées

**Files :**
- Create : `tools/bake.py` (point de départ : `scratchpad/tools/bake.py` de la session), `tools/requirements.txt`, `tools/axolotl-reference.jpg`, `tests/test_bake.py`, `assets/axolotl.v1.bin`

**Interfaces :**
- Produces :
  - `bake(src: str, n: int = 34000, seed: int = 11) -> dict` : clés `pos` (n×3 float32, unités de scène), `col` (n×3 uint8), `geo`, `kind`, `part`, `grow` (n uint8).
  - `write_bin(path: str, data: dict) -> None` et `read_bin(path: str) -> dict` (mêmes clés, `pos` à 1e-3 près).
  - CLI : `python -P tools/bake.py SRC OUT [--points N] [--debug]`. `--debug` écrit `OUT.parts.png` et `OUT.geo.png`.
  - Format binaire little-endian AXL2, documenté en tête de `bake.py` :

    | Offset | Contenu |
    |---|---|
    | 0 | magic `b"AXL2"` |
    | 4 | `uint32 N` |
    | 8 | `int16 pos[3N]` (×1000) |
    | 8+6N | `uint8 col[3N]` |
    | 8+9N | `geo[N]` |
    | 8+10N | `kind[N]` |
    | 8+11N | `part[N]` |
    | 8+12N | `grow[N]` |

  - Valeurs des champs :
    - `kind` : 0 corps, 1 branchie, 2 œil, 3 patte ;
    - `part` : 0 aucune ; pour les pattes, 1 avant gauche (x<0), 2 avant droite, 3 arrière gauche, 4 arrière droite ;
    - `geo` : 0 au museau, 255 au bout de la queue ;
    - `grow` : 0 à l'épaule ou la hanche, 255 au bout des doigts, 0 hors pattes.
  - Rendu de référence : celui de la maquette (`scratchpad/maquette/index.html`). Repère, axes et unités ne changent pas : hauteur ≈ 9,5 unités, tête en +y.

- [ ] **Step 1 : écrire `tests/test_bake.py`.** Une fixture de module appelle `bake("tools/axolotl-reference.jpg")` une fois. Tests :
  - `test_roundtrip` : `write_bin` puis `read_bin` dans `tmp_path` redonne `col/geo/kind/part/grow` identiques, et `pos` à 1e-3 près.
  - `test_kind_proportions` :
    - nombre de points `kind==2` entre 40 et 400 ;
    - proportion `kind==1` entre 0,15 et 0,35 ;
    - proportion `kind==3` ≥ 0,05.
  - `test_four_legs` :
    - chaque `part` de 1 à 4 a au moins 150 points ;
    - `part>0` implique `kind==3` ;
    - x moyen de `part 1` et `part 3` < 0, x moyen de `part 2` et `part 4` > 0 ;
    - y moyen de `part 1` > y moyen de `part 3`.
  - `test_grow_runs_outward` :
    - `grow==0` partout où `kind!=3` ;
    - pour `part==1`, |x| moyen des points `grow>200` > |x| moyen des points `grow<50`.
  - `test_extent` : étendue en y entre 9,0 et 10,0, et max |z| ≤ 1,3.
  - `test_file_size` : `write_bin` du résultat par défaut fait ≤ 450 000 octets.

- [ ] **Step 2 : lancer `python -P -m pytest tests/test_bake.py -v`.** Attendu : échec, car le module ou les fonctions n'existent pas.

- [ ] **Step 3 : implémenter dans `tools/bake.py`.** Repartir du script de la maquette (masque, distance, géodésique, parties, profondeur, couleurs) et y ajouter :
  - **Filaments nets :** au moins 45 % des points de branchies sont tirés sur `skimage.morphology.skeletonize(gill)`, avec un décalage ≤ 0,6 px et un bruit de profondeur σ ≤ 1,2 px.
  - **Identification des pattes :** composantes connexes de `limb` après dilatation de 3 px, rangées par signe de x et par `geo` (avant = `geo < 0.4`).
  - **`grow` :** distance euclidienne au masque `thick`, normalisée par patte.
  - **Nombre de points :** n = 34 000 par défaut.

- [ ] **Step 4 : relancer les tests.** Attendu : tout PASS.

- [ ] **Step 5 : produire `assets/axolotl.v1.bin` avec `--debug`, puis vérifier visuellement.** Ouvrir `parts.png` : 4 pattes distinctes, 6 branchies, 2 yeux, et aucun trait sombre des branchies classé en œil. Ne pas commiter les PNG de debug (ajouter `*.parts.png` et `*.geo.png` à `.gitignore`).

- [ ] **Step 6 : commit.**
  ```bash
  git add tools/ tests/test_bake.py assets/axolotl.v1.bin .gitignore
  git commit -m "Outils : particules AXL2 (filaments, pattes, croissance)"
  ```

### Task 2 : poster de repli

**Files :**
- Create : `tools/poster.py`, `tests/test_poster.py`, `assets/axolotl-poster.v1.webp`

**Interfaces :**
- Consumes : `read_bin` (tâche 1).
- Produces :
  - `render_poster(data: dict, out: str, size=(900, 1100), tilt=-0.38, rot_z=0.36, scale=1.0) -> None`.
  - CLI : `python -P tools/poster.py assets/axolotl.v1.bin assets/axolotl-poster.v1.webp`.
  - Rendu :
    - même pose que la scène (rotation x = `tilt`, puis z = `rot_z`), en projection orthographique ;
    - points ronds doux sur fond **transparent**, couleurs du `.bin` ;
    - WebP avec alpha, qualité 80, au plus 150 Ko.

- [ ] **Step 1 : écrire `tests/test_poster.py`.** Tests :
  - `test_poster_file` : le fichier généré dans `tmp_path` fait ≤ 150 000 octets et est en mode `RGBA`.
  - `test_poster_coverage` : la part de pixels avec alpha > 20 est comprise entre 0,08 et 0,5.

- [ ] **Step 2 : lancer `python -P -m pytest tests/test_poster.py -v`.** Attendu : FAIL.

- [ ] **Step 3 : implémenter `render_poster`.** Accumuler les points dans un tableau numpy RGBA, avec une petite gaussienne par point, puis composer par alpha.

- [ ] **Step 4 : relancer les tests.** Attendu : PASS. Générer le poster, puis l'ouvrir pour vérifier qu'il ressemble au rendu de la maquette.

- [ ] **Step 5 : commit.**
  ```bash
  git add tools/poster.py tests/test_poster.py assets/axolotl-poster.v1.webp
  git commit -m "Outils : poster de repli"
  ```

### Task 3 : balisage, styles et blocages Netlify

**Files :**
- Modify : `index.html` (réécriture complète), `netlify.toml`
- Create : `assets/site.v1.css`, `tests/test_page.py`, `tests/test_netlify.py`

**Interfaces :**
- Produces (contrat DOM utilisé par les tâches 4 et 5) :
  - **Bascule JS :** `<html lang="fr" class="no-js">`, et un script inline dans `<head>` qui remplace `no-js` par `js`.
  - **Canvas :** `<canvas id="gl" aria-hidden="true">`, en position fixe, plein écran, derrière le contenu.
  - **En-tête** `.top` :
    - mot-symbole `a.brand` ;
    - `button#menu-toggle[aria-controls="menu"][aria-expanded="false"]` ;
    - lien rond `a.to-invest[href="#investir"]`.
  - **Menu :** `nav#menu[hidden]` (overlay plein écran), qui contient la liste des 8 sections et une pilule Investir.
  - **Navigation latérale :** `ul.rail` avec `span.dot`, puis 8 `a[data-for]` dont les valeurs sont `intro`, `probleme`, `axolotl`, `produit`, `avantage`, `marche`, `feuille-de-route`, `investir`.
  - **Sections :** une `section[data-sec]` par id ci-dessus, en gardant les ids actuels. Les sections 01 à 07 portent `.card` avec `.num` (« 01 »… « 07 »).
  - **Accueil :**
    - `#intro .hero-stage` : zone vide à droite (ordinateur) ou en haut (mobile), qui sert d'ancre à l'axolotl ;
    - elle contient `img.axo-poster[src="assets/axolotl-poster.v1.webp"][alt=""]`.
  - **Section 02 :** `#axolotl .regen-stage[data-axolotl-stage]` contient le même `img.axo-poster`.
    - Ordinateur : colonne à côté du texte.
    - Mobile (< 900 px) : bloc d'environ 55 vh en haut de la carte, sans fond flouté.
  - **Chiffres :** `.num-figure` porte `data-count="1.15"`, `"2.1"`, `"44"`, `"3"` et `data-decimals`, avec le HTML final d'origine à l'intérieur.
  - **Visionneuse :** `canvas#scan` conservé, avec son HUD, ses 2 `.zone` et sa mention « image synthétique ».
  - **Feuille de route :** `ol.road` avec les classes `done` et `now` conservées.
  - **Classes d'animation :**
    - `.reveal` (glissement vers le haut) ;
    - `.stagger > *` (cascade) ;
    - `h1#title` (découpé en mots par la tâche 4).
  - **Classes d'état posées par la tâche 5 :** `html.gl-on`, qui masque `.axo-poster`.
  - **Scripts :** `assets/site.v1.js` et `assets/axolotl.v1.js` en `defer`, three.js r128 en `defer` avant ce dernier.

- [ ] **Step 1 : écrire `tests/test_page.py`.** Il utilise `html.parser`, et l'ancien HTML est lu via `git show 7cd33dd:index.html`. Tests :
  - `test_all_old_text_kept` :
    - chaque texte de `p`, `h1`, `h2`, `h3`, `li`, `small`, `.price` de l'ancien `<main>` et du `<footer>` doit se retrouver dans le texte du nouveau `index.html` ;
    - avant comparaison, normaliser les espaces, `&nbsp;` et `&#8239;` ;
    - exceptions autorisées : `"Régénération"` et l'ancienne légende commençant par `"Un membre d'axolotl repousse cellule par cellule"`. La légende est remplacée par une version qui ne décrit pas d'animation.
  - `test_form_unchanged` : tous les attributs, champs cachés, noms de champs et options listés dans Global Constraints.
  - `test_head` :
    - `<title>` et `meta[name=description]` identiques à l'ancienne page ;
    - `theme-color` = `#ffffff` ;
    - l'URL three.js exacte ;
    - les polices contiennent `Inter+Tight` et `IBM+Plex+Mono`, et `Bricolage` est absent.
  - `test_sections_and_rail` : les 8 ids existent, et les 8 `a[data-for]` pointent vers eux dans le même ordre.
  - `test_no_fake_controls` : aucun texte `FR` dans `.top`, aucun `input[type=search]`.
  - `test_reveal_states_require_js_class` : dans `site.v1.css`, toute règle qui met `opacity:0` ou un `transform` d'entrée sur `.reveal`, `.stagger` ou `#title` a un sélecteur qui commence par `.js `.
  - `test_assets_versioned` : chaque `src` ou `href` local sous `assets/` contient `.v1.`, sauf les SVG du logo, déjà en place.
- [ ] **Step 2 : écrire `tests/test_netlify.py`.** `tomllib` y lit trois `[[redirects]]` (`from = "/tools/*"`, `"/docs/*"`, `"/tests/*"`), chacun avec `to = "/404"`, `status = 404` et `force = true`. Il vérifie aussi que les `[[headers]]` existants sont toujours là.
- [ ] **Step 3 : lancer `python -P -m pytest tests/test_page.py tests/test_netlify.py -v`.** Attendu : FAIL.
- [ ] **Step 4 : réécrire `index.html` et créer `assets/site.v1.css`, puis modifier `netlify.toml`.**
  - Direction : celle de la spec, avec la maquette comme référence visuelle.
  - Le contenu est copié depuis l'ancienne page.
  - Ajouter un fichier `404.html` minimal dans le même style, cible des redirections.
- [ ] **Step 5 : relancer les tests.** Attendu : PASS.
- [ ] **Step 6 : contrôle visuel sans JS.**
  - Servir le site avec `python -m http.server 5181` depuis la racine du dépôt.
  - Dans Chrome, désactiver JS et faire des captures à 1440 et 390 px.
  - Attendu : tout le contenu est visible, mis en page, et le poster est à sa place.
- [ ] **Step 7 : commit.**
  ```bash
  git add index.html 404.html assets/site.v1.css netlify.toml tests/test_page.py tests/test_netlify.py
  git commit -m "Refonte : balisage, styles et blocages Netlify"
  ```

### Task 4 : interface (`assets/site.v1.js`)

**Files :**
- Create : `assets/site.v1.js`

**Interfaces :**
- Consumes : le contrat DOM de la tâche 3.
- Produces : aucune API globale. Le fichier est autonome et fonctionne même si la tâche 5 échoue.

- [ ] **Step 1 : menu.**
  - Un clic sur `#menu-toggle` ouvre `#menu` : `hidden` retiré, `aria-expanded="true"`, liens révélés en cascade, défilement de la page bloqué.
  - Le focus est piégé dans le menu.
  - Échap, un clic sur un lien ou un nouveau clic sur le bouton le ferment, et rendent le focus au bouton.
- [ ] **Step 2 : navigation latérale et révélations.**
  - La section active est la dernière dont le haut est au-dessus du milieu de l'écran. Le `.dot` glisse vers son lien et `a.on` est mis à jour.
  - Un `IntersectionObserver` (seuil 0,15) ajoute `.in` à `.reveal` et `.stagger`.
  - Le titre `#title` est découpé en mots, avec un délai de 0,07 s par mot.
- [ ] **Step 3 : compteurs, visionneuse, feuille de route, formulaire.**
  - **Compteurs :** `.num-figure` compte de 0 à `data-count` en 1,4 s à la première entrée, puis le HTML d'origine est remis exactement.
  - **Visionneuse :** porter le dessin `#scan` de l'ancien script (lignes 650 à 698 de `7cd33dd:index.html`). À l'entrée, une ligne de scan balaie l'image en 1,6 s. Les 2 zones ambrées s'entourent ensuite l'une après l'autre, puis les `.zone` de la liste apparaissent.
  - **Feuille de route :** le trait de `ol.road` se dessine selon la progression du défilement dans la section (variable CSS `--progress`), et `.now` pulse.
  - **Formulaire :** un filet animé apparaît sous les champs au focus. C'est du CSS pur ; le JS n'intervient que si nécessaire.
- [ ] **Step 4 : mouvement réduit.**
  - Avec `prefers-reduced-motion`, les compteurs affichent directement la valeur finale.
  - La visionneuse est dessinée avec les zones déjà entourées, et rien ne glisse.
- [ ] **Step 5 : vérifier dans Chrome** (`http://localhost:5181/`), puis lancer `python -P -m pytest tests -q`. Attendu :
  - menu utilisable au clavier seul (Tab, Maj+Tab, Échap) ;
  - point de la navigation latérale correct à chaque section ;
  - compteurs qui finissent sur le texte exact ;
  - visionneuse animée ;
  - console sans erreur ;
  - tous les tests PASS.
- [ ] **Step 6 : commit.**
  ```bash
  git add assets/site.v1.js
  git commit -m "Refonte : menu, révélations, compteurs, visionneuse, feuille de route"
  ```

### Task 5 : scène axolotl (`assets/axolotl.v1.js`)

**Files :**
- Create : `assets/axolotl.v1.js`

**Interfaces :**
- Consumes :
  - le format AXL2 de la tâche 1 (vérifier le magic, puis lire aux offsets indiqués) ;
  - dans le DOM : `#gl`, `#intro .hero-stage`, `[data-axolotl-stage]`, `img.axo-poster`.
- Produces :
  - la classe `gl-on` sur `<html>` après la première image rendue ;
  - le paramètre d'URL `?nogl`, qui force le repli (pour les tests).

- [ ] **Step 1 : chargement et repli.**
  - Rester en repli (poster visible, pas de `gl-on`) dans ces cas :
    - mouvement réduit, `?nogl` ou `THREE` absent ;
    - échec du contexte WebGL ;
    - `fetch` en échec ou magic invalide.
  - Toutes les erreurs sont capturées : aucune exception non gérée.
- [ ] **Step 2 : rendu de base, repris de la maquette validée.**
  - Paramètres :
    - `TILT = -0.38` ;
    - `outer.rotation.z = 0.36` ;
    - caméra FOV 35, z = 18 ;
    - tailles de points : branchies 0,7 à 1,6, yeux 2,6.
  - Poussière : 1300 points (500 sur mobile).
  - Cellules ambrées : 180 points (80 sur mobile).
  - Formation en 3,6 s de la tête vers la queue, nettoyage ambré de 3,4 à 5 s.
  - Vie au repos : vague, branchies, pattes, frémissement.
  - Effet souris : écartement des particules et parallaxe.
  - DPR plafonné à 2 (1,5 sur mobile), un point sur deux sous 900 px, pas d'effet souris sur écran tactile.
- [ ] **Step 3 : ancrage et chorégraphie.**
  - **États :**

    | État | Quand | Placement et effet |
    |---|---|---|
    | `hero` | `.hero-stage` visible à plus de 30 % | L'objet est centré et dimensionné sur le rectangle de `.hero-stage`. La hauteur de 9,5 unités correspond à 95 % de la hauteur de l'ancre ; le rectangle est converti en coordonnées monde à z = 0. |
    | `regen` | `[data-axolotl-stage]` visible à plus de 30 % | Même calcul, sur cette ancre |
    | `cloud` | Sinon | `uScroll` monte vers 1 (dispersion), alpha × 0,35 |

  - Les changements d'état se font en douceur (interpolation 0,08 par image).
  - Au chargement, l'état initial est calculé à partir de la position de défilement courante.
  - Les ancres sont recalculées à chaque `resize` et `orientationchange`.
- [ ] **Step 4 : régénération de patte**, à chaque entrée dans l'état `regen` (une fois par passage).
  - Uniform `uRegen` : 1 → 0 en 0,6 s (la patte `part==1` se disperse), puis 0 → 1 en 2,4 s.
  - Un point de patte est visible et à sa place si `grow/255 ≤ uRegen`. Sinon, il est transparent et rabattu vers l'épaule.
  - 40 cellules ambrées sont tirées près des points `part==1` ayant `grow > 180`. Elles apparaissent entre 20 % et 80 % de la repousse, puis s'éteignent avant la fin.
- [ ] **Step 5 : vérifier dans Chrome.** Captures à 1440×900 :
  - accueil à 0 s, 1,5 s et 6 s ;
  - zoom sur les branchies : filaments distincts ;
  - zoom sur les pattes : doigts lisibles ;
  - section 02 pendant puis après la régénération ;
  - section 04 (nuage).

  Avec `?nogl`, le poster doit être en place et la console sans erreur. Renommer temporairement `axolotl.v1.bin` donne le même résultat.
- [ ] **Step 6 : vérifier le rechargement en milieu de page.**
  - Défiler jusqu'à la section 05, recharger, puis attendre 2 s.
  - Attendu : un nuage diffus, pas un axolotl complet par-dessus les cartes.
  - Faire de même en section 02 : l'axolotl se forme à côté de la carte et rejoue la régénération.
- [ ] **Step 7 : vérifier le mobile.** À 390×844 :
  - axolotl en haut de l'accueil, texte lisible en dessous ;
  - section 02 avec la zone de régénération visible au-dessus du texte.
- [ ] **Step 8 : commit.**
  ```bash
  git add assets/axolotl.v1.js
  git commit -m "Refonte : scène axolotl en particules"
  ```

### Task 6 : page merci

**Files :**
- Modify : `merci.html`
- Modify : `tests/test_page.py` (ajouter un test)

- [ ] **Step 1 : ajouter `test_merci`.**
  - `merci.html` contient le même `<h1>` et les mêmes deux paragraphes qu'avant (via `git show 7cd33dd:merci.html`).
  - Il conserve `meta robots noindex`, lie `assets/site.v1.css` et ne mentionne plus `Bricolage`.
  - Il n'y a aucun script three.js.
- [ ] **Step 2 : lancer le test.** Attendu : FAIL.
- [ ] **Step 3 : restyler `merci.html`.**
  - Fond blanc, Inter Tight, logo SVG.
  - Pilule « ← Retour à l'accueil » (le texte du lien reste « ← Retour à l'accueil »).
  - Le poster en petit, en décor.
- [ ] **Step 4 : relancer.** Attendu : PASS. Faire une capture à 1440 et 390 px.
- [ ] **Step 5 : commit.**
  ```bash
  git add merci.html tests/test_page.py
  git commit -m "Refonte : page merci"
  ```

### Task 7 : vérification d'ensemble et envoi de la branche

- [ ] **Step 1 : lancer `python -P -m pytest tests -q`.** Attendu : tout PASS.
- [ ] **Step 2 : captures complètes.**
  - Aux tailles 1440×900, 1366×650, 1024×768, 390×844 et 844×390 (paysage), en haut de page puis dans chaque section.
  - Attendu : jamais de texte sous l'axolotl à l'accueil, et aucune barre de défilement horizontale.
- [ ] **Step 3 : mouvement réduit.** L'émuler (Playwright `browser_emulate_media` avec `reducedMotion: "reduce"`). Attendu : posters, aucun mouvement, contenu complet.
- [ ] **Step 4 : console.** Aucune erreur, ni sur `index.html`, ni sur `merci.html`, ni avec `?nogl`.
- [ ] **Step 5 : demander l'accord du porteur**, puis pousser :
  ```bash
  git push origin refonte-particules
  ```
  Ne pas fusionner dans `main` : c'est le porteur qui décide de la mise en ligne.
