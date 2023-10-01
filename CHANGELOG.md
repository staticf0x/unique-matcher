# v0.5.4

## Changes

### App

- [Fixed] Force UTF-8 everywhere, keep backward compatibility for old CSVs

# v0.5.3

## Changes

### App

- [Fixed] If the screenshot cannot be read (corrupted file),
  Unique Matcher will try again before moving it to errors.
- [Fixed] Force UTF-8 when opening item DB on Windows

# v0.5.2

## Changes

### App

- [Fixed] Errors coming from other places than item identification are now
  properly handled. They will appear as "Unexpected error" in the results table.
- [Fixed] It is now possible to make screenshots faster than 1 per second
  because the filenames now contain milliseconds of the time they were created.

### Item detection

- [Fixed] The Iron Fortress couldn't be identified

# v0.5.1

## Changes

### App

- [Fixed] When clearing result table (either directly or through new snapshot),
  the row numbers start from 1 again
- [Fixed] The app could process some files multiple times, this should be fixed now

### Item detection

- [Fixed] Following items set as non-natural: Coruscating Elixir, Maw of Mischief
- [Fixed] Removed items: Band of the Victor
- [Fixed] Item bases: Maelström Staff, Long Bow (in some cases)

# v0.5.0

## Changes

### App

- [New] New feature to combine selected result CSVs into one (*Results > Combine CSVs*)
- [New] On startup, the app will delete all empty CSVs except the currently used one

### Item detection

- [Fixed] All non-natural drops are now disabled
- [Fixed] Cameria's Avarice detection

# v0.4.0

## Changes

- [New] Tesseract is now part of the installer, users no longer need to set it up manually
- [New] Unique Matcher now has its own icon!
- [New] Option to create a desktop icon during installation
- [Changed] All application data files are now inside one folder, so there's less clutter
- [Changed] Shaved off some unnecessary DLLs, so the installer is now smaller, faster and the installed size is also lower
- [Fixed] Fixed default screenshot shortcut (app could fail if freshly installed)

Note: it is recommended to do a clean install before installing 0.4.0.

**Always backup your data/results CSVs before upgrading.**

# v0.3.0

## Changes

- [New] Added menu bar with several convenience options
- [New] Processed items are now sorted into their respective folders
- [New] Option to create a ZIP file with the processed screenshots to make a new data set for testing ([wiki](https://github.com/staticf0x/unique-matcher/wiki/Test-data-and-benchmarking))
- [New] Option to clear the result table
- [New] Option to report issues on GitHub
- [New] Option to modify the screenshot shortcut
- [New] Option to start AHK script from menu
- [Fixed] Result table expands with the application window size
- [Fixed] Create snapshot button position changes with the application window size
- [Fixed] Holy Chainmail base detection
- [Fixed] Hubris Circlet base detection
- [Fixed] Socketed item accuracy improved by about 6%, fixing Eclipse Solaris (#21)
- [Fixed] Turned off Indigon (non-global drop)

# v0.2.1

## Changes

- [Fixed] Gladius detection
- [Fixed] Occultists Vestment base detection
- [Fixed] Splinter of the Moon was enabled even though it is drop-disabled
- [Fixed] Dev: typing improvements by @ThirVondukr

Contributors: @ThirVondukr

**Always backup your data/results CSVs before upgrading.**

# v0.2.0

## Changes

- [New] The result table now automatically scrolls to the bottom on new results
- [New] Added scrollbar to the results table
- [New] Added row numbers to result table
- [New] Log errors into the result table (doesn't change the result CSV)
- [New] Added `config.ini` to allow users to change the screen where the screenshot is taken
- [New] PoE screen can be auto-detected from PoE config file thanks to @shonya3
- [Changed] Increased result table column widths
- [Changed] Disabled overshoot scroll animation
- [Fixed] Added missing dimension for all items

Contributors: @shonya3

# v0.1.1

## Changes

- [New] Added installer!
- [New] AHK script is now generated when running UniqueMatcher and hides the screenshotting tool
- [Fixed] Creating data directories in the correct place and time
- [Fixed] Initialization of the QML app was wrong
- [Fixed] Winterweave no longer disabled
- [Fixed] Corrected The Blood Thorn sockets
- [Fixed] Ambusher base dimensions
- [Fixed] Detection of Hubris Circlet base
- [Fixed] Linters made happy

**If you have existing data/results CSV files, back them up before installing new version.**

Thanks @ThirVondukr for their first contribution

# v0.1.0

This was the first alpha release.
