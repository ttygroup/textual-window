<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://github.com/user-attachments/assets/800de9df-be91-45ff-87eb-abcc1c19c5a9">
  <img src="https://github.com/user-attachments/assets/06b16b87-a37d-405c-b9fb-44ea2d89de5c">
</picture>

# Textual-Window

![badge](https://img.shields.io/badge/Linted-Ruff-blue&logo=ruff)
![badge](https://img.shields.io/badge/Formatted-Black-black)
![badge](https://img.shields.io/badge/Type_checked-MyPy-blue&logo=python)
![badge](https://img.shields.io/badge/Type_checked-Pyright-blue&logo=python)
![badge](https://img.shields.io/badge/License-MIT-blue)
[![Framework: Textual](https://img.shields.io/badge/framework-Textual-5967FF?logo=python)](https://www.textualize.io/)

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

## Demo App

If you have uv or Pipx, you can immediately try the demo app:

```sh
uvx textual-window 
```

```sh
pipx run textual-window
```

## Documentation

### [Click here for documentation](https://edward-jazzhands.github.io/libraries/textual-window/)

## Video

https://github.com/user-attachments/assets/2bf5f4d9-f289-4e7f-b9ae-e91fd34c1ce3

## Questions, issues, suggestions?

Feel free to post an issue.
