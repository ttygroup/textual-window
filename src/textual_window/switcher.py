"""Module for the WindowSwitcher class.

You don't need to import from this module. You can simply do:
`from textual_window import WindowSwitcher`"""

# ~ Type Checking (Pyright and MyPy) - Strict Mode
# ~ Linting - Ruff
# ~ Formatting - Black - max 110 characters / line

from __future__ import annotations

# from typing import Any  # , Callable, Optional

from textual import on
from textual import events

# from textual.message import Message
from textual.app import ComposeResult
from textual.visual import VisualType
from textual.containers import Horizontal, Container
from textual.screen import ModalScreen
from textual.widget import Widget

# from textual.widgets import Static
from textual.binding import Binding

# from textual.geometry import Offset

from textual_window.manager import window_manager
from textual_window.button_bases import ButtonStatic


class WindowSwitcher(Widget):

    def __init__(self) -> None:
        super().__init__()
        self.display = False

    def show(self) -> None:
        """Show the window switcher."""
        self.app.push_screen(WindowSwitcherScreen())


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
        border: outer $panel;
        border-subtitle-color: $secondary;
    }
    #menu_inner { width: auto; height: auto; }
    WindowSwitcherButton {
        width: auto; height: 4; content-align: center middle;
        border: round $panel;
        &:focus { border: round $primary; }
        &:hover { border: round $secondary; }
        # &.pressed { background: $panel-lighten-2; }        #! use me!
    }
    .label { width: auto; height: 1; content-align: center middle; }    
    """

    BINDINGS = [
        Binding("escape", "cancel"),
        Binding("enter", "confirm"),
        Binding("left", "cycle_previous"),
        Binding("right", "cycle_next"),
    ]

    def __init__(self, cycle_key: str = "f1") -> None:
        super().__init__()
        self.cycle_key = cycle_key
        self.windows = window_manager.get_windows_as_dict()

    def compose(self) -> ComposeResult:

        with Container(id="menu_container"):
            with Horizontal(id="menu_inner"):
                if window_manager.recent_focus_order:
                    for window in window_manager.recent_focus_order:
                        yield WindowSwitcherButton(name=window.name, content=window.name)
                else:
                    raise RuntimeError("Windows not loaded into recent_focus_order.")

    def on_mount(self) -> None:

        self.query_one("#menu_container").border_subtitle = f"Cycle: {self.cycle_key}"

    def on_mouse_up(self) -> None:

        self.dismiss(None)

    @on(WindowSwitcherButton.Pressed)
    def switcher_button_pressed(self, event: WindowSwitcherButton.Pressed) -> None:

        window_name = event.button.name
        if window_name in self.windows:
            window = self.windows[window_name]
            window.open_window()
        else:
            raise ValueError(f"Window {window_name} not found in window manager.")

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
                window_name = button.name
                if window_name in self.windows:
                    window = self.windows[window_name]
                    window.open_window()
                    window.bring_forward()
                    window.focus()
                    break
                else:
                    raise ValueError(f"Window {window_name} not found in window manager.")

        self.dismiss(None)

    def action_cycle_next(self) -> None:
        self.app.action_focus_next()

    def action_cycle_previous(self) -> None:
        self.app.action_focus_previous()
