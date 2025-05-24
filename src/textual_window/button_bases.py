from __future__ import annotations
from typing import Any
from textual import events
from textual.widgets import Static
from textual.message import Message

class NoSelectStatic(Static):

    @property
    def allow_select(self) -> bool:
        return False
    

class ButtonStatic(NoSelectStatic):

    class Pressed(Message):
        def __init__(self, button: ButtonStatic) -> None:
            super().__init__()
            self.button = button

        @property
        def control(self) -> ButtonStatic:
            return self.button
        
    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
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

