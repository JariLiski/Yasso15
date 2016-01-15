# -*- mode: python -*-
import os
import os.path as pth
import sys
import re
import fnmatch
import traits as traits_module

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
    base2 = pth.abspath(pth.join(pth.dirname(traits_module.__file__), '..')) 
    for base in (base2,):
        for item in os.listdir(base):
            if not pth.isdir(pth.join(base, item)):
                continue
                
            print "Comparing", item
            
            if item.lower() == 'traits': 
            	traits = pth.join(base, item)
            	print 'added traits from', item
            if item.lower() == 'traitsui': 
                traitsui = pth.join(base, item)
                print 'added traitsui from', item
            if item.lower() == 'enable': 
                enable = pth.join(base, item)
                print 'added enable from', item
            if item.lower() ==  'chaco': 
                chaco = pth.join(base, item)
                print 'added chaco from', item
            if item.lower().startswith('wx-2.8'): 
                wx = pth.join(base, item)
                print 'added wx from', item
            if item.lower() == 'pyface':
                pyface = pth.join(base, item)
                print 'added pyface from', item
            if item.lower() == 'kiva':
                kiva = pth.join(base, item)
                print 'added kiva from', item

basefiles = [#pth.join(HOMEPATH,'support/_mountzlib.py'),
              #pth.join(base, 'pkg_resources.py'),
              #pth.join(HOMEPATH,'support/useUnicode.py'),
              'unpackMetadata_conda.py',
              '../yasso.py',
              '../modelcall.py',
              ]


hidden_extras = ['enable.wx', 'enable.wx.image', 'pyface.ui.wx.init', 'pyface.ui.wx.timer.timer', 'pyface.ui.wx.timer.do_later',
                 'pyface.ui.wx.about_dialog', 'pyface.ui.wx.application_window', 'pyface.ui.wx.beep', 
                 'pyface.ui.wx.clipboard', 'pyface.ui.wx.confirmation_dialog', 'pyface.ui.wx.dialog', 'pyface.ui.wx.directory_dialog', 'pyface.ui.wx.file_dialog', 'pyface.ui.wx.gui', 'pyface.ui.wx.heading_text', 'pyface.ui.wx.image_cache', 'pyface.ui.wx.image_resource', 'pyface.ui.wx.init', #'pyface.ui.wx.ipython_widget', 
                 'pyface.ui.wx.message_dialog', 'pyface.ui.wx.progress_dialog', 'pyface.ui.wx.python_editor', 'pyface.ui.wx.python_shell', 'pyface.ui.wx.resource_manager', 'pyface.ui.wx.splash_screen', 'pyface.ui.wx.split_widget', 'pyface.ui.wx.system_metrics', 'pyface.ui.wx.widget', 'pyface.ui.wx.window', 'pyface.ui.wx.__init__',
                 'pyface.ui.wx.action.action_item', 'pyface.ui.wx.action.menu_bar_manager', 'pyface.ui.wx.action.menu_manager', 'pyface.ui.wx.action.status_bar_manager', 'pyface.ui.wx.action.tool_bar_manager', 'pyface.ui.wx.action.tool_palette', 'pyface.ui.wx.action.tool_palette_manager', 'pyface.ui.wx.action.__init__',
                            
                 'traits.adapter', 'traits.api', 'traits.category', 'traits.has_dynamic_views', 'traits.has_traits', 'traits.interface_checker', 'traits.traits', 'traits.traits_listener', 'traits.trait_base', 'traits.trait_errors', 'traits.trait_handlers', 'traits.trait_notifiers', 'traits.trait_numeric', 'traits.trait_types', 'traits.trait_value', 'traits.ustr_trait', 'traits.__init__']

hidden_extras = ['enable.wx', 'enable.wx.image', 'pyface.ui.wx.init', 
                 'pyface.ui.wx.timer.timer', 'pyface.ui.wx.timer.do_later',
                 'kiva']
              
a = Analysis(basefiles,
             pathex=[''],
             hookspath=[''],
             hiddenimports=hidden_extras,
             excludes=['wx', 'traits', 'traitsui', 'pyface', 'enable', 'chaco'])
if ETS_INSTALL == 'EPD':
    pyz = PYZ(a.pure)
    enthought = PKG(Tree(enthought), name='enthought.pkg')
else:
    pyz = PYZ(a.pure)
    traits = PKG(Tree(traits), name='traits.pkg')
    traitsui = PKG(Tree(traitsui), name='traitsui.pkg')
    enable = PKG(Tree(enable), name='enable.pkg')
    chaco = PKG(Tree(chaco), name='chaco.pkg')
    pyface = PKG(Tree(pyface), name='pyface.pkg')
    kiva = PKG(Tree(kiva), name="kiva.pkg")
wx = PKG(Tree(wx), name='wx.pkg')

sysid = str.lower(sys.platform[:3])
if sysid=='win':
    exename = 'yasso.exe'
else:
    exename = 'yasso'



exclude_dlls = [('powrprof.dll', '', ''),
               ('secur32.dll', '', ''),
               ('crypt32.dll', '', ''),
               ('mswsock.dll', '', ''),
               ('shfolder.dll', '', ''),
               ('API-MS-Win-Core-ErrorHandling-L1-1-0.dll', '', ''),
               ('API-MS-Win-Core-Interlocked-L1-1-0.dll', '', ''),
               ('API-MS-Win-Core-LibraryLoader-L1-1-0.dll', '', ''),
               ('API-MS-Win-Core-LocalRegistry-L1-1-0.dll', '', ''),
               ('API-MS-Win-Core-Misc-L1-1-0.dll', '', ''),
               ('API-MS-Win-Core-ProcessThreads-L1-1-0.dll', '', ''),
               ('API-MS-Win-Core-Profile-L1-1-0.dll', '', ''),
               ('API-MS-Win-Core-Synch-L1-1-0.dll', '', ''),
               ('API-MS-Win-Core-SysInfo-L1-1-0.dll', '', ''),
               ('API-MS-Win-Security-Base-L1-1-0.dll', '', ''),
               ('HID.dll', '', ''),
               ('SETUPAPI.dll', '', ''),
               ('CFGMGR.dll', '', ''),
               ('DEVOBJ.dll', '', ''),
               ('MSASN1.dll', '', ''),
               ('Microsoft.VC90.CRT.manifest', '', ''),
               ('msvcm90.dll', '', ''),
               ('msvcp90.dll', '', ''),
               ('msvcr90.dll', '', ''),]
               
    
    
if ETS_INSTALL == 'EPD':
    exe = EXE(wx,
              #enthought,
              pyz,
              a.scripts, #+[("v", "", "OPTION")],
              a.binaries+libfiles,
              a.zipfiles,
              name=pth.join('dist', exename),
              debug=False,
              strip=False,
              upx=False,
              icon='..\yasso.ico',
              console=False )
else:
    exe = EXE(wx,
              pyface,
              traitsui,
              traits,
              enable,
              chaco,
              kiva,
              pyz,
              a.scripts, # +[("v", "", "OPTION")],
              a.binaries - exclude_dlls + libfiles,
              a.zipfiles,
              exclude_binaries=0,
              name=pth.join('dist', exename),
              debug=False,
              strip=False,
              upx=False,
              icon='..\yasso.ico',
              console=False
              )
    coll = COLLECT( exe,
                   a.binaries-exclude_dlls+libfiles,
                   a.zipfiles,
                   a.datas,
                   strip=False,
                   upx=False,
                   name=os.path.join('dist', 'bin'))
