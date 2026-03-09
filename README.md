# Joüon Hebrew Grammar

This repository provides tools and structured data for Paul Joüon's **Grammaire de l'hébreu biblique (1923)**, extracted from Wikisource.

## 📖 Description

The objective of this project is to offer a clean, digital, and structured version of Joüon's renowned Hebrew grammar. The data is provided in two main formats:
- `data/jouon_grammaire.html`: The complete work merged into a single HTML file.
- `data/jouon_grammaire.tsv`: A version structured by paragraphs, ready for database import.

This dataset is also integrated into [**Bible Parser**](https://www.bibleparser.net), a comprehensive software suite for biblical analysis and research.

## 🛠️ Processing Pipeline

The project uses three main Python scripts to transform raw content from Wikisource into usable data:

1.  **`scripts/extract.py`**: Fetches the entire book from Wikisource via the MediaWiki API and generates the full HTML file.
2.  **`scripts/html_to_tsv.py`**: Splits the HTML file into sections based on `<h2>` headers and converts the content into TSV (Tab-Separated Values) format.
3.  **`scripts/clean_data.py`**: Applies rigorous HTML cleaning (using a whitelist of allowed tags like `<b>`, `<i>`, `<span>` for Hebrew) to ensure data integrity.

## 🚀 Installation and Usage

### Prerequisites
- Python 3.x
- `lxml` library

```bash
pip install -r requirements.txt
```

### Running the pipeline
1. **Extraction**:
   ```bash
   python scripts/extract.py
   ```
2. **Structuring**:
   ```bash
   python scripts/html_to_tsv.py
   ```
3. **Final Cleaning**:
   ```bash
   python scripts/clean_data.py
   ```

## ⚖️ License and Credits

The textual content originates from [Wikisource](https://fr.wikisource.org/wiki/Grammaire_de_l%E2%80%99h%C3%A9breu_biblique) (Public Domain). The scripts in this repository are provided as-is to facilitate Hebrew language research and study.

---

*Note: A French version of this README is available at [README_FR.md](README_FR.md).*
