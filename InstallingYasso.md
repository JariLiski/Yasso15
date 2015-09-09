## Running Yasso07 ##

For a distribution of Yasso07 that you can just run from a single executable, download either:

[The Windows version](http://yasso07ui.googlecode.com/files/yasso07_1.0_exe_win.zip)

or

[The Linux version](http://yasso07ui.googlecode.com/files/yasso07_1.0_exe_linux.tar.gz)

Note that the Linux version is tested only on Ubuntu 8.04 and 8.10.

For those running Mac or interested in finding out how to run Yasso07 from the source, read on.

## Installing the requirements ##

Yasso07 user interface is written in [Python](http://www.python.org) using the [Enthought Tool Suite](http://code.enthought.com/projects/index.php) (ETS). It's very tedious to set up, so you're well advised on using the [Enthought Python Distribution](http://www.enthought.com/products/getepd.php) that contains a ready Python environment for ETS. For academia, it's free, others have to fork out some cash...

Besides ETS, you need to install the dateutil package:

> `sudo easy_install python-dateutil`

## Finally ##

Grab the source distribution of Yasso07 (see the downloads tab), unzip it, open your console/terminal in the resulting yasso07-folder and issue the command

> `python yasso.py` (on Windows)

> `pythonw yasso.py`(on Mac)


### EPD & virtualenv ###

If you already have a Python installation that you're using, you can hide the EPD installation in a [virtualenv](http://pypi.python.org/pypi/virtualenv), see also [virtualenwrapper](http://www.doughellmann.com/projects/virtualenvwrapper/) which makes virtualenv a lot nicer to use.

To do that
  * install EPD
  * comment out the path modifications make during the installation (see .bash\_profile on OS X)
  * create a new virtualenv specifying the EPD python interpreter as the one to use, e.g. using virtualenvwrapper

> `mkvirtualenv -p /Library/Frameworks/Python.framework/Versions/6.2/bin/python yasso`

> will create a new virtualenv called 'yasso' that will use the EPD python
  * make a symbolic link to pythonw in the virtualenv's bin directory, e.g.:

> `ln -s /Library/Frameworks/Python.framework/Versions/6.2/bin/pythonw2.6 pythonw`