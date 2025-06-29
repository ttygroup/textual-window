"""windowcomponents.py"""

# ~ Type Checking (Pyright and MyPy) - Strict Mode
# ~ Linting - Ruff
# ~ Formatting - Black - max 110 characters / line

# Python imports
from __future__ import annotations
from typing import Any, TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from textual.visual import VisualType
    from textual.app import ComposeResult
    from textual_window.window import Window

# Textual and Rich imports
import textual.events as events
from textual.widget import Widget
from textual import on, work
from textual.geometry import clamp
from textual.containers import Horizontal, Container
from textual.screen import ModalScreen
from textual.geometry import Offset

# Local imports
from textual_window.button_bases import ButtonStatic, NoSelectStatic


BUTTON_SYMBOLS: dict[str, str] = {
    "close": "X",
    "maximize": "☐",
    "restore": "❐",
    "minimize": "—",
    "hamburger": "☰",
    "resizer": "◢",
}


class HamburgerMenu(ModalScreen[None]):

    CSS = """
    HamburgerMenu {
        background: $background 0%;
        align: left top;    /* This will set the starting coordinates to (0, 0) */
    }                       /* Which we need for the absolute offset to work */
    #menu_container {
        background: $surface;
        width: 14; height: 2;
        border-left: wide $panel;
        border-right: wide $panel;        
        &.bottom { border-top: hkey $panel; }
        &.top { border-bottom: hkey $panel; }
        & > ButtonStatic {
            &:hover { background: $panel-lighten-2; }
            &.pressed { background: $primary; }        
        }
    }
    """

    def __init__(
        self,
        menu_offset: Offset,
        window: Window,
        options: dict[str, Callable[..., Optional[Any]]],
    ) -> None:

        super().__init__()
        self.menu_offset = menu_offset
        self.window = window
        self.options = options

    def compose(self) -> ComposeResult:

        with Container(id="menu_container"):
            for key in self.options.keys():
                yield ButtonStatic(key, name=key)

    def on_mount(self) -> None:

        menu = self.query_one("#menu_container")
        y_offset = self.menu_offset.y - 2 if self.menu_offset.y >= 2 else 0
        menu.offset = Offset(self.menu_offset.x - 9, y_offset)

    def on_mouse_up(self) -> None:

        self.dismiss(None)

    @on(ButtonStatic.Pressed)
    def button_pressed(self, event: ButtonStatic.Pressed) -> None:

        if event.button.name:
            self.call_after_refresh(self.options[event.button.name])


class CloseButton(NoSelectStatic):

    def __init__(self, content: VisualType, window: Window, **kwargs: Any):
        super().__init__(content=content, **kwargs)
        self.window = window
        self.click_started_on: bool = False  # see note below

        # You might think that using self.capture_mouse() here would be simpler than
        # using a flag. But it causes issues. capture_mouse really shines when it's
        # used on buttons that need to move around the screen. (And it is used for that
        # purpose below). But for this button and several others, they will never be moving
        # around while actively trying to click them. So using capture_mouse() causes various
        # small issues that are totally unnecessary. (inconsistent behavior, glitchiness, etc.)

    def on_mouse_down(self, event: events.MouseDown) -> None:

        if event.button == 1:  # left button
            self.click_started_on = True
            self.add_class("pressed")
            self.window.focus()

    def on_mouse_up(self) -> None:

        self.remove_class("pressed")
        if self.click_started_on:
            self.window.close_window()
            self.click_started_on = False

    def on_leave(self) -> None:

        self.remove_class("pressed")
        self.click_started_on = False


class HamburgerButton(NoSelectStatic):

    def __init__(
        self,
        content: VisualType,
        window: Window,
        options: dict[str, Callable[..., Optional[Any]]],
        **kwargs: Any,
    ):
        super().__init__(content=content, **kwargs)
        self.window = window
        self.options = options
        self.click_started_on: bool = False

    def on_mouse_down(self, event: events.MouseDown) -> None:

        if event.button == 1:  # left button
            self.click_started_on = True
            self.add_class("pressed")
            self.window.focus()

    async def on_mouse_up(self, event: events.MouseUp) -> None:

        self.remove_class("pressed")
        if self.click_started_on:
            self.show_popup(event)
            self.click_started_on = False

    def on_leave(self) -> None:

        self.remove_class("pressed")
        self.click_started_on = False

    @work
    async def show_popup(self, event: events.MouseUp) -> None:

        menu_offset = event.screen_offset

        await self.app.push_screen_wait(
            HamburgerMenu(
                menu_offset=menu_offset,
                window=self.window,
                options=self.options,
            )
        )


class MaximizeButton(NoSelectStatic):

    def __init__(self, content: VisualType, window: Window, **kwargs: Any):
        super().__init__(content=content, **kwargs)
        self.window = window
        self.click_started_on: bool = False
        self.tooltip = "Maximize" if self.window.maximize_state is False else "Restore"

    def on_mouse_down(self, event: events.MouseDown) -> None:

        if event.button == 1:  # left button
            self.click_started_on = True
            self.add_class("pressed")
            self.window.focus()

    def on_mouse_up(self) -> None:

        self.remove_class("pressed")
        if self.click_started_on:
            self.window.toggle_maximize()
            self.click_started_on = False

    def on_leave(self) -> None:

        self.remove_class("pressed")
        self.click_started_on = False

    def swap_in_restore_icon(self) -> None:

        self.update(BUTTON_SYMBOLS["restore"])
        self.tooltip = "Restore"

    def swap_in_maximize_icon(self) -> None:

        self.update(BUTTON_SYMBOLS["maximize"])
        self.tooltip = "Maximize"


class MinimizeButton(NoSelectStatic):

    def __init__(self, content: VisualType, window: Window, **kwargs: Any):
        super().__init__(content=content, **kwargs)
        self.window = window
        self.click_started_on: bool = False
        self.tooltip = "Minimize"

    def on_mouse_down(self, event: events.MouseDown) -> None:

        if event.button == 1:  # left button
            self.click_started_on = True
            self.add_class("pressed")
            self.window.focus()

    def on_mouse_up(self) -> None:

        self.remove_class("pressed")
        if self.click_started_on:
            self.window.minimize()
            self.click_started_on = False

    def on_leave(self) -> None:

        self.remove_class("pressed")
        self.click_started_on = False


class Resizer(NoSelectStatic):

    def __init__(self, content: VisualType, window: Window, **kwargs: Any) -> None:
        super().__init__(content=content, **kwargs)
        self.window = window

    def set_max_min(self) -> None:

        assert isinstance(self.window.parent, Widget)
        try:
            self.min_width = self.window.min_width
            self.min_height = self.window.min_height
            self.max_width = self.window.max_width if self.window.max_width else self.window.parent.size.width
            self.max_height = (
                self.window.max_height if self.window.max_height else self.window.parent.size.height
            )
        except AttributeError as e:
            self.log.error(f"{self.window.id} does not have min/max width/height set. ")
            raise e

    def on_mouse_move(self, event: events.MouseMove) -> None:

        # App.mouse_captured refers to the widget that is currently capturing mouse events.
        if self.app.mouse_captured == self:

            assert isinstance(self.window.parent, Widget)
            assert self.window.styles.width is not None
            assert self.window.styles.height is not None

            total_delta = event.screen_offset - self.position_on_down
            new_size = self.size_on_down + total_delta

            self.window.styles.width = clamp(new_size.width, self.min_width, self.max_width)
            self.window.styles.height = clamp(new_size.height, self.min_height, self.max_height)

            # * Explanation:
            # Get the absolute position of the mouse right now (event.screen_offset),
            # minus where it was when the mouse was pressed down (position_on_down).
            # That gives the total delta from the original position.
            # Note that this is not the same as the event.delta attribute,
            # that only gives you the delta from the last mouse move event.
            # But we need the total delta from the original position.
            # Once we have that, add the total delta to size of the window.
            # If total_delta is negative, the size will be smaller

    def on_mouse_down(self, event: events.MouseDown) -> None:

        if event.button == 1:  # left button
            self.position_on_down = event.screen_offset
            self.size_on_down = self.window.size

            self.add_class("pressed")
            self.capture_mouse()
            self.window.focus()

    def on_mouse_up(self) -> None:

        self.remove_class("pressed")
        self.release_mouse()
        self.window.clamp_into_parent_area()  # Clamp to parent if resizing put it out of bounds


class TitleBar(NoSelectStatic):

    def __init__(self, window_title: str, window: Window, **kwargs: Any):
        super().__init__(content=window_title, **kwargs)
        self.window = window

    def on_mouse_move(self, event: events.MouseMove) -> None:

        if self.app.mouse_captured == self:
            if not self.window.snap_state:  # not locked, can move freely
                self.window.offset = self.window.offset + event.delta
            else:  # else, if locked to parent:
                assert isinstance(self.window.parent, Widget)
                self.window.offset = self.window.offset + event.delta  # first move into place normally
                self.window.clamp_into_parent_area()  # then clamp back to parent area.

                # Setting the offset and then clamping it again afterwards might not seem efficient,
                # but it looks the best, and least glitchy. I tried doing it in a single operation, and
                # it didn't work as well, or look as good.

    def on_mouse_down(self, event: events.MouseDown) -> None:

        if event.button == 1:  # left button
            self.add_class("pressed")
            self.capture_mouse()
            self.window.focus()

    def on_mouse_up(self) -> None:

        self.remove_class("pressed")
        self.release_mouse()


class TopBar(Horizontal):

    def __init__(  # passing in window might seem redundant because of self.parent,
        self,  # but it gives better type hinting and allows for more advanced
        window: Window,  # dependeny injection of the window down to children widgets.
        window_title: str,
        options: dict[str, Callable[..., Optional[Any]]] | None,
    ):
        super().__init__()
        self.window = window
        self.window_title = (window.icon + " " + window_title) if window.icon else window_title
        self.options = options

    def compose(self) -> ComposeResult:

        yield TitleBar(self.window_title, window=self.window)
        if self.options:
            yield HamburgerButton(
                BUTTON_SYMBOLS["hamburger"], window=self.window, options=self.options, classes="windowbutton"
            )
        yield MinimizeButton(BUTTON_SYMBOLS["minimize"], window=self.window, classes="windowbutton")
        if self.window.allow_maximize_window:
            self.maximize_button = MaximizeButton(
                BUTTON_SYMBOLS["maximize"], window=self.window, classes="windowbutton"
            )
            yield self.maximize_button
        if self.window.window_mode == "temporary":
            yield CloseButton(BUTTON_SYMBOLS["close"], window=self.window, classes="windowbutton close")


class BottomBar(Horizontal):

    def __init__(self, window: Window):
        super().__init__()
        self.window = window

    def compose(self) -> ComposeResult:
        yield NoSelectStatic(id="bottom_bar_text")
        if self.window.allow_resize:
            yield Resizer(BUTTON_SYMBOLS["resizer"], window=self.window, classes="windowbutton")
