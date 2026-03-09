#!/usr/bin/env python3
"""
backfill.py — Fill in missing metadata for books in log.xml.

Currently backfills: isbn, pages, openlibrary (via Open Library API).
Add new backfill steps here as needed.

Usage:
    python backfill.py            # backfill all books with missing data
    python backfill.py --dry-run  # show what would be changed without saving
"""

import argparse
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from openlibrary import fetch_book_data

XML_PATH = Path(__file__).parent / "log.xml"

OPENLIBRARY_FIELDS = ("isbn", "pages", "openlibrary")


def get_field(book: ET.Element, field: str) -> str:
    el = book.find(field)
    return el.text or "" if el is not None else ""


def set_field(book: ET.Element, field: str, value: str) -> None:
    value = value.strip()
    el = book.find(field)
    if value:
        if el is None:
            el = ET.SubElement(book, field)
        el.text = value


def backfill_openlibrary(books: list[ET.Element], dry_run: bool) -> int:
    """Fill in missing isbn, pages, and openlibrary fields from Open Library."""
    updated = 0
    for i, book in enumerate(books, 1):
        title = get_field(book, "title")
        author = get_field(book, "author")
        if not title:
            continue

        missing = [f for f in OPENLIBRARY_FIELDS if not get_field(book, f)]
        if not missing:
            continue

        print(f"  [{i}/{len(books)}] {title} by {author} — looking up {', '.join(missing)}…", end=" ", flush=True)

        # Be polite to the API
        time.sleep(0.5)
        data = fetch_book_data(title, author)

        if not data:
            print("no results")
            continue

        filled = []
        for field in missing:
            if field in data:
                if not dry_run:
                    set_field(book, field, data[field])
                filled.append(f"{field}={data[field]}")

        if filled:
            updated += 1
            print(", ".join(filled))
        else:
            print("nothing new found")

    return updated


def main() -> None:
    parser = argparse.ArgumentParser(description="Backfill missing book metadata in log.xml")
    parser.add_argument("--dry-run", action="store_true", help="Show what would change without saving")
    args = parser.parse_args()

    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    books = root.findall("book")

    print(f"Found {len(books)} books in log.xml\n")

    # --- Open Library backfill ---
    need_ol = sum(1 for b in books if any(not get_field(b, f) for f in OPENLIBRARY_FIELDS))
    print(f"Open Library: {need_ol} books missing isbn/pages/openlibrary")
    if need_ol:
        updated = backfill_openlibrary(books, args.dry_run)
        print(f"\n  → {updated} books {'would be ' if args.dry_run else ''}updated\n")
    else:
        print("  → nothing to do\n")

    # --- Add future backfill steps here ---

    if not args.dry_run and need_ol:
        ET.indent(tree, space="  ")
        tree.write(XML_PATH, encoding="UTF-8", xml_declaration=True)
        print("Saved log.xml")
    elif args.dry_run:
        print("Dry run — no changes saved")


if __name__ == "__main__":
    main()
