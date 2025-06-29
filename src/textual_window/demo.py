"""Module for the textual-window demo app."""

# ~ Type Checking (Pyright and MyPy) - Strict Mode
# ~ Linting - Ruff
# ~ Formatting - Black - max 110 characters / line

# Python imports:
from __future__ import annotations
from typing import get_args
import random

# Textual imports:
from textual.app import App, ComposeResult
from textual import on
from textual.binding import Binding
from textual.widget import Widget
from textual.containers import Container, Horizontal
from rich.text import Text
from textual.screen import Screen
from textual.widgets import (
    Header,
    # Footer,
    Button,
    TextArea,
    RichLog,
    Static,
    Switch,
    Checkbox,
)

# Local imports:
from textual_window import Window, WindowBar, WindowSwitcher
from textual_window.window import STARTING_HORIZONTAL, STARTING_VERTICAL, WindowStylesDict


lorem_ipsum = """Lorem ipsum dolor sit amet, consectetur adipiscing elit. \
Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. \
Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut \
aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in \
voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint \
occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit \
anim id est laborum."""

static_info = """Try right-clicking the buttons on the WindowBar (below) to see \
window-specific context menus. You can also left or right-click on the WindowBar itself to \
see a global context menu.
Note that for transparency to work, your terminal must support it and you must have it enabled. \
Also note that it's known to not look great if using any light themes or system settings."""

static_controls = """\
[$accent]F1[/$accent]: Window Switcher
[$accent]Ctrl+e[/$accent]: WindowBar
[$accent]Ctrl+d[/$accent]: Minimize window
[$accent]Ctrl+w[/$accent]: Close window
[$accent]Ctrl+q[/$accent]: Quit the app \
"""


class DummyScreen(Screen[None]):
    # This exists to force the screen to refresh when toggling the transparency.
    # It's a bit of a hack, but it works.

    def on_mount(self) -> None:
        self.dismiss()


class MyWindow(Window):

    # NOTE: If the given size is not within the confines set by
    # the min/max sizes, the window will be resized to fit within those limits.

    window_styles: WindowStylesDict = {
        "width": 16,  # default is 25
        "height": 7,  # default is 12
        "max_width": 20,  # default is 'size of the parent container'
        "max_height": 10,  # default is 'size of the parent container'
        "min_width": 16,  # default is 12
        "min_height": 7,  # default is 6
    }

    def __init__(self) -> None:
        super().__init__(
            id="window_2",
            allow_resize=True,
            starting_horizontal="right",
            starting_vertical="bottom",
            styles_dict=self.window_styles,
        )

    def compose(self) -> ComposeResult:

        yield Switch(id="switch1")

    @on(Switch.Changed)
    def switch_changed(self, event: Switch.Changed) -> None:

        richlog = self.app.query_one("#rich_log", RichLog)
        richlog.write(f"Switch changed to {event.value}")


class WindowDemo(App[None]):

    CSS_PATH = "demostyles.tcss"

    BINDINGS = [
        Binding("ctrl+e", "toggle_windowbar", "Window Bar"),
        Binding("f1", "toggle_switcher", "Window Switcher", key_display="F1"),
    ]

    app_initialized: bool = False

    def __init__(self) -> None:
        super().__init__()
        self.title = "Textual-Window Demo"
        self.window_counter = 3

    def compose(self) -> ComposeResult:

        window1_menu_options = {
            "Callback 1": self.callback_1,
            "Callback 2": self.callback_2,
        }

        yield WindowSwitcher()
        yield WindowBar(start_open=True)
        # If you have either a Header or Footer, WindowBar Must go
        # before them in the compose method. Otherwise it will cover them up.
        yield Header(show_clock=True, icon="⚙")

        with Container(id="main_container"):

            # * There are 3 different ways to add children to a widget in Textual,
            # 1) Context manager
            # 2) Pass a list of widgets to the constructor
            # 3) Custom widget with compose method
            # and all of them work with the Window widget:

            # 1) Context manager:
            with Window(
                id="window_0",
                icon="🏠",
                mode="permanent",
                starting_horizontal="centerleft",
                starting_vertical="middle",
                start_open=True,
            ):
                yield Static("This window is permanent. It can only be minimized.")
                yield TextArea(id="input1")
                with Horizontal(classes="button_container"):
                    yield Static(classes="spacer")
                    yield Button("Submit", id="button1")

            # 2) Pass a list of widgets to the constructor:
            window_widgets: list[Widget] = [Static(lorem_ipsum), Checkbox("I have read the above")]
            yield Window(
                *window_widgets,
                id="window_1",
                icon="✰",
                starting_horizontal="right",
                starting_vertical="uppermiddle",
                allow_maximize=True,
                menu_options=window1_menu_options,
            )

            # 3) Custom widget with compose method:
            yield MyWindow()

            with Container(id="center_content"):
                with Horizontal(id="main_info_container", classes="upper_info_container"):
                    with Horizontal(classes="upper_info_container left"):
                        yield RichLog(id="rich_log")
                    with Horizontal(classes="upper_info_container"):
                        yield Static(static_controls, classes="info_container controls")
                with Horizontal(classes="button_container"):
                    yield Button("Add Window", id="add_window", classes="bar_button")
                    yield Button("Show/Hide Info", id="hide_info", classes="bar_button")
                    yield Button(
                        "Toggle background transparency",
                        id="toggle_transparency",
                        classes="bar_button",
                    )
                yield Static(static_info, id="bottom_info_container", classes="info_container info")

        # yield WindowBar()      # If you have either a Header or Footer, WindowBar Must go
        # yield Footer()  #        before them in the compose method. Otherwise it will cover them up.

    def on_mount(self) -> None:
        main_container = self.query_one("#main_container")
        main_container.styles.opacity = 0.0  # Chad loading screen
        self.rich_log = self.query_one(RichLog)
        self.rich_log.can_focus = False

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

        self.rich_log.write(Text.from_markup(f"{event.window.name} [bright_red]closed."))

    @on(Window.Opened)
    def window_opened(self, event: Window.Opened) -> None:

        self.rich_log.write(Text.from_markup(f"{event.window.name} [bright_green]opened."))

    @on(Window.Minimized)
    def window_minimized(self, event: Window.Opened) -> None:

        self.rich_log.write(Text.from_markup(f"{event.window.name} [bright_yellow]minimized."))

    @on(Window.Initialized)
    def window_initialized(self, event: Window.Initialized) -> None:

        # Generally speaking, once one window is initialized, you can be confident
        # they're all ready to go and you can disable any loading screen you might have.

        self.rich_log.write(Text.from_markup(f"{event.window.name} [bright_blue]initialized."))
        self.log(f"{event.window.name} initialized.")

        if not self.app_initialized:
            main_container = self.query_one("#main_container")
            main_container.styles.animate("opacity", value=1.0, duration=0.5)  # Chad loading screen
            self.app_initialized = True

    @on(Button.Pressed, "#add_window")
    def add_window(self) -> None:

        # This is an example of how to add a new window dynamically.
        # You can customize the new window as needed.

        icons = ["🚀", "📺", "🔨", "🛒", "🔒", "💾"]

        new_window = Window(
            id=f"window_{self.window_counter}",
            icon=random.choice(icons),
            start_open=True,
            allow_maximize=True,
            starting_horizontal=random.choice(get_args(STARTING_HORIZONTAL)),
            starting_vertical=random.choice(get_args(STARTING_VERTICAL)),
        )
        self.query_one("#main_container").mount(new_window)
        self.window_counter += 1

    @on(WindowBar.DockToggled)
    def windowbar_dock_toggled(self, event: WindowBar.DockToggled) -> None:

        # This is an example of how to trigger something else when the
        # windowbar has the dock location toggled between top and bottom.
        # (left and right not currently supported)

        self.rich_log.write(f"WindowBar docked at {event.dock}.")

    ####################
    # ~ Other Events ~ #
    ####################

    @on(Button.Pressed, "#button1")
    def button1_pressed(self) -> None:

        textarea = self.query_one("#input1", TextArea)
        self.rich_log.write(textarea.text)
        textarea.text = ""

    @on(Button.Pressed, "#hide_info")
    def hide_info(self) -> None:

        upper_info = self.query_one("#main_info_container")
        bottom_info = self.query_one("#bottom_info_container")

        if upper_info.visible:
            upper_info.styles.visibility = "hidden"
        else:
            upper_info.styles.visibility = "visible"

        if bottom_info.visible:
            bottom_info.styles.visibility = "hidden"
        else:
            bottom_info.styles.visibility = "visible"

    @on(Button.Pressed, "#toggle_transparency")
    def toggle_transparency(self) -> None:

        self.ansi_color = not self.ansi_color
        self.push_screen(DummyScreen())

    @on(Checkbox.Changed)
    def checkbox_changed(self, event: Checkbox.Changed) -> None:

        self.rich_log.write(f"Checkbox changed to {event.value}")


def run_demo() -> None:
    WindowDemo().run()


if __name__ == "__main__":
    run_demo()
