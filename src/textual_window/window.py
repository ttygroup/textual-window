"""Module for the Window widget.

You don't need to import from this module. You can simply do:
`from textual_window import Window"""

# ~ Type Checking (Pyright and MyPy) - Strict Mode
# ~ Linting - Ruff
# ~ Formatting - Black - max 110 characters / line

# Python imports
from __future__ import annotations
from typing import Literal, Any, TYPE_CHECKING, Callable, Optional, Iterable, TypedDict
from textual.await_remove import AwaitRemove

if TYPE_CHECKING:
    # from textual.visual import VisualType
    from textual.css.query import QueryType

    # from textual.app import ComposeResult

# Textual and Rich imports
import textual.events as events
from textual._compose import compose  # type: ignore[unused-ignore]
from textual.dom import check_identifiers
from textual.widget import Widget, AwaitMount
from textual.message import Message
from textual.binding import Binding
from textual import on, work
from textual.geometry import clamp, Size
from textual.containers import VerticalScroll
from textual.geometry import Offset
from textual.reactive import reactive

# Local imports
from textual_window.manager import window_manager
from textual_window.windowcomponents import Resizer, TopBar, BottomBar

__all__ = [
    "Window",
    "WindowStylesDict",
    "STARTING_VERTICAL",
    "STARTING_HORIZONTAL",
    "MODE",
]

# These are combined to calculate the starting position.
STARTING_VERTICAL = Literal["top", "uppermiddle", "middle", "lowermiddle", "bottom"]
STARTING_HORIZONTAL = Literal["left", "centerleft", "center", "centerright", "right"]
MODE = Literal["permanent", "temporary"]


class WindowStylesDict(TypedDict, total=False):
    """A dictionary of styles for the Window widget.

    This can be passed into the Window constructor argument named `styles_dict`.
    It provides a way to set window styles entirely through the constructor without
    needing to use CSS. This is useful for integrating into dynamic applications
    that may be using some kind of external process manager to create windows.
    """

    min_width: int
    min_height: int
    max_width: int | None
    max_height: int | None
    width: int | None
    height: int | None
    # More may be added here with time or by request


class WindowMessage(Message):
    """Generic base class for window messages."""

    def __init__(self, window: Window) -> None:
        super().__init__()
        self.window = window

    @property
    def control(self) -> Window:
        return self.window


class Window(Widget):

    DEFAULT_CSS = """
    Window {
        width: 25; height: 12;
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
        width: 1fr; height: 1; max-height: 1;
        background: $panel-lighten-1; 
        &.focused { background: $secondary; }     
    }   
    TitleBar {
        width: 1fr; height: 1; padding: 0 1; 
        &:hover { background: $panel-lighten-3; }          
        &.pressed { background: $primary; }
    }
    .windowbutton {
        width: 3; height: 1;
        padding: 0;
        content-align: center middle;
        &:hover { background: $panel-lighten-3; }
        &.pressed { background: $primary; color: $text; }         
        &.close {
            &:hover { background: $error; }
            &.pressed { background: $error-darken-2; color: $text-error; }          
        }
    }    
    #bottom_bar_text { width: 1fr; height: 1; padding: 0 1; }    
    #content_pane {
        width: 1fr;
        height: 1fr;    
        background: $surface;
        border-left: wide $panel-lighten-1;
        border-right: wide $panel-lighten-1;
        border-top: none;
        border-bottom: none;
        padding: 1 0 1 1; 
        align: center top;
        &.focused {
            border-left: wide $secondary;
            border-right: wide $secondary;
        }        
    }    
    """

    # Copying bindings from the ScrollableContainer class in order to control
    # the scrolling of the content pane while the Window widget itself has
    # the focus. The VerticalScroll is set to not be focusable.
    BINDINGS = [
        Binding("ctrl+w", "close_window", "Close Window"),
        Binding("ctrl+d", "minimize_window", "Minimize Window"),
        # All these below from ScrollableContainer:
        Binding("up", "scroll_up", "Scroll Up", show=False),
        Binding("down", "scroll_down", "Scroll Down", show=False),
        Binding("home", "scroll_home", "Scroll Home", show=False),
        Binding("end", "scroll_end", "Scroll End", show=False),
        Binding("pageup", "page_up", "Page Up", show=False),
        Binding("pagedown", "page_down", "Page Down", show=False),
        Binding("left", "scroll_left", "Scroll Left", show=False),
        Binding("right", "scroll_right", "Scroll Right", show=False),
        Binding("ctrl+pageup", "page_left", "Page Left", show=False),
        Binding("ctrl+pagedown", "page_right", "Page Right", show=False),
    ]

    ###############
    #  REACTIVES  #
    ###############
    open_state: reactive[bool] = reactive(False, init=False)
    """The open/minimized state of the window. You can modify this directly if you wish.
    Note that this does not remove the window from the DOM or the window bar/manager. You
    must use `remove_window()` or `close_window` to do that."""
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
    _id: str  #   Override the parent's Optional[str] typing
    _name: str  # Override the parent's Optional[str] typing

    class Closed(WindowMessage):
        """Message sent when the window is closed."""

    class Opened(WindowMessage):
        """Message sent when the window is opened."""

    class Minimized(WindowMessage):
        """Message sent when the window is minimized."""

    class Initialized(WindowMessage):
        """Message sent when the window is completed initialization."""

    def __init__(
        self,
        *children: Widget,
        id: str,
        mode: MODE = "temporary",
        icon: str | None = None,
        classes: str | None = None,
        name: str | None = None,
        starting_horizontal: STARTING_HORIZONTAL = "center",
        starting_vertical: STARTING_VERTICAL = "middle",
        start_open: bool = False,
        start_snapped: bool = True,
        allow_resize: bool = True,
        allow_maximize: bool = False,
        menu_options: dict[str, Callable[..., Optional[Any]]] | None = None,
        styles_dict: WindowStylesDict | None = None,
        animated: bool = True,
        show_title: bool = True,
        disabled: bool = False,
    ):
        """Initialize a window widget.

        Args:
            *children: Child widgets.
            id: The ID of the window - Used for the window's title bar, the WindowBar, and the
                WindowSwitcher. `id` is REQUIRED, unlike normal Textual widgets. Underscores
                will be replaced with spaces for displaying in the title bar, window bar, and
                window switcher.
                If you want the display name to be different from the ID for some reason,
                you can set the `name` argument to whatever display name you'd like.
                If you do not want the ID to be shown in the title bar, You can set the
                `show_title` argument to False.
            mode: This controls whether the widget should be removable, or a permanent fixture of your app.
                In temporary mode, the close button will remove the window from the DOM as well as the
                window bar and manager (like a normal desktop would). Ctrl-w behavior in this mode is to
                remove the window.
                In permanent mode, the close button is removed from the window and windowbar menus,
                the window is only able to be minimized, and Ctrl-w behavior is to minimize the window.
                (minimize and close will do the same thing in this mode).
            icon: The icon for the window to use in the title bar and window bar.
            classes: The CSS classes for the widget.
            name: The name of the window. If you wish for the display name to be different than the
                ID for some reason, you can set this to whatever display name you'd like.
            starting_horizontal: The starting horizontal position of the window.
            starting_vertical: The starting vertical position of the window.
            start_open: Whether the window should start open or closed.
            start_snapped: Whether the window should start snapped (locked) within the parent area.
            allow_resize: Whether the window should be resizable.
            allow_maximize: Whether to show the maximize button on the top bar.
            menu_options: A dictionary of options to show in a hamburger menu.
                The hamburger menu will be shown automatically if you pass in any options.
                The key is the name of the option as it will be displayed in the menu.
                The value is a callable that will be called when the option is selected.
            styles_dict: A dictionary of styles to apply to the window.
                Setting styles through the constructor is useful for dynamic applications
                where you may have some kind of external process manager that creates windows,
                or you can't use CSS for some reason.
            animated: Whether the window should be animated.
                This will add a fade in/out effect when opening/closing the window. You can modify
                the `animation_duration` attribute to change the duration of the animation.
            show_title: Whether to show the title in the title bar or not.
            disabled: Whether the widget is disabled or not.
        """

        if not id:
            raise ValueError("Windows must provide an ID. It cannot be None or empty.")

        # TODO - add more validation here

        super().__init__(*children, classes=classes, disabled=disabled)

        name_to_use = name if name else id.replace("_", " ").capitalize()

        self._id = id
        self._name = name_to_use
        self.window_mode = mode
        self.initialized = False
        if start_open is False and animated is True:
            self.styles.opacity = 0.0
        self.display = start_open
        self.start_open = start_open  #  This is saved for resetting the window.
        self.starting_snap_state = start_snapped  #  Snap and Lock mean the same thing in this context.
        self.set_reactive(Window.open_state, start_open)  #     <-- Don't want to trigger these animations.
        self.set_reactive(Window.snap_state, start_snapped)  #      These 3 reactives are handled manually.
        self.set_reactive(Window.maximize_state, False)

        self.starting_horizontal = starting_horizontal
        self.starting_vertical = starting_vertical
        self.allow_resize = allow_resize
        self.allow_maximize_window = allow_maximize
        self.menu_options = menu_options
        self.styles_dict = styles_dict
        self.animated = animated
        self.show_title = show_title
        self.icon = icon

        # SECONDARY ATTRIBUTES (non-constructor)
        self.auto_bring_forward = True  #       If windows should be brought forward when opened.
        self.auto_focus = True  #               If windows should be focused when opened.
        self.animation_duration: float = 0.3  # The duration of the fade effect, if enabled

        # self.disable_modifying_snap_state = False    #! [N/I]

        # EXTRAS
        self.starting_width: int | None = None  # The starting width of the window.
        self.starting_height: int | None = None  # The starting height of the window.
        self.saved_size: Size | None = None  # Save the size of the window when it is maximized.
        self.saved_offset: Offset | None = None  # Save the offset of the window when it is maximized.
        self.max_width: int | None = None  # The maximum width of the window.
        self.max_height: int | None = None  # The maximum height of the window.
        self.min_width: int
        self.min_height: int

        # -------------------------------------------------------------------------#

        self.layer_index = Window._current_layer
        Window._current_layer += 1  # increment the class variable for the next window's layer

        # Below are the three widgets that make up the window.
        # The top bar, the content pane, and the bottom bar.
        # All three of these are mounted to the window in the overridden _compose method.
        # When someone uses the window, any children they pass in will be mounted
        # into the content pane. The top and bottom bars are fixed.

        window_title = name_to_use if show_title else ""

        self._top_bar = TopBar(window=self, window_title=window_title, options=self.menu_options)
        self._content_pane = VerticalScroll(id="content_pane", can_focus=False)
        self._bottom_bar = BottomBar(window=self)

        self._window_base_widgets: list[Widget] = [
            self._top_bar,
            self._content_pane,
            self._bottom_bar,
        ]

        self.manager.register_window(self)  # Register this window to the window manager.

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

        if self.app._dom_ready:  # type: ignore[unused-ignore]
            self._dom_ready()
        else:
            self.call_after_refresh(self._dom_ready)

    @work(group="window_ready")
    async def _dom_ready(self) -> None:

        size, min_size, max_size = await self._calculate_all_sizes()

        self.starting_width = size.width
        self.starting_height = size.height
        self.styles.width = size.width
        self.styles.height = size.height
        self.min_width = min_size.width
        self.min_height = min_size.height
        self.max_width = max_size.width
        self.max_height = max_size.height

        self.offset = await self._calculate_starting_position()
        if self.allow_resize:
            self.query_one(Resizer).set_max_min()
        ready_result = await self.manager.window_ready(self)
        if ready_result:  # this means it detected there is a window bar.
            self.manager.signal_window_state(self, self.display)

    async def _calculate_all_sizes(self) -> tuple[Size, Size, Size]:
        "Returns tuple of `(min_size, max_size)`"

        assert isinstance(self.parent, Widget)
        assert self.parent.size.width is not None
        assert self.parent.size.height is not None

        if self.styles.min_width and self.styles.min_width.cells:
            min_width = self.styles.min_width.cells
        else:
            # Minimum width must be set to an integer. This one can't be magicked away.
            # Allowing relative values for a minimum is just not practical.
            raise ValueError(f"Minimum width must be set to an integer value on {self.id}")

        if self.styles.min_height and self.styles.min_height.cells:
            min_height = self.styles.min_height.cells
        else:
            raise ValueError(f"Minimum height must be set to an integer value on {self.id}")

        # MAX #
        if self.styles.max_width and self.styles.max_width.cells:
            max_width = self.styles.max_width.cells
        else:
            # The max is actually None by default (unlike minimum which must be set).
            # So if the max is not set, it will default to the parent size.
            max_width = self.parent.size.width

        if self.styles.max_height and self.styles.max_height.cells:
            max_height = self.styles.max_height.cells
        else:
            max_height = self.parent.size.height

        # NOTE: We will always have a max width and max height, and so we will also
        # by extension always have a width and height.
        width = self.styles.width.cells if self.styles.width and self.styles.width.cells else max_width
        height = self.styles.height.cells if self.styles.height and self.styles.height.cells else max_height

        if self.styles_dict:
            # Any of these which are not None will override any styles
            # set through other methods such as CSS.
            min_width_style = self.styles_dict.get("min_width", None)
            if min_width_style is not None:
                min_width = min_width_style
            min_height_style = self.styles_dict.get("min_height", None)
            if min_height_style is not None:
                min_height = min_height_style
            max_width_style = self.styles_dict.get("max_width", None)
            if max_width_style is not None:
                max_width = max_width_style
            max_height_style = self.styles_dict.get("max_height", None)
            if max_height_style is not None:
                max_height = max_height_style
            width_style = self.styles_dict.get("width", None)
            if width_style is not None:
                width = width_style
            height_style = self.styles_dict.get("height", None)
            if height_style is not None:
                height = height_style

        # Clamp to the set min and maxes (just in case the size set is not within those bounds).
        clamped_width = clamp(width, min_width, max_width)
        clamped_height = clamp(height, min_height, max_height)

        size = Size(clamped_width, clamped_height)
        min_size = Size(min_width, min_height)
        max_size = Size(max_width, max_height)
        return (size, min_size, max_size)

    async def _calculate_starting_position(self) -> Offset:
        """Returns the starting position of the window
        based on the parent size and starting position arguments."""

        assert self.starting_width
        assert self.starting_height
        assert isinstance(self.parent, Widget)

        size = Size(self.starting_width, self.starting_height)
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
        starting_offset = Offset(start_horizontal, start_vertical)  # store this for resetting.

        if not self.initialized:
            self.initialized = True
            self.post_message(self.Initialized(self))
        return starting_offset

    def _execute_remove(self) -> None:
        self.manager.unregister_window(self)
        self.post_message(self.Closed(self))
        self.remove()

    def _close_animation(self, remove: bool) -> None:
        # Note: these are called the 'animation' methods, but they actually run every single
        # time and control the opening and closing logic. I know, not the cleanest
        # naming convention ¯\_(ツ)_/¯. Things were added over time, and the names stuck.

        def close_animation_callback() -> None:
            if remove:
                self._execute_remove()
            else:
                self.display = False
                self.post_message(self.Minimized(self))
                self.manager.signal_window_state(self, False)

        if self.display:  # only do work if its currently displayed
            if self.animated:
                self.styles.animate(
                    "opacity",
                    0.0,
                    duration=self.animation_duration,
                    on_complete=close_animation_callback,
                )
            else:  # if not animated, invoke callback immediately:
                close_animation_callback()
        else:  # if not displayed, check if it was a removal call:
            if remove:
                self._execute_remove()

    def _open_animation(self) -> None:

        self.display = True
        if self.animated:
            self.styles.animate("opacity", 1.0, duration=self.animation_duration)
        self.post_message(self.Opened(self))
        self.manager.signal_window_state(self, True)

    async def _on_mouse_down(self, event: events.MouseDown) -> None:
        await super()._on_mouse_down(event)
        self.bring_forward()

    #! OVERRIDE
    def _on_focus(self, event: events.Focus) -> None:
        self.manager.change_window_focus_order(self)
        if self.auto_bring_forward:
            self.bring_forward()
        super()._on_focus(event)

    #! OVERRIDE
    @property
    def id(self) -> str:
        """The ID of this node.
        This property is overridden from DOMnode because `id` cannot be none in the Window class."""
        return self._id

    # Also an override (part of the above)
    @id.setter
    def id(self, new_id: str) -> str:
        """Sets the ID (may only be done once).

        Args:
            new_id: ID for this node.

        Raises:
            ValueError: If the ID has already been set.
        """
        check_identifiers("id", new_id)
        self._nodes.updated()
        if self._id:  # ~ this line was modified (empty string instead of None)
            raise ValueError(f"Node 'id' attribute may not be changed once set (current id={self._id!r})")
        self._id = new_id
        return new_id

    @property
    def name(self) -> str:
        """The name of the node.
        This property is overridden from DOMnode because `name` cannot be none in the Window class."""
        return self._name

    # These two event handlers below will ensure that the window maintains its
    # focused style when its descendants/children inside the window are focused.
    # So in other words, the window will stay highlighted even when you're actually focused
    # on the window's children/interior contents.
    @on(events.DescendantFocus)
    def descendant_focused(self, event: events.DescendantFocus) -> None:

        self.query_one(TopBar).add_class("focused")
        self.query_one(BottomBar).add_class("focused")
        self.query_one("#content_pane").add_class("focused")

    @on(events.DescendantBlur)
    def descendant_blurred(self, event: events.DescendantBlur) -> None:

        self.query_one(TopBar).remove_class("focused")
        self.query_one(BottomBar).remove_class("focused")
        self.query_one("#content_pane").remove_class("focused")

    ####################
    # ~ WATCH METHODS ~#
    ####################

    def watch_snap_state(self, value: bool) -> None:

        if value:
            self.clamp_into_parent_area()

    def watch_open_state(self, value: bool) -> None:

        if value:
            self._open_animation()
            if self.auto_focus:
                self.focus()
        else:
            self._close_animation(remove=False)
            self.query(Widget).blur()

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
        # Either closes or minimizes depending on the window's `window_mode` setting.
        if self.window_mode == "temporary":
            self.close_window()
        else:  # permanent
            self.open_state = False

    def action_minimize_window(self) -> None:
        self.open_state = False

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

    def remove_window(self) -> None:
        """This will remove the window from the DOM and the Window Bar."""
        self._close_animation(remove=True)

    def close_window(self) -> None:
        """Alias for remove_window. (You may be looking for `Window.minimize`).
        This will remove the window from the DOM and the Window Bar."""
        self.remove_window()

    def open_window(self) -> None:
        """Runs the open animation (if animate=True), and brings the window forward
        (if `auto_bring_forward` is set to True on the window)."""
        self.open_state = True

    def toggle_window(self) -> None:
        """Toggle the window open and closed."""
        self.open_state = not self.open_state

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

    def minimize(self) -> None:
        """This will close the window, but not remove it from the DOM.
        Runs the close animatiom and blurs all children."""
        self.open_state = False

    def restore(self) -> None:
        """(Opposite of maximize) Restore the window to its previous size and position."""
        self.maximize_state = False

    def toggle_maximize(self) -> None:
        """Toggle the window between its maximum size and its previous size."""
        self.maximize_state = not self.maximize_state

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

    async def reset_window(self) -> None:
        """Reset the window to its starting position and size."""

        await self.reset_size()
        await self.reset_position()
        self.snap_state = self.starting_snap_state

        if self.start_open:
            self.open_state = True
        else:
            self.open_state = False

    async def reset_size(self) -> None:
        """Reset the window size to its starting size."""

        size, min_size, max_size = await self._calculate_all_sizes()
        self.styles.width = size.width
        self.styles.height = size.height
        self.min_width = min_size.width
        self.min_height = min_size.height
        self.max_width = max_size.width
        self.max_height = max_size.height

    async def reset_position(self) -> None:
        """Reset the window position to its starting position."""

        self.offset = await self._calculate_starting_position()

    def clamp_into_parent_area(self) -> None:
        """This function returns the widget into its parent area. \n
        There shouldn't be any need to call this manually, but it is here if you need it."""

        if self.initialized:
            assert isinstance(self.parent, Widget)
            x, y = self.parent.size - self.size
            self.offset = Offset(clamp(self.offset.x, 0, x), clamp(self.offset.y, 0, y))

    def mount_in_window(
        self,
        *widgets: Widget,
        before: int | str | Widget | None = None,
        after: int | str | Widget | None = None,
    ) -> AwaitMount:
        """Mount widgets inside of the window. \n
        Do not use `mount` or `mount_all` to mount widgets inside of the window.
        Use this (or `mount_all_in_window`) instead.

        Args:
            *widgets: The widget(s) to mount.
            before: Optional location to mount before. An `int` is the index
                of the child to mount before, a `str` is a `query_one` query to
                find the widget to mount before.
            after: Optional location to mount after. An `int` is the index
                of the child to mount after, a `str` is a `query_one` query to
                find the widget to mount after.

        Returns:
            An awaitable object that waits for widgets to be mounted.

        Raises:
            MountError: If there is a problem with the mount request.

        Note:
            Only one of ``before`` or ``after`` can be provided. If both are
            provided a ``MountError`` will be raised.
        """

        return self._content_pane.mount(
            *widgets,
            before=before,
            after=after,
        )

    def mount_all_in_window(
        self,
        widgets: Iterable[Widget],
        *,
        before: int | str | Widget | None = None,
        after: int | str | Widget | None = None,
    ) -> AwaitMount:
        """Mount widgets from an iterable into the Window. \n
        Do not use `mount` or `mount_all` to mount widgets inside of the window.
        Use this (or `mount_in_window`) instead.

        Args:
            widgets: An iterable of widgets.
            before: Optional location to mount before. An `int` is the index
                of the child to mount before, a `str` is a `query_one` query to
                find the widget to mount before.
            after: Optional location to mount after. An `int` is the index
                of the child to mount after, a `str` is a `query_one` query to
                find the widget to mount after.

        Returns:
            An awaitable object that waits for widgets to be mounted.

        Raises:
            MountError: If there is a problem with the mount request.

        Note:
            Only one of ``before`` or ``after`` can be provided. If both are
            provided a ``MountError`` will be raised.
        """
        return self._content_pane.mount_all(
            widgets,
            before=before,
            after=after,
        )

    def remove_children_in_window(
        self,
        selector: str | type[QueryType] | Iterable[Widget] = "*",
    ) -> AwaitRemove:
        """Remove the widgets inside of this window from the DOM.

        Args:
            selector: A CSS selector or iterable of widgets to remove.

        Returns:
            An awaitable object that waits for the widgets to be removed.
        """

        return self._content_pane.remove_children(selector)
