"""Module for the WindowBar widget.

You don't need to import from this module. You can simply do:
`from textual_window import WindowBar`
"""

# ~ Type Checking (Pyright and MyPy) - Strict Mode
# ~ Linting - Ruff
# ~ Formatting - Black - max 110 characters / line

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from textual_window.window import Window
    from textual.visual import VisualType
from textual.app import ComposeResult
from textual import on, work
from textual.css.query import NoMatches
from textual.geometry import Offset
from textual.screen import ModalScreen
from textual.containers import Horizontal, Container
from textual import events

# from textual.message import Message
from textual.widgets import Header, Footer
from textual.reactive import reactive
from rich.emoji import Emoji

# from textual.binding import Binding

from textual_window.manager import window_manager  # The manager is a singleton instance
from textual_window.button_bases import NoSelectStatic, ButtonStatic

DOCK_DIRECTION = Literal["top", "bottom"]


class WindowBarButton(NoSelectStatic):

    def __init__(self, content: VisualType, window: Window, window_bar: WindowBar, **kwargs: Any):
        super().__init__(content=content, **kwargs)
        self.window = window
        self.window_bar = window_bar
        self.click_started_on: bool = False

    def on_mouse_down(self, event: events.MouseDown) -> None:

        if event.button == 1:  # left click
            self.add_class("pressed")
        elif event.button == 2 or event.button == 3:  # middle or right click
            self.add_class("right_pressed")
        self.click_started_on = True

    async def on_mouse_up(self, event: events.MouseUp) -> None:

        self.remove_class("pressed")
        self.remove_class("right_pressed")
        if self.click_started_on:
            if event.button == 1:  # left click
                self.window.toggle_window()
            elif event.button == 2 or event.button == 3:  # middle or right click
                self.show_popup()
            self.click_started_on = False

    def on_leave(self, event: events.Leave) -> None:

        self.remove_class("pressed")
        self.remove_class("right_pressed")
        self.click_started_on = False

    @work
    async def show_popup(self) -> None:

        absolute_offset = self.screen.get_offset(self)
        await self.app.push_screen_wait(
            WindowBarMenu(
                menu_offset=absolute_offset,
                dock=self.window_bar.dock,
                window=self.window,
            )
        )


class WindowBarBaseButton(NoSelectStatic):

    def __init__(self, window_bar: WindowBar, **kwargs: Any):
        super().__init__(**kwargs)
        self.window_bar = window_bar
        self.click_started_on: bool = False

    def on_mouse_down(self, event: events.MouseDown) -> None:

        self.add_class("pressed")
        self.click_started_on = True

    async def on_mouse_up(self, event: events.MouseUp) -> None:

        self.remove_class("pressed")
        if self.click_started_on:
            self.show_popup(event)
            self.click_started_on = False

    def on_leave(self, event: events.Leave) -> None:

        self.remove_class("pressed")
        self.click_started_on = False

    @work
    async def show_popup(self, event: events.MouseUp) -> None:

        max_size = self.window_bar.size.width - 14
        diff = event.screen_offset.x - max_size
        if diff > 0:
            menu_offset = Offset(max_size, event.screen_offset.y)
        else:
            menu_offset = event.screen_offset

        await self.app.push_screen_wait(
            WindowBarMenu(
                menu_offset=menu_offset,
                dock=self.window_bar.dock,
                window_bar=self.window_bar,
            )
        )


class WindowBarMenu(ModalScreen[None]):

    CSS = """
    WindowBarMenu {
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
        dock: str,
        window: Window | None = None,
        window_bar: WindowBar | None = None,
    ) -> None:

        super().__init__()
        self.menu_offset = menu_offset
        self.dock = dock
        self.window = window
        self.window_bar = window_bar

    def compose(self) -> ComposeResult:

        with Container(id="menu_container"):
            if self.window:
                snap_label = "Unsnap" if self.window.snap_state else "Snap"
                yield ButtonStatic(snap_label, id="snap_unsnap")
                yield ButtonStatic("Reset", id="reset")
            elif self.window_bar:
                yield ButtonStatic("Open all", id="open_all")
                yield ButtonStatic("Close all", id="close_all")
                yield ButtonStatic("Snap all", id="snap_all")
                yield ButtonStatic("Unsnap all", id="unsnap_all")
                yield ButtonStatic("Reset all", id="reset_all")
                if self.window_bar.show_toggle_dock:
                    yield ButtonStatic(f"Toggle Dock {Emoji('arrow_up_down')}", id="toggle_dock")
            else:
                raise RuntimeError("WindowBarMenu must have either a Window or WindowBar")

    def on_mount(self) -> None:

        menu = self.query_one("#menu_container")
        if self.window_bar:
            menu.styles.height = 6

        if self.dock == "top":
            y_offset = self.menu_offset.y + 1  # When at the top, just shift down by 1 row.
        elif self.dock == "bottom":
            y_offset = self.menu_offset.y - (2 if self.window else 6)
        else:
            raise ValueError("Dock must be either 'top' or 'bottom'")

        menu.offset = Offset(self.menu_offset.x, y_offset)

    def on_mouse_up(self) -> None:

        self.dismiss(None)

    @on(ButtonStatic.Pressed)
    def button_pressed(self, event: ButtonStatic.Pressed) -> None:
        # Normally I use the CSS selectors. But in this case, it's actually
        # cleaner to just use nested if statements. You can see why.

        if self.window:
            if event.button.id == "snap_unsnap":
                self.window.toggle_snap()
            elif event.button.id == "reset":
                self.window.reset_window()
        elif self.window_bar:
            if event.button.id == "open_all":
                self.window_bar.manager.open_all_windows()
            elif event.button.id == "close_all":
                self.window_bar.manager.close_all_windows()
            elif event.button.id == "snap_all":
                self.window_bar.manager.snap_all_windows()
            elif event.button.id == "unsnap_all":
                self.window_bar.manager.unsnap_all_windows()
            elif event.button.id == "reset_all":
                self.window_bar.manager.reset_all_windows()
            elif event.button.id == "toggle_dock":
                self.window_bar.toggle_dock()


class WindowBar(Horizontal):

    DEFAULT_CSS = """
    WindowBar {
        align: center bottom;
        background: $panel;     
    }   
    WindowBarButton {
        height: 1; width: auto;
        padding: 0 2;
        &:hover { background: $panel-lighten-1; }
        &.pressed { background: $primary; color: $text; }
        &.right_pressed { background: $accent-darken-3; color: $text; }
    }
    WindowBarBaseButton {
        height: 1; width: 1fr;
        &:hover { background: $boost; }
        &.pressed { background: $panel-lighten-1; }
    }    
    """

    manager = window_manager
    unnamed_window_counter: int = 1

    dock: reactive[str] = reactive[str]("bottom", always_update=True)
    """The direction to dock the bar. Can be either 'top' or 'bottom'.  
    This can be changed in real-time. You can modify this directly if you wish."""

    def __init__(
        self,
        dock: DOCK_DIRECTION = "bottom",
        start_open: bool = False,
        show_toggle_dock: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        """Initialize a WindowBar.

        Args:
            dock: The direction to dock the bar. Can be either "top" or "bottom".
                You can also set this in the CSS. When set in the CSS, it will override
                the constructor value.
            height: The height of the bar. This is set in the CSS, but you can also set it here.
            name: The name of the widget.
            id: The ID of the widget in the DOM.
            classes: The CSS classes for the widget.
            disabled: Whether the widget is disabled or not.
        """
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)

        if dock not in ["top", "bottom"]:
            raise ValueError("Dock must be either 'top' or 'bottom'")

        self.start_open = start_open
        self.display = start_open
        self.show_toggle_dock = show_toggle_dock
        self.initialized = False
        self.set_reactive(WindowBar.dock, dock)  # triggering the reactive this early would not work.

    #! OVERRIDE
    def _on_mount(self, event: events.Mount) -> None:
        super()._on_mount(event)

        if self.styles.dock in ["left", "right"]:
            raise ValueError("Dock must be either 'top' or 'bottom'")

        elif self.styles.dock in ["top", "bottom"]:
            self.log(f"Detected dock in CSS: {self.styles.dock}")
            self.dock = self.styles.dock

        else:  # No dock set in CSS, so set it to the constructor value.
            self.dock = self.dock  # this will trigger the watch_dock method

        self.manager.register_windowbar(self)

    def _on_resize(self) -> None:
        # Every time the bar is opened/shut or resized, it will automatically
        # clamp (snap / lock) all the windows that are in snap/lock mode.

        if self.initialized:
            self.log.debug("Resizing WindowBar")
            windows = self.manager.get_windows_as_list()
            for window in windows:
                if window.initialized and window.snap_state:
                    self.call_after_refresh(window.clamp_into_parent_area)

    def watch_dock(self, new_value: str) -> None:

        try:
            self.app.query_one(Header)
        except NoMatches:
            app_has_header = False
        else:
            app_has_header = True
        try:
            self.app.query_one(Footer)
        except NoMatches:
            app_has_footer = False
        else:
            app_has_footer = True

        if new_value == "top":
            self.styles.dock = "top"
            self.styles.align = ("center", "bottom")
            if app_has_header:
                self.styles.height = 2
            else:
                self.styles.height = 1
        elif new_value == "bottom":
            self.styles.dock = "bottom"
            self.styles.align = ("center", "top")
            if app_has_footer:
                self.styles.height = 2
            else:
                self.styles.height = 1
        else:
            raise ValueError("Dock must be either 'top' or 'bottom'")

    ################
    # ~ Public API ~#
    ################

    async def build_window_buttons(self) -> None:
        """This is called by the WindowManager when it detects the DOM is ready. It will
        get all the windows that are registered with the WindowManager and create buttons
        for them. If for some reason you mount or unmount windows in your app during runtime,
        you will need to call this method again to refresh the buttons.

        #! Note to self: This could potentially be automatic. Future feature?"""

        windows = self.manager.get_windows_as_list()
        window_buttons: list[WindowBarButton | WindowBarBaseButton] = []
        for window in windows:
            if window.name:
                window_buttons.append(
                    WindowBarButton(
                        window=window,
                        window_bar=self,
                        content=f"{window.name}",
                        id=f"{window.id}_button",
                    )
                )
            else:
                window_buttons.append(
                    WindowBarButton(
                        window=window,
                        window_bar=self,
                        content=f"Unnamed Window {WindowBar.unnamed_window_counter}",
                        id=f"unnamed_window_{WindowBar.unnamed_window_counter}_button",
                    )
                )
                WindowBar.unnamed_window_counter += 1

        window_buttons.insert(0, WindowBarBaseButton(window_bar=self, id="windowbar_button_left"))
        window_buttons.append(WindowBarBaseButton(window_bar=self, id="windowbar_button_right"))
        await self.mount_all(window_buttons)
        self.initialized = True
        self.log.debug("WindowBar initialized")

    def set_dock(self, dock: DOCK_DIRECTION = "bottom") -> None:
        self.dock = dock

    def toggle_dock(self) -> None:
        """Toggle if the WindowBar is docked at the top or bottom of the screen."""

        if self.dock == "top":
            self.dock = "bottom"
        else:
            self.dock = "top"

    def toggle_bar(self) -> None:
        self.display = not self.display
