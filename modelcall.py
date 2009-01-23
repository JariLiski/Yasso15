#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import y6c

# the order in which data comes in (defined by list index) and in which
# it should passed to the model (defined in the tuple)
VALUESPEC = [('mass', None), ('acid', 0), ('water', 1), ('ethanol', 2),
              ('non_soluble', 3), ('humus', 4)]

class ModelRunner(object):
    """
    This class is responsible for calling the actual Yasso07 model.
    It converts the data in the UI into the form that can be passed
    to the model
    """

    def __init__(self, timestep):
        """
        Constructor.

        timestep -- the temporal granularity of model runs, min 1 month,
                    given in years
        """
        self._timestep = timestep
        f = open('yasso_param.txt')
        first = [float(val) for val in f.readline().split()]
        parr = numpy.array([first])
        for line in f:
            data = [float(val) for val in line]
            parr = numpy.append(parr, [data])
        self._model_param = parr
        f.close()

    def predict(self, initial, litter, climate, mlrun=False):
        """
        processes the input data before calling the model and then
        runs the model
        initial -- system state at the beginning of the timestep
        litter -- litter input for the timestep
        climate -- climate conditions for the timestep
        firstrun -- first invocation of the model
        mlrun -- run the model using maximum likelihood estimates
        """
        # model parameters
        if mlrun:
            # maximum likelihood estimates for the model parameters
            a_param = self._model_param[0,:]
            # and mean values for the initial state and input
            init_cond = self.__draw_from_distr(initial, VALUESPEC, ml=True)
            inf_input = self.__draw_from_distr(litter, VALUESPEC, ml=True)
        else:
            pind = random.randint(0, self._model_param.shape[0]-1)
            a_param = self._model_param[pind,:]
            init_cond = self.__draw_from_distr(initial, VALUESPEC)
            inf_input = self.__draw_from_distr(litter, VALUESPEC)
        # add size class to the sample
        inf_input.append(litter[-1])
        # climate
        cl_climate = [climate['start month'], climate['duration'],
                      climate['temp'], climate['rain'], climate['amplitude']]
        endstate = y6c.mod6c(a_param, self._timestep, init_cond,
                              inf_input, cl_climate)
        return init_cond, inf_input, endstate

    def __draw_from_distr(self, values, pairs, ml=False):
        """
        Draw a sample from the normal distribution based on the mean and std
        pairs

        values -- a vector containing mean and standard deviation pairs
        pairs -- how many pairs the vector contains
        """
        sample = [None for i in range(len(VALUESPEC))]
        for i in range(len(VALUESPEC)):
            vs = VALUESPEC[i]
            mean = values[i]
            std = values[i+1]
            if std > 0.0 and not ml:
                samplemean = random.gauss(mean, std)
            else:
                samplemean = mean
            if vs[0] == 'mass':
                samplemass = samplemean
                remainingmass = samplemean
            elif vs[0] == 'humus':
                sample[vs[1]] = samplemean
            elif vs[0] != 'water':
                compmass = samplemass * samplemean
                sample[vs[1]] = compmass
                remainingmass -= compmass
            elif vs[0] == 'water':
                waterind = i
        sample[VALUESPEC[waterind][1]] = remainingmass
        return sample
