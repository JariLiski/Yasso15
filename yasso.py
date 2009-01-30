#!/usr/bin/env python
# -*- coding: UTF-8 -*-

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

import pdb

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
    time = String(minlen=4, maxlen=7,
                  regex='^([1|2|3|4|5|6|7|8|9|10|11|12]/){0,1}(\d{4})$')
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

class ConstantClimate(HasTraits):
    annual_rainfall = Float()
    mean_temperature = Float()
    variation_amplitude = Float()

class MonthlyClimate(HasTraits):
    month = Int()
    temperature = Float()
    rainfall = Float()

class YearlyClimate(HasTraits):
    year = Int()
    mean_temperature = Float()
    annual_rainfall = Float()
    variation_amplitude = Float()

###############################################################################
# Table editors
###############################################################################

monthly_climate_te = TableEditor(
    columns = [ObjectColumn(name='month', width=100, editable=False),
               ObjectColumn(name='temperature', width=100),
               ObjectColumn(name='rainfall', width=100),],
    auto_size   = False,
    orientation = 'vertical')

yearly_climate_te = TableEditor(
    columns = [
               ObjectColumn(name='year', width=100),
               ObjectColumn(name='mean_temperature', width=100),
               ObjectColumn(name='annual_rainfall', width=100),
               ObjectColumn(name='variation_amplitude', width=100),
              ],
    auto_size    = False,
    auto_add     = True,
    editable     = True,
    deletable    = True,
    orientation  = 'vertical',
    show_toolbar = True,
    row_factory  = YearlyClimate)

litter_component_te = TableEditor(
    columns = [ObjectColumn(name='mass', width=60),
               ObjectColumn(name='mass_std', width=60),
               ObjectColumn(name='acid', width=60, style='text'),
               ObjectColumn(name='acid_std', width=60),
               ObjectColumn(name='water', width=60, style='text'),
               ObjectColumn(name='water_std', width=60),
               ObjectColumn(name='ethanol', width=60, style='text'),
               ObjectColumn(name='ethanol_std', width=60),
               ObjectColumn(name='non_soluble', width=60, style='text'),
               ObjectColumn(name='non_soluble_std', width=60),
               ObjectColumn(name='humus', width=60, style='text'),
               ObjectColumn(name='humus_std', width=60),
               ObjectColumn(name='size_class', width=60),
               ],
    auto_size    = False,
    auto_add     = True,
    editable     = True,
    deletable    = True,
    orientation  = 'vertical',
    show_toolbar = True,
    row_factory  = LitterComponent)

timed_litter_component_te = TableEditor(
    columns = [ObjectColumn(name='time', width=60),
               ObjectColumn(name='mass', width=60),
               ObjectColumn(name='mass_std', width=60),
               ObjectColumn(name='acid', width=60, style='text'),
               ObjectColumn(name='acid_std', width=60),
               ObjectColumn(name='water', width=60, style='text'),
               ObjectColumn(name='water_std', width=60),
               ObjectColumn(name='ethanol', width=60, style='text'),
               ObjectColumn(name='ethanol_std', width=60),
               ObjectColumn(name='non_soluble', width=60, style='text'),
               ObjectColumn(name='non_soluble_std', width=60),
               ObjectColumn(name='humus', width=60, style='text'),
               ObjectColumn(name='humus_std', width=60),
               ObjectColumn(name='size_class', width=60),
               ],
    auto_size    = False,
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
now = str(date.today().month) + '/' + str(date.today().year)

class Yasso(HasTraits):
    """
    The Yasso model
    """
    # Initial condition
    initial_mode = Enum(['non zero', 'zero'])
    initial_litter = List(trait=LitterComponent)
    # Litter input at each timestep in the simulation
    litter_mode = Enum(['constant', 'timeseries'])
    constant_litter = List(trait=LitterComponent)
    timeseries_litter = List(trait=TimedLitterComponent)
    # Climate definition for the simulation
    climate_mode = Enum(['constant', 'monthly', 'yearly'])
    constant_climate = ConstantClimate()
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
    start_month = String(minlen=6, maxlen=7,
                  regex='^([1|2|3|4|5|6|7|8|9|10|11|12]/){1}(\d{4})$',
                  default=now)
    sample_size = Int()
    duration_unit = Enum(['month', 'year'])
    timestep = Range(low=1)
    simulation_length = Range(low=1)
    result_type = Enum(['C stock', 'C change', 'CO2 yield'])
    presentation_type = Enum(['array', 'chart'])
    # Buttons
    modelrun_event = Button('Run model')
    load_init_event = Button('Load from file...')
    load_constant_litter_event = Button('Load constant input...')
    load_timed_litter_event = Button('Load timeseries input...')
    load_monthly_climate_event = Button('Load monthly data...')
    load_yearly_climate_event = Button('Load yearly data...')
    save_result_event = Button('Save raw results...')
    save_moment_event = Button('Save moment results...')
    # and the results stored
    # Individual model calls
    #     iteration,time, total, woody, acid, water, ethanol, non_soluble, humus
    c_stock = Array(dtype=float32, shape=(0, 9))
    #     iteration,time, total, woody, acid, water, ethanol, non_soluble, humus
    c_change = Array(dtype=float32, shape=(0, 9))
    #     time, iteration, CO2 yield
    co2_yield = Array(dtype=float32, shape=(0, 3))
    # time, mean, mode, var, skewness, kurtosis, 95% conf-, 95% conf+
    stock_tom = Array(dtype=float32, shape=(0, 8))
    stock_woody = Array(dtype=float32, shape=(0, 8))
    stock_acid = Array(dtype=float32, shape=(0, 8))
    stock_water = Array(dtype=float32, shape=(0, 8))
    stock_ethanol = Array(dtype=float32, shape=(0, 8))
    stock_non_soluble = Array(dtype=float32, shape=(0, 8))
    stock_humus = Array(dtype=float32, shape=(0, 8))
    change_tom = Array(dtype=float32, shape=(0, 8))
    change_woody = Array(dtype=float32, shape=(0, 8))
    change_acid = Array(dtype=float32, shape=(0, 8))
    change_water = Array(dtype=float32, shape=(0, 8))
    change_ethanol = Array(dtype=float32, shape=(0, 8))
    change_non_soluble = Array(dtype=float32, shape=(0, 8))
    change_humus = Array(dtype=float32, shape=(0, 8))
    co2 = Array(dtype=float32, shape=(0, 8))

    yassorunner = ModelRunner()

#############################################################
# UI view
#############################################################

    view = View(VGroup(
                       HGroup(
                              Item(name='initial_mode',
                                   style='custom'
                                  ),
                              spring,
                              Item(name='load_init_event',
                                   show_label=False,
                                   visible_when='initial_mode=="non zero"',
                                  ),
                             ),
                       Item('initial_litter',
                            visible_when='initial_mode=="non zero"',
                            show_label=False,
                            editor=litter_component_te,
                           ),
                       label='Initial condition'
                      ),
                VGroup(
                       HGroup(
                              Item('litter_mode',
                                   style='custom'
                                  ),
                              spring,
                              Item(name='load_constant_litter_event',
                                   show_label=False,
                                   visible_when='litter_mode=="constant"',
                                  ),
                              Item(name='load_timed_litter_event',
                                   show_label=False,
                                   visible_when='litter_mode=="timeseries"',
                                  ),
                             ),
                       Item('constant_litter',
                            visible_when='litter_mode=="constant"',
                            show_label=False,
                            editor=litter_component_te,
                           ),
                       Item('timeseries_litter',
                            visible_when='litter_mode=="timeseries"',
                            show_label=False,
                            editor=timed_litter_component_te,
                           ),
                       label='Litter input'
                      ),
                VGroup(
                       HGroup(
                              Item('climate_mode',
                                   style='custom'
                                  ),
                              spring,
                              Item(name='load_yearly_climate_event',
                                   show_label=False,
                                   visible_when='climate_mode=="yearly"',
                                  ),
                              Item(name='load_monthly_climate_event',
                                   show_label=False,
                                   visible_when='climate_mode=="monthly"',
                                  ),
                             ),
                       Item('monthly_climate',
                            show_label=False,
                            visible_when='climate_mode=="monthly"',
                            editor=monthly_climate_te
                           ),
                       Item('yearly_climate',
                            show_label=False,
                            visible_when='climate_mode=="yearly"',
                            width=-200,
                            editor=yearly_climate_te
                           ),
                       VGroup(
                             Item('object.constant_climate.annual_rainfall',
                                  width=-200,
                                 ),
                             Item('object.constant_climate.mean_temperature',
                                  width=-200,
                                 ),
                             Item('object.constant_climate.variation_amplitude',
                                  width=-200,
                                 ),
                             label='Constant climate',
                             show_border=True,
                             visible_when='climate_mode=="constant"'),
                       label='Climate'
                      ),
                VGroup(
                       HGroup(
                              Item('sample_size',
                                   width=-60
                                  ),
                              Item('timestep',
                                   width=-20,
                                  ),
                              Item('duration_unit',
                                   style='custom',
                                   show_label=False,
                                  ),
                              Item('simulation_length',
                                   width=-40,
                                   label='# of timesteps',
                                  ),
                              Item('modelrun_event',
                                   show_label=False
                                  ),
                              spring,
                             ),
                       HGroup(
                              Item('result_type',
                                   style='custom',
                                   label='Show',
                                  ),
                              Item('save_result_event',
                                   show_label=False,
                                  ),
                              Item('save_moment_event',
                                   show_label=False,
                                  ),
                              spring,
                             ),
                       HGroup(
                              Item('presentation_type',
                                   style='custom',
                                   label='As'
                                  ),
                              spring,
                             ),
                       Item('c_stock',
                            visible_when='result_type=="C stock" and \
                                          presentation_type=="array"',
                            show_label=False,
                            editor=c_stock_te,
                           ),
                       Item('c_change',
                            visible_when='result_type=="C change" and \
                                          presentation_type=="array"',
                            show_label=False,
                            editor=c_stock_te,
                           ),
                       Item('co2_yield',
                            visible_when='result_type=="CO2 yield" and \
                                          presentation_type=="array"',
                            show_label=False,
                            editor=co2_yield_te,
                           ),
                       HGroup(
                              ChacoPlotItem(index='p_timestep',
                                            value='ps_tom',
                                            show_label=False,
                                            x_label = 'time',
                                            y_label = 'total organic matter',
                                            resizable=True,
                                            orientation='h',
                                            title = 'Total organic matter',
                                            color = 'red',
                                            bgcolor = 'white',
                                            border_visible=False,
                                            border_width=1,
                                            padding_bg_color = 'lightgray'
                                           ),
                              ChacoPlotItem(index='p_timestep',
                                            value='ps_woody',
                                            show_label=False,
                                            x_label = 'time',
                                            y_label = 'woody matter',
                                            resizable=True,
                                            orientation='h',
                                            title = 'Woody organic matter',
                                            color = 'red',
                                            bgcolor = 'white',
                                            border_visible=False,
                                            border_width=1,
                                            padding_bg_color = 'lightgray'
                                           ),
                              ChacoPlotItem(index='p_timestep',
                                            value='ps_acid',
                                            show_label=False,
                                            x_label = 'time',
                                            y_label = 'acid soluble',
                                            resizable=True,
                                            orientation='h',
                                            title = 'Acid soluble',
                                            color = 'red',
                                            bgcolor = 'white',
                                            border_visible=False,
                                            border_width=1,
                                            padding_bg_color = 'lightgray'
                                           ),
                              visible_when='result_type=="C stock" and \
                                            presentation_type=="chart"',
                             ),
                       HGroup(
                              ChacoPlotItem(index='p_timestep',
                                            value='ps_woody',
                                            show_label=False,
                                            x_label = 'time',
                                            y_label = 'water soluble',
                                            resizable=True,
                                            orientation='h',
                                            title = 'Water soluble',
                                            color = 'red',
                                            bgcolor = 'white',
                                            border_visible=False,
                                            border_width=1,
                                            padding_bg_color = 'lightgray'
                                           ),
                              ChacoPlotItem(index='p_timestep',
                                            value='ps_ethanol',
                                            show_label=False,
                                            x_label = 'time',
                                            y_label = 'ethanol soluble',
                                            resizable=True,
                                            orientation='h',
                                            title = 'Ethanol soluble',
                                            color = 'red',
                                            bgcolor = 'white',
                                            border_visible=False,
                                            border_width=1,
                                            padding_bg_color = 'lightgray'
                                           ),
                              ChacoPlotItem(index='p_timestep',
                                            value='ps_non_soluble',
                                            show_label=False,
                                            x_label = 'time',
                                            y_label = 'non soluble',
                                            resizable=True,
                                            orientation='h',
                                            title = 'Non soluble',
                                            color = 'red',
                                            bgcolor = 'white',
                                            border_visible=False,
                                            border_width=1,
                                            padding_bg_color = 'lightgray'
                                           ),
                              visible_when='result_type=="C stock" and \
                                            presentation_type=="chart"',
                             ),
                       HGroup(
                              ChacoPlotItem(index='p_timestep',
                                            value='ps_humus',
                                            show_label=False,
                                            x_label = 'time',
                                            y_label = 'humus',
                                            resizable=True,
                                            orientation='h',
                                            title = 'Humus',
                                            color = 'red',
                                            bgcolor = 'white',
                                            border_visible=False,
                                            border_width=1,
                                            padding_bg_color = 'lightgray'
                                           ),
                              ChacoPlotItem(index='',
                                            value='',
                                            show_label=False,
                                            x_label = '',
                                            y_label = '',
                                            resizable=True,
                                            orientation='h',
                                            title = '',
                                            color = 'red',
                                            bgcolor = 'white',
                                            border_visible=False,
                                            border_width=1,
                                            padding_bg_color = 'lightgray'
                                           ),
                              ChacoPlotItem(index='',
                                            value='',
                                            show_label=False,
                                            x_label = '',
                                            y_label = '',
                                            resizable=True,
                                            orientation='h',
                                            title = '',
                                            color = 'red',
                                            bgcolor = 'white',
                                            border_visible=False,
                                            border_width=1,
                                            padding_bg_color = 'lightgray'
                                           ),
                              visible_when='result_type=="C stock" and \
                                            presentation_type=="chart"',
                             ),

                       label='Model run',
                      ),
                title     = 'Yasso 07',
                id        = 'simosol.yasso07',
                dock      = 'horizontal',
                resizable = True,
                scrollable= True,
                buttons   = NoButtons
               )

###############################################################################
# Event handlers
###############################################################################

    @on_trait_change('stock_tom, stock_woody, stock_acid, stock_water, \
                     stock_non_soluble, stock_humus, change_tom, change_woody,\
                     change_acid, change_water, change_ethanol, \
                     change_non_soluble, change_humus, co2')
    def set_plot_data(self):
        self.p_timestep = self.stock_tom[:,0]
        self.ps_tom = self.stock_tom[:,1]
        self.ps_woody = self.stock_woody[:,1]
        self.ps_acid = self.stock_acid[:,1]
        self.ps_water = self.stock_water[:,1]
        self.ps_ethanol = self.stock_ethanol[:,1]
        self.ps_non_soluble = self.stock_non_soluble[:,1]
        self.ps_humus = self.stock_humus[:,1]
        self.pc_tom = self.stock_tom[:,1]
        self.pc_woody = self.stock_woody[:,1]
        self.pc_acid = self.stock_acid[:,1]
        self.pc_water = self.stock_water[:,1]
        self.pc_ethanol = self.stock_ethanol[:,1]
        self.pc_non_soluble = self.stock_non_soluble[:,1]
        self.pc_humus = self.stock_humus[:,1]
        self.p_co2 = self.co2[:,1]


    def _modelrun_event_fired(self):
        self.__init_results()
        self.yassorunner.run_model(self)

    def _load_init_event_fired(self):
        errmsg = 'Litter components should contain: \n'\
                      ' mass, mass std, acid, acid std, water, water std,\n'\
                      ' ethanol, ethanol std, non soluble, non soluble std,'\
                      '\n humus, humus std, size class'
        filename = open_file()
        if filename != '':
            try:
                f=open(filename)
                self.initial_litter = []
                for line in f:
                    ok, obj = self.__load_litter_object(line, errmsg)
                    if not ok:
                        break
                    self.initial_litter.append(obj)
                f.close()
            except:
                pass

    def _load_constant_litter_event_fired(self):
        errmsg = 'Litter components should contain: \n'\
                      ' mass, mass std, acid, acid std, water, water std,\n'\
                      ' ethanol, ethanol std, non soluble, non soluble std,'\
                      '\n humus, humus std, size class'
        filename = open_file()
        print 'constant load'
        if filename != '':
            try:
                f=open(filename)
                self.constant_litter = []
                for line in f:
                    print 'loading'
                    ok, obj = self.__load_litter_object(line, errmsg)
                    if not ok:
                        break
                    print obj
                    self.constant_litter.append(obj)
                    print self.constant_litter
                f.close()
            except:
                pass

    def _load_timed_litter_event_fired(self):
        errmsg = 'Timed litter components should contain: \n'\
                      ' time, mass, mass std, acid, acid std, water, '\
                      'water std,\n'\
                      ' ethanol, ethanol std, non soluble, non soluble std,'\
                      '\n humus, humus std, size class'
        filename = open_file()
        if filename != '':
            try:
                f=open(filename)
                self.timeseries_litter = []
                for line in f:
                    ok, obj = self.__load_litter_object(line, errmsg, True)
                    if not ok:
                        break
                    self.timeseries_litter.append(obj)
                f.close()
            except:
                pass

    def _load_yearly_climate_event_fired(self):
        filename = open_file()
        errmsg = 'Yearly climate should contain: year, mean temperature,\n'\
                 'annual rainfall and temperature variation amplitude'
        if filename!='':
            try:
                f=open(filename)
                self.yearly_climate = []
                for line in f:
                    data = line.split()
                    if len(data)==4:
                        obj = YearlyClimate(year=int(data[0]),
                                  mean_temperature=float(data[1]),
                                  annual_rainfall=float(data[2]),
                                  variation_amplitude=float(data[3])),
                        self.yearly_climate.append(obj)
                    elif line[0]!='#' and len(line)>0:
                        error(errmsg, title='error reading data',
                              buttons=['ok'])
                        break
                f.close()
            except:
                pass

    def _load_monthly_climate_event_fired(self):
        filename = open_file()
        errmsg = 'Monthly data should contain: month,\n'\
                 'temperature and rainfall'
        if filename != '':
            try:
                f=open(filename)
                self.monthly_climate = []
                for line in f:
                    data = line.split()
                    if len(data)==3:
                        obj = MonthlyClimate(month=int(data[0]),
                                  temperature=float(data[1]),
                                  rainfall=float(data[2]))
                        self.monthly_climate.append(obj)
                    elif line[0]!='#' and len(line)>0:
                        error(errmsg, title='Error reading data',
                              buttons=['ok'])
                        break
                f.close()
            except:
                pass

    def _save_moment_event_fired(self):
        filename = save_file()
        if filename != '':
            f=open(filename, 'w')
            if self.result_type=='C stock':
                comps = (('tom', self.stock_tom), ('woody', self.stock_woody),
                       ('acid', self.stock_acid), ('water', self.stock_water),
                       ('non_soluble', self.stock_non_soluble),
                       ('humus', self.stock_humus))
                header = '# C stock\n# component, time step, '\
                         'mean, mode, var, skewness, kurtosis, '\
                         '95% confidence lower limit, 95% upper limit'
            elif self.result_type=='C change':
                comps = (('tom', self.change_tom), ('woody', self.change_woody),
                       ('acid', self.change_acid), ('water', self.change_water),
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

    def __load_litter_object(self, line, errmsg, hastime=False):
        obj = None
        loaded = True
        data = line.split()
        if hastime:
            if len(data)==14:
                obj = TimedLitterComponent(time=data[0],
                        mass=float(data[1]),
                        mass_std=float(data[2]),
                        acid=float(data[3]),
                        acid_std=float(data[4]),
                        water=float(data[5]),
                        water_std=float(data[6]),
                        ethanol=float(data[7]),
                        ethanol_std=float(data[8]),
                        non_soluble=float(data[9]),
                        non_soluble_std=float(data[10]),
                        humus=float(data[11]),
                        humus_std=float(data[12]),
                        size_class=float(data[13]))
            elif line[0]!='#' and len(line)>0:
                error(errmsg, title='Error reading data',
                      buttons=['OK'])
                loaded = False
        else:
            if len(data)==13:
                print 'data'
                obj = LitterComponent(mass=float(data[0]),
                        mass_std=float(data[1]),
                        acid=float(data[2]),
                        acid_std=float(data[3]),
                        water=float(data[4]),
                        water_std=float(data[5]),
                        ethanol=float(data[6]),
                        ethanol_std=float(data[7]),
                        non_soluble=float(data[8]),
                        non_soluble_std=float(data[9]),
                        humus=float(data[10]),
                        humus_std=float(data[11]),
                        size_class=float(data[12]))
                print obj
            elif line[0]!='#' and len(line)>0:
                error(errmsg, title='Error reading data',
                      buttons=['OK'])
                loaded = False
        return loaded, obj

    def __init_results(self):
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

# Run the demo (if invoked from the command line):
if __name__ == '__main__':
    yasso.configure_traits()

