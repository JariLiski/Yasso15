# -*- mode: python -*-

import os
import sys
import enthought.traits.ui.wx

base = os.path.dirname(enthought.traits.ui.wx.__file__)
walker = os.walk(base)
files = []
for item in walker:
    if not '.svn' in item[0]:
        for file in item[2]:
            if file != '__init__.py' and file.endswith('.py'):
                filename = os.path.join(item[0], file)
                #print 'adding', filename, 'to analysis...'
                files.append(filename)

import enthought
base = os.path.abspath(os.path.join(os.path.dirname(enthought.__file__), '..', '..')) 
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

basefiles = [os.path.join(HOMEPATH,'support/_mountzlib.py'),
              #os.path.join(HOMEPATH,'support/unpackTK.py'),
              #os.path.join(HOMEPATH,'support/useTK.py'),
              os.path.join(HOMEPATH,'support/useUnicode.py'),
              'unpackMetadata.py',
              '../yasso.py',
              '../modelcall.py',
              #os.path.join(HOMEPATH,'support/removeTK.py'),
              ]
basefiles.extend(files)
a = Analysis(basefiles,
             pathex=[''],
             hookspath=[''])
pyz = PYZ(a.pure)
        
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
          traitswx,
          traitsgui,
          traits,
          enable,
          enthought,
          chaco,
          pyz,
          a.scripts +[("v", "", "OPTION")],
          a.binaries,
          a.zipfiles,
          name=os.path.join('dist', exename),
          debug= True,
          strip=False,
          upx=False,
          console=True )
