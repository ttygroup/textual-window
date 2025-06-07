"""Module for the button base classes used in the textual-window package."""

from __future__ import annotations

from textual.visual import VisualType
from textual import events
from textual.widgets import Static
from textual.message import Message


class NoSelectStatic(Static):
    """This class is used in window.py and windowbar.py to create buttons."""

    @property
    def allow_select(self) -> bool:
        return False


class ButtonStatic(NoSelectStatic):
    """This class is used in window.py, windowbar.py, and switcher.py to create buttons."""

    class Pressed(Message):
        def __init__(self, button: ButtonStatic) -> None:
            super().__init__()
            self.button = button

        @property
        def control(self) -> ButtonStatic:
            return self.button

    def __init__(
        self,
        content: VisualType = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        markup: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            content=content,
            expand=expand,
            shrink=shrink,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.click_started_on: bool = False

    def on_mouse_down(self, event: events.MouseDown) -> None:

        self.add_class("pressed")
        self.click_started_on = True

    def on_mouse_up(self, event: events.MouseUp) -> None:

        self.remove_class("pressed")
        if self.click_started_on:
            self.post_message(self.Pressed(self))
            self.click_started_on = False

    def on_leave(self, event: events.Leave) -> None:

        self.remove_class("pressed")
        self.click_started_on = False
