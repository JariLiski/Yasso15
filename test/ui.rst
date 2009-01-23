.. -ui-py:

#####
ui.py
#####


**********************************
class YassoController(Controller):
**********************************

Controller and the default view for the Yasso07 program. YassoModel provides the model for the MVC application and ModelRunner class takes care of actually running the prediction model::
    
    >>> from yassodata import YassoModel
    >>> class ModelRunner(object):
    >>>     
    >>> yasso = YassoController(model=YassoModel())
    
def run_model(self):
======================

Determines for how many timesteps the model should be run and creates the diffeinitial state and input combination scenarios. Then iterates over the different scenarios sampling each with the given sample size for each timestep. In each iteration determines the climatic conditions for the timestep and calls the prediction model, and stores the model results::

    >>>

def __add_c_stock_result(self, sample, timestep, woody, nonwoody):
======================================================

Adds the model prediction results to the result array. The timestep and iteration identifiers have been added to the model results before adding them to the result array. If there already are results for the particular timestep and iteration in the array, the new results are added to those

sample -- sample ordinal
timestep -- timestep ordinal
woody -- mass of woody component (for the size class the model was called with)
nonwoody -- masses of the non woody components::

    >>> 

def __calculate_c_change(self, s, ts):
======================================

The change of mass per component during the timestep

s -- sample ordinal
ts -- timestep ordinal::

    >>>

def __calculate_co2_yield(self, s, ts):
=======================================

The yield of CO2 during the timestep

s -- sample ordinal
ts -- timestep ordinal::

    >>>


def __calculate_timesteps(self):
================================

The number of simulation timesteps are the simulation length divided by the simulation timestep lenght and rounded to the nearest biggest integer::

    >>> 

def __create_input(self, timestep):
==========================
Create the different initial state and input conditions that the model should be run with for the current timestep::

    >>>

def __define_components(self, fromme, tome, ind=None):
======================================================

Adds the component specification to list to be passed to the model

fromme -- the component specification from the ui
tome -- the list on its way to the model
ind -- indices if the components are taken from a timeseries::

    >>>

def __fill_input(self):
=======================

Makes sure that both the initial state and litter input have the same size classes::
    
    >>> 

def __map_timestep2timeind(self, timestep):
===========================================

Convert the timestep index to the nearest time defined in the litter timeseries array

timestep -- ordinal number of the simulation run timestep::

    >>> 

def __predict(self, initial, litter, climate):
==============================================

Calls the prediction model with the given initial condition, litter input and climate. For sample size of one, the call should be made with the maximum likelihood parameteter and input values. The same applies for the first model call when the sample size is greater than one::

    >>>

def __process_next_nw_init(self, mode, nonwoody=None):
======================================================

During a single timestep the model output for non woody components is added together for all the size classes. Before moving to the next timestep this accumulated non woody output is converted as the non woody initial state::

    >>>

