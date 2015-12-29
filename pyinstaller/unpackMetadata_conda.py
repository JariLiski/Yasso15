import PyInstaller.loader.pyi_carchive as carchive
import sys
import os
import uuid
import colorsys
import shelve
import cgi

#ETS_INSTALL = 'EPD'
ETS_INSTALL = 'pypi'

this = carchive.CArchive(sys.executable)
if hasattr(sys, "_MEIPASS"):
    archives = sys._MEIPASS
elif hasattr(sys, "_MEIPASS2"):
    archives = sys._MEIPASS2
else:
    archives = os.environ['_MEIPASS2']
# on OS X this will be behind a symbolic link which will cause import troubles
sys.path.append(os.path.realpath(archives))
if ETS_INSTALL == 'EPD':
    pkgs = ['wx', 'enthought']
else:
    pkgs = ['enable', 'traits', 'kiva', 'traitsui', 'chaco', 'wx', 'pyface']

for pkg in pkgs:
    mp = this.openEmbedded('%s.pkg' % pkg)
    targetdir = os.path.join(archives, pkg)
    os.mkdir(targetdir)
    print "Extracting %s to %s..." % (pkg, targetdir)
    for fnm in mp.contents():
        try:
            stuff = mp.extract(fnm)[1]
            outnm = os.path.join(targetdir, fnm)
            dirnm = os.path.dirname(outnm)
            if not os.path.exists(dirnm):
                os.makedirs(dirnm)
            open(outnm, 'wb').write(stuff)
        except Exception, mex:
            print mex
    mp = None
    
    if pkg == 'wx':
        sys.path.insert(0, targetdir)
    if ETS_INSTALL == 'EPD' and pkg == 'enthought':
        imagepath = os.path.join(targetdir, 'traits', 'ui', 'image', 'library')
        os.environ['TRAITS_IMAGES'] = imagepath
        os.putenv('TRAITS_IMAGES', imagepath)
    elif ETS_INSTALL == 'pypi' and pkg == 'traitsui':
        imagepath = os.path.join(targetdir, 'pymodules', 'traitsui',
                                     'image', 'library')
        os.environ['TRAITS_IMAGES'] = imagepath
        os.putenv('TRAITS_IMAGES', imagepath)
    print "ok"
    os.putenv('ETS_TOOLKIT', 'wx')
    os.environ['ETS_TOOLKIT'] = 'wx'
sys.path.insert(0, archives)
    
import code, keyword
import kiwisolver

import wx
import wx.html
import wx.lib.scrolledpanel
from wx import *
