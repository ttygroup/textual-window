"""Module for the textual-window demo app."""

# ~ Type Checking (Pyright and MyPy) - Strict Mode
# ~ Linting - Ruff
# ~ Formatting - Black - max 110 characters / line

# Python imports:
from __future__ import annotations
from typing import cast

# Textual imports:
from textual.app import App, ComposeResult
from textual import on
from textual.binding import Binding
from textual.widget import Widget
from textual.containers import Container, Horizontal
from rich.text import Text
from textual.widgets import (
    # Header,
    Footer,
    Button,
    TextArea,
    RichLog,
    Static,
    Switch,
    Checkbox,
)

# Local imports:
from textual_window import Window, WindowBar, WindowSwitcher


lorem_ipsum = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. \
Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. \
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut \
aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in \
voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint \
occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit \
anim id est laborum."""

static_info = """Try right-clicking the buttons on the WindowBar (below) to see \
window-specific context menus. You can also left or right-click on the WindowBar itself to \
see a global context menu."""


class MyWindow(Window):

    def compose(self) -> ComposeResult:

        yield Switch(id="switch1")

    @on(Switch.Changed)
    def switch_changed(self, event: Switch.Changed) -> None:

        richlog = cast(RichLog, self.app.query_one("#rich_log"))
        richlog.write(f"Switch changed to {event.value}")


class WindowDemo(App[None]):

    CSS = """
    RichLog { border: outer $secondary; width: 80%; height: 4fr; margin: 2 0;}
    # WindowBar { dock: top; }       /* Setting dock here will override the constructor setting */
    #main_container { align: center middle; }
    #center_content { align: center middle; }
    #info_container { 
        width: 80%; height: 1fr;
        content-align: center middle;
        border: solid $primary;
        margin: 0 0 1 0; padding: 0 1;
    }
    #window0 {                         
        width: 25; height: 13;      
        min-width: 22; min-height: 13;      /* These min and max settings will be respected */
        max-width: 40; max-height: 20;      /* when the window is resized */
    }                                       /* The default min w/h is 12/6 */
    #window1 { width: 35; height: 16; }     /* The default max w/h is the size of the parent container */
    #window2 { width: 15; height: 7; min-width:14 ; min-height: 7;}
    .spacer { width: 1fr; }
    .button_container { height: 3; padding: 0 1; }
    .bar_button { width: auto; height: 1; padding: 0 2; } 
    """

    BINDINGS = [
        Binding("ctrl+e", "toggle_windowbar", "Window Bar"),
        Binding("f1", "toggle_switcher", "Window Switcher", key_display="F1"),
    ]

    app_initialized: bool = False

    def compose(self) -> ComposeResult:

        window1_menu_options = {
            "Callback 1": self.callback_1,
            "Callback 2": self.callback_2,
        }

        yield WindowSwitcher()
        yield WindowBar(start_open=True)  # If you have either a Header or Footer, WindowBar Must go
        # yield Header()         # before them in the compose method. Otherwise it will cover them up.

        with Container(id="main_container"):

            # * There are 3 different ways to add children to a widget in Textual,
            # 1) Context manager
            # 2) Pass a list of widgets to the constructor
            # 3) Custom widget with compose method
            # and all of them work with the Window widget:

            # 1) Context manager:
            with Window(
                id="window0",
                name="Window 0",
                starting_horizontal="center",
                starting_vertical="uppermiddle",
            ):
                yield TextArea(id="input1")
                with Horizontal(classes="button_container"):
                    yield Static(classes="spacer")
                    yield Button("Submit", id="button1")

            # 2) Pass a list of widgets to the constructor:
            window_widgets: list[Widget] = [Static(lorem_ipsum), Checkbox("I have read the above")]
            yield Window(
                *window_widgets,
                id="window1",
                name="Window 1",
                starting_horizontal="left",
                starting_vertical="middle",
                show_maximize_button=True,
                menu_options=window1_menu_options,
            )

            # 3) Custom widget with compose method:
            yield MyWindow(
                id="window2",
                name="Window 2",
                allow_resize=False,
                animated=False,  # animated=False will disable the Fade effect.
                starting_horizontal="centerright",
                starting_vertical="lowermiddle",
                start_open=False,
            )

            with Container(id="center_content"):
                self.rich_log = RichLog(id="rich_log")
                yield self.rich_log
                yield Static(static_info, id="info_container")

        # yield WindowBar()      # If you have either a Header or Footer, WindowBar Must go
        yield Footer()  # before them in the compose method. Otherwise it will cover them up.

    def on_mount(self) -> None:
        main_container = self.query_one("#main_container")
        main_container.styles.opacity = 0.0  # Chad loading screen
        self.query_one(RichLog).can_focus = False

    ################################
    # ~ Hamburger Menu Callbacks ~ #
    ################################

    def callback_1(self) -> None:
        self.rich_log.write("Callback 1")

    def callback_2(self) -> None:
        self.rich_log.write("Callback 2")
        self.notify("Callback 2")

    #################################
    # ~ Window Events and Actions ~ #
    #################################

    def action_toggle_windowbar(self) -> None:

        windowbar = self.query_one(WindowBar)
        windowbar.toggle_bar()

    def action_toggle_switcher(self) -> None:

        cycler = self.query_one(WindowSwitcher)
        cycler.show()

    @on(Window.Closed)
    def window_closed(self, event: Window.Closed) -> None:

        self.rich_log.write(Text.from_markup(f"{event.window.id} [red]closed."))

    @on(Window.Opened)
    def window_opened(self, event: Window.Opened) -> None:

        self.rich_log.write(Text.from_markup(f"{event.window.id} [green]opened."))

    @on(Window.Initialized)
    def window_initialized(self, event: Window.Initialized) -> None:

        # Generally speaking, once one window is initialized, you can be confident
        # they're all ready to go and you can disable any loading screen you might have.

        self.rich_log.write(Text.from_markup(f"{event.window.id} [blue]initialized."))
        self.log(f"{event.window.id} initialized.")

        if not self.app_initialized:
            main_container = self.query_one("#main_container")
            main_container.styles.animate("opacity", value=1.0, duration=0.5)  # Chad loading screen
            self.app_initialized = True

    ####################
    # ~ Other Events ~ #
    ####################

    @on(Button.Pressed, "#button1")
    def button1_pressed(self) -> None:

        textarea = cast(TextArea, self.query_one("#input1"))
        self.rich_log.write(textarea.text)
        textarea.text = ""

    @on(Checkbox.Changed)
    def checkbox_changed(self, event: Checkbox.Changed) -> None:

        self.rich_log.write(f"Checkbox changed to {event.value}")


def run_demo() -> None:
    WindowDemo().run()


if __name__ == "__main__":
    run_demo()
