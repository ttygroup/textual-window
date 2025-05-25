# Textual-Window

![badge](https://img.shields.io/badge/linted-Ruff-blue?style=for-the-badge&logo=ruff)
![badge](https://img.shields.io/badge/formatted-black-black?style=for-the-badge)
![badge](https://img.shields.io/badge/type_checked-MyPy-blue?style=for-the-badge&logo=python)
![badge](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)

Textual-Window is an extension library for [Textual](https://github.com/Textualize/textual).

It provides a Window widget, along with an included WindowBar and WindowSwitcher, that makes it extremely
easy to create a desktop GUI-like experience inside of a TUI built with Textual.

Window widgets are floating, draggable, resizable, closable, and many more.

## Features

- Close and open windows with the close button or the desktop standard, ctrl-w
- Resize, maximize, and restore windows. Set the window's min and max size through Textual CSS as you normally would, and the window will respect those
settings when resizing. Resizing can also be disabled per window.
- Included fully-automatic Window Bar (aka Task Bar). Don't worry about keeping track of the windows. Just compose and go. The library will track them for you.
- Included Window Switcher, to cycle window focus like you'd expect. The most recently focused window is always at the start (left side).
- WindowBar can toggle the dock between top and bottom of the screen in real-time.
- Windows snap to the terminal by default, toggle this on/off in real-time.
- Window Bar has right-click context menus, one for each window, as well as a global context menu with options such as close/open all or snap/unsnap all.
- Windows highlight to show which one is focused. Controls are passed from the highlighted window to its inner scrolling container.
- Set the window's starting location on the screen using plain descriptions (ie. right + bottom), as well as whether to initialize open or closed.
- An optional hamburger menu for custom callbacks - The window has a 'menu_options' argument. Pass in a dictionary of functions (label + callback) and these functions will appear in that window's hamburger menu. (If nothing is passed in, the window is not shown).
- Smooth fade in/out animation adds a convincing touch.
- Create windows in all 3 ways textual supports - context manager, passing in a list of children, and custom Window objects.
- ...and many small QoL things too numerous to list here.

See the documentation for more details.

## Demo App

If you have uv or Pipx, you can immediately try the demo app:

```sh
uvx textual-window 
```

```sh
pipx textual-window
```

## Documentation

### [Click here for documentation](https://edward-jazzhands.github.io/libraries/textual-window/)

## Questions, issues, suggestions?

Feel free to post an issue.

## Video

Coming soon
