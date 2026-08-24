# rag/loaders.py

from pathlib import Path
from app.utils.logger import logger

from llama_index.readers.file import (
    FlatReader,
    HTMLTagReader,
    MarkdownReader,
    PyMuPDFReader,
)


SUPPORTED_EXTENSIONS = {
    ".md": "markdown",
    ".mdx": "markdown",
    ".html": "html",
    ".py": "python",
    ".txt": "text",
    ".pdf": "pdf",
}


def enrich_metadata(documents):
    for document in documents:

        file_path = document.metadata.get("file_path")
        if not file_path:
            continue

        path = Path(file_path)
        parts = path.parts

        try:
            data_index = parts.index("data")
            source = parts[data_index + 1]
        except (ValueError, IndexError):
            source = "unknown"

        source_type = "unknown"

        for directory in ["docs", "examples", "api", "pdf"]:
            if directory in parts:
                source_type = directory
                break

        document.metadata.update({
            "source": source,
            "source_type": source_type,
            "file_extension": path.suffix.lower(),
        })

    return documents


def load_file(file_path: Path):

    extension = file_path.suffix.lower()

    if extension in {".md", ".mdx"}:
        reader = MarkdownReader()

    elif extension == ".html":
        reader = HTMLTagReader()

    elif extension in {".py", ".txt"}:
        reader = FlatReader()

    elif extension == ".pdf":
        reader = PyMuPDFReader()

    else:
        return []

    # return reader.load_data(file_path)
    documents = reader.load_data(file_path)

    for document in documents:
        document.metadata["file_path"] = str(file_path)

    return documents


def load_documents(data_dir: str = "data"):

    data_path = Path(data_dir)

    if not data_path.exists():
        raise FileNotFoundError(
            f"Data directory not found: {data_path}"
        )

    documents = []

    for extension, file_type in SUPPORTED_EXTENSIONS.items():

        files = list(data_path.rglob(f"*{extension}"))

        # Remove non-English FastAPI translations
        filtered_files = []

        for file_path in files:

            parts = file_path.parts

            if "fastapi" in parts:
                try:
                    fastapi_index = parts.index("fastapi")

                    # Only filter language directories inside fastapi/docs/
                    if (
                        len(parts) > fastapi_index + 2
                        and parts[fastapi_index + 1] == "docs"
                    ):
                        language = parts[fastapi_index + 2]

                        # Keep only English FastAPI docs
                        if language != "en":
                            continue

                except (ValueError, IndexError):
                    pass

            filtered_files.append(file_path)

        if not filtered_files:
            continue
        
        logger.info(
            f"Loading {len(filtered_files)} "
            f"{file_type} files..."
        )

        for file_path in filtered_files:

            try:
                loaded_documents = load_file(file_path)
                documents.extend(loaded_documents)

            except Exception as e:
                logger.info(
                    f"Failed to load {file_path}: {e}"
                )

    documents = enrich_metadata(documents)

    logger.info(
        f"\nTotal documents loaded: "
        f"{len(documents)}"
    )

    return documents


if __name__ == "__main__":
    documents = load_documents()

    from collections import Counter

    print("\nFastAPI sources:")
    print(Counter(
        doc.metadata.get("source")
        for doc in documents
        if doc.metadata.get("source") == "fastapi"
    ))

    print("\nNon-English FastAPI files:")
    for doc in documents:
        path = doc.metadata.get("file_path", "")
        if "/fastapi/docs/" in path and "/en/" not in path:
            print(path)

    # if documents:
    #     logger.info("\nExample document:")
    #     logger.info("------------------")
    #     logger.info(documents[0].text[:500])

    #     logger.info("\nMetadata:")
    #     logger.info(documents[0].metadata)