#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from scipy import array
from datetime import date
from enthought.traits.api import *

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
    litter = LitterComponent()

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
    annual_rainfall = Float()
    mean_temperature = Float()
    variation_amplitude = Float()

###############################################################################
# Model run data classes
###############################################################################
now = str(date.today().month + '/' + str(date.today().year)

class YassoModel(HasTraits):
    """
    The MVC model for Yasso
    """
    # Initial condition
    initial_mode = Enum(['zero', 'non zero'])
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
    # and the results stored
    # Individual model calls
    #     time, iteration, woody, acid, water, ethanol, non_soluble, humus
    c_stock = Array(dtype=float, shape=(None, 8))
    #     time, itration, woody, acid, water, ethanol, non_soluble, humus
    c_change = Array(dtype=float, shape=(None, 8))
    #     time, iteration, CO2 yield
    co2_yield = Array(dtype=float, shape=(None, 3))
    # summary results
    #     common format: time, mean, mode, var, skewness, kurtosis,
    #     50%, 90%, 95%, 99%
    c_stock_total_organic = Array(dtype=float, shape=(None, 10))
    c_stock_acid = Array(dtype=float, shape=(None, 10))
    c_stock_water = Array(dtype=float, shape=(None, 10))
    c_stock_ethanol = Array(dtype=float, shape=(None, 10))
    c_stock_non_soluble = Array(dtype=float, shape=(None, 10))
    c_stock_humus = Array(dtype=float, shape=(None, 10))
    c_stock_woody = Array(dtype=float, shape=(None, 10))
    c_change_total_organic = Array(dtype=float, shape=(None, 10))
    c_change_acid = Array(dtype=float, shape=(None, 10))
    c_change_water = Array(dtype=float, shape=(None, 10))
    c_change_ethanol = Array(dtype=float, shape=(None, 10))
    c_change_non_soluble = Array(dtype=float, shape=(None, 10))
    c_change_humus = Array(dtype=float, shape=(None, 10))
    c_change_woody = Array(dtype=float, shape=(None, 10))
    co2 = Array(dtype=float, shape=(None, 10))
