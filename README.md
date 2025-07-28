<picture class="only-github">
  <source media="(prefers-color-scheme: dark)" srcset="https://ttygroup.github.io/assets/textual-window/banner-dark-theme.png">
  <source media="(prefers-color-scheme: light)" srcset="https://ttygroup.github.io/assets/textual-window/banner-light-theme.png">  
  <img src="https://ttygroup.github.io/assets/textual-window/banner-light-theme.png">
</picture>

<!-- MKDOCS-START
![banner](https://ttygroup.github.io/assets/textual-window/banner-light-theme.png#only-light)
![banner](https://ttygroup.github.io/assets/textual-window/banner-dark-theme.png#only-dark)
MKDOCS-END -->

# Textual-Window

[![badge](https://img.shields.io/pypi/v/textual-window)](https://pypi.org/project/textual-window/)
[![badge](https://img.shields.io/github/v/release/edward-jazzhands/textual-window)](https://github.com/edward-jazzhands/textual-window/releases/latest)
[![badge](https://img.shields.io/badge/Requires_Python->=3.9-blue&logo=python)](https://python.org)
[![badge](https://img.shields.io/badge/Strictly_Typed-MyPy_&_Pyright-blue&logo=python)](https://mypy-lang.org/)
[![badge](https://img.shields.io/badge/license-MIT-blue)](https://opensource.org/license/mit)

Textual-Window is an extension library for [Textual](https://github.com/Textualize/textual).

It provides a Window widget, along with an included WindowBar and WindowSwitcher, that makes it
easy to create a desktop GUI-like experience inside of a TUI built with Textual.

Window widgets are floating, draggable, resizable, snappable, closable, and you can even cycle through them in a manner similar to alt-tab. It's like a mini desktop inside of your terminal. (Is it ridiculous? Yes, yes it is. But is it awesome? Also yes.)

## Features

- Drag, resize, and maximize windows. Close windows with ctrl+w.
- Windows can focus, and highlight to show which one is focused. Controls are passed from the highlighted window to its inner scrolling container.
- Included fully-automatic Window Bar (aka Task Bar). Don't worry about keeping track of the windows. Just compose and go. The library will track them for you.
- Included Window Switcher, to cycle window focus in a manner similar to alt-tab. The most recently focused window is always at the start (left side).
- Set the window's min and max size through Textual CSS as you normally would, and the window will respect those settings when resizing. Resizing can also be disabled per window.
- Windows snap to the terminal by default, toggle this on/off in real-time.
- WindowBar can toggle the dock between top and bottom of the screen in real-time.
- Window Bar has right-click context menus, one for each window, as well as a global context menu with options such as close/open all or snap/unsnap all.
- Set the window's starting location on the screen using plain descriptions (ie. right + bottom), as well as whether to initialize open or closed.
- An optional hamburger menu for custom callbacks - The window has a 'menu_options' argument. Pass in a dictionary of functions (label + callback) and these functions will appear in that window's hamburger menu. (If nothing is passed in, the menu is not shown).
- Smooth fade in/out animation adds a convincing touch.
- Create windows in all 3 ways textual supports - context manager, passing in a list of children, and custom Window objects.
- ...and many small QoL things too numerous to list here.

See the documentation for more details.

Note: This library is under pretty active development and so the API is subject to change. If you find a bug, please report it on the issues page.

## Demo App

If you have [uv](https://docs.astral.sh/uv/) or [pipx](https://pipx.pypa.io/stable/), you can immediately try the demo app:

```sh
uvx textual-window 
```

```sh
pipx run textual-window
```

## Documentation

### [Click here for documentation](https://edward-jazzhands.github.io/libraries/textual-window/docs/)

## Video

<video style="width: 100%; height: auto;" controls loop>
  <source src="https://ttygroup.github.io/assets/textual-window/demo-0.3.5-handbrake.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>

[](https://github.com/user-attachments/assets/2bf5f4d9-f289-4e7f-b9ae-e91fd34c1ce3)

## Questions, Issues, Suggestions?

Use the [issues](https://github.com/edward-jazzhands/textual-window/issues) section for bugs or problems, and post ideas or feature requests on the [TTY group discussion board](https://github.com/orgs/ttygroup/discussions).
