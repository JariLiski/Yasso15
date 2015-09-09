## Known problems with Yasso07 user interface ##


---


**Problem**: The main window disappears

When you minimize or maximize the program window for Yasso07, nothing seems to happen.

**Solution**: Quit the program and remove this file:
  * XP: `C:\Documents and Settings\<Your username>\Application Data\Enthought\traits\traits_ui`
  * Vista: `C:\Users\<Your username>\AppData\Local\Enthought\traits\traits_ui` or `C:\Users\<Your username>\AppData\Roaming\Enthought\traits\traits_ui`
  * Linux/OS X: `~/.enthought/traits/traits_ui`


---


**Problem**: Opening a datafile fails if the path contains characters outside the ASCII range

If the file or directory name for your datafile contains characters outside the A-Z and 0-9 range, opening the file fails.

**Solution**: The only working one at the moment is the obvious one; use only A-Z/0-9 in the file and directory names.


---


**Problem**: Creating a new data file or using Save As.. on OS X

There was a bug in [Enthought Tool Suite](http://code.enthought.com/projects/index.php), which Yasso07 uses, prior to version 3.2

**Solution**: Upgrade your ETS intallation, see InstallingYasso