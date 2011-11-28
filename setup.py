# from: http://tinyurl.com/d9642fv

from distutils.core import setup
import py2exe
import os
import glob

includes = []
includes.append('numpy')
includes.append('numpy.core')
#includes.append('configobj')
#includes.append('scipy')
#includes.append('xml')
#includes.append('xml.etree')
#includes.append('xml.etree.*')

includes.append('wx')
includes.append('wx.*')

includes.append('traits')
includes.append('traitsui')
includes.append('traitsui.*')
includes.append('traitsui.editors')
includes.append('traitsui.editors.*')
includes.append('traitsui.extras')
includes.append('traitsui.extras.*')

includes.append('traitsui.wx')
includes.append('traitsui.wx.*')

includes.append('kiva')

includes.append('chaco')
includes.append('chaco.*')

includes.append('pyface')
includes.append('pyface.*')
includes.append('pyface.wx')

includes.append('pyface.ui.wx')
includes.append('pyface.ui.wx.init')
includes.append('pyface.ui.wx.*')
includes.append('pyface.ui.wx.grid.*')
includes.append('pyface.ui.wx.action.*')
includes.append('pyface.ui.wx.timer.*')
includes.append('pyface.ui.wx.wizard.*')
includes.append('pyface.ui.wx.workbench.*')

includes.append('enable')
includes.append('enable.drawing')
includes.append('enable.tools')
includes.append('enable.wx')
includes.append('enable.wx.*')

includes.append('enable.savage')
includes.append('enable.savage.*')
includes.append('enable.savage.svg')
includes.append('enable.savage.svg.*')
includes.append('enable.savage.svg.backends')
includes.append('enable.savage.svg.backends.wx')
includes.append('enable.savage.svg.backends.wx.*')
includes.append('enable.savage.svg.css')
includes.append('enable.savage.compliance')
includes.append('enable.savage.trait_defs')
includes.append('enable.savage.trait_defs.*')
includes.append('enable.savage.trait_defs.ui')
includes.append('enable.savage.trait_defs.ui.*')
includes.append('enable.savage.trait_defs.ui.wx')
includes.append('enable.savage.trait_defs.ui.wx.*')

packages = []

data_folders = []

# Traited apps:
ETS_folder = r'C:\Python27_EPD\Lib\site-packages'

data_folders.append((os.path.join(ETS_folder,r'chaco\tools\toolbars\images'),
                     r'chaco\tools\toolbars\images'))
data_folders.append(( os.path.join(ETS_folder,r'enable\images'),
                     r'enable/images'))
data_folders.append(( os.path.join(ETS_folder,r'pyface\images'),
                     r'pyface\images'))
data_folders.append(( os.path.join(ETS_folder,r'pyface\action\images'),
                     r'pyface\action\images'))
data_folders.append(( os.path.join(ETS_folder,r'pyface\dock\images'),
                     r'pyface\dock\images'))
data_folders.append(( os.path.join(ETS_folder,r'pyface\tree\images'),
                     r'pyface\tree\images'))
data_folders.append(( os.path.join(ETS_folder,r'pyface\ui\wx\images'),
                     r'pyface\ui\wx\images'))
data_folders.append((os.path.join(ETS_folder,r'pyface\ui\wx\grid\images'),
                     r'pyface\ui\wx\grid\images'))
data_folders.append((os.path.join(ETS_folder,r'traitsui\wx\images'),
                     r'traitsui\wx\images'))
data_folders.append((os.path.join(ETS_folder,r'traitsui\image\library'),
                     r'traitsui\image\library'))

data_folders.append((os.path.join(ETS_folder,r'enable\savage\compliance\images'),
                     r'enable\savage\compliance\images'))
data_folders.append((os.path.join(ETS_folder,r'enable\savage\trait_defs\ui\wx\data'),
                     r'enable\savage\trait_defs\ui\wx\data'))

data_files = []
# Matplotlib
#import matplotlib as mpl
#data_files = mpl.get_py2exe_datafiles()

# Parsing folders and building the data_files table
for folder, relative_path in data_folders:
    for file in os.listdir(folder):
        f1 = os.path.join(folder,file)
        if os.path.isfile(f1): # skip directories
            f2 = relative_path, [f1]
            data_files.append(f2)

data_files.append((r'enable',[os.path.join(ETS_folder,r'enable\images.zip')]))

setup(windows=[{'script': 'yasso.py',
                'icon_resources': [(1,'yasso.ico')],
               }],
    author="Simosol Oy",
    version = "1.1",
    description = "Yasso07 user interface",
    name = "Yasso07UI",
    options = {"py2exe": {"optimize": 0,
                          "packages": packages,
                          "includes": includes,
                          "dist_dir": 'dist',
                          "bundle_files":2,
                          "xref": False,
                          "skip_archive": True,
                          "ascii": False,
                          "custom_boot_script": '',
                          "compressed":False,
                          },},
    data_files=data_files)

