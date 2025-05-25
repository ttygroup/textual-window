"""Module for the Window Manager.

You don't need to import from this module. You can simply do:
`from textual_window import window_manager`.
It is a singleton. Do not use the WindowManager class directly."""

# ~ Type Checking (Pyright and MyPy) - Strict Mode
# ~ Linting - Ruff
# ~ Formatting - Black - max 110 characters / line

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from textual_window.window import Window
    from textual_window.windowbar import WindowBar
import asyncio
from collections import deque

# from textual.css.query import NoMatches
from textual import work
from textual._context import NoActiveAppError  # type: ignore[unused-ignore]
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

    If you want to interact with the window manager directly for some reason, you can
    import the `window_manager` instance:
    ```py
    from textual_window import window_manager
    ```"""

    def __init__(self) -> None:
        super().__init__()

        self.windows: dict[str, Window] = {}  # Dictionary to store windows by their ID
        self.ready = False
        self.watching_started = False
        self.windowbar: WindowBar | None = None
        self.recent_focus_order: deque[Window] | None = None

    def add_window(self, window: Window) -> None:
        """Used by windows to register with the manager.
        Windows do this automatically when they are mounted. There should not be any
        need to call this method manually."""

        if window.name:
            self.windows[window.name] = window
        else:
            raise ValueError(
                "Window name is not set. "
                "Please set the name of the window before registering it with the manager."
            )

    def remove_window(self, window: Window) -> None:
        """Used by windows to unregister with the manager.
        Windows do this automatically when they are unmounted. There should not be any
        need to call this method manually."""

        if window.name in self.windows:
            self.windows.pop(window.name)
        else:
            raise ValueError(
                "Window name not found in the manager. "
                "Please make sure the window is registered with the manager before unregistering it."
            )

    def get_windows_as_dict(self) -> dict[str, Window]:
        """Get a dictionary of all windows."""
        return self.windows

    def get_windows_as_list(self) -> list[Window]:
        """Get a list of all windows."""

        windows = [window for window in self.windows.values()]
        return windows

    def rebuild_windows_dict(self) -> None:
        """Rebuild the windows dictionary. This is not used anywhere by the library itself,
        but it is here for convenience if you can find a reason for it.

        This will query the app for all windows in the app."""

        self.windows.clear()
        windows = self.app.query(Window)
        for window in windows:
            if window.name:
                self.windows[window.name] = window
            else:
                raise ValueError(
                    "Window name is not set. "
                    "Please set the name of the window before registering it with the manager."
                )

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

    def append_focus_order(self, window: Window) -> None:
        """Append a window to the focus order. This is used by the WindowSwitcher to
        display the windows in the order they were focused."""

        if self.recent_focus_order:
            self.recent_focus_order.remove(window)
            self.recent_focus_order.appendleft(window)
        else:
            raise RuntimeError("No recent focus order found. Please make sure the DOM is ready.")

    async def windowbar_build_buttons(self) -> None:

        if self.windowbar:
            await self.windowbar.build_window_buttons()
        else:
            self.log.debug("func windowbar_build_buttons: App does not have a WindowBar. ")

    def open_all_windows(self) -> None:
        for window in self.windows.values():
            window.open_state = True

    def close_all_windows(self) -> None:
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
            window._calculate_max_size()  # type: ignore[unused-ignore]

    def debug(self) -> None:
        """Log self.windows and self.app on the WindowManager to console."""
        self.log.debug(self.windows)
        self.log.debug(f"Layers: \n{self.app.screen.styles.layers}")

    def watch_for_dom_ready_runner(self) -> None:

        if not self.watching_started:
            self.watching_started = True
            self.watch_for_dom_ready()

    @work(group="window_manager")
    async def watch_for_dom_ready(self) -> None:

        try:
            self.ready = self.app._dom_ready  # type: ignore[unused-ignore]
        except NoActiveAppError:
            raise NoActiveAppError("No active app. Window manager has launched too early. Library bug.")
        except Exception as e:
            self.log.error(f"Error: {e}")
            raise e
        else:
            while not self.ready:
                await asyncio.sleep(0.2)
                self.ready = self.app._dom_ready  # type: ignore[unused-ignore]
                if not self.ready:
                    self.log("DOM not ready yet. Retrying...")

            self.log.debug("DOM is ready.")
            self.recent_focus_order = deque(maxlen=len(self.windows))
            self.recent_focus_order.extend(self.windows.values())
            self.reset_all_window_positions()  # Triggers the position calculation functions.
            self.calculate_all_max_sizes()
            await self.windowbar_build_buttons()


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
