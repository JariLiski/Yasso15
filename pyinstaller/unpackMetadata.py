import carchive
import sys
import os
import uuid
import colorsys
import shelve
import wx
import wx.html
import wx.lib.scrolledpanel
import cgi
from wx import *

#if hasattr(sys, 'frozen'):
#    __file__ = ''.join((os.path.dirname(sys.executable), 'unpackMetadata.py'))

this = carchive.CArchive(sys.executable)
archives = os.environ['_MEIPASS2']
pkgs = ['traits', 'traitswx', 'chaco', 'enthought', 'enable', 'traitsgui']
for pkg in pkgs:
    mp = this.openEmbedded('%s.pkg' % pkg)
    targetdir = os.path.join(archives,pkg)
    os.mkdir(targetdir)
    print "Extracting %s ..." % pkg,
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
    if pkg == 'traitsgui':
        imagepath = os.path.join(targetdir, 'enthought', 'traits', 'ui', 'image', 'library')
        os.environ['TRAITS_IMAGES'] = imagepath
        os.putenv('TRAITS_IMAGES', imagepath)
    print "ok"

from resource_path_override import ResourcePathOverride    
resource_override = ResourcePathOverride(archives)

#DEBUG        
#print "Files are at", archives 
#raw_input("press enter to continue...")
