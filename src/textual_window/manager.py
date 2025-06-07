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

from __future__ import annotations
from typing import TYPE_CHECKING  # , Any

if TYPE_CHECKING:
    # from textual.app import App
    from textual_window.window import Window
    from textual_window.windowbar import WindowBar
# import asyncio
# from collections import deque

# from textual.css.query import NoMatches
# from textual import work
# from textual._context import NoActiveAppError  # type: ignore[unused-ignore]
from textual.dom import DOMNode

# Note: all type ignores with 'unused-ignore' are because Pyright and MyPy
# disagree with each other about whether the line is actually an error.
# Pyright says it is because of the private attribute access. But MyPy
# does not seem to care about this (even in strict mode).


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

        #! self.windows could possibly be reactive?
        self.windows: dict[str, Window] = {}  # Dictionary to store windows by their ID
        self.last_focused_window: Window | None = None
        self.windowbar: WindowBar | None = None
        self.recent_focus_order: list[Window] = []

    def register_windowbar(self, windowbar: WindowBar) -> None:
        """Register the windowbar with the manager. This is done automatically when the
        windowbar is mounted. You shouldn't need to call this manually.

        Note that there can only be one windowbar in the app. If you try to mount a second
        windowbar, it will raise an error. It is not designed to be used that way.
        Multiple windowbars with different windows on them is an interesting idea, but it's not
        currently supported."""

        if not self.windowbar:
            self.log.debug("func register_windowbar: Registering windowbar with the manager.")
            self.windowbar = windowbar
        else:
            raise RuntimeError(
                "There is already a WindowBar registered with the WindowManager. "
                "You cannot have more than one WindowBar in the app."
            )

    def register_window(self, window: Window) -> None:
        """Used by windows to register with the manager.
        Windows do this automatically when they are mounted. There should not be any
        need to call this method manually."""

        if window.id:
            self.windows[window.id] = window
        else:
            raise ValueError(
                "Window ID is not set. "
                "Please set the ID of the window before registering it with the manager."
            )
        self.recent_focus_order.append(window)

    def window_ready(self, window: Window) -> None:
        if self.windowbar:
            self.windowbar._add_window(window)  # type: ignore[unused-ignore]

    def remove_window(self, window: Window) -> None:
        """Used by windows to unregister with the manager.
        Windows do this automatically when they are unmounted. There should not be any
        need to call this method manually."""

        if window.id in self.windows:
            self.windows.pop(window.id)
            self.log.debug(f"func remove_window: Unregistered {window.id} from the manager.")
        else:
            raise ValueError(
                "Window ID not found in the manager. "
                "Please make sure the window is registered with the manager before unregistering it."
            )
        self.recent_focus_order.remove(window)

        if self.windowbar:
            self.windowbar._remove_window(window)  # type: ignore[unused-ignore]
        else:
            self.log.debug("func windowbar_build_buttons: App does not have a WindowBar. ")

    def get_windows_as_dict(self) -> dict[str, Window]:
        """Get a dictionary of all windows."""
        return self.windows

    def get_windows_as_list(self) -> list[Window]:
        """Get a list of all windows."""

        windows = [window for window in self.windows.values()]
        return windows

    def change_focus_order(self, window: Window) -> None:
        """This is used by the WindowSwitcher to display the windows
        in the order they were focused."""

        if self.recent_focus_order:
            self.recent_focus_order.remove(window)
            self.recent_focus_order.insert(0, window)
        else:
            raise RuntimeError("No recent focus order found. Please make sure the DOM is ready.")

    def open_all_windows(self) -> None:
        for window in self.windows.values():
            window.open_state = True

    def close_all_windows(self) -> None:
        windows_copy = self.windows.copy()

        for window in windows_copy.values():
            if window.window_mode == "temporary":
                window.remove_window()
            else:
                window.open_state = False

    def minimize_all_windows(self) -> None:
        for window in self.windows.values():
            window.open_state = False

    def snap_all_windows(self) -> None:
        """Snap/Lock all windows."""
        for window in self.windows.values():
            window.snap_state = True

    def unsnap_all_windows(self) -> None:
        """Unsnap/Unlock all windows."""
        for window in self.windows.values():
            window.snap_state = False

    def reset_all_windows(self) -> None:
        """Reset all windows to their starting position and size."""
        for window in self.windows.values():
            window.reset_window()

    def reset_all_window_positions(self) -> None:
        """Reset all windows to their starting position."""
        for window in self.windows.values():
            window.reset_position()

    def reset_all_windows_size(self) -> None:
        """Reset all windows to their starting size."""
        for window in self.windows.values():
            window.reset_size()

    def calculate_all_max_sizes(self) -> None:
        """Calculate the maximum size of all windows."""
        for window in self.windows.values():
            window._calculate_max_min_sizes()  # type: ignore[unused-ignore]

    def debug(self) -> None:
        """Log self.windows and self.app on the WindowManager to console."""
        self.log.debug(self.windows)
        self.log.debug(f"Layers: \n{self.app.screen.styles.layers}")


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
