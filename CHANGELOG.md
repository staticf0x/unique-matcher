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
