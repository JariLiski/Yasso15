#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from collections import defaultdict
import re
from numpy import empty, float32
from datetime import date
from enthought.traits.api import *
from enthought.traits.ui.api import *
from enthought.traits.ui.menu import *
from enthought.traits.ui.table_column import ObjectColumn
from enthought.traits.ui.file_dialog import open_file, save_file
from enthought.traits.ui.message import error
from enthought.traits.ui.tabular_adapter import TabularAdapter
from enthought.chaco.chaco_plot_editor import ChacoPlotItem

from modelcall import ModelRunner

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
    timestep = Float()
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

class YearlyClimate(HasTraits):
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

monthly_climate_te = TableEditor(
    columns = [ObjectColumn(name='month', editable=False),
               ObjectColumn(name='temperature'),
               ObjectColumn(name='rainfall'),],
    auto_size   = True,
    rows        = 12,
    orientation = 'vertical')

yearly_climate_te = TableEditor(
    columns = [
               ObjectColumn(name='mean_temperature'),
               ObjectColumn(name='annual_rainfall'),
               ObjectColumn(name='variation_amplitude'),
              ],
    auto_size    = True,
    rows         = 10,
    auto_add     = True,
    editable     = True,
    deletable    = True,
    orientation  = 'vertical',
    show_toolbar = True,
    row_factory  = YearlyClimate)

litter_component_te = TableEditor(
    columns = [ObjectColumn(name='mass', width=50),
               ObjectColumn(name='mass_std', width=50),
               ObjectColumn(name='acid', style='text', width=50),
               ObjectColumn(name='acid_std', width=50),
               ObjectColumn(name='water', style='text', width=50),
               ObjectColumn(name='water_std', width=50),
               ObjectColumn(name='ethanol', style='text', width=50),
               ObjectColumn(name='ethanol_std', width=55),
               ObjectColumn(name='non_soluble', style='text', width=60),
               ObjectColumn(name='non_soluble_std', width=75),
               ObjectColumn(name='humus', style='text', width=50),
               ObjectColumn(name='humus_std', width=50),
               ObjectColumn(name='size_class', width=50),
               ],
    auto_size    = False,
    rows         = 5,
    auto_add     = True,
    editable     = True,
    deletable    = True,
    orientation  = 'vertical',
    show_toolbar = True,
    row_factory  = LitterComponent)

timed_litter_component_te = TableEditor(
    columns = [ObjectColumn(name='timestep', width=50),
               ObjectColumn(name='mass', width=50),
               ObjectColumn(name='mass_std', width=50),
               ObjectColumn(name='acid', style='text', width=50),
               ObjectColumn(name='acid_std', width=50),
               ObjectColumn(name='water', style='text', width=50),
               ObjectColumn(name='water_std', width=50),
               ObjectColumn(name='ethanol', style='text', width=50),
               ObjectColumn(name='ethanol_std', width=55),
               ObjectColumn(name='non_soluble', style='text', width=60),
               ObjectColumn(name='non_soluble_std', width=75),
               ObjectColumn(name='humus', style='text', width=50),
               ObjectColumn(name='humus_std', width=50),
               ObjectColumn(name='size_class', width=50),
               ],
    auto_size    = False,
    rows         = 5,
    auto_add     = True,
    editable     = True,
    deletable    = True,
    orientation  = 'vertical',
    show_toolbar = True,
    row_factory  = TimedLitterComponent)

class CStockAdapter(TabularAdapter):
    columns = [('sample', 0), ('time step', 1), ('total om', 2),
               ('woody om', 3), ('acid', 4), ('water', 5), ('ethanol', 6),
               ('non soluble', 7), ('humus', 8)]
    font        = 'Courier 10'
    alignment   = 'right'
    format      = '%.4f'

class CO2YieldAdapter(TabularAdapter):
    columns = [('sample', 0), ('time step', 1), ('CO2 yield', 2)]
    font        = 'Courier 10'
    alignment   = 'right'
    format      = '%.4f'

c_stock_te = TabularEditor(
    adapter = CStockAdapter(),
   )

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
    # Initial condition
    initial_mode = Enum(['non zero', 'zero'])
    initial_litter = List(trait=LitterComponent)
    # Litter input at each timestep in the simulation
    litter_mode = Enum(['yearly', 'constant yearly', 'monthly'])
    constant_litter = List(trait=LitterComponent)
    monthly_litter = List(trait=TimedLitterComponent)
    yearly_litter = List(trait=TimedLitterComponent)
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
    # How the model will be run
    sample_size = Int()
    duration_unit = Enum(['year', 'month'])
    timestep_length = Range(low=1)
    simulation_length = Range(low=1)
    result_type = Enum(['C stock', 'C change', 'CO2 yield'])
    presentation_type = Enum(['array', 'chart'])
    # Buttons
    load_all_data_event = Button('Load all data from file...')
    modelrun_event = Button('Run model')
    load_init_event = Button('Load from file...')
    load_constant_litter_event = Button('Load constant input...')
    load_monthly_litter_event = Button('Load monthly input...')
    load_yearly_litter_event = Button('Load yearly input...')
    load_monthly_climate_event = Button('Load monthly data...')
    load_yearly_climate_event = Button('Load yearly data...')
    save_result_event = Button('Save raw results...')
    save_moment_event = Button('Save moment results...')
    # and the results stored
    # Individual model calls
    #     iteration,time, total, woody, acid, water, ethanol, non_soluble, humus
    c_stock = Array(dtype=float32, shape=(None, 9))
    #     iteration,time, total, woody, acid, water, ethanol, non_soluble, humus
    c_change = Array(dtype=float32, shape=(None, 9))
    #     time, iteration, CO2 yield
    co2_yield = Array(dtype=float32, shape=(None, 3))
    # time, mean, mode, var, skewness, kurtosis, 95% conf-, 95% conf+
    stock_tom = Array(dtype=float32, shape=(None, 8))
    stock_woody = Array(dtype=float32, shape=(None, 8))
    stock_acid = Array(dtype=float32, shape=(None, 8))
    stock_water = Array(dtype=float32, shape=(None, 8))
    stock_ethanol = Array(dtype=float32, shape=(None, 8))
    stock_non_soluble = Array(dtype=float32, shape=(None, 8))
    stock_humus = Array(dtype=float32, shape=(None, 8))
    change_tom = Array(dtype=float32, shape=(None, 8))
    change_woody = Array(dtype=float32, shape=(None, 8))
    change_acid = Array(dtype=float32, shape=(None, 8))
    change_water = Array(dtype=float32, shape=(None, 8))
    change_ethanol = Array(dtype=float32, shape=(None, 8))
    change_non_soluble = Array(dtype=float32, shape=(None, 8))
    change_humus = Array(dtype=float32, shape=(None, 8))
    co2 = Array(dtype=float32, shape=(None, 8))
    # plot variables
    p_timestep = Property(Array, depends_on=['simulation_length'])
    ps_tom = Property(Array, depends_on=['stock_tom'])
    ps_woody = Property(Array, depends_on=['stock_woody'])
    ps_acid = Property(Array, depends_on=['stock_acid'])
    ps_water = Property(Array, depends_on=['stock_water'])
    ps_ethanol = Property(Array, depends_on=['stock_ethanol'])
    ps_non_soluble = Property(Array, depends_on=['stock_non_soluble'])
    ps_humus = Property(Array, depends_on=['stock_humus'])
    pc_tom = Property(Array, depends_on=['change_tom'])
    pc_woody = Property(Array, depends_on=['change_woody'])
    pc_acid = Property(Array, depends_on=['change_acid'])
    pc_water = Property(Array, depends_on=['change_water'])
    pc_ethanol = Property(Array, depends_on=['change_ethanol'])
    pc_non_soluble = Property(Array, depends_on=['change_non_soluble'])
    pc_humus = Property(Array, depends_on=['change_humus'])
    yassorunner = ModelRunner()

#############################################################
# UI view
#############################################################

    view = View(
        VGroup(
            HGroup(
                Item('load_all_data_event', show_label=False,),
                spring,
                ),
            VGroup(
                HGroup(
                    Item(name='initial_mode', style='custom',
                         show_label=False,),
                    spring,
                    Item(name='load_init_event', show_label=False,
                         visible_when='initial_mode=="non zero"',),
                    spring,
                    ),
                HGroup(
                    Item('initial_litter',
                         visible_when='initial_mode=="non zero"',
                         show_label=False,
                         editor=litter_component_te,
                         width=700,
                        ),
                    spring,
                    ),
                label='initial condition',
                ),
            Group(
                HGroup(
                    Item('litter_mode', style='custom', show_label=False,),
                    spring,
                    Item(name='load_constant_litter_event', show_label=False,
                         visible_when='litter_mode=="constant yearly"',),
                    Item(name='load_monthly_litter_event', show_label=False,
                         visible_when='litter_mode=="monthly"',),
                    Item(name='load_yearly_litter_event', show_label=False,
                         visible_when='litter_mode=="yearly"',),
                    spring,
                    ),
                HGroup(
                    Item('constant_litter',
                         visible_when='litter_mode=="constant yearly"',
                         show_label=False, editor=litter_component_te,
                         width=790,),
                    Item('monthly_litter',
                         visible_when='litter_mode=="monthly"',
                         show_label=False, editor=timed_litter_component_te,
                         width=790,),
                    Item('yearly_litter',
                         visible_when='litter_mode=="yearly"',
                         show_label=False, editor=timed_litter_component_te,
                         width=790,),
                    spring,
                    ),
                label='Litter input'
                ),
            Group(
                HGroup(
                    Item('climate_mode', style='custom', show_label=False,),
                    spring,
                    Item(name='load_yearly_climate_event', show_label=False,
                       visible_when='climate_mode=="yearly"',),
                    Item(name='load_monthly_climate_event', show_label=False,
                       visible_when='climate_mode=="monthly"',),
                    spring,
                    ),
                HGroup(
                    Item('monthly_climate', show_label=False,
                         visible_when='climate_mode=="monthly"',
                         editor=monthly_climate_te, width=400, height=400,),
                    Item('yearly_climate', show_label=False,
                        visible_when='climate_mode=="yearly"',
                        editor=yearly_climate_te, width=400, height=400,),
                    VGroup(
                        Item('object.constant_climate.annual_rainfall',
                              width=200,),
                        Item('object.constant_climate.mean_temperature',
                              width=200,),
                        Item('object.constant_climate.variation_amplitude',
                              width=200,),
                        show_border=True,
                        visible_when='climate_mode=="constant yearly"'
                        ),
                    spring,
                    ),
                label='Climate'
                ),
            label='Data',
            ),
        VGroup(
            HGroup(
                Item('sample_size', width=-60),
                Item('timestep_length', width=-30,),
                Item('duration_unit', style='custom', show_label=False,),
                Item('simulation_length', width=-40, label='# of timesteps',),
                Item('modelrun_event', show_label=False),
                spring,
                ),
            HGroup(
                Item('result_type', style='custom', label='Show',),
                Item('save_result_event', show_label=False,),
                Item('save_moment_event', show_label=False,),
                spring,
                ),
            HGroup(
                Item('presentation_type', style='custom', label='As'),
                spring,
                ),
            Item('c_stock', visible_when='result_type=="C stock" and \
                  presentation_type=="array"', show_label=False,
                  editor=c_stock_te,),
            Item('c_change', visible_when='result_type=="C change" and \
                  presentation_type=="array"', show_label=False,
                  editor=c_stock_te,),
            Item('co2_yield', visible_when='result_type=="CO2 yield" and \
                  presentation_type=="array"', show_label=False,
                  editor=co2_yield_te,),
            HGroup(
                ChacoPlotItem('p_timestep', 'ps_tom', show_label=False,
                              x_label = 'time',
                              y_label = 'total organic matter',
                              resizable=True, orientation='h',
                              title = 'Total organic matter',
                              color = 'red', bgcolor = 'white',
                              border_visible=False, border_width=1,
                              padding_bg_color = 'lightgray'),
                ChacoPlotItem('p_timestep', 'ps_woody', show_label=False,
                              x_label = 'time', y_label = 'woody matter',
                              resizable=True, orientation='h',
                              title = 'Woody organic matter', color = 'red',
                              bgcolor = 'white', border_visible=False,
                              border_width=1, padding_bg_color = 'lightgray'),
                ChacoPlotItem('p_timestep', 'ps_acid', show_label=False,
                              x_label = 'time', y_label = 'acid soluble',
                              resizable=True, orientation='h',
                              title = 'Acid soluble', color = 'red',
                              bgcolor = 'white', border_visible=False,
                              border_width=1, padding_bg_color = 'lightgray'),
                visible_when='result_type=="C stock" and \
                              presentation_type=="chart"',
                ),
            HGroup(
                ChacoPlotItem('p_timestep', 'ps_water', show_label=False,
                              x_label = 'time', y_label = 'water soluble',
                              resizable=True, orientation='h',
                              title = 'Water soluble', color = 'red',
                              bgcolor = 'white', border_visible=False,
                              border_width=1, padding_bg_color = 'lightgray'),
                ChacoPlotItem('p_timestep', 'ps_ethanol', show_label=False,
                              x_label = 'time', y_label = 'ethanol soluble',
                              resizable=True, orientation='h',
                              title = 'Ethanol soluble', color = 'red',
                              bgcolor = 'white', border_visible=False,
                              border_width=1, padding_bg_color = 'lightgray'),
                ChacoPlotItem('p_timestep', 'ps_non_soluble', show_label=False,
                              x_label = 'time', y_label = 'non soluble',
                              resizable=True, orientation='h',
                              title = 'Non soluble', color = 'red',
                              bgcolor = 'white', border_visible=False,
                              border_width=1, padding_bg_color = 'lightgray'),
                visible_when='result_type=="C stock" and \
                              presentation_type=="chart"',
                ),
            HGroup(
                ChacoPlotItem('p_timestep', 'ps_humus', show_label=False,
                              x_label = 'time', y_label = 'humus',
                              resizable=True, orientation='h',
                              title = 'Humus', color = 'red',
                              bgcolor = 'white', border_visible=False,
                              border_width=1, padding_bg_color = 'lightgray'),
                ChacoPlotItem(index='', value='', show_label=False,
                              x_label = '', y_label = '', resizable=True,
                              orientation='h', title = '', color = 'red',
                              bgcolor = 'white', border_visible=False,
                              border_width=1, padding_bg_color = 'lightgray'),
                ChacoPlotItem(index='', value='', show_label=False,
                              x_label = '', y_label = '', resizable=True,
                              orientation='h', title = '', color = 'red',
                              bgcolor = 'white', border_visible=False,
                              border_width=1, padding_bg_color = 'lightgray'),
                visible_when='result_type=="C stock" and \
                                    presentation_type=="chart"',
                ),
            label='Model run',
            ),
        title     = 'Yasso 07',
        id        = 'simosol.yasso07',
        dock      = 'horizontal',
        resizable = True,
        width     = 800,
        height    = 600,
        scrollable= True,
        buttons   = NoButtons,
        menubar = MenuBar(
            Menu(CloseAction, name = 'File'),
            Menu(UndoAction, RedoAction, RevertAction, name = 'Edit'),
            Menu(HelpAction, name = 'Help')),
        )



###############################################################################
# Event handlers
###############################################################################

#########################
# for plot data
#########################

    def _get_p_timestep(self):
        return range(self.simulation_length)

    def _get_ps_tom(self):
        return self.stock_tom[:,1]

    def _get_ps_woody(self):
        return self.stock_woody[:,1]

    def _get_ps_acid(self):
        return self.stock_acid[:,1]

    def _get_ps_water(self):
        return self.stock_water[:,1]

    def _get_ps_ethanol(self):
        return self.stock_ethanol[:,1]

    def _get_ps_non_soluble(self):
        return self.stock_non_soluble[:,1]

    def _get_ps_humus(self):
        return self.stock_humus[:,1]

    def _get_pc_tom(self):
        return self.change_tom[:,1]

    def _get_pc_woody(self):
        return self.change_woody[:,1]

    def _get_pc_acid(self):
        return self.change_acid[:,1]

    def _get_pc_water(self):
        return self.change_water[:,1]

    def _get_pc_ethanol(self):
        return self.change_ethanol[:,1]

    def _get_pc_non_soluble(self):
        return self.change_non_soluble[:,1]

    def _get_pc_humus(self):
        return self.change_humus[:,1]

    def _modelrun_event_fired(self):
        self._init_results()
        self.yassorunner.run_model(self)

########################
# for buttons
########################

    def _load_all_data_event_fired(self):
        """
        Loads all data from a single file. Data in sections defined by [name],
        data in whitespace delimited rows
        """
        filename = open_file()
        sectionp = re.compile('\[(\w+\s\w+)\]')
        datap = re.compile('[+-Ee\d+\.\d*\s*]+')
        active = None
        data = defaultdict(list)
        if filename != '':
            try:
                f=open(filename)
                for line in f:
                    m = re.match(sectionp, line)
                    if m is not None:
                        active = m.group(1)
                    d = re.match(datap, line)
                    if d is not None:
                        vals = [float(val) for val in d.group(0).split()]
                        data[active].append(vals)
                f.close()
                for section, vallist in data.items():
                    if section=='Initial state':
                        self._set_initial_state(vallist)
                    elif section=='Constant litterfall':
                        self._set_constant_litter(vallist)
                    elif section=='Monthly litterfall':
                        self._set_monthly_litter(vallist)
                    elif section=='Yearly litterfall':
                        self._set_yearly_litter(vallist)
                    elif section=='Constant climate':
                        self._set_constant_climate(vallist)
                    elif section=='Monthly climate':
                        self._set_monthly_climate(vallist)
                    elif section=='Yearly climate':
                        self._set_yearly_climate(vallist)
            except:
                pass

    def _load_init_event_fired(self):
        data = self._load_file()
        if data != []:
            self._set_initial_state(data)

    def _set_initial_state(self, data):
        errmsg = 'Litter components should contain: \n'\
                      ' mass, mass std, acid, acid std, water, water std,\n'\
                      ' ethanol, ethanol std, non soluble, non soluble std,'\
                      '\n humus, humus std, size class'
        for vals in data:
            ok, obj = self._load_litter_object(vals, errmsg)
            if not ok:
                break
            self.initial_litter.append(obj)

    def _load_constant_litter_event_fired(self):
        data = self._load_file()
        if data != []:
            self._set_constant_litter(data)

    def _set_constant_litter(self, data):
        errmsg = 'Litter components should contain: \n'\
                      ' mass, mass std, acid, acid std, water, water std,\n'\
                      ' ethanol, ethanol std, non soluble, non soluble std,'\
                      '\n humus, humus std, size class'
        for vals in data:
            ok, obj = self._load_litter_object(vals, errmsg)
            if not ok:
                break
            self.constant_litter.append(obj)

    def _load_monthly_litter_event_fired(self):
        data = self._load_file()
        if data != []:
            self._set_monthly_litter(data)

    def _set_constant_litter(self, data):
        errmsg = 'Litter components should contain: \n'\
                      'mass, mass std, acid, acid std, water, '\
                      'water std,\n'\
                      ' ethanol, ethanol std, non soluble, non soluble std,'\
                      '\n humus, humus std, size class'
        for vals in data:
            ok, obj = self._load_litter_object(vals, errmsg, False)
            if not ok:
                break
            self.constant_litter.append(obj)

    def _set_monthly_litter(self, data):
        errmsg = 'Timed litter components should contain: \n'\
                      ' timestep, mass, mass std, acid, acid std, water, '\
                      'water std,\n'\
                      ' ethanol, ethanol std, non soluble, non soluble std,'\
                      '\n humus, humus std, size class'
        for vals in data:
            ok, obj = self._load_litter_object(vals, errmsg, True)
            if not ok:
                break
            self.monthly_litter.append(obj)

    def _load_yearly_litter_event_fired(self):
        data = self._load_file()
        if data != []:
            self._set_yearly_litter(data)

    def _set_yearly_litter(self, data):
        errmsg = 'Timed litter components should contain: \n'\
                      ' timestep, mass, mass std, acid, acid std, water, '\
                      'water std,\n'\
                      ' ethanol, ethanol std, non soluble, non soluble std,'\
                      '\n humus, humus std, size class'
        for vals in data:
            ok, obj = self._load_litter_object(vals, errmsg, True)
            if not ok:
                break
            self.yearly_litter.append(obj)

    def _load_yearly_climate_event_fired(self):
        data = self._load_file()
        if data != []:
            self._set_yearly_climate(data)

    def _set_yearly_climate(self, data):
        errmsg = 'Yearly climate should contain: mean temperature,\n'\
                 'annual rainfall and temperature variation amplitude'
        self.yearly_climate = []
        for vals in data:
            if len(vals)==3:
                obj = YearlyClimate(mean_temperature=vals[0],
                          annual_rainfall=vals[1],
                          variation_amplitude=vals[2])
                self.yearly_climate.append(obj)
            elif vals!=[]:
                error(errmsg, title='error reading data',
                      buttons=['OK'])
                break

    def _set_constant_climate(self, data):
        errmsg = 'Constant climate should contain: mean temperature,\n'\
                 'annual rainfall and temperature variation amplitude'
        if data!=[]:
            if len(data[0])==3:
                self.constant_climate.mean_temperature = data[0][0]
                self.constant_climate.annual_rainfall = data[0][1]
                self.constant_climate.variation_amplitude = data[0][2]
            else:
                error(errmsg, title='error reading data',
                      buttons=['OK'])

    def _load_monthly_climate_event_fired(self):
        data = self._load_file()
        if data != []:
            self._set_monthly_climate(data)

    def _set_monthly_climate(self, data):
        errmsg = 'Monthly climate data should contain: month,\n'\
                 'temperature and rainfall'
        self.monthly_climate = []
        for vals in data:
            if len(vals)==3:
                obj = MonthlyClimate(month=int(vals[0]),
                          temperature=vals[1],
                          rainfall=vals[2])
                self.monthly_climate.append(obj)
            elif vals!=[]:
                print vals
                error(errmsg, title='Error reading data',
                      buttons=['OK'])
                break

    def _load_file(self):
        data = []
        filename = open_file()
        if filename != '':
            try:
                f=open(filename)
                for line in f:
                    if line[0] != '#' and len(line) > 1:
                        data.append([float(val) for val in line.split()])
                f.close()
            except:
                pass
        return data

    def _load_litter_object(self, data, errmsg, hastime=False):
        obj = None
        loaded = True
        if hastime:
            if len(data)==14:
                obj = TimedLitterComponent(timestep=data[0],
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
                       ('acid', self.stock_acid), ('water', self.stock_water),
                       ('ethanol', self.stock_ethanol),
                       ('non_soluble', self.stock_non_soluble),
                       ('humus', self.stock_humus))
                header = '# C stock\n# component, time step, '\
                         'mean, mode, var, skewness, kurtosis, '\
                         '95% confidence lower limit, 95% upper limit'
            elif self.result_type=='C change':
                comps = (('tom', self.change_tom), ('woody', self.change_woody),
                       ('acid', self.change_acid), ('water', self.change_water),
                       ('ethanol', self.change_ethanol),
                       ('non_soluble', self.change_non_soluble),
                       ('humus', self.change_humus))
                header = '# C change\n# component, time step, '\
                         'mean, mode, var, skewness, kurtosis, '\
                         '95% confidence lower limit, 95% upper limit'
            elif self.result_type=='CO2 yield':
                comps = (('CO2', self.co2))
                header = '# CO2 yield\n# component, time step, '\
                         'mean, mode, var, skewness, kurtosis, '\
                         '95% confidence lower limit, 95% upper limit'
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
                header = '# sample, time step, total om, woody om, acid, '\
                         'water, ethanol, non soluble, humus'
            elif self.result_type=='C change':
                res = self.c_change
                header = '# sample, time step, total om, woody om, acid, '\
                         'water, ethanol, non soluble, humus'
            elif self.result_type=='CO2 yield':
                res = self.co2_yield
                header = '# sample, time step, CO2 yield'
            f.write(header+'\n')
            for row in res:
                resrow = ''
                for num in row:
                    resrow = ' '.join([resrow, str(num)])
                f.write(resrow+'\n')
            f.close()

    def _init_results(self):
        """
        model results: stock & change
         sample, timestep, tom, woody, acid, water, ethanol, non soluble
         humus
        model results: CO2
         sample, timestep, CO2 yield
        summary results
         common format: time, mean, mode, var, skewness, kurtosis,
         95% confidence-, 95% confidence+
        """
        self.c_stock = empty(dtype=float32, shape=(0, 9))
        self.c_change = empty(dtype=float32, shape=(0, 9))
        self.co2_yield = empty(dtype=float32, shape=(0, 3))
        self.stock_tom = empty(dtype=float32, shape=(0, 8))
        self.stock_woody = empty(dtype=float32, shape=(0, 8))
        self.stock_acid = empty(dtype=float32, shape=(0, 8))
        self.stock_water = empty(dtype=float32, shape=(0, 8))
        self.stock_ethanol = empty(dtype=float32, shape=(0, 8))
        self.stock_non_soluble = empty(dtype=float32, shape=(0, 8))
        self.stock_humus = empty(dtype=float32, shape=(0, 8))
        self.change_tom = empty(dtype=float32, shape=(0, 8))
        self.change_woody = empty(dtype=float32, shape=(0, 8))
        self.change_acid = empty(dtype=float32, shape=(0, 8))
        self.change_water = empty(dtype=float32, shape=(0, 8))
        self.change_ethanol = empty(dtype=float32, shape=(0, 8))
        self.change_non_soluble = empty(dtype=float32, shape=(0, 8))
        self.change_humus = empty(dtype=float32, shape=(0, 8))
        self.co2 = empty(dtype=float32, shape=(0, 8))

yasso = Yasso()
yasso.sample_size = 10
yasso.simulation_length = 10

# Run the demo (if invoked from the command line):
if __name__ == '__main__':
    yasso.configure_traits()

