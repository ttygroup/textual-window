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
from typing import TYPE_CHECKING, Callable, Awaitable

if TYPE_CHECKING:
    from textual_window.window import Window
    from textual_window.windowbar import WindowBar
    import rich.repr

# Library imports
from ezpubsub import Signal

# Textual imports
from textual import log

__all__ = [
    "window_manager",
]


class WindowManager:
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
        self._windowbar: WindowBar | None = None
        self._last_focused_window: Window | None = None
        self._recent_focus_order: list[Window] = []
        self._mounting_callbacks: dict[str, Callable[[Window], Awaitable[None]]] = {}

        # These 3 variables are just used to keep track of the closing process.
        # All 3 get reset every time the process finishes.
        self._closing_in_progress = False
        self._num_of_temporary_windows = 0
        self._checked_in_closing_windows = 0

        # ~ Signals ~ #

        self.signal_window_unregistered: Signal[Window] = Signal("window-unregistered")

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

    @property
    def last_focused_window(self) -> Window | None:
        """Get the last focused window."""
        # called by Window.action_confirm()
        return self._last_focused_window

    @last_focused_window.setter
    def last_focused_window(self, window: Window) -> None:
        """Set the last focused window."""
        # called by Window._on_focus()
        self._last_focused_window = window

    @property
    def recent_window_focus_order(self) -> list[Window]:
        """Get the list of windows in the order they were most recently focused."""
        # called by Window.compose()
        return self._recent_focus_order

    @property
    def mounting_callbacks(self) -> dict[str, Callable[[Window], Awaitable[None]]]:
        """Get the dictionary of mounting callbacks."""
        return self._mounting_callbacks

    #######################
    # ~ Container Methods #
    #######################

    def register_mounting_callback(
        self,
        callback: Callable[[Window], Awaitable[None]],
        callback_id: str,
    ) -> None:
        """Register a callback which can be used by the Window Manager to mount windows
        that are passed into it with the `mount_window` method.

        Args:
            callback (Callable[[Window], None]): The callback function that will be called
                when a window is mounted. It should accept a single argument, which is the
                `Window` instance to be mounted.
            callback_id (str): A unique identifier for the callback. This is used to identify the
                callback when mounting a window. It should be unique for each callback.
        Raises:
            KeyError: If a callback with the same ID already exists.

        """

        if callback_id in self._mounting_callbacks:
            log.warning(
                f"func register_mounting_callback: Callback with ID {callback_id} already exists. "
                "Overwriting the existing callback."
            )
        self._mounting_callbacks[callback_id] = callback
        log.debug(f"func register_mounting_callback: Registered mounting callback for {callback_id}.")

    async def mount_window(self, window: Window, callback_id: str) -> None:
        """Mount a window using a callback registered with the `register_mounting_callback`
        method.
        This allows the manager to handle the mounting of windows without needing to mount them
        directly into their destination. If you have a process manager of some sort that creates
        and manages windows, this allows the process manager to just send them to the window manager.

        Args:
            window (Window): The window to be mounted.
            callback_id (str): The ID of the callback to be used for mounting the window. This would be whatever
                ID you used when registering the callback with `register_mounting_callback`.
        Raises:
            KeyError: If no callback with the given ID is registered.
        """

        try:
            log.debug(f"func mount_window: Mounting window {window.id} with callback {callback_id}.")
            callback = self._mounting_callbacks[callback_id]
            await callback(window)
        except KeyError as e:
            log.error(
                f"func mount_window: No mounting callback registered for "
                f"ID '{callback_id}'. Window {window.id} was not mounted."
            )
            raise KeyError(f"No mounting callback registered for ID '{callback_id}'.") from e

    #########################
    # ~ WindowBar Methods ~ #
    #########################

    def register_windowbar(self, windowbar: WindowBar) -> None:
        """Register the windowbar with the manager. This is done automatically when the
        windowbar is mounted. You shouldn't need to call this manually.

        Note that there can only be one windowbar in the app. If you try to mount a second
        windowbar, it will raise an error. It is not designed to be used that way.
        Multiple windowbars with different windows on them is an interesting idea, but it's not
        currently supported."""
        # called by Window.__init__()

        if not self._windowbar:
            log.debug("func register_windowbar: Registering windowbar with the manager.")
            self._windowbar = windowbar
        else:
            raise RuntimeError(
                "There is already a WindowBar registered with the WindowManager. "
                "You cannot have more than one WindowBar in the app."
            )

    def unregister_windowbar(self) -> None:
        """Unregister the windowbar from the manager. This is done automatically when the
        windowbar is unmounted. You shouldn't need to call this manually."""
        # called by Window._on_unmount()

        if self._windowbar:
            log.debug("func unregister_windowbar: Unregistering windowbar from the manager.")
            self._windowbar = None
        else:
            raise RuntimeError(
                "There is no WindowBar registered with the WindowManager. "
                "You cannot unregister a WindowBar that is not registered."
            )

    def signal_window_state(self, window: Window, state: bool) -> None:
        """This method triggers the WindowBar to update the window's button on the bar
        when a window is minimized or maximized to show its current state (adds or
        removes the dot.)"""
        # called by Window._dom_ready(), _open_animation(), _close_animation()

        if self._windowbar:
            self._windowbar.update_window_button_state(window, state)

    ######################
    # ~ Window Methods ~ #
    ######################

    async def window_ready(self, window: Window) -> bool | None:
        # called by Window._dom_ready()

        if self._windowbar:
            button_worker = self._windowbar.add_window_button(window)  # type: ignore[unused-ignore]
            await button_worker.wait()
            return True
        else:
            return None

    def register_window(self, window: Window) -> None:
        """Used by windows to register with the manager.
        Windows do this automatically when they are mounted. There should not be any
        need to call this method manually."""
        # called by Window.__init__()

        if window.id:
            self._windows[window.id] = window
        else:
            raise ValueError(
                "Window ID is not set. "
                "Please set the ID of the window before registering it with the manager."
            )
        self._recent_focus_order.append(window)

    def unregister_window(self, window: Window) -> None:
        """Used by windows to unregister with the manager.
        Windows do this automatically when they are unmounted. There should not be any
        need to call this method manually."""
        # called by Window._execute_remove()

        if window.id in self._windows:
            self._windows.pop(window.id)
            log.debug(f"func unregister_window: Unregistered {window.id} from the manager.")
        else:
            raise ValueError(
                "Window ID not found in the manager. "
                "Please make sure the window is registered with the manager before unregistering it."
            )
        self._recent_focus_order.remove(window)

        if self._windowbar:
            self._windowbar.remove_window_button(window)

        self.signal_window_unregistered.publish(window)

        if self._closing_in_progress:
            # NOTE: Temporary windows will not be closed as part of the close_all_windows
            # process. But I'm leaving this check here just in case.
            # Technically there is nothing stopping a temporary window from being closed
            # if someone were to do it programattically.
            if window.window_mode == "temporary":  # <- this shouldn't be necessary
                self._checked_in_closing_windows += 1

            if self._checked_in_closing_windows == self._num_of_temporary_windows:
                self._checked_in_closing_windows = 0
                self._num_of_temporary_windows = 0
                self._closing_in_progress = False

        # ? Explanation of the above `_closing_in_progress` thing:
        # If the `close_all_windows` method is called, all of the windows will *first*
        # unregister themselves from the manager, and then they will all be removed.
        # This creates a problem: As Textual is actually unmounting windows from the DOM,
        # it will try to shift focus to the next window in Textual's internal focus order.
        # Windows automatically update the recent focus order when Textual focuses them.
        # However in this case, the _recent_focus_order list will be empty, since we empty it first.
        # Thus, we need a way to keep track of whether there is a 'closing in progress' or not.
        # If there is, then we know the list is empty because we are closing all windows.
        # Without this check, there would be no way to know if the list is empty because
        # of a closing in progress, or if it is empty because it is supposed to be empty.

    def change_window_focus_order(self, window: Window) -> None:
        """recent_focus_order attribute is read by the WindowSwitcher to display
        the windows in the order they were most recently focused."""
        # called by Window._on_focus()

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

    def get_windows_as_dict(self) -> dict[str, Window]:
        """Get a dictionary of all windows."""
        return self._windows

    def get_windows_as_list(self) -> list[Window]:
        """Get a list of all windows."""
        windows = [window for window in self._windows.values()]
        return windows

    #############################
    # ~ Actions for all windows ~
    #############################

    # These are all called by WindowBar.buttonpressed()
    jump_clicker: type[WindowBar]  # noqa: F842 # type: ignore

    def open_all_windows(self) -> None:
        """Open all windows."""

        for window in self._windows.values():
            window.open_state = True

    def close_all_windows(self) -> None:
        """Close all windows. This will close all temporary windows and
        minimize all permanent windows."""

        # First we need to count how many temporary windows there are.
        # It counts them as they unregister so it knows when it can set
        # closing_in_progress back to False.
        #! Note: maybe it should just know this info without needing to query for it?
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

    def minimize_all_windows(self) -> None:
        """Minimize all windows."""

        for window in self._windows.values():
            window.open_state = False

    def snap_all_windows(self) -> None:
        """Snap/Lock all windows."""

        for window in self._windows.values():
            window.snap_state = True

    def unsnap_all_windows(self) -> None:
        """Unsnap/Unlock all windows."""

        for window in self._windows.values():
            window.snap_state = False

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
