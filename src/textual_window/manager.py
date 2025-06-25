"""Module for the Window Manager.

You don't need to import from this module. You can simply do:
`from textual_window import window_manager`.
It is a singleton. Do not use the WindowManager class directly.

Note that you can also access the window manager from any window,
or the Window Bar, with `self.manager`. The same instance is attached
to all of them."""

# ~ Type Checking (Pyright and MyPy) - Strict Mode
# ~ Linting - Ruff
# ~ Formatting - Black - max 110 characters / line

# Python imports
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual_window.window import Window
    from textual_window.windowbar import WindowBar
    from textual_window.switcher import WindowSwitcherScreen
    import rich.repr

# Textual imports
from textual.dom import DOMNode
# from rich.text import Text

__all__ = [
    "window_manager",
]


class WindowManager(DOMNode):
    """! Do not import this class directly. Use the `window_manager` instance instead.

    This class is the blueprint for a singleton instance used internally by the
    library for all of the windows to register themselves, so they can appear automatically
    on the WindowBar. The library is designed so there is no need for you to interact
    directly with the manager.

    Everything this manager does is fully automated. There shouldn't be any real need
    to use or interact with it directly. It is used by windows and the WindowBar to
    manage everything.

    If you want to interact with the window manager directly for some reason, you can
    import the `window_manager` instance:
    ```py
    from textual_window import window_manager
    ```"""

    def __init__(self) -> None:
        super().__init__()

        #! self._windows could possibly be reactive?
        self._windows: dict[str, Window] = {}  # Dictionary to store windows by their ID
        self._last_focused_window: Window | None = None
        self._windowbar: WindowBar | None = None
        self._recent_focus_order: list[Window] = []

        # These 3 variables are just used to keep track of the closing process.
        # All 3 get reset every time the process finishes.
        self._closing_in_progress = False
        self._num_of_temporary_windows = 0
        self._checked_in_closing_windows = 0

    ##################
    # ~ Properties ~ #
    ##################

    @property
    def windows(self) -> dict[str, Window]:
        """Get the dictionary of all windows."""
        return self._windows
    
    @property
    def windowbar(self) -> WindowBar | None:
        """Get the windowbar instance."""
        return self._windowbar
    
    used_by: type[WindowSwitcherScreen]  # methods: [compose]
    @property
    def recent_focus_order(self) -> list[Window]:
        """Get the list of windows in the order they were most recently focused."""
        return self._recent_focus_order
    
    used_by: type[WindowSwitcherScreen]  # methods: [action_confirm]
    @property
    def last_focused_window(self) -> Window | None:
        """Get the last focused window."""
        return self._last_focused_window    
    
    #########################
    # ~ WindowBar Methods ~ #
    #########################

    called_by_2: type[WindowBar]  # methods: [__init__]
    def register_windowbar(self, windowbar: WindowBar) -> None:
        """Register the windowbar with the manager. This is done automatically when the
        windowbar is mounted. You shouldn't need to call this manually.

        Note that there can only be one windowbar in the app. If you try to mount a second
        windowbar, it will raise an error. It is not designed to be used that way.
        Multiple windowbars with different windows on them is an interesting idea, but it's not
        currently supported."""

        if not self._windowbar:
            self.log.debug("func register_windowbar: Registering windowbar with the manager.")
            self._windowbar = windowbar
        else:
            raise RuntimeError(
                "There is already a WindowBar registered with the WindowManager. "
                "You cannot have more than one WindowBar in the app."
            )
        
    called_by: type[Window]  # methods: [_dom_ready, _open_animation, _close_animation]
    def signal_window_state(self, window: Window, state: bool) -> None:
        """This method triggers the WindowBar to update the window's button on the bar
        when a window is minimized or maximized to show its current state (adds or
        removes the dot.)"""
        if self._windowbar:
            self._windowbar.update_window_button_state(window, state)        

    ######################
    # ~ Window Methods ~ #
    ######################

    called_by: type[Window]  # methods: [_dom_ready]
    async def window_ready(self, window: Window) -> bool | None:

        if self._windowbar:
            button_worker = self._windowbar.add_window_button(window)  # type: ignore[unused-ignore]
            await button_worker.wait()
            return True
        else:
            return None

    called_by: type[Window]  # methods: [__init__]
    def register_window(self, window: Window) -> None:
        """Used by windows to register with the manager.
        Windows do this automatically when they are mounted. There should not be any
        need to call this method manually."""

        if window.id:
            self._windows[window.id] = window
        else:
            raise ValueError(
                "Window ID is not set. "
                "Please set the ID of the window before registering it with the manager."
            )
        self._recent_focus_order.append(window)

    called_by: type[Window]  # methods: [_execute_remove]
    def unregister_window(self, window: Window) -> None:
        """Used by windows to unregister with the manager.
        Windows do this automatically when they are unmounted. There should not be any
        need to call this method manually."""

        if window.id in self._windows:
            self._windows.pop(window.id)
            self.log.debug(f"func unregister_window: Unregistered {window.id} from the manager.")
        else:
            raise ValueError(
                "Window ID not found in the manager. "
                "Please make sure the window is registered with the manager before unregistering it."
            )
        self._recent_focus_order.remove(window)

        if self._windowbar:
            self._windowbar.remove_window_button(window)  # type: ignore[unused-ignore]

        if self._closing_in_progress:
            if window.window_mode == "temporary":  # <- this shouldn't be necessary.
                self._checked_in_closing_windows += 1

            if self._checked_in_closing_windows == self._num_of_temporary_windows:
                self._checked_in_closing_windows = 0
                self._num_of_temporary_windows = 0
                self.call_after_refresh(lambda: setattr(self, "closing_in_progress", False))
    
    called_by: type[Window]  # methods: [_on_focus]
    def change_focus_order(self, window: Window) -> None:
        """recent_focus_order attribute is read by the WindowSwitcher to display
         the windows in the order they were most recently focused."""

        if self._recent_focus_order:
            self._recent_focus_order.remove(window)
            self._recent_focus_order.insert(0, window)
        else:
            if not self._closing_in_progress:
                raise RuntimeError(
                    "No windows in the recent focus order. "
                    "This should not happen. Please report this issue."
                )
        self._last_focused_window = window

    def __rich_repr__(self) -> rich.repr.Result:
        yield "windows", self._windows
        yield "layers", self.app.screen.styles.layers

    called_by_3: type[WindowSwitcherScreen]  # methods: [__init__]
    def get_windows_as_dict(self) -> dict[str, Window]:
        """Get a dictionary of all windows."""
        return self._windows

    called_by_2: type[WindowBar]  # methods: [_on_resize]
    def get_windows_as_list(self) -> list[Window]:
        """Get a list of all windows."""

        windows = [window for window in self._windows.values()]
        return windows

    #############################
    # ~ Actions for all windows ~
    #############################

    called_by_2: type[WindowBar]  # methods: [button_pressed]
    def open_all_windows(self) -> None:
        """Open all windows."""
        for window in self._windows.values():
            window.open_state = True

    called_by_2: type[WindowBar]  # methods: [button_pressed]
    def close_all_windows(self) -> None:
        """Close all windows. This will close all temporary windows and
        minimize all permanent windows."""

        # First we need to count how many temporary windows there are.
        # It counts them as they unregister so it knows when it can set
        # closing_in_progress back to False.
        self._num_of_temporary_windows = len(
            [w for w in self._windows.values() if w.window_mode == "temporary"]
        )

        # This makes a copy because otherwise it would get smaller
        # while iterating over it.
        windows_copy = self._windows.copy()

        self._closing_in_progress = True
        for window in windows_copy.values():
            if window.window_mode == "temporary":
                window.remove_window()
            else:
                window.open_state = False

    called_by_2: type[WindowBar]  # methods: [button_pressed]
    def minimize_all_windows(self) -> None:
        """Minimize all windows."""
        for window in self._windows.values():
            window.open_state = False

    called_by_2: type[WindowBar]  # methods: [button_pressed]
    def snap_all_windows(self) -> None:
        """Snap/Lock all windows."""
        for window in self._windows.values():
            window.snap_state = True

    called_by_2: type[WindowBar]  # methods: [button_pressed]
    def unsnap_all_windows(self) -> None:
        """Unsnap/Unlock all windows."""
        for window in self._windows.values():
            window.snap_state = False

    called_by_2: type[WindowBar]  # methods: [button_pressed]
    async def reset_all_windows(self) -> None:
        """Reset all windows to their starting position and size."""
        for window in self._windows.values():
            await window.reset_window()


window_manager = WindowManager()  # ~ <-- Create a window manager instance.
"""Global Window Manager for all the windows in the application.  
This is a singleton instance that can be used throughout the application to manage
windows. It is used by the WindowBar widget to display all windows on the bar and let
you manage them, and it is also attached to each window with the self.manager attribute.  
It is not necessary to use the manager instance directly. However, it is
available to import if you want to use it for whatever reason.

To import:
```python
from textual_window import window_manager
```
"""
