# Refonte du site Axolotl : direction « particules », style MYDNA

Date : 2026-11-07
Statut : validé en conversation, en attente de relecture

## Intention

Axolotl est une page pour investisseurs. Elle présente une IA d'aide à la lecture d'imagerie médicale qui signale aux radiologues les signes précoces de cancer. Le projet est basé à Cotonou et ouvre son premier tour de financement.

Le porteur du projet veut un site qui impressionne dès l'arrivée et qui soit « parfait dans son ensemble ». La référence visuelle choisie est le concept MYDNA (Dribbble) :
- un fond blanc très aéré, une typographie fine et des libellés en petites capitales ;
- un grand objet 3D en particules à droite de l'accueil ;
- une navigation latérale verticale, des boutons en pilule ;
- des sections numérotées présentées en cartes.

L'objet en particules est un **axolotl très détaillé**. Il reprend l'histoire que raconte déjà le site : l'axolotl régénère ses membres sans que la croissance ne s'emballe, et c'est ce contrôle qu'Axolotl veut aider à surveiller.

Une maquette jetable de l'accueil a été validée par le porteur. Elle se trouve hors du dépôt, dans le dossier temporaire de la session (`scratchpad/maquette/index.html`, avec `axolotl.bin` et `scratchpad/tools/bake.py`), et sert de référence de rendu.

Le rendu validé est celui de `maquette/index.html` :
- `TILT = -0.38` ;
- diagonale `outer.rotation.z = 0.36` ;
- échelle 0.98 sur ordinateur ;
- taille des points : branchies 0.7, yeux 2.6.

Le fichier `scratchpad/tools/particles.js` est une version intermédiaire périmée, à ne pas suivre.

## Objectifs

1. Reprendre **tout le contenu actuel** de `index.html` (textes, chiffres, sources, mentions légales) dans la nouvelle direction artistique.
2. Placer un axolotl en particules détaillé et animé comme pièce maîtresse :
   - l'animal est reconnaissable au premier coup d'œil : 6 branchies plumeuses, 4 pattes avec doigts, yeux, queue ;
   - il « vit » : vague de nage, branchies qui frémissent, pattes qui pagaient.
3. Avoir des animations soignées dans chaque section, sans gêner la lecture.
4. Offrir une version mobile aussi soignée que la version ordinateur.
5. Garder le formulaire investisseurs Netlify **fonctionnellement identique**.

## Non-objectifs

- Pas de nouveau contenu ni de réécriture des textes, sauf micro-libellés d'interface (« Défiler pour découvrir », numéros de section).
- Pas de framework, pas d'étape de build. Le site reste en HTML/CSS/JS statique, publié tel quel par Netlify (`publish = "."`).
- Pas de version anglaise. Le sélecteur « FR » de la maquette est retiré, car il ne mène nulle part.
- Pas de mode sombre (choix de Claude, voir plus bas).

## Anti-objectifs (échec même si « ça marche »)

- Un axolotl flou ou méconnaissable, ou une forme générique en particules.
- Un texte illisible parce que les particules passent dessous sans fond.
- Une page vide ou cassée si WebGL, le CDN ou le fichier de particules ne chargent pas.
- Des animations qui saccadent sur un ordinateur portable ordinaire, ou un téléphone qui chauffe.
- Un formulaire qui ne remonte plus dans Netlify Forms.
- Des faux éléments d'interface : boutons sans effet, recherche, son.

## Contraintes

- **Fichiers** : `index.html`, `merci.html`, `netlify.toml`, `assets/`, dans le dépôt `Constantin2105/AXOLOTL` (branche `main`). Commit et push uniquement quand le porteur le demande.
- **Bibliothèque externe** : uniquement three.js r128 depuis cdnjs (`https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js`), comme dans la maquette. Pas d'autre dépendance d'exécution.
- **Polices** : Google Fonts, Inter Tight (300/400/500) et IBM Plex Mono (400/500).
- **Formulaire** : conserver à l'identique l'attribut `name="investisseurs"`, `data-netlify="true"`, `netlify-honeypot="bot-field"`, les champs cachés `form-name` et `subject`, les champs et leurs `name`, `action="/merci"`.
- **Accessibilité** :
  - `prefers-reduced-motion` désactive tout mouvement : l'axolotl s'affiche formé et immobile, les textes apparaissent sans glissement ;
  - focus visible partout, menu utilisable au clavier (Échap pour fermer, focus piégé dans le menu ouvert) ;
  - les canvas sont `aria-hidden` ou ont une description.
- **Poids** : particules ≤ 450 Ko. Page complète, hors polices et three.js, autour de 1 Mo maximum.
- **Ordre de chargement** : le texte de l'accueil s'affiche avant la scène 3D. La scène se charge ensuite, sans décaler la mise en page.

## Direction artistique (décidée)

- **Fond** blanc `#ffffff`. Encre `#111518`, texte secondaire `#62696d`, filets `#e4e7e9`.
- **Particules** : dégradé le long du corps, de la tête à la queue : `#f27fa0` → `#d8479a` → `#8d55d8` → `#4f8fe0`. Branchies magenta vif.
- **Ambre** `#f2a93b` réservé au « signal », c'est-à-dire ce que l'IA repère : cellules qui débordent, zones entourées sur la mammographie.
- **Titres** : Inter Tight 400, interlettrage serré. Libellés en IBM Plex Mono, petites capitales.
- **Boutons pilule** : contour noir avec survol plein noir, et une pilule noire « Défiler pour découvrir ».
- **Cartes numérotées** (01, 02…) : fond blanc translucide avec flou d'arrière-plan, pour que les particules restent visibles derrière sans gêner la lecture.
- **Navigation latérale fixe** (ordinateur) : liste des sections, filet vertical et petit cercle qui glisse vers la section en cours.
- **En-tête** : mot-symbole « AXOLOTL » en capitales espacées, bouton « Menu » (deux traits), bouton rond flèche vers « Investir ». Le logo SVG existant reste en favicon et en pied de page.

## L'axolotl en particules

### Source et pipeline (décidé)

- **Source** : une illustration générée par Gemini (vue de dessus, fond blanc, 2048×2048). Elle est à ajouter au dépôt sous `tools/axolotl-reference.jpg` ; l'original est dans Téléchargements, `Gemini_Generated_Image_sq2p0bsq2p0bsq2p.jpg`.
- **Script hors ligne** `tools/bake.py` (Python, numpy, scipy, scikit-image, Pillow). Il produit `assets/axolotl.bin` : environ 36 000 points avec position 3D, couleur, distance le long du corps et type de partie (corps, branchie, œil, patte). Le format binaire est documenté en tête du script. Le script de la maquette sert de point de départ.
- **Volume** : il vient de la distance au contour (corps arrondi, pattes et branchies fines).
- **Densité** : plus de points sur les contours et les détails du dessin, pour que les doigts et les yeux se lisent.
- **Le navigateur** charge `axolotl.bin`, ajoute la poussière ambiante et les cellules ambrées, et anime tout dans un shader.

### Exigence de netteté

À la taille de l'accueil sur ordinateur, les branchies doivent montrer des **filaments distincts**, et pas un nuage rose comme dans la maquette.

Le moyen est laissé au constructeur, par exemple : générer les filaments en code le long des tiges détectées, réduire le bruit de profondeur, ou ajuster tailles et densité. Vérification par capture zoomée.

### Comportements

- **Formation** à l'arrivée, environ 3,5 s : les points convergent d'un nuage dispersé, de la tête vers la queue.
- **Cellules ambrées** : pendant la formation, des cellules poussent juste hors du corps, pulsent, puis disparaissent. C'est le « contrôle de la croissance ».
- **Vie au repos** :
  - une vague parcourt le corps, d'amplitude croissante vers la queue ;
  - les branchies frémissent, déphasées ;
  - les pattes pagaient ;
  - de légers mouvements de respiration et de balancement.
- **Souris** : les particules s'écartent doucement sous le curseur, et l'animal pivote légèrement vers la souris (parallaxe).
- **Pose** : vue de trois quarts, en diagonale, la tête vers le haut, comme l'hélice de MYDNA. La queue peut déborder sur la première carte.

### Chorégraphie au défilement

- **Accueil** : l'axolotl est complet, à droite du texte.
- **En quittant l'accueil** : il se dissout en nuage diffus qui reste derrière les cartes.
- **Section 02 « Pourquoi ce nom »** : il se reforme à côté de la carte (plus petit si nécessaire) et rejoue une **régénération de patte**. Une patte avant se disperse, puis repousse de l'épaule jusqu'aux doigts. Des cellules ambrées débordent et sont éliminées, puis la croissance s'arrête exactement à la forme d'origine. La séquence se déclenche à l'entrée dans la section, une fois par passage. La légende existante sur la régénération est reprise dans la carte.
- **En quittant la section 02** : retour au nuage diffus.
- **Section 02 sur mobile (< 900 px)** (choix de Claude) : la carte 02 réserve en haut une zone transparente d'environ 55 vh, sans fond flouté. L'axolotl s'y reforme et rejoue la régénération, déclenchée quand cette zone est visible. Le texte de la carte suit en dessous.
- **Ancien canvas 2D `#regen`** (choix de Claude) : il est supprimé avec son libellé « Régénération ». En repli (sans WebGL ou en mouvement réduit), la section 02 montre l'image fixe de l'axolotl. La légende est reformulée pour ne pas décrire une animation absente.

### Repli

Sans WebGL, sans three.js, si `axolotl.bin` ne charge pas ou en mouvement réduit, une **image fixe** de l'axolotl en particules s'affiche à la même place (capture du rendu, au format WebP ou PNG, de 150 Ko maximum). La page reste complète et lisible.

### Mobile

- Moitié des points.
- L'axolotl en haut de l'écran d'accueil, le texte en dessous.
- Pas d'effet souris.
- Rendu en pause quand l'onglet est caché (comportement par défaut de `requestAnimationFrame`).

## Structure de la page et animations par section

Le contenu de chaque section est repris de `index.html`.

| # | Section (ancre) | Contenu | Animation |
|---|---|---|---|
| — | En-tête | AXOLOTL, Menu, bouton Investir | Apparition en fondu au chargement |
| — | Accueil (`#intro`) | Libellé « Mission d'Axolotl », h1 « L'IA qui repère le cancer à temps. », texte d'intro (version longue actuelle), pilule « Recevoir le dossier investisseur », lien « Voir le produit », 3 preuves (MedGemma, Cotonou, premier tour), pilule « Défiler pour découvrir » | Titre révélé mot par mot, puis texte et boutons en fondu décalé. Axolotl qui se forme. |
| 01 | Le problème (`#probleme`) | Titre, texte, 4 chiffres (1,15 M ; 2,1 M ; 44 % ; 3 / million) avec renvois, 4 sources | Carte qui monte. Chiffres en compteur à l'entrée (une fois). |
| 02 | Pourquoi ce nom (`#axolotl`) | Titre, 3 paragraphes, note avec lien vers l'article, citation | Régénération de patte (voir plus haut) |
| 03 | Le produit (`#produit`) | Titre, intro, 3 étapes, visionneuse de mammographie (canvas synthétique existant, HUD, 2 zones, mention « image synthétique ») | Étapes en cascade. La visionneuse est balayée par une ligne de scan, puis les 2 zones ambrées s'entourent l'une après l'autre et les lignes de la liste apparaissent. |
| 04 | Notre avantage (`#avantage`) | Titre, 6 arguments | Cartes en cascade |
| 05 | Le marché (`#marche`) | Titre, intro, 3 types de clients avec modèle de prix | Cartes en cascade |
| 06 | Feuille de route (`#feuille-de-route`) | Titre, 4 étapes (1 faite, 2 en cours, 3–4 à venir) | Ligne de temps qui se dessine au défilement. Étape en cours avec un point qui pulse. |
| 07 | Investir (`#investir`) | Titre, intro, 4 usages des fonds, formulaire | Carte qui monte. Champs avec un filet animé au focus. |
| — | Pied de page | Logo, mentions (aide au diagnostic non validée, pas une offre de titres, MedGemma/Google), © 2026 | — |

- La **navigation latérale** liste : Intro, Le problème, Axolotl, Le produit, Avantage, Marché, Feuille de route, Investir.
- Le **menu plein écran** (bouton « Menu ») montre les mêmes entrées en grand, révélées en cascade, plus la pilule Investir. Il se ferme au clic sur un lien, sur le bouton ou avec Échap.
- **`merci.html`** reprend le même style : fond blanc, Inter Tight, pilule « Retour à l'accueil ». Une petite poignée de particules ou le logo, sans three.js.
- Les **métadonnées** de `index.html` (title, description, Open Graph, favicon) sont conservées. `theme-color` passe à `#ffffff`.

## Choix faits par Claude (non discutés, modifiables)

- Inter Tight remplace Bricolage Grotesque et IBM Plex Sans, pour coller au style fin de MYDNA.
- Le dégradé rose → violet → bleu remplace le vert profond (`#0e3534`) comme couleur d'ambiance. Le vert disparaît du site.
- Le site est en clair uniquement. Le mode sombre actuel est retiré, car la direction MYDNA repose sur le blanc.
- Le sélecteur « FR » de la maquette est retiré.
- La carte numérotée sert de gabarit pour chaque section. Les sections longues (02, 03, 07) peuvent devenir de grandes cartes avec une mise en page interne propre.
- L'axolotl ne réapparaît pas en entier en bas de page. Il reste en nuage diffus après la section 02.
- `tools/` et `docs/` sont dans le dépôt, mais bloqués en ligne : `netlify.toml` renvoie une 404 forcée pour `/tools/*` et `/docs/*`, pour que le script, l'image source et ce document ne soient pas servis sur le domaine investisseurs.
- `assets/*` a un cache `immutable`. Les fichiers qui changent (`axolotl.bin`, image de repli, éventuel `site.js`) portent donc un suffixe de version dans leur nom (`axolotl.v1.bin`).

## Laissé au constructeur

- La découpe interne de chaque carte et les espacements exacts, dans l'esprit de la maquette.
- Les courbes et durées exactes des animations. Repère : 0,8 à 1,2 s, `cubic-bezier(.2,.8,.2,1)`.
- La technique pour obtenir des filaments de branchies nets.
- La technique de la régénération de patte dans le shader : uniform de progression, masque par type « patte » et proximité de l'épaule.
- L'organisation du JS : un seul `<script>` ou un fichier `assets/site.js`.

## Vérification attendue

- Captures à 1440, 1024 et 390 px de large, en haut de page et dans chaque section.
- Capture zoomée des branchies et des pattes.
- Mouvement réduit activé.
- Scène 3D désactivée (WebGL bloqué ou `axolotl.bin` absent) : la page reste complète.
- Console sans erreur.
- Formulaire testé en local pour l'affichage. L'envoi réel ne peut se vérifier qu'une fois déployé sur Netlify.
