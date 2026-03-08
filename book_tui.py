#!/usr/bin/env python3
"""
book_tui.py — Terminal UI for browsing and editing log.xml
Requires: pip install textual
"""

import calendar as _cal
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.events import Key
from textual.screen import ModalScreen, Screen
from textual.widgets import DataTable, Input, Label, Button, Header, Static
from textual.containers import Vertical, Horizontal, ScrollableContainer

XML_PATH = Path(__file__).parent / "log.xml"

FIELDS = ["author", "title", "finished", "tag", "started", "isbn", "notes", "review"]
DATE_FIELDS = {"finished", "started"}


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
        if el is not None:
            book.remove(el)


# ---------------------------------------------------------------------------
# Date helpers
# ---------------------------------------------------------------------------

def parse_book_date(value: str) -> date | None:
    """Parse YYYY.MM.DD → date, or None on failure."""
    try:
        parts = value.strip().split(".")
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except Exception:
        return None


def format_book_date(d: date) -> str:
    """Format date → YYYY.MM.DD."""
    return d.strftime("%Y.%m.%d")


# ---------------------------------------------------------------------------
# CalendarModal
# ---------------------------------------------------------------------------

class CalendarModal(ModalScreen):
    """
    A modal month-calendar date picker.

    Navigate: ←→ day, ↑↓ week, PgUp/PgDn month.
    Confirm with Enter, cancel with Esc.
    Dismisses with the selected date, or None on cancel.
    """

    BINDINGS = [
        Binding("escape",   "cancel",      "Cancel",     show=False),
        Binding("enter",    "confirm",     "Select",     show=False),
        Binding("left",     "prev_day",    "Prev day",   show=False),
        Binding("right",    "next_day",    "Next day",   show=False),
        Binding("up",       "prev_week",   "Prev week",  show=False),
        Binding("down",     "next_week",   "Next week",  show=False),
        Binding("pageup",   "prev_month",  "Prev month", show=False),
        Binding("pagedown", "next_month",  "Next month", show=False),
    ]

    DEFAULT_CSS = """
    CalendarModal {
        align: center middle;
    }
    #cal-container {
        width: 28;
        height: 18;
        border: round $accent;
        background: $surface;
        padding: 1 2;
    }
    #cal-month {
        height: 1;
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    #cal-grid {
        height: 8;
        text-align: center;
    }
    #cal-help {
        height: 2;
        color: $text-muted;
        text-align: center;
        margin-top: 1;
    }
    """

    def __init__(self, initial: date | None = None):
        super().__init__()
        self._selected = initial or date.today()

    def compose(self) -> ComposeResult:
        with Vertical(id="cal-container"):
            yield Static("", id="cal-month")
            yield Static("", id="cal-grid")
            yield Static(
                "←→ day  ↑↓ week  PgUp/Dn month\n"
                "Enter confirm  Esc cancel",
                id="cal-help",
            )

    def on_mount(self) -> None:
        self._redraw()

    def _redraw(self) -> None:
        sel = self._selected
        today = date.today()

        self.query_one("#cal-month", Static).update(sel.strftime("%B %Y"))

        # Build 7-column grid (Mon … Sun)
        lines = ["Mo Tu We Th Fr Sa Su"]
        first_weekday = sel.replace(day=1).weekday()   # 0 = Mon
        num_days = _cal.monthrange(sel.year, sel.month)[1]

        row: list[str] = ["  "] * first_weekday
        for day in range(1, num_days + 1):
            d = date(sel.year, sel.month, day)
            cell = f"{day:2d}"
            if d == sel:
                cell = f"[bold reverse]{cell}[/bold reverse]"
            elif d == today:
                cell = f"[yellow]{cell}[/yellow]"
            row.append(cell)
            if len(row) == 7:
                lines.append(" ".join(row))
                row = []
        if row:
            row += ["  "] * (7 - len(row))
            lines.append(" ".join(row))

        self.query_one("#cal-grid", Static).update("\n".join(lines))

    # -- navigation actions --------------------------------------------------

    def action_prev_day(self) -> None:
        self._selected -= timedelta(days=1)
        self._redraw()

    def action_next_day(self) -> None:
        self._selected += timedelta(days=1)
        self._redraw()

    def action_prev_week(self) -> None:
        self._selected -= timedelta(weeks=1)
        self._redraw()

    def action_next_week(self) -> None:
        self._selected += timedelta(weeks=1)
        self._redraw()

    def action_prev_month(self) -> None:
        sel = self._selected
        new_year = sel.year - 1 if sel.month == 1 else sel.year
        new_month = 12 if sel.month == 1 else sel.month - 1
        max_day = _cal.monthrange(new_year, new_month)[1]
        self._selected = date(new_year, new_month, min(sel.day, max_day))
        self._redraw()

    def action_next_month(self) -> None:
        sel = self._selected
        new_year = sel.year + 1 if sel.month == 12 else sel.year
        new_month = 1 if sel.month == 12 else sel.month + 1
        max_day = _cal.monthrange(new_year, new_month)[1]
        self._selected = date(new_year, new_month, min(sel.day, max_day))
        self._redraw()

    def action_confirm(self) -> None:
        self.dismiss(self._selected)

    def action_cancel(self) -> None:
        self.dismiss(None)


# ---------------------------------------------------------------------------
# DateField  (Input + calendar-picker button)
# ---------------------------------------------------------------------------

class DateField(Horizontal):
    """
    A labelled date input with an attached calendar picker button.

    The inner Input uses the ID supplied as `input_id` so that BookForm's
    get_values() can query it by #input_{field} just like plain Inputs.
    Press Enter in the input or click 📅 to open the calendar modal.
    """

    DEFAULT_CSS = """
    DateField {
        height: auto;
    }
    DateField Button {
        width: 7;
        min-width: 7;
        margin-left: 1;
    }
    """

    def __init__(self, value: str, input_id: str):
        super().__init__()
        self._initial_value = value
        self._input_id = input_id

    def compose(self) -> ComposeResult:
        yield Input(
            value=self._initial_value,
            id=self._input_id,
            placeholder="YYYY.MM.DD  (F2 = calendar)",
        )
        yield Button("[Cal]", id=f"_cal_btn_{self._input_id}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == f"_cal_btn_{self._input_id}":
            self._open_picker()
            event.stop()

    def on_key(self, event: Key) -> None:
        """Open calendar on F2 while focus is anywhere inside the DateField."""
        if event.key == "f2":
            self._open_picker()
            event.stop()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Open calendar when Enter is pressed inside the date input."""
        self._open_picker()
        event.stop()

    def _open_picker(self) -> None:
        current = self.query_one(f"#{self._input_id}", Input).value
        self.app.push_screen(CalendarModal(parse_book_date(current)), self._on_picked)

    def _on_picked(self, result: date | None) -> None:
        if result is not None:
            self.query_one(f"#{self._input_id}", Input).value = format_book_date(result)


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
            if field in DATE_FIELDS:
                yield DateField(
                    value=self._values.get(field, ""),
                    input_id=f"input_{field}",
                )
            else:
                yield Input(
                    value=self._values.get(field, ""),
                    id=f"input_{field}",
                    placeholder=field,
                )

    def on_key(self, event: Key) -> None:
        if event.key not in ("up", "down"):
            return
        inputs = list(self.query(Input))
        focused = self.app.focused
        if focused not in inputs:
            return
        idx = inputs.index(focused)
        if event.key == "up" and idx > 0:
            inputs[idx - 1].focus()
        elif event.key == "down" and idx < len(inputs) - 1:
            inputs[idx + 1].focus()
        event.stop()

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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self.action_save()
        elif event.button.id == "btn-discard":
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

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self.action_save()
        elif event.button.id == "btn-discard":
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
            return f"Jump to row: {self._jump_buffer}  [[Enter]] confirm  [[Esc]] cancel"
        return "  [[q]] Quit    [[n]] New book    [[e]] / Enter Edit    [[0-9]] Jump to row"

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
