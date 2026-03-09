# Jouon Hebrew Grammar

Ce dépôt contient les outils et les données structurées pour la **Grammaire de l'hébreu biblique (1923)** de Paul Joüon, extraite depuis Wikisource.

## 📖 Description

Le but de ce projet est de fournir une version numérique, structurée et nettoyée de la célèbre grammaire hébraïque de Joüon. Les données sont disponibles sous deux formats principaux :
- `data/jouon_grammaire.html` : L'œuvre complète assemblée en un seul fichier HTML.
- `data/jouon_grammaire.tsv` : Une version structurée par paragraphes, prête à être importée dans une base de données.

Ces données sont également intégrées dans [**Bible Parser**](https://www.bibleparser.net), un outil complet d'analyse et de recherche biblique.

## 🛠️ Pipeline de Traitement

Le projet utilise trois scripts Python principaux pour transformer le contenu brut de Wikisource en données exploitables :

1.  **`scripts/extract.py`** : Récupère l'intégralité du livre depuis Wikisource via l'API MediaWiki et génère le fichier HTML complet.
2.  **`scripts/html_to_tsv.py`** : Découpe le fichier HTML en sections basées sur les titres `<h2>` et convertit le contenu en format TSV (Tab-Separated Values).
3.  **`scripts/clean_data.py`** : Applique un nettoyage HTML rigoureux (via une whitelist de balises autorisées comme `<b>`, `<i>`, `<span>` pour l'hébreu) pour garantir des données propres.

## 🚀 Installation et Usage

### Prérequis
- Python 3.x
- Bibliothèque `lxml`

```bash
pip install -r requirements.txt
```

### Exécution du pipeline
1. **Extraction** :
   ```bash
   python scripts/extract.py
   ```
2. **Structuration** :
   ```bash
   python scripts/html_to_tsv.py
   ```
3. **Nettoyage final** :
   ```bash
   python scripts/clean_data.py
   ```

## ⚖️ Licence et Crédits

Le contenu textuel provient de [Wikisource](https://fr.wikisource.org/wiki/Grammaire_de_l%E2%80%99h%C3%A9breu_biblique) (domaine public). Les scripts de ce dépôt sont fournis tels quels pour faciliter la recherche et l'étude de la langue hébraïque.
