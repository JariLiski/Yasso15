.. -modelcall-py:

############
modelcall.py
############


**************************
class ModelRunner(object):
**************************

This class is responsible for calling the actual Yasso07 model.  It converts the data in the UI into the form that can be passed to the model

def __init__(self, timestep):
=============================

Sets the timestep of the model run, and reads the model parameter value predictions from the file 'yasso_param.txt' which must be in the same directory as the module file::

    >>> mr = ModelRunner(1.0)
    >>> mr.__model_param[0]

def run_model(self):
======================

Determines for how many timesteps the model should be run and creates the diffeinitial state and input combination scenarios. Then iterates over the different scenarios sampling each with the given sample size for each timestep. In each iteration determines the climatic conditions for the timestep and calls the prediction model, and stores the model results::

    >>>

def _add_c_stock_result(self, sample, timestep, woody, nonwoody):
======================================================

Adds the model prediction results to the result array. The timestep and iteration identifiers have been added to the model results before adding them to the result array. If there already are results for the particular timestep and iteration in the array, the new results are added to those

sample -- sample ordinal
timestep -- timestep ordinal
woody -- mass of woody component (for the size class the model was called with)
nonwoody -- masses of the non woody components::

    >>> 

def _calculate_c_change(self, s, ts):
======================================

The change of mass per component during the timestep

s -- sample ordinal
ts -- timestep ordinal::

    >>>

def _calculate_co2_yield(self, s, ts):
=======================================

The yield of CO2 during the timestep

s -- sample ordinal
ts -- timestep ordinal::

    >>>


def _calculate_timesteps(self):
================================

The number of simulation timesteps are the simulation length divided by the simulation timestep lenght and rounded to the nearest biggest integer::

    >>> 

def _construct_climate(self, timestep):
=======================================

From the different ui options, creates a unified climate description (type, start month, duration, temperature, rainfall, amplitude)

def _construct_monthly_climate(self, cl, sm, dur):
==================================================

Summarizes the monthly climate data into rain, temp and amplitude given the start month and duration

cl -- climate dictionary
sm -- start month
dur -- timestep duration in months

def _construct_yearly_climate(self, cl, sm, sy, dur):
=====================================================

Summarizes the yearly climate data into rain, temp and amplitude given the start month, start year and duration

cl -- climate dictionary
sm -- start month
sy -- start year
dur -- timestep duration in years

def _create_input(self, timestep):
==================================
create the different initial state and input conditions that the model should be run with for the current timestep::

    >>>

def _define_components(self, fromme, tome, ind=None):
======================================================

Adds the component specification to list to be passed to the model

fromme -- the component specification from the ui
tome -- the list on its way to the model
ind -- indices if the components are taken from a timeseries::

    >>>

def _draw_from_distr(self, values, pairs, ml):
==============================================

Draw a sample from the normal distribution based on the mean and std pairs

values -- a vector containing mean and standard deviation pairs
pairs -- how many pairs the vector contains
ml -- boolean for using the maximum likelihood values

def _fill_input(self):
=======================

Makes sure that both the initial state and litter input have the same size classes::
    
    >>> 
    
def _fill_moment_results(self):
===============================

Fills the result arrays used for storing the calculated moments common format: time, mean, mode, var, skewness, kurtosis, 95% confidence lower limit, 95% upper limit

gef _get_now(self, timestep):
=============================

Returns the date for the simulation step.

def _map_timestep2timeind(self, timestep):
===========================================

Convert the timestep index to the nearest time defined in the litter timeseries array

timestep -- ordinal number of the simulation run timestep::

    >>> 

def _predict(self, sc, initial, litter, climate):
=================================================
Processes the input data before calling the model and then runs the model

sc -- non-woody / size of the woody material modelled
initial -- system state at the beginning of the timestep
litter -- litter input for the timestep
climate -- climate conditions for the timestep
firstrun -- first invocation of the model
mlrun -- run the model using maximum likelihood estimates
draw -- should the values be drawn from the distribution or not
ltype -- litter input type: 'constant' or 'timeseries'

For sample size of one, the call should be made with the maximum likelihood parameteter and input values. The same applies for the first model call when the sample size is greater than one::

    >>>

