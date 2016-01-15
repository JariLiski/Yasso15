#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from collections import defaultdict
import ConfigParser
import codecs
import re
import sys
import os
import glob


# Redirecting stderr
sys.stderr = codecs.open('yasso_stderr.log', 'w', 'utf8')

from numpy import empty, float32

from traits.api import Array, Button, Enum, Float, HasTraits,\
    Instance, Int, List, Range, Str
    
from traitsui.api import CodeEditor, Group, HGroup, VGroup, Item,\
    Label, spring, TabularEditor, View, EnumEditor
from traitsui.menu import \
    UndoAction, RedoAction, RevertAction, CloseAction, \
    Menu, MenuBar, NoButtons
from traitsui.file_dialog import open_file, save_file
from traitsui.message import error
from traits.trait_errors import TraitError
from traitsui.tabular_adapter import TabularAdapter
from chaco.api import ArrayPlotData, Plot, GridContainer
from enable.component_editor import ComponentEditor

from modelcall import ModelRunner
import sys


APP_INFO="""
For detailed information, including a user's manual, see:
http://www.syke.fi/projects/yasso

Inside the program help is available by clicking the label texts.
Program wiki is at https://github.com/JariLiski/Yasso15

Yasso15 model by Finnish Environment Institute (SYKE, www.environment.fi)
User interface by Simosol Oy (www.simosol.fi)

The program is distributed under the GNU Lesser General Public License (LGPL)
The source code is available at https://github.com/JariLiski/Yasso15
"""

DATA_STRING = """
# THE CHANGES YOU MAKE HERE HAVE ONLY EFFECT AFTER YOU SAVE THE CHANGES
#
# commented out rows begin with the # character
# numbers must be whitespace separated (space or tab)
# decimal separator is ., no thousands separator
#
[Initial state]
# Data as value pairs, mean and standard deviation, except for the size of
# woody litter mean only
# Mass as unit of mass, chemical composition as percentages of the total mass,
# size of woody litter as diameter in cm
# Data: mass, acid hydrolyzable, water soluble, ethanol soluble, non-soluble,
# humus, size of woody litter (diameter in cm)

[Constant soil carbon input]
# Data as value pairs, mean and standard deviation, except for the size of
# woody litter mean only
# Mass as unit of mass, chemical composition as percentages of the total mass,
# size of woody litter as diameter in cm
# Data: mass, acid hydrolyzable, water soluble, ethanol soluble, non-soluble,
# humus, size of woody litter (diameter in cm)

[Monthly soil carbon input]
# Data as value pairs, mean and standard deviation, except for the size of
# woody litter mean only
# Mass as unit of mass, chemical composition as percentages of the total mass,
# size of woody litter as diameter in cm
# Data: month, mass, acid hydrolyzable, water soluble, ethanol soluble,
# non-soluble, humus, size of woody litter (diameter in cm)

[Yearly soil carbon input]
# Data as value pairs, mean and standard deviation, except for the size of
# woody litter mean only
# Mass as unit of mass, chemical composition as percentages of the total mass,
# size of woody litter as diameter in cm
# Data: year, mass, acid hydrolyzable, water soluble,
# ethanol soluble, non-soluble, humus, size of woody litter (diameter in cm)

[Relative area change]
# Timestep, relative change in area

[Constant climate]
# Data: mean temperature, precipitation, amplitude of monthly mean temperature
# variation

[Yearly climate]
# Data: timestep, mean temperature, precipitation

[Monthly climate]
# Data: timestep, mean temperature, precipitation
"""
from pyface.image_resource import ImageResource
app_ir = ImageResource("yasso.ico")


def _get_parameter_files():
    """
    Extracts the available parameter files from the param sub folder
    """
    fn = os.path.split(sys.executable)
    if fn[1].lower().startswith('python'):
        exedir = os.path.abspath(os.path.split(sys.argv[0])[0])
    else:
        exedir = fn[0]
    join = os.path.join
    pdir = join(exedir, 'param')
    if os.path.exists(pdir):
        p_files = glob.glob(join(pdir, '*.dat'))
        pset = []
        for f in p_files:
            p = os.path.basename(f).split('.')[0]
            pset.append(p)
        
        return pset
    else:
        print "Not finding the parameter directory", pdir
        errmsg = 'The model parameter directory param is missing. '\
                 'It must be in the same directory as the program '\
                 'executable'
        error(errmsg, title='Error starting the program',
              buttons=['OK'])
        sys.exit(-1)

###############################################################################
# Basic data container classes
###############################################################################

class LitterComponent(HasTraits):
    mass = Float()
    mass_std = Float()
    acid = Range(low=0.0, high=100.0)
    acid_std = Float()
    water = Range(low=0.0, high=100.0)
    water_std = Float()
    ethanol = Range(low=0.0, high=100.0)
    ethanol_std = Float()
    non_soluble = Range(low=0.0, high=100.0)
    non_soluble_std = Float()
    humus = Range(low=0.0, high=100.0)
    humus_std = Float()
    size_class = Float(default=0.0)

class TimedLitterComponent(HasTraits):
    timestep = Int()
    mass = Float()
    mass_std = Float()
    acid = Range(low=0.0, high=100.0)
    acid_std = Float()
    water = Range(low=0.0, high=100.0)
    water_std = Float()
    ethanol = Range(low=0.0, high=100.0)
    ethanol_std = Float()
    non_soluble = Range(low=0.0, high=100.0)
    non_soluble_std = Float()
    humus = Range(low=0.0, high=100.0)
    humus_std = Float()
    size_class = Float(default_value=0.0)

class AreaChange(HasTraits):
    timestep = Int()
    rel_change = Float()

class YearlyClimate(HasTraits):
    timestep = Int()
    mean_temperature = Float()
    annual_rainfall = Float()
    variation_amplitude = Float()

class MonthlyClimate(HasTraits):
    month = Int()
    temperature = Float()
    rainfall = Float()

###############################################################################
# Table editors
###############################################################################


class MonthlyClimateAdapter(TabularAdapter):
    columns = [('month', 'month'), ('temperature', 'temperature'),
               ('rainfall', 'rainfall')]
    font  = 'Arial 9'
    default_value = MonthlyClimate()

monthly_climate_te = TabularEditor(
    adapter = MonthlyClimateAdapter(),
    editable = False,
    )

class YearlyClimateAdapter(TabularAdapter):
    columns = [('timestep', 'timestep'), ('mean temp', 'mean_temperature'),
               ('annual rainfall', 'annual_rainfall'),
               ('temp variation amplitude', 'variation_amplitude')]
    font  = 'Arial 9'
    default_value = YearlyClimate()

yearly_climate_te = TabularEditor(
    adapter = YearlyClimateAdapter(),
    editable = False,
    )

class LitterAdapter(TabularAdapter):
    columns = [('mass', 'mass'),
               ('mass std', 'mass_std'), ('A', 'acid'),
               ('A std', 'acid_std'), ('W', 'water'),
               ('W std', 'water_std'), ('E', 'ethanol'),
               ('E std', 'ethanol_std'), ('N', 'non_soluble'),
               ('N std', 'non_soluble_std'), ('H', 'humus'),
               ('H std', 'humus_std'), ('size class', 'size_class')]
    font = 'Arial 9'
    acid_width = 50
    acid_std_width = 50
    default_value = LitterComponent()

litter_te = TabularEditor(
    adapter = LitterAdapter(),
    editable = False,
    )

class ChangeAdapter(TabularAdapter):
    columns = [('timestep', 'timestep'),
               ('relative change in area', 'rel_change')]
    font = 'Arial 9'
    default_value = AreaChange()

change_te = TabularEditor(
    adapter = ChangeAdapter(),
    editable = False,
    )

class TimedLitterAdapter(TabularAdapter):
    columns = [('timestep', 'timestep'),('mass', 'mass'),
               ('mass std', 'mass_std'), ('A', 'acid'),
               ('A std', 'acid_std'), ('W', 'water'),
               ('W std', 'water_std'), ('E', 'ethanol'),
               ('E std', 'ethanol_std'), ('N', 'non_soluble'),
               ('N std', 'non_soluble_std'), ('H', 'humus'),
               ('H std', 'humus_std'), ('size class', 'size_class')]
    font = 'Arial 9'
    acid_width = 50
    acid_std_width = 50
    default_value = TimedLitterComponent()

timed_litter_te = TabularEditor(
    adapter = TimedLitterAdapter(),
    editable = False,
    )

class CStockAdapter(TabularAdapter):
    columns = [('sample', 0), ('time step', 1), ('total om', 2),
               ('woody om', 3), ('non-woody om', 4), ('acid', 5),
               ('water', 6), ('ethanol', 7), ('non soluble', 8), ('humus', 9)]
    font        = 'Courier 10'
    alignment   = 'right'
    format      = '%.4f'

c_stock_te = TabularEditor(
    adapter = CStockAdapter(),
   )

class CO2YieldAdapter(TabularAdapter):
    columns = [('sample', 0), ('time step', 1), ('CO2 production', 2)]
    font        = 'Courier 10'
    alignment   = 'right'
    format      = '%.4f'


co2_yield_te = TabularEditor(
    adapter = CO2YieldAdapter(),
   )
   

###############################################################################
# Yasso model
###############################################################################


class Yasso(HasTraits):
    """
    The Yasso model
    """
    # Parameters
    p_sets = _get_parameter_files()
    parameter_set = Enum(p_sets)
    
    leaching = Float()
    # Initial condition
    initial_mode = Enum(['non zero', 'zero', 'steady state'])
    initial_litter = List(trait=LitterComponent)
    steady_state = List(trait=LitterComponent)
    # Litter input at each timestep in the simulation
    litter_mode = Enum(['zero', 'yearly', 'constant yearly', 'monthly'])
    constant_litter = List(trait=LitterComponent)
    monthly_litter = List(trait=TimedLitterComponent)
    yearly_litter = List(trait=TimedLitterComponent)
    zero_litter = List(trait=LitterComponent) # Assumes that this defaults to 0
    woody_size_limit = Float(default_value=3.0)
    area_change = List(trait=AreaChange)
    # Climate definition for the simulation
    climate_mode = Enum(['yearly', 'constant yearly', 'monthly'])
    constant_climate = YearlyClimate()
    monthly_climate = List(trait=MonthlyClimate,
            value=[MonthlyClimate(month=1),
                   MonthlyClimate(month=2),
                   MonthlyClimate(month=3),
                   MonthlyClimate(month=4),
                   MonthlyClimate(month=5),
                   MonthlyClimate(month=6),
                   MonthlyClimate(month=7),
                   MonthlyClimate(month=8),
                   MonthlyClimate(month=9),
                   MonthlyClimate(month=10),
                   MonthlyClimate(month=11),
                   MonthlyClimate(month=12)]
            )
    yearly_climate = List(trait=YearlyClimate)
    # All data as text
    all_data = Str()
    data_file = Str()
    # How the model will be run
    sample_size = Int()
    duration_unit = Enum(['year', 'month'])
    timestep_length = Range(low=1)
    simulation_length = Range(low=1)
    result_type = Enum(['C stock', 'C change', 'CO2 production'])
    presentation_type = Enum(['chart', 'array'])
    chart_type = Enum(['common scale', 'autofit'])
    # Buttons
    new_data_file_event = Button('New...')
    open_data_file_event = Button('Open...')
    save_data_file_event = Button('Save')
    save_as_file_event = Button('Save as...')
    modelrun_event = Button('Run model')
    save_result_event = Button('Save raw results...')
    save_moment_event = Button('Save moment results...')
    # and the results stored
    # Individual model calls
    #     iteration,time, total, woody, acid, water, ethanol, non_soluble, humus
    c_stock = Array(dtype=float32, shape=(None, 10))
    #     iteration,time, total, woody, acid, water, ethanol, non_soluble, humus
    c_change = Array(dtype=float32, shape=(None, 10))
    #     time, iteration, CO2 production
    co2_yield = Array(dtype=float32, shape=(None, 3))
    # time, mean, mode, var, skewness, kurtosis, 95% conf-, 95% conf+
    stock_tom = Array(dtype=float32, shape=(None, 8))
    stock_woody = Array(dtype=float32, shape=(None, 8))
    stock_non_woody = Array(dtype=float32, shape=(None, 8))
    stock_acid = Array(dtype=float32, shape=(None, 8))
    stock_water = Array(dtype=float32, shape=(None, 8))
    stock_ethanol = Array(dtype=float32, shape=(None, 8))
    stock_non_soluble = Array(dtype=float32, shape=(None, 8))
    stock_humus = Array(dtype=float32, shape=(None, 8))
    change_tom = Array(dtype=float32, shape=(None, 8))
    change_woody = Array(dtype=float32, shape=(None, 8))
    change_non_woody = Array(dtype=float32, shape=(None, 8))
    change_acid = Array(dtype=float32, shape=(None, 8))
    change_water = Array(dtype=float32, shape=(None, 8))
    change_ethanol = Array(dtype=float32, shape=(None, 8))
    change_non_soluble = Array(dtype=float32, shape=(None, 8))
    change_humus = Array(dtype=float32, shape=(None, 8))
    co2 = Array(dtype=float32, shape=(None, 8))
    # plot variables
    stock_plots = Instance(GridContainer)
    change_plots = Instance(GridContainer)
    co2_plot = Instance(GridContainer)
    p_timestep = Array()
    ps_tom = Array()
    ps_woody = Array()
    ps_non_woody = Array()
    ps_acid = Array()
    ps_water = Array()
    ps_ethanol = Array()
    ps_non_soluble = Array()
    ps_humus = Array()
    pc_tom = Array()
    pc_non_woody = Array()
    pc_acid = Array()
    pc_water = Array()
    pc_ethanol = Array()
    pc_non_soluble = Array()
    pc_humus = Array()
    

#############################################################
# UI view
#############################################################

    view = View(
        VGroup(
            HGroup(
                Item('new_data_file_event', show_label=False,),
                Item('open_data_file_event', show_label=False,),
                Item('save_data_file_event', show_label=False,),
                Item('save_as_file_event', show_label=False,),
                Item('data_file', style='readonly', show_label=False,),
                ),
            HGroup(
                Item('all_data', show_label=False, editor=CodeEditor(),
                     has_focus=True,
                     width=300, height=400,
                     ),
                ),
            label='All data',
            ),
        VGroup(
            HGroup(
                Item('parameter_set', width=-145),
                Item('leaching', width=-45,
                     label='Leaching parameter',
                     visible_when='initial_mode!="steady state"'),
                show_border=True,
                
            ),
            VGroup(
                HGroup(
                    Item(name='initial_mode', style='custom',
                         label='Initial state:', emphasized=True,
                         ),
                    ),
                Item('initial_litter',
                     visible_when='initial_mode=="non zero"',
                     show_label=False, editor=litter_te,
                     width=790, height=75,
                    ),
                ),
            VGroup(
                HGroup(
                    Item('litter_mode', style='custom',
                         label='Soil carbon input:', emphasized=True
                         )
                    ),
                HGroup(
                    Item('constant_litter',
                         visible_when='litter_mode=="constant yearly"',
                         show_label=False, editor=litter_te,
                         full_size=False, springy=False,
                         #width=-790, height=-75
                         ),
                    Item('monthly_litter',
                         visible_when='litter_mode=="monthly"',
                         show_label=False, editor=timed_litter_te,
                         full_size=False, springy=False,
                         #width=-790, height=-75
                         ),
                    Item('yearly_litter',
                         visible_when='litter_mode=="yearly"',
                         show_label=False, editor=timed_litter_te,
                         full_size=False, springy=False,
                         #width=-790,height=-75
                         ),
                    ),
                HGroup(
                    Item('area_change',
                         visible_when='litter_mode=="yearly" or '\
                                      'litter_mode=="monthly"',
                         show_label=False, editor=change_te,
                         full_size=False, springy=False,
                         width=-150,height=-75
                         ),
                    spring,
                    ),
                ),
            VGroup(
                HGroup(
                    Item('climate_mode', style='custom',
                        label='Climate:', emphasized=True,
                        ),
                    ),
                HGroup(
                    Item('monthly_climate', show_label=False,
                         visible_when='climate_mode=="monthly"',
                         editor=monthly_climate_te, width=200, height=75
                         ),
                    Item('yearly_climate', show_label=False,
                        visible_when='climate_mode=="yearly"',
                        editor=yearly_climate_te, width=200, height=75
                        ),
                    VGroup(
                        Item('object.constant_climate.mean_temperature',
                              style='readonly',),
                        Item('object.constant_climate.annual_rainfall',
                              style='readonly',),
                        Item('object.constant_climate.variation_amplitude',
                              style='readonly',),
                        show_border=True,
                        visible_when='climate_mode=="constant yearly"'
                        ),
                    ),
                ),
            label='Data to use',
            ),
        VGroup(
            Group(
                HGroup(
                    Item('sample_size', width=-45,
                         ),
                    Item('simulation_length', width=-45,
                         label='Number of timesteps',
                         ),
                    Item('timestep_length', width=-45,
                         ),
                    Item('duration_unit', style='custom',
                         show_label=False,),
                    ),
                HGroup(
                    Item('woody_size_limit', width=-45,
                         ),
                    Item('modelrun_event', show_label=False),
                    ),
                show_border=True
            ),
            HGroup(
                Item('result_type', style='custom', label='Show',
                     emphasized=True, ),
                Item('save_result_event', show_label=False,),
                Item('save_moment_event', show_label=False,),
                ),
            HGroup(
                Item('presentation_type', style='custom', label='As',
                     emphasized=True, ),
                Item('chart_type', style='custom', label='Chart type',
                     visible_when='presentation_type=="chart"'),
                ),
            HGroup(
                Item('c_stock', visible_when='result_type=="C stock" and \
                      presentation_type=="array"', show_label=False,
                      editor=c_stock_te, #width=600
                      ),
                Item('c_change', visible_when='result_type=="C change" and \
                      presentation_type=="array"', show_label=False,
                      editor=c_stock_te,),
                Item('co2_yield', visible_when='result_type=="CO2 production" '\
                      'and presentation_type=="array"', show_label=False,
                      editor=co2_yield_te,),
                Item('stock_plots', editor=ComponentEditor(),
                     show_label=False,
                     visible_when='result_type=="C stock" and \
                                  presentation_type=="chart"',),
                Item('change_plots', editor=ComponentEditor(),
                     show_label=False,
                     visible_when='result_type=="C change" and \
                                  presentation_type=="chart"',),
                Item('co2_plot', editor=ComponentEditor(),
                     show_label=False,
                     visible_when='result_type=="CO2 production" and \
                                  presentation_type=="chart"',),
                ),
            label='Model run',
            ),
        VGroup(
            Label(label='Yasso15 soil carbon model', emphasized=True),
            Label(label="<placeholder>", id="about_text"),
            label='About',
            ),
        title     = 'Yasso 15',
        id        = 'simosol.yasso15',
        dock      = 'horizontal',
        width     = 800,
        height    = 600,
        resizable = True,
        scrollable= True,
        buttons=NoButtons,
        icon=app_ir,
        menubar = MenuBar(
            Menu(CloseAction, name = 'File'),
            Menu(UndoAction, RedoAction, RevertAction, name = 'Edit'),
            ),
        help=False,
        )


###############################################################################
# Initialisation
###############################################################################

    def __init__(self):
        self.sample_size = 10
        self.simulation_length = 10
        fn = os.path.split(sys.executable)
        if fn[1].lower().startswith('python'):
            exedir = os.path.abspath(os.path.split(sys.argv[0])[0])
            self.data_file = self._get_data_file_path(exedir)
        else:
            self.data_file = self._get_data_file_path(fn[0])
        try:
            f = codecs.open(self.data_file, 'r', 'utf8')
            self._load_all_data(f)
            f.close()
        except:
            self.all_data = DATA_STRING
            self.data_file = ''
            
        try:
            cfg = ConfigParser.ConfigParser()

            
            fn = os.path.split(sys.executable)
            if fn[1].lower().startswith('python'):
                exedir = os.path.abspath(os.path.split(sys.argv[0])[0])
            else:
                exedir = fn[0]
            
            inipath = os.path.join(exedir, 'yasso.ini')
            cfg.readfp(codecs.open(inipath, "r", "utf8"))
            about_text = cfg.get("about", "text")
            about_text = about_text.replace("\\n", "\n")
            
            default_param = cfg.get("data", "default_param")
            if default_param in self.p_sets:
                self.parameter_set = default_param
            
            self.trait_view('about_text').label = about_text
            
        except Exception as error:
            print "Error reading yasso.ini. See the error log for details."
            raise error
            
                

    def _get_data_file_path(self, exedir):
        join = os.path.join
        self.state_file = join(exedir, 'yasso.state')
        if os.path.exists(self.state_file):
            f = codecs.open(self.state_file, 'r', 'utf8')
            datafile = f.read()
            if len(datafile)>0 and datafile[-1]=='\n':
                datafile = datafile[:-1]
            f.close()
            if not os.path.exists(datafile):
                os.remove(self.state_file)
                datafile = join(exedir, 'demo_data.txt')
        else:
            datafile = join(exedir, 'demo_data.txt')
        return datafile

    def _write_state(self, filename):
        f = codecs.open(self.state_file, 'w', 'utf8')
        f.write(filename)
        f.close()
        
###############################################################################
# Custom derived properties
###############################################################################

    @property
    def leach_parameter(self):
        """Leach parameter can only be 0 when the initialization mode is
        by steady state. In other cases, the leaching parameter is the
        trait "leaching". This is to be called
        from the YassoModel instead of the traits themselves."""
        if self.initial_mode=='steady state':
            return 0
        else:
            return self.leaching

###############################################################################
# Event handlers
###############################################################################

#########################
# for plot data
#########################

    def _create_stock_plots(self, common_scale=False):
        max = None
        min = 0
        stom, max, min = self._create_plot(max, min, self.stock_tom,
                                      'Total organic matter')
        swoody, max, min = self._create_plot(max, min, self.stock_woody,
                                        'Woody matter')
        snonwoody, max, min = self._create_plot(max, min, self.stock_non_woody,
                                        'Non-woody matter')
        sa, max, min = self._create_plot(max, min, self.stock_acid,
                                         'A')
        sw, max, min = self._create_plot(max, min, self.stock_water,
                                         'W')
        se, max, min = self._create_plot(max, min, self.stock_ethanol,
                                         'E')
        sn, max, min = self._create_plot(max, min, self.stock_non_soluble,
                                         'N')
        sh, max, min = self._create_plot(max, min, self.stock_humus, 'H')
        if common_scale:
            for pl in (stom, swoody, snonwoody, sa, sw, se, sn, sh):
                pl.value_range.set_bounds(min, max)
        container = GridContainer(stom, swoody, snonwoody, sa, sw, se, sn, sh)
        container.shape = (3,3)
        container.spacing = (-8,-8)
        self.stock_plots = container

    def _create_change_plots(self, common_scale=False):
        max = None
        min = 0
        ctom, max, min = self._create_plot(max, min, self.change_tom,
                                           'Total organic matter')
        cwoody, max, min = self._create_plot(max, min, self.change_woody,
                                             'Woody matter')
        cnonwoody, max, min = self._create_plot(max, min, self.change_non_woody,
                                             'Non-woody matter')
        ca, max, min = self._create_plot(max, min, self.change_acid,
                                         'A')
        cw, max, min = self._create_plot(max, min, self.change_water,
                                         'W')
        ce, max, min = self._create_plot(max, min, self.change_ethanol,
                                         'E')
        cn, max, min = self._create_plot(max, min, self.change_non_soluble,
                                         'N')
        ch, max, min = self._create_plot(max, min, self.change_humus, 'H')
        if common_scale:
            for pl in (ctom, cwoody, cnonwoody, ca, cw, ce, cn, ch):
                pl.value_range.set_bounds(min, max)
        container = GridContainer(ctom, cwoody, cnonwoody, ca, cw, ce, cn, ch)
        container.shape = (3,3)
        container.spacing = (-15,-15)
        self.change_plots = container

    def _create_co2_plot(self):
        max = None
        min = 0
        co2, max, min = self._create_plot(max, min, self.co2,
                 'CO2 production (in carbon)')
        container = GridContainer(co2, Plot(), Plot(), Plot())
        container.shape= (2,2)
        self.co2_plot = container

    def _create_plot(self, max, min, dataobj, title):
        x = dataobj[:,0]
        y = dataobj[:,1]
        if y.max()>max:
            max = y.max()
        if y.min()<min:
            min = y.min()
        if self.sample_size>1:
            y2 = dataobj[:,6]
            y3 = dataobj[:,7]
            if y3.max()>max:
                max = y3.max()
            if y2.min()<min:
                min = y2.min()
            plotdata = ArrayPlotData(x=x, y=y, y2=y2, y3=y3)
        else:
            plotdata = ArrayPlotData(x=x, y=y)
        plot = Plot(plotdata)
        plot.plot(("x", "y"), type="line", color="blue")
        if self.sample_size>1:
            plot.plot(("x", "y2"), type="line", color="red")
            plot.plot(("x", "y3"), type="line", color="red")
        plot.title = title
        plot.title_font = 'Arial 10'
        return plot, max, min

########################
# for running the model
########################

    def _modelrun_event_fired(self):
        # set the parameter set to use
        fn = os.path.split(sys.executable)
        if fn[1].lower().startswith('python'):
            exedir = os.path.abspath(os.path.split(sys.argv[0])[0])
        else:
            exedir = fn[0]
        pdir = os.path.join(exedir, 'param')
        parfile = os.path.join(pdir, '%s.dat' % self.parameter_set)
        
        if self.initial_mode=='zero' and self.litter_mode=='zero':
            errmsg = ("Both soil carbon input and initial state may not be "
                     "zero simultaneously.")
            error(errmsg, title='Invalid model parameters', buttons=['OK'])
            return
        
        if self.climate_mode=='yearly' and not self.yearly_climate:
            errmsg = ("Climate mode may not be 'yearly' if there are no "
                      "yearly climate entries in the data file.")
            error(errmsg, title='Invalid model parameters', buttons=['OK'])
            return

        if self.leaching>0:
            errmsg = ("Leaching parameter may not be larger than 0.")
            error(errmsg, title='Invalid model parameters', buttons=['OK'])
            return
        
        if self.climate_mode=='monthly' and not self.monthly_climate:
            errmsg = ("Climate mode may not be 'monthly' if there are no "
                      "monthly climate entries in the data file.")
            error(errmsg, title='Invalid model parameters', buttons=['OK'])
            return
            
            
        yassorunner = ModelRunner(parfile)
        
        if not yassorunner.is_usable_parameter_file():
            errmsg = ("The selected parameter file has wrong number of columns "
                "and cannot be used.")
            error(errmsg, title='Invalid model parameters', buttons=['OK'])
            return
        
        self.yassorunner = yassorunner   
        if self.initial_mode=='steady state':
            steady_state = self.yassorunner.compute_steady_state(self)
            self._set_steady_state(steady_state)
        self._init_results()
        self.c_stock, self.c_change, self.co2_yield = \
                self.yassorunner.run_model(self)
                
        self._create_co2_plot()
        self._chart_type_changed()

########################
# for chart type
########################

    def _chart_type_changed(self):
        if self.chart_type=='autofit':
            self._create_stock_plots()
            self._create_change_plots()
        elif self.chart_type=='common scale':
            self._create_stock_plots(common_scale=True)
            self._create_change_plots(common_scale=True)

########################
# for buttons
########################

    def _new_data_file_event_fired(self):
        filename = save_file()
        if filename != '':
            try:
                self._reset_data()
                f=codecs.open(filename, 'w', 'utf8')
                f.close()
                self.data_file = filename
                self._write_state(filename)
                self.all_data=DATA_STRING
            except:
                pass

    def _open_data_file_event_fired(self):
        filename = open_file()
        if filename != '':
            try:
                f=codecs.open(filename, 'r', 'utf8')
                self.data_file = filename
                self._write_state(filename)
                self._load_all_data(f)
                f.close()
            except:
                pass

    def _save_data_file_event_fired(self):
        if self.data_file=='':
            filename = save_file()
            if filename=='':
                return
            self.data_file = filename
            self._write_state(filename)
        self._save_all_data()

    def _save_as_file_event_fired(self):
        filename = save_file()
        if filename=='':
            return
        self.data_file = filename
        self._write_state(filename)
        self._save_all_data()

    def _load_all_data(self, datafile):
        """
        Loads all data from a single file. Data in sections defined by [name],
        data in whitespace delimited rows
        """
        self._reset_data()
        sectionp = re.compile('\[([\w+\s*]+)\]')
        datap = re.compile('[+-Ee\d+\.\d*\s*]+')
        active = None
        data = defaultdict(list)
        alldata = ''
        linecount = 0
        for line in datafile:
            linecount += 1
            alldata += line
            m = re.match(sectionp, line)
            if m is not None:
                active = m.group(1)
            d = re.match(datap, line)
            if d is not None:
                try:
                    vals = [float(val) for val in d.group(0).split()]
                    data[active].append(vals)
                except ValueError:
                    errmsg="There's an error on line %s\n  %s"\
                        "for section %s\n"\
                        "Values must be space separated and . is the decimal"\
                        " separator" % (linecount, d.group(0), active)
                    error(errmsg, title='Error saving data', buttons=['OK'])
        self.all_data = alldata
        for section, vallist in data.items():
            if section=='Initial state':
                self._set_initial_state(vallist)
            elif section=='Constant soil carbon input':
                self._set_constant_litter(vallist)
            elif section=='Monthly soil carbon input':
                self._set_monthly_litter(vallist)
            elif section=='Yearly soil carbon input':
                self._set_yearly_litter(vallist)
            elif section=='Relative area change':
                self._set_area_change(vallist)
            elif section=='Constant climate':
                self._set_constant_climate(vallist)
            elif section=='Monthly climate':
                self._set_monthly_climate(vallist)
            elif section=='Yearly climate':
                self._set_yearly_climate(vallist)

    def _save_all_data(self):
        f = codecs.open(self.data_file, 'w', 'utf8')
        f.write(self.all_data)
        f.close()
        f = codecs.open(self.data_file, 'r', 'utf8')
        self._load_all_data(f)
        f.close()

    def _reset_data(self):
        """
        Empties all input data structures
        """
        self.initial_litter = []
        self.steady_state = []
        self.constant_litter = []
        self.monthly_litter = []
        self.yearly_litter = []
        self.area_change = []
        self.constant_climate.mean_temperature = 0
        self.constant_climate.annual_rainfall = 0
        self.constant_climate.variation_amplitude = 0
        self.yearly_climate = []
        self.monthly_climate = []

    def _set_initial_state(self, data):
        errmsg = 'Soil carbon components should contain: \n'\
                      ' mass, mass std, acid, acid std, water, water std,\n'\
                      ' ethanol, ethanol std, non soluble, non soluble std,'\
                      '\n humus, humus std, size class'
        for vals in data:
            ok, obj = self._load_litter_object(vals, errmsg)
            if not ok:
                break
            self.initial_litter.append(obj)

    def _set_steady_state(self, data):
        errmsg = 'Soil carbon components should contain: \n'\
                      ' mass, mass std, acid, acid std, water, water std,\n'\
                      ' ethanol, ethanol std, non soluble, non soluble std,'\
                      '\n humus, humus std, size class'
        self.steady_state = []
        for vals in data:
            ok, obj = self._load_litter_object(vals, errmsg)
            if not ok:
                break
            self.steady_state.append(obj)

    def _set_constant_litter(self, data):
        errmsg = 'Soil carbon components should contain: \n'\
                      ' mass, mass std, acid, acid std, water, water std,\n'\
                      ' ethanol, ethanol std, non soluble, non soluble std,'\
                      '\n humus, humus std, size class'
        for vals in data:
            ok, obj = self._load_litter_object(vals, errmsg)
            if not ok:
                break
            self.constant_litter.append(obj)

    def _set_monthly_litter(self, data):
        errmsg = 'timed soil carbon components should contain: \n'\
                      ' timestep, mass, mass std, acid, acid std, water, '\
                      'water std,\n'\
                      ' ethanol, ethanol std, non soluble, non soluble std,'\
                      '\n humus, humus std, size class'
        for vals in data:
            ok, obj = self._load_litter_object(vals, errmsg, True)
            if not ok:
                break
            self.monthly_litter.append(obj)

    def _set_yearly_litter(self, data):
        errmsg = 'timed soil carbon components should contain: \n'\
                  ' timestep, mass, mass std, acid, acid std, water, '\
                  'water std,\n'\
                  ' ethanol, ethanol std, non soluble, non soluble std,'\
                  '\n humus, humus std, size class'
        for vals in data:
            ok, obj = self._load_litter_object(vals, errmsg, True)
            if not ok:
                break
            self.yearly_litter.append(obj)

    def _set_area_change(self, data):
        errmsg = 'Area change should contain:\n  timestep, relative area change'
        for vals in data:
            if len(vals)==2:
                obj = AreaChange(timestep=int(vals[0]),
                          rel_change=vals[1])
                self.area_change.append(obj)
            elif vals!=[]:
                errmsg = errmsg + '\n%s data values found, 2 needed' % (len(data))
                error(errmsg, title='error reading data',
                      buttons=['OK'])
                break

    def _set_yearly_climate(self, data):
        errmsg = 'Yearly climate should contain: timestep, mean temperature,\n'\
                 'annual rainfall and temperature variation amplitude'
        for vals in data:
            if len(vals)==4:
                obj = YearlyClimate(timestep=int(vals[0]),
                          mean_temperature=vals[1],
                          annual_rainfall=vals[2],
                          variation_amplitude=vals[3])
                self.yearly_climate.append(obj)
            elif vals!=[]:
                errmsg = errmsg + '\n%s data values found, 4 needed' % (len(data))
                error(errmsg, title='error reading data',
                      buttons=['OK'])
                break

    def _set_constant_climate(self, data):
        errmsg = 'Constant climate should contain: mean temperature,\n'\
                 'annual rainfall and temperature variation amplitude'
        if len(data[0])==3:
            self.constant_climate.mean_temperature = data[0][0]
            self.constant_climate.annual_rainfall = data[0][1]
            self.constant_climate.variation_amplitude = data[0][2]
        elif data[0]!=[]:
            errmsg = errmsg + '\n%s data values found, 3 needed' % (len(data))
            error(errmsg, title='error reading data',
                  buttons=['OK'])

    def _set_monthly_climate(self, data):
        errmsg = 'Monthly climate data should contain: month,\n'\
                 'temperature and rainfall'
        for vals in data:
            if len(vals)==3:
                obj = MonthlyClimate(month=int(vals[0]),
                          temperature=vals[1],
                          rainfall=vals[2])
                self.monthly_climate.append(obj)
            elif vals!=[]:
                errmsg = errmsg + '\n%s data values found, 3 needed' % (len(data))
                error(errmsg, title='Error reading data',
                      buttons=['OK'])
                break

    def _load_litter_object(self, data, errmsg, hastime=False):
        obj = None
        loaded = True
        if hastime:
            if len(data)==14:
                obj = TimedLitterComponent(timestep=int(data[0]),
                        mass=data[1],
                        mass_std=data[2],
                        acid=data[3],
                        acid_std=data[4],
                        water=data[5],
                        water_std=data[6],
                        ethanol=data[7],
                        ethanol_std=data[8],
                        non_soluble=data[9],
                        non_soluble_std=data[10],
                        humus=data[11],
                        humus_std=data[12],
                        size_class=data[13])
            elif data!=[]:
                errmsg = errmsg + '\n%s data values found, 14 needed' % (len(data))
                error(errmsg, title='Error reading data',
                      buttons=['OK'])
                loaded = False
            elif data==[]:
                loaded = False
        else:
            if len(data)==13:
                obj = LitterComponent(mass=data[0],
                        mass_std=data[1],
                        acid=data[2],
                        acid_std=data[3],
                        water=data[4],
                        water_std=data[5],
                        ethanol=data[6],
                        ethanol_std=data[7],
                        non_soluble=data[8],
                        non_soluble_std=data[9],
                        humus=data[10],
                        humus_std=data[11],
                        size_class=data[12])
            elif data!=[]:
                errmsg = errmsg + '\n%s data values found, 13 needed' % (len(data))
                error(errmsg, title='Error reading data',
                      buttons=['OK'])
                loaded = False
            elif data==[]:
                loaded = False
        return loaded, obj

    def _save_moment_event_fired(self):
        filename = save_file()
        if filename != '':
            f=codecs.open(filename, 'w', 'utf8')
            if self.result_type=='C stock':
                comps = (('tom', self.stock_tom), ('woody', self.stock_woody),
                        ('non-woody', self.stock_non_woody),
                       ('acid', self.stock_acid), ('water', self.stock_water),
                       ('ethanol', self.stock_ethanol),
                       ('non-soluble', self.stock_non_soluble),
                       ('humus', self.stock_humus))
            elif self.result_type=='C change':
                comps = (('tom', self.change_tom), ('woody', self.change_woody),
                        ('non-woody', self.change_non_woody),
                       ('acid', self.change_acid), ('water', self.change_water),
                       ('ethanol', self.change_ethanol),
                       ('non-soluble', self.change_non_soluble),
                       ('humus', self.change_humus))
            elif self.result_type=='CO2 production':
                comps = (('CO2', self.co2),)
            header = '# component, time step, mean, mode, var, skewness, '\
                     'kurtosis, 95% confidence lower limit, 95% upper limit'
            header = self._make_result_header(header)
            f.write(header+'\n')
            for comp, res in comps:
                for row in res:
                    resrow = ''
                    for num in row:
                        resrow = ' '.join([resrow, str(num)])
                    resrow = ' '.join((comp, resrow))
                    f.write(resrow+'\n')
            f.close()

    def _save_result_event_fired(self):
        filename = save_file()
        if filename != '':
            f=codecs.open(filename, 'w', 'utf8')
            if self.result_type=='C stock':
                res = self.c_stock
                header = '# sample, time step, total om, woody om, non-woody om,'\
                         ' acid, water, ethanol, non-soluble, humus'
            elif self.result_type=='C change':
                res = self.c_change
                header = '# sample, time step, total om, woody om, non-woody om,'\
                         ' acid, water, ethanol, non soluble, humus'
            elif self.result_type=='CO2 production':
                res = self.co2_yield
                header = '# sample, time step, CO2 production (in carbon)'
            header = self._make_result_header(header)
            f.write(header+'\n')
            for row in res:
                resrow = ''
                for num in row:
                    resrow = ' '.join([resrow, str(num)])
                f.write(resrow+'\n')
            f.close()

    def _make_result_header(self, header):
        '''Adds metadata about the results into the header'''
        hstr = '#########################################################\n'
        hstr += '# ' + self.result_type + '\n'
        hstr += '#########################################################\n'
        hstr += '# Datafile used: ' + self.data_file + '\n'
        hstr += '# Settings:\n'
        hstr += '#   initial state: ' + self.initial_mode + '\n'
        hstr += '#   soil carbon input: ' + self.litter_mode + '\n'
        hstr += '#   climate: ' + self.climate_mode + '\n'
        hstr += '#   sample size: ' + str(self.sample_size) + '\n'
        hstr += ''.join(['#   timestep length: ', str(self.timestep_length),
                         ' (', self.duration_unit, ')\n'])
        hstr += '#   woody litter size limit: ' + str(self.woody_size_limit)+'\n'
        hstr += '#\n'
        return hstr + header

    def _init_results(self):
        """
        model results: stock & change
         sample, timestep, tom, woody, non-woody, acid, water, ethanol,
         non soluble humus
        model results: CO2
         sample, timestep, CO2 production
        summary results
         common format: time, mean, mode, var, skewness, kurtosis,
         95% confidence-, 95% confidence+
        """
        self.c_stock = empty(dtype=float32, shape=(0, 10))
        self.c_change = empty(dtype=float32, shape=(0, 10))
        self.co2_yield = empty(dtype=float32, shape=(0, 3))
        self.stock_tom = empty(dtype=float32, shape=(0, 8))
        self.stock_woody = empty(dtype=float32, shape=(0, 8))
        self.stock_non_woody = empty(dtype=float32, shape=(0, 8))
        self.stock_acid = empty(dtype=float32, shape=(0, 8))
        self.stock_water = empty(dtype=float32, shape=(0, 8))
        self.stock_ethanol = empty(dtype=float32, shape=(0, 8))
        self.stock_non_soluble = empty(dtype=float32, shape=(0, 8))
        self.stock_humus = empty(dtype=float32, shape=(0, 8))
        self.change_tom = empty(dtype=float32, shape=(0, 8))
        self.change_woody = empty(dtype=float32, shape=(0, 8))
        self.change_non_woody = empty(dtype=float32, shape=(0, 8))
        self.change_acid = empty(dtype=float32, shape=(0, 8))
        self.change_water = empty(dtype=float32, shape=(0, 8))
        self.change_ethanol = empty(dtype=float32, shape=(0, 8))
        self.change_non_soluble = empty(dtype=float32, shape=(0, 8))
        self.change_humus = empty(dtype=float32, shape=(0, 8))
        self.co2 = empty(dtype=float32, shape=(0, 8))

yasso = Yasso()

# Run the demo (if invoked from the command line):
if __name__ == '__main__':
    yasso.configure_traits(view="view")

