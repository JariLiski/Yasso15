#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from numpy import array, float32
from datetime import date
from enthought.traits.api import *
from enthought.traits.ui.api import *
from enthought.traits.ui.menu import *
from enthought.traits.ui.table_column import ObjectColumn
from enthought.traits.ui.file_dialog import open_file

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
    variation_amplitude = Float()
    annual_rainfall = Float()

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
    columns = [ObjectColumn(name='year', width=100),
               ObjectColumn(name='mean_temperature', width=100),
               ObjectColumn(name='variation_amplitude', width=100),
               ObjectColumn(name='annual_rainfall', width=100)],
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
               ObjectColumn(name='acid', width=60),
               ObjectColumn(name='acid_std', width=60),
               ObjectColumn(name='water', width=60),
               ObjectColumn(name='water_std', width=60),
               ObjectColumn(name='ethanol', width=60),
               ObjectColumn(name='ethanol_std', width=60),
               ObjectColumn(name='non_soluble', width=60),
               ObjectColumn(name='non_soluble_std', width=60),
               ObjectColumn(name='humus', width=60),
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
               ObjectColumn(name='acid', width=60),
               ObjectColumn(name='acid_std', width=60),
               ObjectColumn(name='water', width=60),
               ObjectColumn(name='water_std', width=60),
               ObjectColumn(name='ethanol', width=60),
               ObjectColumn(name='ethanol_std', width=60),
               ObjectColumn(name='non_soluble', width=60),
               ObjectColumn(name='non_soluble_std', width=60),
               ObjectColumn(name='humus', width=60),
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
    modelrun_event = Button('Run model')
    load_init_event = Button('Load from file...')
    load_constant_litter_event = Button('Load constant input...')
    load_timed_litter_event = Button('Load timeseries input...')
    load_monthly_climate_event = Button('Load monthly data...')
    load_yearly_climate_event = Button('Load yearly data...')
    # and the results stored
    # Individual model calls
    #     time,iteration, total, woody, acid, water, ethanol, non_soluble, humus
    c_stock = Array(dtype=float32, shape=(None, 9))
    #     time,iteration, total, woody, acid, water, ethanol, non_soluble, humus
    c_change = Array(dtype=float32, shape=(None, 9))
    #     time, iteration, CO2 yield
    co2_yield = Array(dtype=float32, shape=(None, 3))
    # summary results
    #     common format: time, mean, mode, var, skewness, kurtosis,
    #     50%, 90%, 95%, 99%
    c_stock_total_organic = Array(dtype=float32, shape=(None, 10))
    c_stock_acid = Array(dtype=float32, shape=(None, 10))
    c_stock_water = Array(dtype=float32, shape=(None, 10))
    c_stock_ethanol = Array(dtype=float32, shape=(None, 10))
    c_stock_non_soluble = Array(dtype=float32, shape=(None, 10))
    c_stock_humus = Array(dtype=float32, shape=(None, 10))
    c_stock_woody = Array(dtype=float32, shape=(None, 10))
    c_change_total_organic = Array(dtype=float32, shape=(None, 10))
    c_change_acid = Array(dtype=float32, shape=(None, 10))
    c_change_water = Array(dtype=float32, shape=(None, 10))
    c_change_ethanol = Array(dtype=float32, shape=(None, 10))
    c_change_non_soluble = Array(dtype=float32, shape=(None, 10))
    c_change_humus = Array(dtype=float32, shape=(None, 10))
    c_change_woody = Array(dtype=float32, shape=(None, 10))
    co2 = Array(dtype=float32, shape=(None, 10))

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
                              spring
                             ),
                       HGroup(
                              Item('timestep',
                                   width=-20,
                                  ),
                              Item('duration_unit',
                                   style='custom',
                                   show_label=False,
                                  ),
                              spring
                             ),
                       HGroup(
                              Item('simulation_length',
                                   width=-20,
                                   label='# of timesteps',
                                  ),
                              spring,
                             ),
                       HGroup(
                              Item('modelrun_event',
                                   show_label=False
                                  ),
                              spring
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

    def _modelrun_event_fired(self):
        self.yassorunner.run_model(self)

    def _load_init_event_fired(self):
        filename = open_file()
        if filename != '':
            self.__load_litter_components(filename, self.initial_litter)

    def _load_constant_litter_event_fired(self):
        filename = open_file()
        if filename != '':
            self.__load_litter_components(filename, self.constant_litter)

    def _load_timed_litter_event_fired(self):
        filename = open_file()
        if filename != '':
            self.__load_litter_components(filename, self.timeseries_litter,
                                          hastime=True)

    def _load_yearly_climate_event_fired(self):
        filename = open_file()
        if filename != '':
            try:
                f=open(filename)
                self.yearly_climate = []
                for line in f:
                    data = line.split()
                    if len(data)==4:
                        obj = YearlyClimate(year=int(data[0]),
                                  mean_temperature=float(data[1]),
                                  variation_amplitude=float(data[2]),
                                  annual_rainfall=float(data[3]))
                        self.yearly_climate.append(obj)
                f.close()
            except:
                pass

    def _load_monthly_climate_event_fired(self):
        filename = open_file()
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
                f.close()
            except:
                pass

    def __load_litter_components(filename, target, hastime=False):
        try:
            f=open(filename)
            target = []
            for line in f:
                obj = None
                data = line.split()
                if hastime:
                    if len(data)==14:
                        obj = LitterComponent(time=data[0],
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
                else:
                    if len(data)==13:
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
                if obj is not None:
                    target.append(obj)
            f.close()
        except:
            pass

yasso = Yasso()

# Run the demo (if invoked from the command line):
if __name__ == '__main__':
    yasso.configure_traits()

