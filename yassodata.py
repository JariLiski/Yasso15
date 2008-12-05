#!/usr/bin/env python
# -*- coding: UTF-8 -*-

from scipy import array
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
    woody = Bool(defaul_value=False)
    wood_size_class = Float()

class TimedLitterComponent(HasTraits):
    time = String(minlen=4, maxlen=7,
                  regex='^([1|2|3|4|5|6|7|8|9|10|11|12]/){0,1}(\d{4})$')
    litter = LitterComponent()

class ConstantClimate(HasTraits):
    annual_rainfall = Float()
    mean_temperature = Float()
    variation_amplitude = Float()

class MonthlyClimate(HasTraits):
    month = Range(low=1, high=12)
    temperature = Float()
    rainfall = Float()

class YearlyClimate(HasTraits):
    year = Range(low=1800)
    annual_rainfall = Float()
    mean_temperature = Float()
    variation_amplitude = Float()

###############################################################################
# Model run data classes
###############################################################################

class InitialState(HasTraits):
    """
    The definition of the initial litter composition
    """
    mode = Enum(['zero', 'non zero'])
    litter = List(trait=LitterComponent)

class LitterInput(HasTraits):
    """
    Litter input at each timestep in the simulation
    """
    mode = Enum(['constant', 'timeseries'])
    constant = List(trait=LitterComponent)
    timeseries = List(trait=TimedLitterComponent)

class Climate(HasTraits):
    """
    Climate definition for the simulation
    """
    mode = Enum(['constant', 'monthly', 'yearly'])
    constant = ConstantClimate()
    monthly = List(trait=MonthlyClimate)
    yearly = List(trait=YearlyClimate)

class ModelRun(HasTraits):
    """
    How the model will be run
    """
    sample_size = Int()
    timestep = Enum(['1 month', '1 year'])
    simulation_length = Range(low=1)
    duration_unit = Enum(['month', 'year'])

###############################################################################
# Model output
###############################################################################

class ModelResult(HasTraits):
    # time, iteration, woody, acid, water, ethanol, non_soluble, humus
    c_stock = Array(dtype=float, shape=(8, None))
    # time, itration, woody, acid, water, ethanol, non_soluble, humus
    c_change = Array(dtype=float, shape=(8, None))
    # time, iteration, CO2 yield
    co2_yield = Array(dtype=float, shape=(3, None))

class SummaryResult(HasTraits):
    # common format: time, mean, mode, var, skewness, kurtosis, 50%, 90%, 95%, 99%
    c_stock_total_organic = Array(dtype=float, shape=(10, None))
    c_stock_acid = Array(dtype=float, shape=(10, None))
    c_stock_water = Array(dtype=float, shape=(10, None))
    c_stock_ethanol = Array(dtype=float, shape=(10, None))
    c_stock_non_soluble = Array(dtype=float, shape=(10, None))
    c_stock_humus = Array(dtype=float, shape=(10, None))
    c_stock_woody = Array(dtype=float, shape=(10, None))
    c_change_total_organic = Array(dtype=float, shape=(10, None))
    c_change_acid = Array(dtype=float, shape=(10, None))
    c_change_water = Array(dtype=float, shape=(10, None))
    c_change_ethanol = Array(dtype=float, shape=(10, None))
    c_change_non_soluble = Array(dtype=float, shape=(10, None))
    c_change_humus = Array(dtype=float, shape=(10, None))
    c_change_woody = Array(dtype=float, shape=(10, None))
    co2 = Array(dtype=float, shape=(10, None))
