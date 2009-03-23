# -*- mode: python -*-

import os
import sys
import re
import enthought
base = os.path.abspath(os.path.join(os.path.dirname(enthought.__file__), '..', '..')) 

sys_id = str.lower(sys.platform[:3])
libfiles = []
if sys_id == 'lin':
    print 'Finding additional library files...'
    try:
        filelist = os.listdir('/usr/lib')
        for file in filelist:
            if (file.startswith('libwx') or file.startswith('libgfortran')) and \
               re.search(r'so[.][0-9]$', file):
                target = file
                try:
                    target = os.readlink(os.path.join('/usr/lib', file))
                except OSError:
                    pass
                if not target.startswith('/usr/lib'): 
                    target = os.path.join('/usr/lib', file)
                print 'Adding', target, 'as', file
                libfiles.append((file, target, 'BINARY'))
    except OSError, err:
        print err
#THE FOLLOWING IS REQUIRED IF YOU INCLUDE SCIPY!
#    try:
#        filelist = os.listdir('/usr/lib/atlas')
#        for file in filelist:
#            if re.search(r'3gf$', file):
#                target = file
#                try:
#                    target = os.readlink(os.path.join('/usr/lib/atlas', file))
#                except OSError:
#                    pass
#                if not target.startswith('/usr/lib/atlas'): 
#                    target = os.path.join('/usr/lib/atlas', file)
#                print 'Adding', target, 'as', file
#                libfiles.append((file, target, 'BINARY'))
#    except OSError, err:
#        print err
#    filelist = ['libf77blas.so.3gf', 'libcblas.so.3gf', 'libblas.so.3gf', 
#            'libatlas.so.3gf', 'libblas.so.3', 'libgslcblas.so.0']
#    for file in filelist:
#        if os.path.exists(os.path.join('/usr/lib', file)):
#            target = file
#            try:
#                target = os.readlink(os.path.join('/usr/lib', file))
#            except OSError:
#                pass
#            if not target.startswith('/usr/lib'): 
#                target = os.path.join('/usr/lib', file)
#            print 'Adding', target, 'as', file
#            libfiles.append((file, target, 'BINARY'))

for item in os.listdir(base):
    if item.startswith('Traits-'): 
        traits = os.path.join(base, item)
        print 'added traits from', item
    if item.startswith('TraitsGUI'): 
        traitsgui = os.path.join(base, item)
        print 'added traitsgui from', item
    if item.startswith('TraitsBackendWX'): 
        traitswx = os.path.join(base, item)
        print 'added traitswx from', item
    if item.startswith('Enable'): 
        enable = os.path.join(base, item)
        print 'added enable from', item
    if item.startswith('Enthought'): 
        enthought = os.path.join(base, item)
        print 'added enthought from', item
    if item.startswith('Chaco'): 
        chaco = os.path.join(base, item)
        print 'added chaco from', item
    if item.startswith('wx-'): 
        wx = os.path.join(base, item)
        print 'added wx from', item

basefiles = [os.path.join(HOMEPATH,'support/_mountzlib.py'),
              #os.path.join(HOMEPATH,'support/unpackTK.py'),
              #os.path.join(HOMEPATH,'support/useTK.py'),
              os.path.join(HOMEPATH,'support/useUnicode.py'),
              os.path.join(base, 'pkg_resources.py'),
              'unpackMetadata.py',
              '../yasso.py',
              '../modelcall.py',
              #os.path.join(HOMEPATH,'support/removeTK.py'),
              ]
a = Analysis(basefiles,
             pathex=[''],
             hookspath=[''],
             excludes=['enthought', 'wx'])
#DEBUG
#print "Appending extra libraries", libfiles
pyz = PYZ(a.pure)
wx = PKG(Tree(wx), name='wx.pkg')      
traits = PKG(Tree(traits), name='traits.pkg')
traitsgui = PKG(Tree(traitsgui), name='traitsgui.pkg')
traitswx = PKG(Tree(traitswx), name='traitswx.pkg')
enable = PKG(Tree(enable), name='enable.pkg')
enthought = PKG(Tree(enthought), name='enthought.pkg')
chaco = PKG(Tree(chaco), name='chaco.pkg')

sysid = str.lower(sys.platform[:3])
if sysid=='win':
    exename = 'yasso.exe'
else:
    exename = 'yasso'

exe = EXE(#TkPKG(), 
          wx,
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
          name=os.path.join('dist', exename),
          debug= False,
          strip=False,
          upx=False,
          icon='yasso.ico',
          console=False )
