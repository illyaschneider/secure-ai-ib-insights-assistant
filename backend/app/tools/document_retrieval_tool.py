from pathlib import Path
from pypdf import PdfReader

CURRENT_PATH = Path(__file__).resolve()
ROOT_PATH = CURRENT_PATH.parents[3]
DOCS_PATH = ROOT_PATH / "data" / "docs"
APPROVED_DOCUMENT_PATHS = [
    DOCS_PATH / "data_story_map.md",
    DOCS_PATH / "technology_2026q1_market_update.pdf",
]

MAX_MATCHES = 5
SNIPPET_RADIUS = 100


def _normalize_search_text(text: str) -> str:
    return " ".join(text.casefold().split())


def _load_markdown_document(path: Path) -> str:
    with path.open(mode="r", encoding="utf-8") as file:
        return file.read()


def _load_pdf_pages(path: Path) -> list[dict]:
    reader = PdfReader(path)
    pages = []
    for page_number, page in enumerate(reader.pages, start=1):
        page_text = " ".join((page.extract_text() or "").split())
        pages.append(
            {
                "source": path.name,
                "page": page_number,
                "text": page_text,
            }
        )
    return pages


def _load_approved_documents():
    loaded_documents = []
    for path in APPROVED_DOCUMENT_PATHS:
        if not path.exists():
            continue

        if path.suffix.casefold() == ".md":
            loaded_documents.append(
                {
                    "source": path.name,
                    "page": None,
                    "text": _load_markdown_document(path),
                }
            )
        elif path.suffix.casefold() == ".pdf":
            loaded_documents.extend(_load_pdf_pages(path))

    if not loaded_documents:
        raise ValueError("No approved documents are available")

    return loaded_documents


def _build_snippet(
    text: str,
    match_position: int,
    query_length: int,
) -> tuple[str, int]:
    # returning excerpt sized by 100 symbols to each side
    start = max(match_position - SNIPPET_RADIUS, 0)
    end = min(match_position + query_length + SNIPPET_RADIUS, len(text))
    return ("..." + text[start:end] + "..."), end


def retrieve_document_evidence(query: str) -> dict:
    query = str(query).strip()
    if not query:
        raise ValueError("Enter a valid search query")

    query_normalized = _normalize_search_text(query)
    matches = []
    loaded_documents = _load_approved_documents()

    for document in loaded_documents:
        document_normalized = _normalize_search_text(document["text"])
        search_position = 0
        # stopping the search after 5 finds
        while len(matches) < MAX_MATCHES:
            match_position = document_normalized.find(query_normalized, search_position)
            if match_position == -1:
                break
            snippet, snippet_end = _build_snippet(document_normalized, match_position, len(query_normalized))
            matches.append(
                {
                    "source": document["source"],
                    "page": document["page"],
                    "snippet": snippet,
                }
            )
            # skip overlapping or nearby excerpts
            search_position = snippet_end

    if not matches:
        raise ValueError(f"{query} not found in approved documents")

    sources = sorted({match["source"] for match in matches})

    query_dict = {
        "query": query,
        "sources": sources,
        "match_count": len(matches),
        "matches": matches,
        "limitations": [
            "Keyword search only; no semantic retrieval yet.",
            "PDF extraction depends on machine-readable text; scanned PDFs are not supported yet.",
        ]
    }
    return query_dict

def main():
    query = "sponsor-backed software"
    document = retrieve_document_evidence(query)
    print(document)

if __name__ == "__main__":
    main()
