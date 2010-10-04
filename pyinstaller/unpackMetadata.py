import carchive
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
archives = os.environ['_MEIPASS2']
# on OS X this will be behind a symbolic link which will cause import troubles
sys.path.append(os.path.realpath(archives))
if ETS_INSTALL == 'EPD':
    pkgs = ['wx', 'enthought']
else:
    pkgs = ['wx', 'traits', 'traitswx', 'chaco', 'enthought', 'enable',
            'traitsgui']
for pkg in pkgs:
    mp = this.openEmbedded('%s.pkg' % pkg)
    targetdir = os.path.join(archives, pkg)
    os.mkdir(targetdir)
    print "Extracting %s ..." % (pkg, )
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
    sys.path.insert(0, targetdir)
    if ETS_INSTALL == 'EPD' and pkg == 'enthought':
        imagepath = os.path.join(targetdir, 'traits', 'ui', 'image', 'library')
        os.environ['TRAITS_IMAGES'] = imagepath
        os.putenv('TRAITS_IMAGES', imagepath)
    elif ETS_INSTALL == 'pypi' and pkg == 'traitsgui':
        imagepath = os.path.join(targetdir, 'enthought', 'traits', 'ui',
                                     'image', 'library')
        os.environ['TRAITS_IMAGES'] = imagepath
        os.putenv('TRAITS_IMAGES', imagepath)
    print "ok"

import code, keyword
import wx
import wx.html
import wx.lib.scrolledpanel
from wx import *

if ETS_INSTALL != 'EPD':
    from resource_path_override import ResourcePathOverride
    resource_override = ResourcePathOverride(archives)

#DEBUG
#print "Files are at", archives
#print "sys.path is:"
#for i in sys.path: print i
#raw_input("press enter to continue...")
