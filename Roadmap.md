# Features checklist

## Features to add

- [ ] Build system for windowbar to manage overflowing / many windows.
- [ ] Turn Window switcher into a grid so it grows vertically (connected to above).
- [ ] Add option to make the WindowBar floating.
- [ ] Implement way to deal with relative sizes.  
- [ ] Add switch between snapping to parent container and snapping to screen.  
- [ ] Add ability to disable toggling the snap.
- [ ] Turn allow_resize into a reactive variable.
- [ ] Add a way to change the mouse controls, something other than right-clicking
- [ ] Add a Modal window option (Modal screen + window combo)
- [ ] Add more validation in the window constructor

## Finished (0.4.0)

- [X] Add a new mounting callback registry and mount_window method to the Window Manager.

## Finished (0.3.2)

- [X] Added new dot on windowbar buttons that shows which windows are currently minimized
- [X] Added a new "Desktop" button in the window switcher which will minimize all windows

## Finished (0.3.0)

- [X] Build a secondary mode where windows can be mounted and unmounted
- [X] Add button to make the demo background transparent.
- [X] Replace the looping DOM ready worker in the manager with call_after_refresh system
- [X] Replace the windowbar's build at launch system with a dynamic system for the secondary mode.
- [X] Make switcher toggle minimize state of the focused window
- [X] Change the 'name' attribute being required to 'id' instead.
- [X] Add icons to Window title and Window Bar
- [X] Randomize the add window button in the demo

## Finished (0.2.0)

- [X] Maximize symbol should change to '_' symbol after maximizing
- [X] Restoring (unmaximizing) a window should restore to its previous state
- [X] Make the resize button slightly larger
- [X] Replace lock button with a generic hamburger menu ☰
- [X] Build a custom command system for the hamburger menu
- [X] Add help info about right clicking behavior into the demo
- [X] Add snap/lock state indicator for windows on the WindowBar.
- [X] Build window focus cycler screen
- [X] Build way to focus windows / tell which is focused
- [X] Pass through focus controls to inner content_pane (content_pane focusing now disabled)
- [X] WindowSwitcher shows windows in order of last focus

## Finished (0.1.0)

- [X] Add a close button to the top bar.  
- [X] Add a lock to screen option.  
- [X] Add a resize button to the bottom right corner.  
- [X] Add a title argument to the window.  
- [X] Add a way to set the starting position of the window.  
- [X] Add method to reset size and position of the window.  
- [X] Add open / close animations.  
- [X] Make it possible to set min/max size through both CSS and constructor.  
- [X] Button to Enable / Disable window locking.  
- [X] Add a window manager bar / task bar system.  
- [X] Find way to fix issues with all windows starting closed.  
- [X] Add an intialized message to complement the Reset message.  
- [X] Add setting to dock WindowBar to the top instead of the bottom.  
- [X] Fix initialization if all windows start with display=False
- [X] Add a generic WindowBar menu for all windows.
- [X] Implement a maximize ability.
- [X] Implement start_open option in WindowBar.
- [X] Add option to change WindowBar dock in real-time menu.
