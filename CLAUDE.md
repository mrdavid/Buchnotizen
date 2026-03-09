# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal book reading log/tracker. Books are stored in `log.xml`, and `generate_Readme.py` parses the XML to produce `README.md` and three chart images.

## Regenerating the README

```bash
python generate_Readme.py
```

This writes `README.md` directly (no stdout redirect needed) and regenerates `book_recorded.png`, `book_read.png`, and `book_gaps.png`.

Dependencies are listed in `requirements.txt` (`pandas`, `matplotlib`, `textual`). See Environment Setup below.

## Data Model

All book data lives in `log.xml`. Each `<book>` entry supports these fields:
- **Required:** `<author>`, `<title>`, `<finished>` (date format: `YYYY.MM.DD`), `<tag>`
- **Optional:** `<started>`, `<bought>`, `<isbn>`, `<pages>`, `<notes>`, `<amazon>`, `<review>`

The `<tag>` field categorizes books (Fiction, Nonfiction, Business, Physics, etc.). Some books have a linked notes file in `Notizen/`.

## Architecture

```
log.xml  →  generate_Readme.py  →  README.md + book_recorded.png + book_read.png + book_gaps.png
```

The Python script:
1. Parses XML with `xml.etree.ElementTree`
2. Builds a pandas DataFrame for statistics and charts
3. Writes `README.md` directly via `open()`

### Charts
- `book_recorded.png` — bar chart of books recorded per year (with dashed line at 12)
- `book_read.png` — 5-month rolling average of books read per month
- `book_gaps.png` — normalized histogram (%) of days between consecutive finished books

## Book TUI (`book_tui.py`)

Terminal UI for browsing and editing `log.xml`, built with [Textual](https://textual.textualize.io/).

```bash
python book_tui.py
```

### Key bindings (list view)
| Key | Action |
|-----|--------|
| `n` | Add new book |
| `e` / `Enter` | Edit selected book |
| `r` | Regenerate README and charts |
| `q` | Quit |

### Key bindings (edit/new form)
| Key | Action |
|-----|--------|
| `Ctrl+S` | Save |
| `Ctrl+L` | Auto-fill ISBN and pages from Open Library |
| `Escape` | Discard |
| `Up` / `Down` | Move between fields |
| `F2` (date fields) | Open date picker |

## Environment Setup

The project uses a `.venv` virtual environment managed by [`uv`](https://github.com/astral-sh/uv).

**First-time setup:**
```bash
bash setup.sh
```
This creates `.venv` and installs all dependencies from `requirements.txt`.

**Activating the environment:**
```bash
source activate.sh
```

## Workflow

New books are added via `book_tui.py` (preferred) or directly to `log.xml`. Commit message should match the book title. After adding a book, run `python generate_Readme.py` to regenerate `README.md` and the charts (or press `r` in the TUI).
