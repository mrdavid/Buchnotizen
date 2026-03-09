"""
openlibrary.py — Open Library API connector for looking up book metadata.
"""

import json as _json
from difflib import SequenceMatcher
from urllib.parse import urlencode
from urllib.request import urlopen


def _search(title: str, author: str, timeout: int) -> list[dict]:
    """Run a single Open Library search and return the docs list."""
    params = urlencode({
        "title": title, "author": author,
        "fields": "title,key,isbn,number_of_pages_median", "limit": "5",
    })
    url = f"https://openlibrary.org/search.json?{params}"
    try:
        with urlopen(url, timeout=timeout) as resp:
            data = _json.loads(resp.read())
    except Exception:
        return []
    return data.get("docs", [])


def _pick_best(docs: list[dict], title: str) -> dict[str, str]:
    """Select the best-matching doc and extract isbn, pages, openlibrary."""
    title_lower = title.lower()
    doc = max(docs, key=lambda d: SequenceMatcher(
        None, title_lower, d.get("title", "").lower()
    ).ratio())
    result = {}
    # ISBN: prefer ISBN-13
    isbns = doc.get("isbn", [])
    for isbn in isbns:
        if len(isbn) == 13 and isbn.startswith(("978", "979")):
            result["isbn"] = isbn
            break
    if "isbn" not in result and isbns:
        result["isbn"] = isbns[0]
    # Pages
    pages = doc.get("number_of_pages_median")
    if pages:
        result["pages"] = str(pages)
    # Open Library link
    key = doc.get("key")
    if key:
        result["openlibrary"] = f"https://openlibrary.org{key}"
    return result


def fetch_book_data(title: str, author: str, timeout: int = 5) -> dict[str, str]:
    """Look up ISBN, page count, and Open Library link via Search API.

    If no results are found and the title contains '(', retries with the
    title truncated at the first open bracket (e.g. "Fulgrim (Horus Heresy 5)"
    becomes "Fulgrim").

    Returns a dict with optional keys: isbn, pages, openlibrary.
    """
    docs = _search(title, author, timeout)
    if docs:
        return _pick_best(docs, title)

    # Retry with title truncated at first '('
    if "(" in title:
        short_title = title[:title.index("(")].strip()
        if short_title:
            docs = _search(short_title, author, timeout)
            if docs:
                return _pick_best(docs, short_title)

    return {}
