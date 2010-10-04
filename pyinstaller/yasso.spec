# -*- mode: python -*-
import os
import os.path as pth
import sys
import re
import fnmatch
import enthought

#ETS_INSTALL = 'EPD'
ETS_INSTALL = 'pypi'

sys_id = str.lower(sys.platform[:3])
libfiles = []
if sys_id == 'lin':
    print 'Finding additional library files...'
    try:
        filelist = os.listdir('/usr/lib')
        for file in filelist:
            if (file.startswith('libwx') or file.startswith('libgfortran')) \
               and re.search(r'so[.][0-9]$', file):
                target = file
                try:
                    target = os.readlink(pth.join('/usr/lib', file))
                except OSError:
                    pass
                if not target.startswith('/usr/lib'): 
                    target = pth.join('/usr/lib', file)
                print 'Adding', target, 'as', file
                libfiles.append((file, target, 'BINARY'))
    except OSError, err:
        print err

if sys_id == 'dar':
    print 'Finding additional library files...'
    try:
        ets_base = pth.abspath(pth.dirname(enthought.__file__)) 
        libs = pth.join(ets_base, 'kiva', 'mac') 
        filelist = os.listdir(libs)
        for file in filelist:
            if fnmatch.fnmatch(file, '*.so'):
                so_file = pth.join(libs, file)
                libfiles.append((file, so_file, 'BINARY'))
    except OSError, err:
        print err

if ETS_INSTALL == 'EPD':
    base = pth.abspath(pth.join(pth.dirname(enthought.__file__), '..')) 
    enthought = pth.join(base, 'enthought')
    print 'added enthought from enthought'
    wx = pth.join(base, 'wx')
    print 'added wx from wx'
else:
    base = pth.abspath(pth.join(pth.dirname(enthought.__file__), '..', '..')) 
    for item in os.listdir(base):
        if item.lower().startswith('traits-'): 
            traits = pth.join(base, item)
            print 'added traits from', item
        if item.lower().startswith('traitsgui'): 
            traitsgui = pth.join(base, item)
            print 'added traitsgui from', item
        if item.lower().startswith('traitsbackendwx'): 
            traitswx = pth.join(base, item)
            print 'added traitswx from', item
        if item.lower().startswith('enable'): 
            enable = pth.join(base, item)
            print 'added enable from', item
        if item.lower().startswith('enthought'): 
            enthought = pth.join(base, item)
            print 'added enthought from', item
        if item.lower().startswith('chaco'): 
            chaco = pth.join(base, item)
            print 'added chaco from', item
        if item.lower().startswith('wx-'): 
            wx = pth.join(base, item)
            print 'added wx from', item

basefiles = [pth.join(HOMEPATH,'support/_mountzlib.py'),
              #pth.join(HOMEPATH,'support/unpackTK.py'),
              #pth.join(HOMEPATH,'support/useTK.py'),
              pth.join(HOMEPATH,'support/useUnicode.py'),
              pth.join(base, 'pkg_resources.py'),
              'unpackMetadata.py',
              '../yasso.py',
              '../modelcall.py',
              #pth.join(HOMEPATH,'support/removeTK.py'),
              ]
a = Analysis(basefiles,
             pathex=[''],
             hookspath=[''],
             excludes=['enthought', 'wx'])
#DEBUG
#print "Appending extra libraries", libfiles
if ETS_INSTALL == 'EPD':
    pyz = PYZ(a.pure)
    enthought = PKG(Tree(enthought), name='enthought.pkg')
else:
    pyz = PYZ(a.pure)
    traits = PKG(Tree(traits), name='traits.pkg')
    traitsgui = PKG(Tree(traitsgui), name='traitsgui.pkg')
    traitswx = PKG(Tree(traitswx), name='traitswx.pkg')
    enable = PKG(Tree(enable), name='enable.pkg')
    enthought = PKG(Tree(enthought), name='enthought.pkg')
    chaco = PKG(Tree(chaco), name='chaco.pkg')
wx = PKG(Tree(wx), name='wx.pkg')      

sysid = str.lower(sys.platform[:3])
if sysid=='win':
    exename = 'yasso.exe'
else:
    exename = 'yasso'

if ETS_INSTALL == 'EPD':
    exe = EXE(wx,
              enthought,
              pyz,
              a.scripts, #+[("v", "", "OPTION")],
              a.binaries+libfiles,
              a.zipfiles,
              name=pth.join('dist', exename),
              debug= False,
              strip=False,
              upx=False,
              icon='yasso.ico',
              console=False )
else:
    exe = EXE(wx,
              traitswx,
              traitsgui,
              traits,
              enable,
              enthought,
              chaco,
              pyz,
              a.scripts, #+[("v", "", "OPTION")],
              a.binaries+libfiles,
              a.zipfiles,
              name=pth.join('dist', exename),
              debug= True,
              strip=False,
              upx=False,
              icon='yasso.ico',
              console=True )

