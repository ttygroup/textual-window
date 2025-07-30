# Textual-Window Changelog

## [0.7.1] 2025-07-30

### Changed

- Dropped the required Textual version back down to 3.7.1 (last 3.x.x release) to maintain compatibility with Textual 3.x.x.
- [dev] Changed `ci-checks.yml` to run Nox instead of individual commands for MyPy, Ruff, Pytest, etc.

### Added

- [dev] Added `/tests` directory with unit tests, a [pytest] section in `pyproject.toml`, and added `just test` command to the justfile.
- [dev] Added Nox testing and `noxfile.py` to run tests in different Python versions and across different versions of Textual.
- [dev] Added pytest, pytest-asyncio, and pytest-textual-snapshot to dev dependencies.

### Removed

- [dev] Deleted `ci-requirements.txt` as it is no longer needed with the new Nox setup.

## [0.7.0] 2025-07-28

### Usage / API changes

- Upgraded to Textual 5.0.0.

### Code and project changes

- Renamed Changelog.md to CHANGELOG.md
- Added 2 workflow to .github/workflows:
  - ci-checks.yml - runs Ruff, MyPy, BasedPyright (will add Pytest later)
  - release.yml - Workflow to publish to PyPI and github releases
- Added 2 scripts to .github/scripts:
  - adds .github/scripts/validate_main.sh
  - adds .github/scripts/tag_release.py
- Added 1 new file to root: `ci-requirements.txt` - this is used by the ci-checks.yml workflow to install the dev dependencies.
- Added basedpyright as a dev dependency to help with type checking. Made the `just typecheck` command run it after MyPy and set it to 'strict' mode in the config (added [tool.basedpyright] section to pyproject.toml).
- Replaced build and publish commands in the justfile with a single release command that runs the two above scripts and then pushes the new tag to Github
- Workflow `update-docs.yml` now runs only if the `release.yml` workflow is successful, so it will only update the docs if a new release is made (Still possible to manually run it if needed, should add a 'docs' tag in the future for this purpose).
- Changed the `.python-version` file to use `3.9` instead of `3.12`.

## [0.6.0] (2025-07-21)

- Potentially Breaking change: The `WindowManager` class no longer inherits from `textual.dom.DOMNode`. This change was made to simplify the class and remove unnecessary complexity. The window manager is not mounted in the DOM. I was using it to give access to certain Textual widget features, but I just refactored the code to not need them anymore.
- Added EzPubSub to the `WindowManager` class. This is a new cross-framework pub-sub system that I built to facilitate communication between the window manager and other parts of the application that may not be Textual widgets (and thus could not use Textual's built-in pub-sub system). This allows for more flexible communication between the window manager and other parts of the application.

## 0.5.2 (2025-07-1)

- Added new property `mounting_callbacks` to the `WindowManager` class, which returns a dictionary of all registered mounting callbacks. Just a wrapper over `_mounting_callbacks` (honestly I just forgot to add it).

## 0.5.1 (2025-07-02)

- Bug fix: Forgot to actually await the callback in the `mount_window` method.

## 0.5.0 (2025-07-01)

- Breaking change: The `mount_window` method (added in 0.4.0) is now an async method and must be awaited. This change was made to allow the callback to be awaited, which is necessary for proper asynchronous behavior in Textual.
- Added a new `WindowStylesDict` type to the window module, which is a typed dictionary that can be used to define styles for windows through the constructor. This was added to make it easy for some kind of external process manager to create and style windows through Python without needing to know the internals of the window class or use CSS.
- Added new corresponding `styles_dict` argument to the `Window` constructor which takes a `WindowStylesDict` as an argument.
- Updated the demo to use the new `styles_dict` argument for one of the windows to demonstrate how it works.
- Changed: `_calculate_min_max_sizes` in Window renamed to `_calculate_all_sizes`

## 0.4.1 (2025-06-27)

- renamed the `id` argument in `register_mounting_callback` and `mount_window` to `callback_id` for clarity. Also added an Args section to the docstrings of these methods to clarify the purpose of the `callback_id` argument.

## 0.4.0 (2025-06-27)

- Added new methods for mounting windows through the manager:
  - `register_mounting_callback`: Register a callback that can be used to mount windows.
  - `mount_window`: Mount a window using a registered callback.
These new methods allow for more flexible window management, enabling some external source to register a callback with the manager, and then pass windows into the manager to be mounted using that callback. This is useful for integrating with other systems or frameworks that need to manage windows dynamically or use their own process management in some way.
- Improved the window manager API somewhat by making some things read-only properties and making all the self-attributes private.

## 0.3.5 (2025-06-14)

- Added a `DockToggled` message to the Windowbar which will emit a message whenever the windowbar has the dock location toggled. Can handle with `@on(WindowBar.DockToggled)`.

## 0.3.4 (2025-06-11)

- Replaced default for `menu_options` argument to be None instead of empty dictionary. Forgot that you can't use a mutable value as a default in a method, it would result in unexpected behavior.

## 0.3.3 (2025-06-10)

- New feature: Windows now maintain their highlighting focus color when their children (contents in the window) are being interacted with.
- Breaking change - `show_maximize_button` argument for Window class renamed to `allow_maximize` to be more similar to `allow_resize`.
- Refactored some logic so focusing now brings windows forward according to `always_bring_forward` instead of it being a separate call.

## 0.3.2

- New feature: added a dot on WindowBar buttons to mark which windows are currently minimized.
- Breaking change - `reset_window`, `reset_size`, and `reset_position` in the Window class were made into async functions and now must be awaited. Likewise the correspoding `reset_all_windows` in the manager was also made async.
- Breaking change - `reset_all_window_positions` and `reset_all_windows_size` methods in the manager were removed, as I think they're just unnecessary (not used anywhere in the library).
- Breaking change - `set_dock` and `toggle_dock` in window manager renamed to `set_dock_location` and `toggle_dock_location` respectively.
- `_dom_ready` in Window class was made into a normal (non-threaded) worker.
- `_calculate_max_min_sizes` and `_calculate_starting_position` were made into async functions (They do not yield themselves but now the `_dom_ready` worker can await them upon initialization, which is a very mild benefit.)

## 0.3.1

- Added a 'Desktop' button in the window switcher which will minimize all windows.
- Fixed bug with window switcher crashing when there are no windows.
- Made the cycle key be an argument on the WindowSwitcher class.
- Added __all__ variables to windowbar.py, switcher.py, and manager.py
- Manager's `remove_window` method renamed to `unregister_window`.
- Fixed bug in manager where close_all_windows crashed from a window trying to focus while the stack is being closed.
- Renamed `_add_window` and `_remove_window` in the window bar to `add_window_button` and `remove_window_button`.

## 0.3.0 - Dynamic windows update

- Breaking change: The `name` attribute is no longer required, the `id` attribute is now required instead. The window will automatically replace any underscores in the id with spaces to use for the display name (in titlebar, etc).
- Windows have a new 'mode' setting to choose between "temporary" and "permanent". In temporary mode, windows will be removed from the DOM and windowbar when closed (as a normal Desktop would). In permanent mode, the close button is removed and the window can only be minimized.
- Windows can now be added and removed from the DOM and the window bar and manager will update automatically.
- Added a new "Add window" button to the demo to demonstrate the dynamic windows feature.
- Added new "close" and "minimize" options to the WindowBar menus to reflect how these are now 2 different options.
- Added new buttons in the demo to hide the RichLog and to make the background transparent.
- Added new hotkey "ctrl-d" to windows for minimizing.
- Window switcher now toggles the minimize state of the currently focused window.
- Added a new icon argument for the window.
- Removed the footer from the demo because the transparency mode (ansi_color) messes it up for some reason (but nothing else, strangely).
- Replaced the windowbar system that built windows at start with a new dynamic system that can add and remove window buttons in real time.
- Replaced the manager worker that watched for _dom_ready on a loop to instead rely on `call_after_refresh` in a window's `on_mount` method.
- Windows now track the DOM ready themselves due to the above feature, and calculate their own max sizes and starting positions accordingly, and add themselves to the window bar (still through the manager) when they're ready.

## 0.2.3

- Moved all button symbols to a single dictionary to remove code duplication.
- Slightly modified the button rendering logic to remove whitespace, hopefully fixes a graphical glitching issue.

## 0.2.2

- Added 3 new methods:
  - `mount_in_window`
  - `mount_all_in_window`
  - `remove_children_in_window`
  
These 3 methods make it possible to change the widgets inside of a window after it has been created. They are bridge methods that connect to `mount`, `mount_all`, and `remove_children` in the content pane.

## 0.2.1

- Small fixes to documentation.
- Made the Window.calculate_starting_position and Window.calculate_max_size methods into private methods

## 0.2.0

Huge update with many improvements:

- Breaking change: Made the name argument for the window be mandatory.
- Built a window focus cycler screen. This will dynamically show which window had most recent focus using a Queue and works very similar to alt-tab in a normal desktop.
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
