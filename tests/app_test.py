"""Module for the textual-window demo app."""

# ~ Type Checking (Pyright and MyPy) - Strict Mode
# ~ Linting - Ruff
# ~ Formatting - Black - max 110 characters / line

# Python imports:
from __future__ import annotations

# Textual imports:
from textual.app import App, ComposeResult
from textual.widget import Widget
from textual.containers import Container, Horizontal
from textual.widgets import Button, TextArea, Static, Checkbox

# Local imports:
from textual_window import Window, WindowBar, WindowSwitcher
from textual_window.window import WindowStylesDict


lorem_ipsum = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. \
Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. \
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut \
aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in \
voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint \
occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit \
anim id est laborum."""


class MyWindow(Window):

    window_styles: WindowStylesDict = {
        "width": 16,  #         default is 25
        "height": 7,  #         default is 12
        "max_width": 20,  #     default is 'size of the parent container'
        "max_height": 10,  #    default is 'size of the parent container'
        "min_width": 16,  #     default is 12
        "min_height": 7,  #     default is 6
    }

    def __init__(self) -> None:
        super().__init__(
            id="window_2",
            allow_resize=True,
            start_open=True,
            starting_horizontal="right",
            starting_vertical="bottom",
            styles_dict=self.window_styles,
        )


class WindowTestApp(App[None]):

    CSS= """
    Button { &:focus {text-style: none;} }
    #main_container { 
        align: center middle; 
        background: transparent;
        hatch: cross $surface-lighten-1;
    } 
    #window_0 {                         
        width: 30; height: 14;      
        min-width: 22; min-height: 13;      
        max-width: 40; max-height: 20;      
    }                                       
    #window_1 { width: 35; height: 16; }    
    .spacer { width: 1fr; }
    .button_container { height: 3; padding: 0 1; }
    """

    def compose(self) -> ComposeResult:

        yield WindowSwitcher()
        yield WindowBar(start_open=True)

        with Container(id="main_container"):
            # 1) Context manager:
            with Window(
                id="window_0",
                starting_horizontal="centerleft",
                starting_vertical="middle",
                start_open=True,
            ):
                yield TextArea(id="input1")
                with Horizontal(classes="button_container"):
                    yield Static(classes="spacer")
                    yield Button("Submit", id="button1")

            # 2) Pass a list of widgets to the constructor:
            window_widgets: list[Widget] = [Static(lorem_ipsum), Checkbox("I have read the above")]
            yield Window(
                *window_widgets,
                id="window_1",
                starting_horizontal="right",
                starting_vertical="uppermiddle",
                start_open=True,
                allow_maximize=True,
            )

            # 3) Custom widget with compose method:
            yield MyWindow()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.query_one("#window_1").focus()

def run_demo() -> None:
    WindowTestApp().run()


if __name__ == "__main__":
    run_demo()
