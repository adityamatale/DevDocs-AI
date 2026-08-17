import requests
import zipfile
from pathlib import Path


# =========================
# CONFIG
# =========================

VERSION = "3.13.9"

BASE_DIR = Path("data/python")
DOCS_DIR = BASE_DIR / "docs"

BASE_URL = f"https://www.python.org/ftp/python/doc/{VERSION}/"
ARCHIVE_NAME = f"python-{VERSION}-docs-html.zip"

ARCHIVE_PATH = BASE_DIR / ARCHIVE_NAME
DOWNLOAD_URL = BASE_URL + ARCHIVE_NAME


# =========================
# CREATE DIRECTORY
# =========================

DOCS_DIR.mkdir(parents=True, exist_ok=True)


# =========================
# DOWNLOAD
# =========================

print(f"Downloading Python {VERSION} HTML documentation...")

response = requests.get(DOWNLOAD_URL, stream=True)
response.raise_for_status()

with open(ARCHIVE_PATH, "wb") as f:
    for chunk in response.iter_content(chunk_size=8192):
        if chunk:
            f.write(chunk)

print("Download complete.")


# =========================
# EXTRACT
# =========================

print("Extracting documentation...")

with zipfile.ZipFile(ARCHIVE_PATH, "r") as zip_ref:
    zip_ref.extractall(DOCS_DIR)

print("Extraction complete.")


# =========================
# REMOVE ZIP
# =========================

ARCHIVE_PATH.unlink()


# =========================
# SUMMARY
# =========================

html_files = list(DOCS_DIR.rglob("*.html"))

print("\n==============================")
print("Python documentation complete!")
print("==============================")
print(f"Version     : {VERSION}")
print(f"HTML files  : {len(html_files)}")
print(f"Saved to    : {DOCS_DIR.resolve()}")
print("==============================")