"""Module for the WindowSwitcher class.

You don't need to import from this module. You can simply do:
`from textual_window import WindowSwitcher`"""

# ~ Type Checking (Pyright and MyPy) - Strict Mode
# ~ Linting - Ruff
# ~ Formatting - Black - max 110 characters / line

# Python imports
from __future__ import annotations
from typing import Any

# Textual imports
from textual import on
from textual import events
from textual.app import ComposeResult
from textual.visual import VisualType
from textual.containers import Horizontal, Container
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.binding import Binding

# Local imports
from textual_window.manager import window_manager
from textual_window.button_bases import ButtonStatic

__all__ = [
    "WindowSwitcher",
]


class WindowSwitcher(Widget):

    def __init__(self, cycle_key: str = "f1", **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.display = False
        self.cycle_key = cycle_key

    def show(self) -> None:
        """Show the window switcher."""
        self.app.push_screen(WindowSwitcherScreen(self.cycle_key))


class WindowSwitcherButton(ButtonStatic):
    can_focus = True

    def __init__(self, name: str, content: VisualType = "") -> None:
        super().__init__(name=name, content=content)


class WindowSwitcherScreen(ModalScreen[None]):

    CSS = """
    WindowSwitcherScreen { align: center middle; }
    WindowSwitcher { background: $background 30%; }                   
    #menu_container {
        background: $surface;
        width: auto; height: auto;
        min-width: 15; min-height: 6;
        border: outer $panel;
        border-subtitle-color: $secondary;
    }
    #menu_inner { width: auto; height: auto; }
    WindowSwitcherButton {
        width: auto; height: 4;
        content-align: center middle;
        border: round $panel;
        &:focus { border: round $primary; }
        &:hover { border: round $secondary; }
        # &.pressed { background: $panel-lighten-2; }        #! use me!
    }
    .label { width: auto; height: 1; content-align: center middle; }    
    """

    manager = window_manager

    BINDINGS = [
        Binding("escape", "cancel"),
        Binding("enter", "confirm"),
        Binding("left", "cycle_previous"),
        Binding("right", "cycle_next"),
    ]

    def __init__(self, cycle_key: str) -> None:
        super().__init__()
        self.cycle_key = cycle_key
        self.windows = self.manager.get_windows_as_dict()

    def compose(self) -> ComposeResult:

        with Container(id="menu_container"):
            with Horizontal(id="menu_inner"):
                if self.manager.recent_window_focus_order:
                    for window in self.manager.recent_window_focus_order:
                        yield WindowSwitcherButton(name=window.id, content=window.name)
                        # using name instead of id above, because otherwise it would be
                        # trying to re-use a unique id, and cause a bug.
                        # The ol' name/id switcheroo.
                yield WindowSwitcherButton(name="desktop", content="Desktop")

    def on_mount(self) -> None:

        self.query_one("#menu_container").border_subtitle = f"Cycle: {self.cycle_key}"

    def on_mouse_up(self) -> None:

        self.dismiss(None)

    @on(WindowSwitcherButton.Pressed)
    def switcher_button_pressed(self, event: WindowSwitcherButton.Pressed) -> None:
        """Handles clicking on a window button."""

        window_id = event.button.name
        if window_id in self.windows:
            window = self.windows[window_id]
            window.open_window()
        elif window_id == "desktop":
            self.manager.minimize_all_windows()
        else:
            raise ValueError(f"Window {window_id} not found in window manager.")

    ##############################
    # ~ Actions / Key handling ~ #
    ##############################

    def on_key(self, event: events.Key) -> None:
        # This is what allows it to use a dynamic keybinding.
        # The key is passed in as a string in the constructor.

        if event.key == self.cycle_key:
            self.action_cycle_next()
        elif event.key == f"shift+{self.cycle_key}":
            self.action_cycle_previous()

    def action_confirm(self) -> None:

        buttons = self.query(WindowSwitcherButton)
        for button in buttons:
            if button.has_focus:
                window_id = button.name
                if window_id in self.windows:
                    window = self.windows[window_id]
                    if window == self.manager.last_focused_window and window.display:
                        window.minimize()
                    else:
                        window.open_window()
                        window.focus()
                    break
                elif window_id == "desktop":
                    self.manager.minimize_all_windows()
                else:
                    raise ValueError(f"Window {window_id} not found in window manager.")

        self.dismiss(None)

    def action_cycle_next(self) -> None:
        self.app.action_focus_next()

    def action_cycle_previous(self) -> None:
        self.app.action_focus_previous()

    def action_cancel(self) -> None:
        """Dismiss the screen without taking any action."""
        self.dismiss(None)
