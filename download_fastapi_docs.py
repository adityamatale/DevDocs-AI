import requests
from pathlib import Path

# =========================
# CONFIG
# =========================

REPO = "fastapi/fastapi"
BRANCH = "master"

BASE_DIR = Path("data/fastapi")
DOCS_DIR = BASE_DIR / "docs"
EXAMPLES_DIR = BASE_DIR / "examples"
API_DIR = BASE_DIR / "api"
PDF_DIR = BASE_DIR / "pdf"

GITHUB_API = (
    f"https://api.github.com/repos/{REPO}"
    f"/git/trees/{BRANCH}?recursive=1"
)

RAW_BASE = (
    f"https://raw.githubusercontent.com/"
    f"{REPO}/{BRANCH}/"
)


# =========================
# CREATE DIRECTORIES
# =========================

for directory in [
    DOCS_DIR,
    EXAMPLES_DIR,
    API_DIR,
    PDF_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)


# =========================
# GET REPOSITORY FILES
# =========================

def get_repo_files():
    response = requests.get(GITHUB_API)
    response.raise_for_status()

    data = response.json()

    if data.get("truncated"):
        print("WARNING: GitHub repository tree was truncated.")

    return [
        item["path"]
        for item in data["tree"]
        if item["type"] == "blob"
    ]


# =========================
# DOWNLOAD FILE
# =========================

def download_file(repo_path, output_path):

    url = RAW_BASE + repo_path

    response = requests.get(url)
    response.raise_for_status()

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(output_path, "wb") as f:
        f.write(response.content)

    print(f"[+] {repo_path}")


# =========================
# MAIN
# =========================

def main():

    print("Fetching FastAPI repository...")

    files = get_repo_files()

    print(f"Found {len(files)} files\n")

    docs_count = 0
    examples_count = 0
    api_count = 0
    pdf_count = 0

    for file_path in files:

        lower = file_path.lower()

        # =====================================
        # 1. DOCUMENTATION
        # =====================================

        if file_path.startswith("docs/"):

            if lower.endswith((".md", ".mdx")):

                output = DOCS_DIR / file_path.replace(
                    "docs/", "", 1
                )

                download_file(
                    file_path,
                    output
                )

                docs_count += 1

        # =====================================
        # 2. DOCUMENTATION EXAMPLES
        # =====================================

        elif file_path.startswith("docs_src/"):

            # Only useful source/code files
            if lower.endswith(
                (
                    ".py",
                    ".pyi",
                    ".json",
                    ".yaml",
                    ".yml",
                    ".toml",
                    ".txt",
                )
            ):

                output = EXAMPLES_DIR / file_path.replace(
                    "docs_src/", "", 1
                )

                download_file(
                    file_path,
                    output
                )

                examples_count += 1

        # =====================================
        # 3. API / OPENAPI MATERIAL
        # =====================================

        elif (
            "openapi" in lower
            or "swagger" in lower
            or "redoc" in lower
        ):

            if lower.endswith(
                (
                    ".json",
                    ".yaml",
                    ".yml",
                    ".md",
                    ".mdx",
                )
            ):

                output = API_DIR / file_path

                download_file(
                    file_path,
                    output
                )

                api_count += 1

        # =====================================
        # 4. PDF FILES
        # =====================================

        elif lower.endswith(".pdf"):

            output = PDF_DIR / file_path

            download_file(
                file_path,
                output
            )

            pdf_count += 1

    # =====================================
    # SUMMARY
    # =====================================

    print("\n==============================")
    print("Download complete!")
    print("==============================")
    print(f"Documentation : {docs_count}")
    print(f"Examples      : {examples_count}")
    print(f"API material  : {api_count}")
    print(f"PDFs          : {pdf_count}")
    print("==============================")
    print(f"Saved to: {BASE_DIR.resolve()}")


if __name__ == "__main__":
    main()