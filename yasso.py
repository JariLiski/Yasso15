#!/usr/bin/env python
#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from collections import defaultdict
import re
import sys
import os
import glob
from numpy import empty, float32
from traits.api import Array, Button, Enum, Float, HasTraits,\
    Instance, Int, List, Range, Str
from traitsui.api import CodeEditor, Group, HGroup, VGroup, Item,\
    Label, spring, TabularEditor, View
from traitsui.menu import \
    UndoAction, RedoAction, RevertAction, CloseAction, \
    Menu, MenuBar, NoButtons
from traitsui.file_dialog import open_file, save_file
from traitsui.message import error
from traitsui.tabular_adapter import TabularAdapter
from chaco.api import ArrayPlotData, Plot, GridContainer
from enable.component_editor import ComponentEditor

from modelcall import ModelRunner
import sys

# Redirecting stderr
sys.stderr = open('yasso_stderr.log', 'w')

APP_INFO="""
Version 1.1.0

For detailed information, including a user's manual, see:
www.environment.fi/syke/yasso

Inside the program help is available by clicking the label texts.
Program wiki is at code.google.com/p/yasso07ui

Yasso07 model by Finnish Environment Institute (SYKE, www.environment.fi)
User interface by Simosol Oy (www.simosol.fi)

The program is distributed under the GNU Lesser General Public License (LGPL)
The source code is available at code.google.com/p/yasso07ui/
"""
PARAMETER_SET_HELP = """
The model calibration data set on which the model run parameterisation will be based on
"""
LEACHING_HELP = """
Litter bag adjustment coefficient due to leaching and effect on decomposers
"""
INITIAL_STATE_HELP = """
There are three alternative ways to give the initial soil carbon stock to Yasso07,<ul>1) the stock specified by user</ul>
<ul>2) the stock set equal to zero</ul>
<ul>3) a steady-state stock calculated with the model based on carbon input to soil in the beginning of the simulation</ul>
<p>If the soil carbon input is set to be yearly or monthly, the input from <b>timestep 0</b> is used to compute the steady state. If no input for timestep 0 is defined, input from <b>step 1</b> is used. Input from timestep 0 is not used in the actual simulation run; i.e., it's only used for steady state prediction.</p>
"""
SOIL_CARBON_INPUT_HELP = """
Soil carbon input can be one of
<ul>1) yearly time series</ul>
<ul>2) yearly constant values</ul>
<ul>3) monthly time series</ul>
<p><b>Area change</b>: for time series input you can define timesteps when the area under simulation changes. The changes are given as relative changes meaning that a change of 0.01 increases the area by 1 % and a change of -0.1 reduces it by 10 %. The change in area will be directly reflected in the initial carbon stock in soil for the next timestep</p>
<p>If the simulation run is longer than the defined time series, no input is used for the remaining time.</p>
<p>Note that if you define input for the timestep 0 for yearly or monthly timeseries, it will be used only for the steady state prediction. In the absence of timestep 0 data, the steady state prediction will be based on the input of timestep 1</p>
"""
CLIMATE_HELP = """
Climate definition can be one of
<ul>1) yearly time series</ul>
<ul>2) yearly constant values</ul>
<ul>3) monthly time series</ul>
<p>In case of the time series, the series will be applied several times if the simulation run is longer than the defined series; i.e., when the last values from the series are used in the simulation, for the next step the values from the beginning of the climate series will be used.</p>
<p>Note that the <b>monthly time series</b> is limited to 12 months; i.e., it is used to define the climate variation within a single year, for a simulation covering several years, the same climate is applied repeatedly.
<p>For <b>steady state prediction</b>, yearly climate from timestep 0 is used if defined, otherwise the climate from step 1 will be used.
"""
SAMPLE_SIZE_HELP = """
Number of parameter combinations to be used in the simulation.
"""
SIMULATION_LENGTH_HELP = """
The number of timesteps of the simulation
"""
TIMESTEP_LENGTH_HELP = """
The duration of each timestep in the simulation
"""
WOODY_SIZE_LIMIT_HELP = """
Minimum size of litter (diameter in cm) classified in the results as woody organic matter. Litter components having smaller size classes than the limit as classified as non-woody organic matter.
"""
SHOW_HELP = """
Besides evaluating the values on the screen, the simulation results can be saved to a file in two formats
<ul>1) raw results based on each parameter combination used for the simulation</ul>
<ul>2) statistical characteristics calculated from the raw results.</ul>
<p>The result files will contain a header detailing the contents of the file and the settings used to derive the values</p>
"""
AS_HELP = """
The charts illustrate the most probable values and their 95 % error estimates (based on the normality assumption).
"""
DATA_STRING = """
# THE CHANGES YOU MAKE HERE HAVE ONLY EFFECT AFTER YOU SAVE THE CHANGES
#
# commented out rows begin with the # chacter
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
               ('mass std', 'mass_std'), ('acid', 'acid'),
               ('acid std', 'acid_std'), ('water', 'water'),
               ('water std', 'water_std'), ('ethanol', 'ethanol'),
               ('ethanol std', 'ethanol_std'), ('non soluble', 'non_soluble'),
               ('non soluble std', 'non_soluble_std'), ('humus', 'humus'),
               ('humus std', 'humus_std'), ('size class', 'size_class')]
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
               ('mass std', 'mass_std'), ('acid', 'acid'),
               ('acid std', 'acid_std'), ('water', 'water'),
               ('water std', 'water_std'), ('ethanol', 'ethanol'),
               ('ethanol std', 'ethanol_std'), ('non soluble', 'non_soluble'),
               ('non soluble std', 'non_soluble_std'), ('humus', 'humus'),
               ('humus std', 'humus_std'), ('size class', 'size_class')]
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
    leaching = Float(default_value=0.0)
    # Initial condition
    initial_mode = Enum(['non zero', 'zero', 'steady state'])
    initial_litter = List(trait=LitterComponent)
    steady_state = List(trait=LitterComponent)
    # Litter input at each timestep in the simulation
    litter_mode = Enum(['yearly', 'constant yearly', 'monthly'])
    constant_litter = List(trait=LitterComponent)
    monthly_litter = List(trait=TimedLitterComponent)
    yearly_litter = List(trait=TimedLitterComponent)
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
                     #width=300, height=400,
                     ),
                ),
            label='All data',
            ),
        VGroup(
            HGroup(
                Item('parameter_set', width=-145,
                     help=PARAMETER_SET_HELP),
                Item('leaching', width=-45,
                     label='Litter bag adjustment coefficient',
                     help=LEACHING_HELP,),
                show_border=True
            ),
            VGroup(
                HGroup(
                    Item(name='initial_mode', style='custom',
                         label='Initial state:', emphasized=True,
                         help=INITIAL_STATE_HELP, ),
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
                         label='Soil carbon input:', emphasized=True,
                         help=SOIL_CARBON_INPUT_HELP,),
                    ),
                HGroup(
                    Item('constant_litter',
                         visible_when='litter_mode=="constant yearly"',
                         show_label=False, editor=litter_te,
                         full_size=False, springy=False,
                         width=-790, height=-75),
                    Item('monthly_litter',
                         visible_when='litter_mode=="monthly"',
                         show_label=False, editor=timed_litter_te,
                         full_size=False, springy=False,
                         width=-790, height=-75),
                    Item('yearly_litter',
                         visible_when='litter_mode=="yearly"',
                         show_label=False, editor=timed_litter_te,
                         full_size=False, springy=False,
                         width=-790,height=-75),
                    ),
                HGroup(
                    Item('area_change',
                         visible_when='litter_mode=="yearly" or '\
                                      'litter_mode=="monthly"',
                         show_label=False, editor=change_te,
                         full_size=False, springy=False,
                         width=-150,height=-75),
                    spring,
                    ),
                ),
            VGroup(
                HGroup(
                    Item('climate_mode', style='custom',
                        label='Climate:', emphasized=True,
                        help=CLIMATE_HELP,),
                    ),
                HGroup(
                    Item('monthly_climate', show_label=False,
                         visible_when='climate_mode=="monthly"',
                         editor=monthly_climate_te, width=200, height=75),
                    Item('yearly_climate', show_label=False,
                        visible_when='climate_mode=="yearly"',
                        editor=yearly_climate_te, width=200, height=75),
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
                         help=SAMPLE_SIZE_HELP),
                    Item('simulation_length', width=-45,
                         label='Number of timesteps',
                         help=SIMULATION_LENGTH_HELP,),
                    Item('timestep_length', width=-45,
                         help=TIMESTEP_LENGTH_HELP),
                    Item('duration_unit', style='custom',
                         show_label=False,),
                    ),
                HGroup(
                    Item('woody_size_limit', width=-45,
                         help=WOODY_SIZE_LIMIT_HELP,),
                    Item('modelrun_event', show_label=False),
                    ),
                show_border=True
            ),
            HGroup(
                Item('result_type', style='custom', label='Show',
                     emphasized=True, help=SHOW_HELP,),
                Item('save_result_event', show_label=False,),
                Item('save_moment_event', show_label=False,),
                ),
            HGroup(
                Item('presentation_type', style='custom', label='As',
                     emphasized=True, help=AS_HELP,),
                Item('chart_type', style='custom', label='Chart type',
                     visible_when='presentation_type=="chart"'),
                ),
            HGroup(
                Item('c_stock', visible_when='result_type=="C stock" and \
                      presentation_type=="array"', show_label=False,
                      editor=c_stock_te, width=600),
                Item('c_change', visible_when='result_type=="C change" and \
                      presentation_type=="array"', show_label=False,
                      editor=c_stock_te,),
                Item('co2_yield', visible_when='result_type=="CO2 production" '\
                      'and presentation_type=="array"', show_label=False,
                      editor=co2_yield_te,),
                Item('stock_plots', editor=ComponentEditor(),
                     show_label=False, width=600, height=600,
                     visible_when='result_type=="C stock" and \
                                  presentation_type=="chart"',),
                Item('change_plots', editor=ComponentEditor(),
                     show_label=False, width=600, height=600,
                     visible_when='result_type=="C change" and \
                                  presentation_type=="chart"',),
                Item('co2_plot', editor=ComponentEditor(),
                     show_label=False, width=600, height=600,
                     #springy=False, full_size=False, resizable=False,
                     visible_when='result_type=="CO2 production" and \
                                  presentation_type=="chart"',),
                ),
            label='Model run',
            ),
        VGroup(
            Label(label='Yasso07 soil carbon model', emphasized=True),
            Label(label=APP_INFO,),
            label='About',
            ),
        title     = 'Yasso 07',
        id        = 'simosol.yasso07',
        dock      = 'horizontal',
        resizable = True,
        width     = 800,
        height    = 600,
        scrollable= True,
        buttons=NoButtons,
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
            f = open(self.data_file)
            self._load_all_data(f)
            f.close()
        except:
            self.all_data = DATA_STRING
            self.data_file = ''

    def _get_data_file_path(self, exedir):
        join = os.path.join
        self.state_file = join(exedir, 'yasso.state')
        if os.path.exists(self.state_file):
            f = open(self.state_file)
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
        f = open(self.state_file, 'w')
        f.write(filename)
        f.close()

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
                                         'Acid soluble')
        sw, max, min = self._create_plot(max, min, self.stock_water,
                                         'Water soluble')
        se, max, min = self._create_plot(max, min, self.stock_ethanol,
                                         'Ethanol soluble')
        sn, max, min = self._create_plot(max, min, self.stock_non_soluble,
                                         'Non soluble')
        sh, max, min = self._create_plot(max, min, self.stock_humus, 'Humus')
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
                                         'Acid soluble')
        cw, max, min = self._create_plot(max, min, self.change_water,
                                         'Water soluble')
        ce, max, min = self._create_plot(max, min, self.change_ethanol,
                                         'Ethanol soluble')
        cn, max, min = self._create_plot(max, min, self.change_non_soluble,
                                         'Non soluble')
        ch, max, min = self._create_plot(max, min, self.change_humus, 'Humus')
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
        #plot.padding_right = 45
        #plot.padding_left = 25
        #plot.padding_top = 25
        #plot.padding_bottom = 25
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
        self.yassorunner = ModelRunner(parfile)
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
                f=open(filename, 'w')
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
                f=open(filename)
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
        f = open(self.data_file, 'w')
        f.write(self.all_data)
        f.close()
        f = open(self.data_file)
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
            f=open(filename, 'w')
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
            f=open(filename, 'w')
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
    yasso.configure_traits()

