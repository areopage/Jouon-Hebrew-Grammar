# jouon_html_to_clean_tsv.py
# Dépendance: lxml (pip install lxml)

import re
import csv
import html as htmllib
from lxml import html

INPUT_HTML = "data/jouon_grammaire.html"
OUTPUT_TSV = "data/jouon_grammaire.tsv"

H2_RE = re.compile(r"<h2\b[^>]*>(.*?)</h2>", re.IGNORECASE | re.DOTALL)
TAG_RE = re.compile(r"<[^>]+>")

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
}

REMOVE_ENTIRELY = {"meta", "link", "style", "script", "noscript"}

DROP_BY_ID = {"ws-data", "headertemplate", "subheader"}
DROP_BY_CLASS_SUBSTR = {"ws-noexport", "mw-parser-output", "headertemplate"}


def extract_h2_title(section_html: str) -> str:
    m = H2_RE.search(section_html)
    if not m:
        return ""
    raw = m.group(1)
    raw = TAG_RE.sub(" ", raw)
    raw = htmllib.unescape(raw)
    raw = re.sub(r"\s+", " ", raw).strip()
    return raw


def one_line(s: str) -> str:
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"\s*\n\s*", " ", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def should_drop_element(el) -> bool:
    el_id = (el.get("id") or "").strip()
    if el_id in DROP_BY_ID:
        return True
    cls = (el.get("class") or "")
    for token in DROP_BY_CLASS_SUBSTR:
        if token and token in cls:
            return True
    return False


def safe_drop_tag(el) -> None:
    """
    drop_tag() sécurisé:
    - ne fait rien si pas de parent
    - ne drop pas html/body
    """
    parent = el.getparent()
    if parent is None:
        return
    tag = (el.tag or "").lower()
    if tag in {"html", "body"}:
        return
    el.drop_tag()


def clean_jouon_html(html_text: str) -> str:
    if not html_text or not html_text.strip():
        return ""

    parser = html.HTMLParser(remove_comments=True, recover=True)
    try:
        root = html.fromstring(html_text, parser=parser)
    except Exception:
        return one_line(html_text)

    # IMPORTANT: on fige la liste des éléments (on ne modifie pas pendant une itération "vivante")
    elements = list(root.iterdescendants())

    # 1) drop_tree (tags/blocks inutiles)
    for el in elements:
        if el.getparent() is None:
            continue
        tag = (el.tag or "").lower()

        if tag in REMOVE_ENTIRELY:
            el.drop_tree()
            continue

        if should_drop_element(el):
            el.drop_tree()
            continue

    # 2) whitelist + nettoyage attributs + unwrap
    # Re-fige une liste, car l'arbre a changé
    elements = list(root.iterdescendants())

    for el in elements:
        parent = el.getparent()
        if parent is None:
            continue

        tag = (el.tag or "").lower()
        if not tag:
            continue

        if tag not in ALLOWED_TAGS:
            safe_drop_tag(el)
            continue

        allowed = ALLOWED_ATTRS.get(tag, set())
        for attr in list(el.attrib):
            if attr not in allowed:
                del el.attrib[attr]

        if tag == "span" and not el.attrib:
            safe_drop_tag(el)

    cleaned = html.tostring(root, encoding="unicode", method="html")
    cleaned = re.sub(r"\s+([,.;:!?])", r"\1", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()
    return one_line(cleaned)


def iter_sections_from_file(filepath: str):
    in_section = False
    buf = []

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            stripped = line.strip()

            if in_section and stripped == "<!--":
                yield "".join(buf)
                buf = []
                in_section = False
                continue

            if (not in_section) and re.search(r"<h2\b", line, flags=re.IGNORECASE):
                in_section = True
                buf = [line]
                continue

            if in_section:
                buf.append(line)

    if in_section and buf:
        yield "".join(buf)


def main():
    with open(OUTPUT_TSV, "w", encoding="utf-8", newline="") as out:
        w = csv.writer(out, delimiter="\t", quoting=csv.QUOTE_MINIMAL, lineterminator="\n")
        w.writerow(["paragraphe", "entrée"])

        n = 0
        for section_html in iter_sections_from_file(INPUT_HTML):
            titre = extract_h2_title(section_html)
            entree_clean = clean_jouon_html(section_html)
            w.writerow([titre, entree_clean])
            n += 1

    print(f"OK: {n} sections -> {OUTPUT_TSV}")


if __name__ == "__main__":
    main()
