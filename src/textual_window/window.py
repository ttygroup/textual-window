"""Module for the Window widget.

You don't need to import from this module. You can simply do:
`from textual_window import Window"""

# ~ Type Checking (Pyright and MyPy) - Strict Mode
# ~ Linting - Ruff
# ~ Formatting - Black - max 110 characters / line

from __future__ import annotations
from typing import Literal, Any, TYPE_CHECKING, Callable, Optional
from typing_extensions import Self

if TYPE_CHECKING:
    from textual.visual import VisualType

import textual.events as events
from textual._compose import compose  # type: ignore[unused-ignore]
from textual.widget import Widget
from textual.message import Message
from textual.binding import Binding

from textual import on, work
from textual.app import ComposeResult
from textual.geometry import clamp, Size

# from textual.widgets import Static
from textual.containers import Horizontal, VerticalScroll, Container
from textual.screen import ModalScreen
from textual.geometry import Offset
from textual.reactive import reactive

# from rich.emoji import Emoji

from textual_window.manager import window_manager
from textual_window.button_bases import ButtonStatic, NoSelectStatic

__all__ = ["Window"]

# These are combined to calculate the starting position.
STARTING_VERTICAL = Literal["top", "uppermiddle", "middle", "lowermiddle", "bottom"]
STARTING_HORIZONTAL = Literal["left", "centerleft", "center", "centerright", "right"]


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
            self.window.bring_forward()

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
            self.window.bring_forward()

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
            self.window.bring_forward()

    def on_mouse_up(self) -> None:

        self.remove_class("pressed")
        if self.click_started_on:
            self.window.toggle_maximize()
            self.click_started_on = False

    def on_leave(self) -> None:

        self.remove_class("pressed")
        self.click_started_on = False

    def swap_in_restore_icon(self) -> None:

        self.update(" - ")
        self.tooltip = "Restore"

    def swap_in_maximize_icon(self) -> None:

        self.update(" ☐ ")
        self.tooltip = "Maximize"


class Resizer(NoSelectStatic):

    def __init__(self, content: VisualType, window: Window, **kwargs: Any) -> None:
        super().__init__(content=content, **kwargs)
        self.window = window

        self.call_after_refresh(self.set_max_min)

    def set_max_min(self) -> None:

        assert isinstance(self.window.parent, Widget)
        self.min_width = self.window.min_width
        self.min_height = self.window.min_height
        self.max_width = self.window.max_width if self.window.max_width else self.window.parent.size.width
        self.max_height = self.window.max_height if self.window.max_height else self.window.parent.size.height

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
            self.window.bring_forward()

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
            self.window.bring_forward()

    def on_mouse_up(self) -> None:

        self.remove_class("pressed")
        self.release_mouse()


class TopBar(Horizontal):

    def __init__(  # passing in window might seem redundant because of self.parent,
        self,  # but it gives better type hinting and allows for more advanced
        window: Window,  # dependeny injection of the window down to children widgets.
        window_title: str,
        options: dict[str, Callable[..., Optional[Any]]],
    ):
        super().__init__()
        self.window = window
        self.window_title = window_title
        self.options = options

    def compose(self) -> ComposeResult:

        yield TitleBar(self.window_title, window=self.window)
        if self.options:
            yield HamburgerButton(" ☰ ", window=self.window, options=self.options)
        if self.window.show_maximize_button:
            self.maximize_button = MaximizeButton(" ☐ ", window=self.window)
            yield self.maximize_button
        yield CloseButton(" X ", window=self.window)

        self.app.screen.maximize


class BottomBar(Horizontal):

    def __init__(self, window: Window):
        super().__init__()
        self.window = window

    def compose(self) -> ComposeResult:
        yield NoSelectStatic(id="bottom_bar_text")
        if self.window.allow_resize:
            yield Resizer("◢", window=self.window)


class Window(Widget):

    DEFAULT_CSS = """
    Window {
        width: 20; height: 10;
        min-width: 12; min-height: 6;
        &:focus { 
            & > TopBar, BottomBar { background: $secondary; }
            & > #content_pane { 
                border-left: wide $secondary;
                border-right: wide $secondary;
            }
        }
    }
    TopBar, BottomBar {
        height: 1; max-height: 1; width: 1fr;
        background: $panel-lighten-1; 
    }   
    TitleBar {
        width: 1fr; height: 1; padding: 0 1; 
        &:hover { background: $panel-lighten-3; }          
        &.pressed { background: $primary; }
    }
    CloseButton {
        width: 3; height: 1; padding: 0;
        &:hover { background: $error; }
        &.pressed { background: $error-darken-2; color: $text-error; }        
    }
    MaximizeButton {
        width: 3; height: 1; padding: 0;
        &:hover { background: $panel-lighten-3; }
        &.pressed { background: $primary; color: $text; }        
    }    
    HamburgerButton {
        width: 3; height: 1; padding: 0;
        &:hover { background: $panel-lighten-3; }
        &.pressed { background: $primary; }        
    }    
    Resizer {
        width: 2; height: 1; padding: 0; content-align: right middle;
        &:hover { background: $panel-lighten-3; }
        &.pressed { background: $primary; }
    }
    #bottom_bar_text { width: 1fr; height: 1; padding: 0 1; }    
    #content_pane {
        background: $surface;
        border-left: wide $panel-lighten-1;
        border-right: wide $panel-lighten-1;
        padding: 1 0 1 1; 
        align: center top;
        width: 1fr; height: 1fr;
    }    
    """

    # Copying bindings from the ScrollableContainer class in order to control
    # the scrolling of the content pane while the Window widget itself has
    # the focus. The VerticalScroll is set to not be focusable.
    BINDINGS = [
        Binding("ctrl+w", "close_window", "Close Window"),
        # All these below from ScrollableContainer:
        Binding("up", "scroll_up", "Scroll Up", show=False),
        Binding("down", "scroll_down", "Scroll Down", show=False),
        Binding("home", "scroll_home", "Scroll Home", show=False),
        Binding("end", "scroll_end", "Scroll End", show=False),
        Binding("pageup", "page_up", "Page Up", show=False),
        Binding("pagedown", "page_down", "Page Down", show=False),
        # Binding("left", "scroll_left", "Scroll Left", show=False),
        # Binding("right", "scroll_right", "Scroll Right", show=False),
        # Binding("ctrl+pageup", "page_left", "Page Left", show=False),
        # Binding("ctrl+pagedown", "page_right", "Page Right", show=False),
    ]

    ###############
    #  REACTIVES  #
    ###############
    open_state: reactive[bool] = reactive(False, init=False)
    "The open/closed state of the window. You can modify this directly if you wish."
    snap_state: reactive[bool] = reactive(True, init=False)
    "The lock state (snap to parent) of the window. You can modify this directly if you wish."
    maximize_state: reactive[bool] = reactive(False, init=False)
    "The maximize state of the window. You can modify this directly if you wish."

    #####################
    # Other class setup #
    #####################
    manager = window_manager  # ~ Reference the window manager instance.
    _current_layer = 0  #   Class variable to track the next available layer
    can_focus = True

    class Closed(Message):
        """Message sent when the window is closed."""

        def __init__(self, window: Window) -> None:
            super().__init__()
            self.window = window

        @property
        def control(self) -> Window:
            return self.window

    class Opened(Message):
        """Message sent when the window is opened."""

        def __init__(self, window: Window) -> None:
            super().__init__()
            self.window = window

        @property
        def control(self) -> Window:
            return self.window

    class Initialized(Message):
        """Message sent when the window is completed initialization."""

        def __init__(self, window: Window) -> None:
            super().__init__()
            self.window = window

        @property
        def control(self) -> Window:
            return self.window

    def __init__(
        self,
        *children: Widget,
        name: str,
        starting_horizontal: STARTING_HORIZONTAL = "center",
        starting_vertical: STARTING_VERTICAL = "middle",
        start_open: bool = False,
        start_snapped: bool = True,
        allow_resize: bool = True,
        show_maximize_button: bool = False,
        menu_options: dict[str, Callable[..., Optional[Any]]] = {},
        animated: bool = True,
        show_title: bool = True,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ):
        """Initialize a window widget.

        Args:
            *children: Child widgets.
            name: The name of the widget - Used for the window's title bar, the WindowBar, and the
                WindowSwitcher. `name` is REQUIRED, unlike normal Textual widgets. You can set
                `show_title` to False to hide the Window's name in the title bar.
            starting_horizontal (str): The starting horizontal position of the window.
            starting_vertical (str): The starting vertical position of the window.
            start_open (bool): Whether the window should start open or closed.
            start_snapped (bool): Whether the window should start snapped (locked) within the parent area.
            allow_resize (bool): Whether the window should be resizable.
            show_maximize_button (bool): Whether to show the maximize button on the top bar.
            menu_options (dict): A dictionary of options to show in a hamburger menu.
                The hamburger menu will be shown automatically if you pass in any options.
                The key is the name of the option as it will be displayed in the menu.
                The value is a callable that will be called when the option is selected.
                #! add note about functools partial?
            animated (bool): Whether the window should be animated.
                This will add a fade in/out effect when opening/closing the window. You can modify
                the `animation_duration` attribute to change the duration of the animation.
            show_title (bool): Whether to show the title bar or not.
            id: The ID of the widget in the DOM.
            classes: The CSS classes for the widget.
            disabled: Whether the widget is disabled or not.
        """

        super().__init__(
            *children,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self._name = name  #  This is an override from DOMnode. Because _name cannot be None here.
        self.initialized = False
        if start_open is False and animated is True:
            self.styles.opacity = 0.0
        self.display = start_open
        self.start_open = start_open  #     This is saved for resetting the window.
        self.starting_snap_state = start_snapped  #     Snap and Lock mean the same thing in this context.
        self.set_reactive(Window.open_state, start_open)  #     Don't want to trigger the animations.
        self.set_reactive(Window.snap_state, start_snapped)  #  These 3 reactives are handled manually.
        self.set_reactive(Window.maximize_state, False)

        self.starting_horizontal = starting_horizontal
        self.starting_vertical = starting_vertical
        self.allow_resize = allow_resize
        self.animated = animated
        self.show_maximize_button = show_maximize_button
        self.menu_options = menu_options
        self.show_title = show_title

        # SECONDARY ATTRIBUTES (non-constructor)
        self.auto_bring_forward = True  #       If windows should be brought forward when opened.
        self.auto_focus = True  #               If windows should be focused when opened.
        self.animation_duration: float = 0.3  # The duration of the fade effect, if enabled

        # self.disable_modifying_snap_state = False    #! [N/I]

        # EXTRAS
        self.saved_size: Size | None = None  # Save the size of the window when it is maximized.
        self.saved_offset: Offset | None = None  # Save the offset of the window when it is maximized.
        self.max_width: int | None = None  # The maximum width of the window.
        self.max_height: int | None = None  # The maximum height of the window.

        # -------------------------------------------------------------------------#

        self.layer_index = Window._current_layer
        Window._current_layer += 1  # increment the class variable for the next window's layer

        # Below are the three widgets that make up the window.
        # The top bar, the content pane, and the bottom bar.
        # All three of these are mounted to the window in the overridden _compose method.
        # When someone uses the window, any children they pass in will be mounted
        # into the content pane. The top and bottom bars are fixed.

        window_title = name if show_title else ""

        self._top_bar = TopBar(window=self, window_title=window_title, options=self.menu_options)
        self._content_pane = VerticalScroll(id="content_pane", can_focus=False)
        self._bottom_bar = BottomBar(window=self)

        self._window_base_widgets: list[Widget] = [
            self._top_bar,
            self._content_pane,
            self._bottom_bar,
        ]

    #! OVERRIDE
    async def _compose(self) -> None:

        # This is the fancy layer system. Its what allows the window to be windowy.
        # Using the _current_layer class variable, we can keep track of the next available layer.
        current_layers = self.screen.layers
        if f"window{self.layer_index}" not in current_layers:
            layers = [layer for layer in current_layers if not layer.startswith("_")]
            # '_' denotes textual built-in layers. We want to skip those. Textual handles them
            # behind the scenes, and we don't want to mess with them.
            layers.extend([f"window{self.layer_index}"])  # add our new layer onto the non-built ins
            self.screen.styles.layers = tuple(layers)  # type: ignore
        self.styles.layer = f"window{self.layer_index}"
        #! type ignore from: (Tuple size mismatch; expected 1 but received indeterminate)

        await self.mount_all(self._window_base_widgets)  # Mount the top bar, content pane, and bottom bar.

        #! ^^^ Everything above this comment is a new addition. ^^^

        try:
            widgets = [*self._pending_children, *compose(self)]
            self._pending_children.clear()
        except TypeError as error:
            raise TypeError(f"{self!r} compose() method returned an invalid result; {error}") from error
        except Exception as error:
            self.app._handle_exception(error)  # type: ignore[unused-ignore]
        else:
            self._extend_compose(widgets)
            # ~ The below line was modified (mounting into the content pane)
            await self._content_pane.mount_composed_widgets(widgets)

        self.absolute_offset = self.offset  # ~ This is a new addition.
        # The above line is necessary to make the resizing work properly
        # (otherwise it will expand from the center)

    #! OVERRIDE
    def compose_add_child(self, widget: Widget) -> None:
        _rich_traceback_omit = True
        self._content_pane._pending_children.append(widget)  # ~ This line was modified

    #! OVERRIDE
    def _on_mount(self, event: events.Mount) -> None:
        super()._on_mount(event)

        self.starting_width = self.styles.width  # lock this in for Resetting later.
        self.starting_height = self.styles.height

        # Setting the min/max/starting styles needs to be done in the mount method
        # because they won't be available to read before this point.

        if self.styles.max_width and self.styles.max_width.cells:
            self.max_width = self.styles.max_width.cells
        else:
            self.max_width = None  #! These should maybe be reactive incase someone tries to change them.

        if self.styles.max_height and self.styles.max_height.cells:
            self.max_height = self.styles.max_height.cells
        else:
            self.max_height = None

        if self.styles.min_width and self.styles.min_width.cells:
            self.min_width = self.styles.min_width.cells
        else:
            raise ValueError(f"Minimum width must be set to an integer value on {self.id}")

        if self.styles.min_height and self.styles.min_height.cells:
            self.min_height = self.styles.min_height.cells
        else:
            raise ValueError(f"Minimum height must be set to an integer value on {self.id}")

        self.log.debug(f"layer {self.layer} with ID {self.id} mounted.")

        self.manager.add_window(self)  # Register this window to the window manager.
        self.manager.watch_for_dom_ready_runner()

    def _on_unmount(self) -> None:
        self.manager.remove_window(self)  # Remove this window from the window manager.
        super()._on_unmount()

    def _calculate_starting_position(self) -> Offset:

        assert self.starting_width and self.starting_width.cells
        assert self.starting_height and self.starting_height.cells
        assert isinstance(self.parent, Widget)

        size = Size(self.starting_width.cells, self.starting_height.cells)
        x, y = self.parent.size - size

        # Parent size minus the window size will be equal to
        # how far it can move left/right(x) or up/down(y) before
        # hitting the edge of the parent.

        starting_horizontals = {  # Example: x = 20
            "left": 0,  # 0              = 0
            "centerleft": x // 4,  # 20 / 4         = 5
            "center": x // 2,  # 20 / 2         = 10
            "centerright": x - (x // 4),  # 20 - (20 / 4)  = 15
            "right": x,  # 20             = 20
        }
        starting_verticals = {
            "top": 0,
            "uppermiddle": y // 4,
            "middle": y // 2,
            "lowermiddle": y - (y // 4),
            "bottom": y,
        }

        start_horizontal = starting_horizontals[self.starting_horizontal]
        start_vertical = starting_verticals[self.starting_vertical]
        self.starting_offset = Offset(start_horizontal, start_vertical)  # store this for resetting.

        if not self.initialized:
            self.initialized = True
            self.post_message(self.Initialized(self))
        return self.starting_offset

    def _calculate_max_size(self) -> Size:
        # This is used by the window manager, it's only called when it detects
        # the DOM is ready.

        assert isinstance(self.parent, Widget)
        assert self.parent.size.width is not None
        assert self.parent.size.height is not None

        if self.styles.max_width and self.styles.max_width.cells:
            self.max_width = self.styles.max_width.cells
        else:
            self.max_width = self.parent.size.width
        if self.styles.max_height and self.styles.max_height.cells:
            self.max_height = self.styles.max_height.cells
        else:
            self.max_height = self.parent.size.height
        return Size(self.max_width, self.max_height)

    def _close_animation(self) -> None:

        def _close_animation_callback() -> None:
            self.display = False

        if self.animated:
            self.styles.animate(
                "opacity",
                0.0,
                duration=self.animation_duration,
                on_complete=_close_animation_callback,
            )
        else:
            self.display = False

    def _open_animation(self) -> None:

        self.display = True
        if self.animated:
            self.styles.animate("opacity", 1.0, duration=self.animation_duration)

    def on_mouse_down(self) -> None:
        self.bring_forward()

    def focus(self, scroll_visible: bool = True) -> Self:
        self.manager.append_focus_order(self)
        return super().focus(scroll_visible=scroll_visible)

    @property
    def name(self) -> str:
        """The name of the node."""
        return self._name  # type: ignore

    ####################
    # ~ WATCH METHODS ~#
    ####################

    def watch_snap_state(self, value: bool) -> None:

        if value:
            self.clamp_into_parent_area()

    def watch_open_state(self, value: bool) -> None:

        if value:
            self._open_animation()
            if self.auto_bring_forward:
                self.bring_forward()
            if self.auto_focus:
                self.focus()
            self.post_message(self.Opened(self))
        else:
            self._close_animation()
            children = self.query(Widget)
            for child in children:  # Anything focused in the window needs to be unfocused.
                child.blur()  # self.display handles this mostly well, but
            self.post_message(self.Closed(self))  # this is a safety net to prevent any issues.

    def watch_maximize_state(self, value: bool) -> None:

        if value:
            self.saved_size = Size(self.size.width, self.size.height)
            self.saved_offset = Offset(self.offset.x, self.offset.y)
            self.styles.width = self.max_width
            self.styles.height = self.max_height
            self._top_bar.maximize_button.swap_in_restore_icon()
            self.call_after_refresh(self.clamp_into_parent_area)
        else:
            assert self.saved_size is not None, "This should never happen."
            assert self.saved_offset is not None, "This should never happen."
            self.styles.width = self.saved_size.width
            self.styles.height = self.saved_size.height
            self.offset = self.saved_offset
            self._top_bar.maximize_button.swap_in_maximize_icon()

    ###############
    # ~ Actions ~ #
    ###############

    def action_close_window(self) -> None:
        self.close_window()

    def action_scroll_up(self) -> None:
        self._content_pane.action_scroll_up()

    def action_scroll_down(self) -> None:
        self._content_pane.action_scroll_down()

    def action_scroll_home(self) -> None:
        self._content_pane.action_scroll_home()

    def action_scroll_end(self) -> None:
        self._content_pane.action_scroll_end()

    def action_page_up(self) -> None:
        self._content_pane.action_page_up()

    def action_page_down(self) -> None:
        self._content_pane.action_page_down()

    ##################
    # ~ Public API ~ #
    ##################

    def bring_forward(self) -> None:
        """This is called automatically when the window is opened, as long as
        `auto_bring_forward` is set to True on the window. If you want manual control,
        you can set that to False and call this method yourself."""

        # Get all layers that are not this widget's layer:
        layers = tuple(x for x in self.screen.styles.layers if x != self.layer)
        # Append this widget's layer to the end of the tuple:
        self.screen.styles.layers = layers + tuple([self.styles.layer])  # type: ignore
        #! Tuple size mismatch; expected 1 but received indeterminate

    def maximize(self) -> None:
        """Resize the window to its maximum."""
        self.maximize_state = True

    def restore(self) -> None:
        """(Opposite of maximize) Restore the window to its previous size and position."""
        self.maximize_state = False

    def toggle_maximize(self) -> None:
        """Toggle the window between its maximum size and its previous size."""
        self.maximize_state = not self.maximize_state

    def close_window(self) -> None:
        """Runs the close animatiom and blurs all children."""
        self.open_state = False

    def open_window(self) -> None:
        """Runs the open animation, and optionally brings the window forward."""
        self.open_state = True

    def toggle_window(self) -> None:
        """Toggle the window open and closed."""
        self.open_state = not self.open_state

    def enable_snap(self) -> None:
        """Enable window locking (set snap_state to True)"""
        self.snap_state = True

    def disable_snap(self) -> None:
        """Disable window locking (set snap_state to False)"""
        self.snap_state = False

    def toggle_snap(self) -> None:
        """Toggle the window snap (lock) state."""
        self.snap_state = not self.snap_state

    def toggle_lock(self) -> None:
        """Alias for toggle_snap(). Toggle the window snap (lock) state."""
        self.snap_state = not self.snap_state

    def reset_window(self) -> None:
        """Reset the window to its starting position and size."""

        self.reset_size()
        self.reset_position()
        self.snap_state = self.starting_snap_state

        if self.start_open:
            self.open_state = True
        else:
            self.open_state = False

    def reset_size(self) -> None:
        """Reset the window size to its starting size."""

        self.styles.width = self.starting_width
        self.styles.height = self.starting_height

    def reset_position(self) -> None:
        """Reset the window position to its starting position."""

        self._calculate_starting_position()
        self.offset = self.starting_offset

    def clamp_into_parent_area(self) -> None:
        """This function returns the widget into its parent area.
        There shouldn't be any need to call this manually, but it is here if you need it."""

        if self.initialized:
            assert isinstance(self.parent, Widget)
            x, y = self.parent.size - self.size
            self.offset = Offset(clamp(self.offset.x, 0, x), clamp(self.offset.y, 0, y))
