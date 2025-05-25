# Textual-Window Changelog

## 0.2.1

- Small fixes to documentation.
- Made the Window.calculate_starting_position and Window.calculate_max_size methods into private methods

## 0.2.0

Huge update with many improvements:

- Breaking change: Made the name argument for the window be mandatory.
- Built a window focus cycler screen. This will dynamically show which window had most recent focus using a Queue and works very similar to alt-tab in a normal desktop.
- Built a custom command system for the hamburger menu.
- Built a way to focus windows / tell which is focused.
- Disabled focusing for inner content pane (The vertical scroll). Now it passes through all the scrolling controls from the window to the vertical scroll while the window is focused. Overrode several `action_scroll` methods to do this.
- Replaced the lock button with a generic hamburger menu ☰, which now shows a list of callbacks which can be passed into the window as an argument.
- Add snap/lock state indicator for windows on the WindowBar.
- Make the resize button slightly larger.
- Restoring (unmaximizing) a window now restores to its previous size and location.
- Maximize symbol now changes to '_' symbol after maximizing.
- Added more help info to the demo.

## 0.1.2

- Fixed bug with double quotes containing double quotes (apparently allowed in Python >= 3.12)
- Changed Python required version to 3.10

## 0.1.0

- First public release
