#!/usr/bin/env python3
"""
book_tui.py — Terminal UI for browsing and editing log.xml
Requires: pip install textual
"""

import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import date

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.events import Key
from textual.screen import Screen
from textual.widgets import DataTable, Input, Label, Button, Footer, Header, Static
from textual.containers import Vertical, Horizontal, ScrollableContainer

XML_PATH = Path(__file__).parent / "log.xml"

FIELDS = ["author", "title", "finished", "tag", "started", "isbn", "notes", "review"]


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------

def load_xml() -> tuple[ET.ElementTree, ET.Element, list[ET.Element]]:
    tree = ET.parse(XML_PATH)
    root = tree.getroot()
    books = root.findall("book")
    return tree, root, books


def save_xml(tree: ET.ElementTree) -> None:
    ET.indent(tree, space="  ")
    tree.write(XML_PATH, encoding="UTF-8", xml_declaration=True)


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
    else:
        # Remove element if empty value provided
        if el is not None:
            book.remove(el)


# ---------------------------------------------------------------------------
# Book form (shared by Edit and New screens)
# ---------------------------------------------------------------------------

class BookForm(Vertical):
    """A set of labelled input fields for a book entry."""

    DEFAULT_CSS = """
    BookForm {
        padding: 1 2;
    }
    BookForm Label {
        margin-top: 1;
        color: $text-muted;
    }
    BookForm Input {
        margin-bottom: 0;
    }
    """

    def __init__(self, values: dict[str, str]):
        super().__init__()
        self._values = values

    def compose(self) -> ComposeResult:
        for field in FIELDS:
            yield Label(field.capitalize())
            yield Input(value=self._values.get(field, ""), id=f"input_{field}", placeholder=field)

    def get_values(self) -> dict[str, str]:
        return {
            field: self.query_one(f"#input_{field}", Input).value
            for field in FIELDS
        }


# ---------------------------------------------------------------------------
# EditBookScreen
# ---------------------------------------------------------------------------

class EditBookScreen(Screen):
    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("escape", "discard", "Discard"),
    ]

    DEFAULT_CSS = """
    EditBookScreen {
        align: center middle;
    }
    #edit-container {
        width: 70;
        height: auto;
        max-height: 90vh;
        border: round $accent;
        background: $surface;
    }
    #edit-title {
        text-align: center;
        padding: 1;
        background: $accent;
        color: $text;
    }
    #button-row {
        height: 3;
        align: center middle;
        margin: 1 0;
    }
    """

    def __init__(self, book_index: int):
        super().__init__()
        self._book_index = book_index

    def compose(self) -> ComposeResult:
        _, _, books = load_xml()
        book = books[self._book_index]
        values = {field: get_field(book, field) for field in FIELDS}

        with Vertical(id="edit-container"):
            yield Label(f"Edit book #{self._book_index + 1}", id="edit-title")
            with ScrollableContainer():
                yield BookForm(values)
            with Horizontal(id="button-row"):
                yield Button("Save (Ctrl+S)", variant="primary", id="btn-save")
                yield Button("Discard (Esc)", id="btn-discard")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self.action_save()
        else:
            self.action_discard()

    def action_save(self) -> None:
        form = self.query_one(BookForm)
        values = form.get_values()
        tree, root, books = load_xml()
        book = books[self._book_index]
        for field, value in values.items():
            set_field(book, field, value)
        save_xml(tree)
        self.app.pop_screen()

    def action_discard(self) -> None:
        self.app.pop_screen()


# ---------------------------------------------------------------------------
# NewBookScreen
# ---------------------------------------------------------------------------

class NewBookScreen(Screen):
    BINDINGS = [
        Binding("ctrl+s", "save", "Save"),
        Binding("escape", "discard", "Discard"),
    ]

    DEFAULT_CSS = """
    NewBookScreen {
        align: center middle;
    }
    #new-container {
        width: 70;
        height: auto;
        max-height: 90vh;
        border: round $success;
        background: $surface;
    }
    #new-title {
        text-align: center;
        padding: 1;
        background: $success;
        color: $text;
    }
    #button-row {
        height: 3;
        align: center middle;
        margin: 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        today = date.today().strftime("%Y.%m.%d")
        values = {"finished": today}

        with Vertical(id="new-container"):
            yield Label("Add new book", id="new-title")
            with ScrollableContainer():
                yield BookForm(values)
            with Horizontal(id="button-row"):
                yield Button("Save (Ctrl+S)", variant="success", id="btn-save")
                yield Button("Discard (Esc)", id="btn-discard")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self.action_save()
        else:
            self.action_discard()

    def action_save(self) -> None:
        form = self.query_one(BookForm)
        values = form.get_values()

        tree, root, books = load_xml()
        new_book = ET.Element("book")
        for field in FIELDS:
            if values.get(field, "").strip():
                el = ET.SubElement(new_book, field)
                el.text = values[field].strip()

        # Insert as first child
        root.insert(0, new_book)
        save_xml(tree)
        self.app.pop_screen()

    def action_discard(self) -> None:
        self.app.pop_screen()


# ---------------------------------------------------------------------------
# BookListScreen
# ---------------------------------------------------------------------------

class BookListScreen(Screen):
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("n", "new_book", "New book"),
        Binding("e", "edit_book", "Edit"),
        Binding("enter", "edit_book", "Edit", show=False),
    ]

    DEFAULT_CSS = """
    BookListScreen {
        layout: vertical;
    }
    DataTable {
        height: 1fr;
    }
    #status-bar {
        height: 1;
        padding: 0 1;
        background: $panel;
        color: $text-muted;
        dock: bottom;
    }
    #status-bar.jumping {
        color: $warning;
    }
    """

    def __init__(self):
        super().__init__()
        self._jump_buffer: str = ""

    def compose(self) -> ComposeResult:
        yield Header()
        yield DataTable(id="book-table", zebra_stripes=True, cursor_type="row")
        yield Static(self._status_text(), id="status-bar")

    def _status_text(self) -> str:
        if self._jump_buffer:
            return f"Jump to row: {self._jump_buffer}  [Enter] confirm  [Esc] cancel"
        return "  [q] Quit    [n] New book    [e / Enter] Edit    [0-9] Jump to row"

    def on_mount(self) -> None:
        self.call_after_refresh(self._populate_table)

    def on_key(self, event: Key) -> None:
        if event.character and event.character.isdigit():
            self._jump_buffer += event.character
            self._update_jump_label()
            event.prevent_default()
        elif self._jump_buffer:
            event.prevent_default()
            if event.key == "enter":
                n = int(self._jump_buffer)
                table = self.query_one(DataTable)
                table.move_cursor(row=max(0, min(n - 1, table.row_count - 1)))
            self._jump_buffer = ""
            self._update_jump_label()

    def _update_jump_label(self) -> None:
        bar = self.query_one("#status-bar", Static)
        bar.update(self._status_text())
        if self._jump_buffer:
            bar.add_class("jumping")
        else:
            bar.remove_class("jumping")

    def _populate_table(self, restore_row: int = 0) -> None:
        table = self.query_one(DataTable)
        table.clear(columns=True)
        table.add_columns("#", "Title", "Author", "Finished", "Tag")

        _, _, books = load_xml()
        for i, book in enumerate(books, 1):
            title = get_field(book, "title")
            author = get_field(book, "author")
            finished = get_field(book, "finished")
            tag = get_field(book, "tag")
            table.add_row(str(i), title, author, finished, tag)

        if table.row_count > 0:
            table.move_cursor(row=min(restore_row, table.row_count - 1))
        table.refresh()

    def on_screen_resume(self) -> None:
        """Refresh table when returning from edit/new screens."""
        cursor_row = self.query_one(DataTable).cursor_row
        self._populate_table(restore_row=cursor_row)

    def action_edit_book(self) -> None:
        table = self.query_one(DataTable)
        if table.row_count == 0:
            return
        row_index = table.cursor_row
        self.app.push_screen(EditBookScreen(row_index))

    def action_new_book(self) -> None:
        self.app.push_screen(NewBookScreen())

    def action_quit(self) -> None:
        self.app.exit()


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

class BuchnoizenApp(App):
    TITLE = "Buchnotizen"
    SUB_TITLE = "Book log editor"

    def on_mount(self) -> None:
        self.push_screen(BookListScreen())


if __name__ == "__main__":
    BuchnoizenApp().run()
