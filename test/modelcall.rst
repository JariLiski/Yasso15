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

def predict(self, initial, litter, climate, mlrun=False):
=========================================================================

Processes the input data before calling the model and then runs the model 
    initial -- system state at the beginning of the timestep
    litter -- litter input for the timestep
    climate -- climate conditions for the timestep
    mlrun -- run the model using maximum likelihood estimates


