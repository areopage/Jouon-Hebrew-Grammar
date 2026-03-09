#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Export d'un LIVRE Wikisource en un seul fichier HTML.

Cas typique : Grammaire de l’hébreu biblique
https://fr.wikisource.org/wiki/Grammaire_de_l%E2%80%99h%C3%A9breu_biblique

Principe :
- On part de la page principale du livre.
- On récupère son HTML (via l'API MediaWiki, action=parse&prop=text).
- On extrait tous les liens <a href="/wiki/TITRE/..."> qui prolongent ce livre.
- Pour chacun, on récupère le HTML rendu (action=parse&prop=text&page=...).
- On assemble tout dans un unique fichier HTML.
"""

import sys
import json
import time
import urllib.request
import urllib.parse
from html.parser import HTMLParser

USER_AGENT = "BibleParserWikisourceBookFetcher/1.0 (https://www.bibleparser.net/)"
DEFAULT_OUTPUT = "data/jouon_grammaire.html"


# ----------------------------------------------------------------------
# HTTP utilitaire
# ----------------------------------------------------------------------

def http_get(url, params=None):
    """
    GET avec User-Agent correct.
    Si params est fourni (dict), ils sont ajoutés à l'URL.
    """
    if params:
        query = urllib.parse.urlencode(params)
        sep = "&" if "?" in url else "?"
        url = url + sep + query

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read().decode("utf-8")
    return data


# ----------------------------------------------------------------------
# Parser HTML pour extraire les liens de chapitres
# ----------------------------------------------------------------------

class BookLinkParser(HTMLParser):
    """
    Extrait tous les <a href="/wiki/<prefix>/..."> du fragment HTML de la
    page principale.
    prefix doit être la partie encodée du titre du livre, ex. :
      "Grammaire_de_l%E2%80%99h%C3%A9breu_biblique"
    """

    def __init__(self, encoded_prefix):
        HTMLParser.__init__(self)
        self.encoded_prefix = encoded_prefix
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return

        href = None
        for k, v in attrs:
            if k.lower() == "href":
                href = v
                break

        if not href:
            return

        # Ex: /wiki/Grammaire_de_l%E2%80%99h%C3%A9breu_biblique/Introduction/Paragraphe_1
        expected_start = "/wiki/" + self.encoded_prefix + "/"
        if href.startswith(expected_start):
            title_enc = href.split("/wiki/", 1)[1]  # ce qui suit /wiki/
            title = urllib.parse.unquote(title_enc)
            if title not in self.links:
                self.links.append(title)


# ----------------------------------------------------------------------
# API MediaWiki : HTML d'une page
# ----------------------------------------------------------------------

def get_page_html_from_api(domain, title):
    """
    Récupère le HTML rendu pour un titre donné via l'API MediaWiki.
    domain ex. "https://fr.wikisource.org"
    """
    api_endpoint = domain + "/w/api.php"
    params = {
        "action": "parse",
        "format": "json",
        "prop": "text",
        "page": title
    }
    data = http_get(api_endpoint, params)
    js = json.loads(data)

    parse = js.get("parse")
    if not parse:
        raise RuntimeError("Impossible de parser la page : %s" % title)

    text_obj = parse.get("text", {})
    html_fragment = text_obj.get("*", "")
    if not html_fragment:
        raise RuntimeError("HTML vide pour la page : %s" % title)

    return html_fragment


# ----------------------------------------------------------------------
# Export du livre
# ----------------------------------------------------------------------

def export_wikisource_book(root_url, output_filename):
    """
    Export complet d'un livre Wikisource à partir de l'URL de sa page principale.
    """
    parsed = urllib.parse.urlparse(root_url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError("URL Wikisource invalide : %s" % root_url)

    domain = parsed.scheme + "://" + parsed.netloc        # ex. https://fr.wikisource.org
    path = parsed.path

    if "/wiki/" not in path:
        raise ValueError("L'URL ne semble pas être une page /wiki/... : %s" % root_url)

    # Partie encodée et décodée du titre
    title_enc = path.split("/wiki/", 1)[1]                # ex. Grammaire_de_l%E2%80%99h%C3%A9breu_biblique
    book_title = urllib.parse.unquote(title_enc)          # ex. Grammaire_de_l’hébreu_biblique

    print("Domaine :", domain)
    print("Titre de l'œuvre :", book_title)

    # 1) Récupérer le HTML de la page principale via l'API
    print("\nRécupération de la page principale (table des matières)...")
    root_html = get_page_html_from_api(domain, book_title)

    # 2) Extraire les liens internes vers les chapitres/paragraphes
    print("Analyse de la table des matières pour extraire les liens...")
    parser = BookLinkParser(title_enc)
    parser.feed(root_html)
    chapter_titles = parser.links
    print("Nombre de pages de chapitres détectées :", len(chapter_titles))

    if not chapter_titles:
        print("Aucun lien de chapitre détecté dans la page. "
              "Le livre est peut-être structuré autrement ou très court.")

    # 3) Écriture du fichier final
    print("\nTéléchargement et assemblage du contenu dans", output_filename)
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html>\n<html lang=\"fr\">\n<head>\n")
        f.write("<meta charset=\"utf-8\">\n")
        f.write("<title>%s (Wikisource)</title>\n" % book_title)
        f.write("</head>\n<body>\n")
        f.write("<h1>%s</h1>\n" % book_title)
        f.write("<hr>\n")

        # Page principale en premier (souvent table des matières)
        f.write("<h2>(Page principale)</h2>\n")
        f.write(root_html)
        f.write("\n<hr>\n")

        # Puis chaque chapitre / paragraphe
        for idx, chap_title in enumerate(chapter_titles, start=1):
            print("  [%d/%d] %s" % (idx, len(chapter_titles), chap_title))
            try:
                chap_html = get_page_html_from_api(domain, chap_title)
            except Exception as e:
                print("    ERREUR sur la page %s : %s" % (chap_title, e))
                continue

            # Sous-titre lisible : partie après "book_title/"
            if chap_title.startswith(book_title + "/"):
                subtitle = chap_title[len(book_title) + 1:]   # +1 pour le '/'
            else:
                subtitle = chap_title

            f.write("<h2>%s</h2>\n" % subtitle)
            f.write(chap_html)
            f.write("\n<hr>\n")

            time.sleep(0.3)  # Petite pause pour ne pas surcharger Wikisource

        f.write("</body>\n</html>\n")

    print("\nExport terminé.")
    print("Fichier généré :", output_filename)


# ----------------------------------------------------------------------
# Interface CLI simple
# ----------------------------------------------------------------------

def main():
    print("=== Export d'un LIVRE Wikisource en HTML ===\n")

    url = input("URL de la page principale du livre Wikisource :\n> ").strip()
    if not url:
        print("Aucune URL fournie. Fin.")
        sys.exit(0)

    out = input("Nom du fichier HTML de sortie [%s] : " % DEFAULT_OUTPUT).strip()
    if not out:
        out = DEFAULT_OUTPUT

    try:
        export_wikisource_book(url, out)
    except Exception as e:
        print("\nERREUR :", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
