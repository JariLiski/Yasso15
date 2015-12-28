import PyInstaller.loader.pyi_carchive as carchive
import sys
import os
import uuid
import colorsys
import shelve
import cgi

#ETS_INSTALL = 'EPD'
ETS_INSTALL = 'pypi'

#if hasattr(sys, 'frozen'):
#    __file__ = ''.join((os.path.dirname(sys.executable), 'unpackMetadata.py'))

this = carchive.CArchive(sys.executable)
print "ENVIRON:"
print "\n".join(sorted(os.environ.keys()))
if hasattr(sys, "_MEIPASS"):
    print "Sys has MEIPASS"
    archives = sys._MEIPASS
elif hasattr(sys, "_MEIPASS2"):
    print "Sys has MEIPASS2"
    archives = sys._MEIPASS2
else:
    archives = os.environ['_MEIPASS2']
# on OS X this will be behind a symbolic link which will cause import troubles
sys.path.append(os.path.realpath(archives))
if ETS_INSTALL == 'EPD':
    pkgs = ['wx', 'enthought']
else:
    pkgs = ['enable', 'traits', 'kiva', 'traitsui', 'chaco', 'wx', 'pyface']
    #pkgs = ['enable', 'traits', 'traitsui', 'chaco', 'pyface']
#targetdir = os.path.join(archives, "pymodules")
#os.mkdir(targetdir)
#sys.path.insert(0, targetdir)

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
    
    print "The contents of the target subdir now:"
    print sorted(os.listdir(targetdir))
    
    #print "Appended to sys.path:", targetdir
    if pkg == 'wx':
        print "Appending to sys.path"
        sys.path.insert(0, targetdir)
    #os.path.join(targetdir, pkg))
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
print "FINAL SYS PATH:", sys.path
    
import code, keyword

print "Trying to import wx"
import wx
print "WX file:", wx.__file__
print "Trying to import wx.html"
import wx.html
print "Trying to import wx.lib.scrolledpanel"
import wx.lib.scrolledpanel
print "Trying to import everything from wx"
from wx import *
