# clean_tsv_jouon.py
# Dépendance: lxml (pip install lxml)
# Entrée : tsv_jouon.tsv  (colonnes: paragraphe \t entrée)
# Sortie : tsv_jouon_clean.tsv (paragraphe \t entrée nettoyée, 1 ligne)

import csv
import sys
import re
from lxml import html

csv.field_size_limit(sys.maxsize)  # ← AJOUT IMPORTANT


INPUT_TSV = "data/jouon_grammaire.tsv"
OUTPUT_TSV = "data/jouon_grammaire_clean.tsv"

# --- Whitelist adaptée à ton HTML Wikisource/MediaWiki ---
ALLOWED_TAGS = {
    "h2", "p", "b", "i", "em", "strong",
    "ol", "ul", "li",
    "table", "tbody", "tr", "td",
    "sup", "sub",
    "a", "span", "abbr"
}

ALLOWED_ATTRS = {
    "a": {"href", "title"},
    "span": {"lang", "dir"},
    "abbr": {"title"},
    "td": {"rowspan", "colspan", "align"},
    "tr": set(),
    "table": set(),
}

REMOVE_ENTIRELY = {"meta", "link", "style", "script", "noscript"}

# Supprime aussi quelques blocs MediaWiki “connus” quand ils apparaissent
# (header templates, ws-data, etc.)
DROP_BY_ID = {"ws-data", "headertemplate", "subheader"}
DROP_BY_CLASS_SUBSTR = {"ws-noexport", "mw-parser-output", "headertemplate"}


def one_line(s: str) -> str:
    """Assure une seule ligne (DB/import friendly)."""
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"\s*\n\s*", " ", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def should_drop_element(el) -> bool:
    """Décide si on supprime l'élément (drop_tree) selon id/class."""
    el_id = (el.get("id") or "").strip()
    if el_id in DROP_BY_ID:
        return True

    cls = (el.get("class") or "")
    # Beaucoup de tes sources ont "xclass=" au lieu de "class=" : on enlève quand même xclass ailleurs.
    # Ici on gère seulement class si présent.
    for token in DROP_BY_CLASS_SUBSTR:
        if token and token in cls:
            return True

    return False


def clean_jouon_html(html_text: str) -> str:
    """
    Nettoyage du HTML issu de Wikisource/MediaWiki :
    - supprime meta/link/style/script
    - supprime certains blocs ws-noexport & co
    - whitelist de tags
    - whitelist d'attributs
    - retire xclass, style, itemscope/itemprop, id, etc.
    - conserve span[lang,dir] (hébreu) + a[href,title] + abbr[title] + td[rowspan,colspan,align]
    """
    if not html_text or not html_text.strip():
        return ""

    # Parser tolérant
    parser = html.HTMLParser(remove_comments=True, recover=True)
    try:
        root = html.fromstring(html_text, parser=parser)
    except Exception:
        # Fallback ultra-safe : retourne une version 1-ligne brute
        return one_line(html_text)

    # 1) Drop_tree pour certains éléments inutiles
    # Itération via xpath pour éviter les surprises quand on modifie l'arbre
    for el in root.xpath("//*"):
        tag = (el.tag or "").lower()

        if tag in REMOVE_ENTIRELY:
            el.drop_tree()
            continue

        if should_drop_element(el):
            el.drop_tree()
            continue

    # 2) Whitelist tags + nettoyage attributs
    for el in root.xpath("//*"):
        tag = (el.tag or "").lower()

        # Si ce n'est pas un tag normal (comment/processing) : ignorer
        if not tag:
            continue

        if tag not in ALLOWED_TAGS:
            # unwrap : on garde le texte/enfants, on enlève la balise
            el.drop_tag()
            continue

        allowed = ALLOWED_ATTRS.get(tag, set())
        # Retire TOUS les attributs non autorisés
        for attr in list(el.attrib):
            if attr not in allowed:
                del el.attrib[attr]

        # Si span n'a plus d'attribut → unwrap (évite spans parasites)
        if tag == "span" and not el.attrib:
            el.drop_tag()

    cleaned = html.tostring(root, encoding="unicode", method="html")

    # Bonus : supprime espaces avant ponctuation et quelques scories fréquentes
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()

    return one_line(cleaned)


def main():
    count_in = 0
    count_out = 0

    with open(INPUT_TSV, "r", encoding="utf-8", newline="") as f_in, \
         open(OUTPUT_TSV, "w", encoding="utf-8", newline="") as f_out:

        r = csv.DictReader(f_in, delimiter="\t")
        if not r.fieldnames or "paragraphe" not in r.fieldnames or "entrée" not in r.fieldnames:
            raise ValueError("TSV invalide : colonnes attendues = 'paragraphe' et 'entrée'.")

        w = csv.DictWriter(f_out, fieldnames=["paragraphe", "entrée"], delimiter="\t",
                           quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        w.writeheader()

        for row in r:
            count_in += 1
            paragraphe = (row.get("paragraphe") or "").strip()
            entree = row.get("entrée") or ""
            entree_clean = clean_jouon_html(entree)

            w.writerow({"paragraphe": paragraphe, "entrée": entree_clean})
            count_out += 1

    print(f"OK: {count_out}/{count_in} lignes -> {OUTPUT_TSV}")


if __name__ == "__main__":
    main()
