#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement

import y07
import numpy
import math
import struct
from datetime import date
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import random
import stats
from enthought.pyface.api import ProgressDialog
from enthought.traits.ui.message import error

# the order in which data comes in (defined by list index) and in which
# it should passed to the model (defined in the tuple)
VALUESPEC = [('mass', None), ('acid', 0), ('water', 1), ('ethanol', 2),
             ('non_soluble', 3), ('humus', 4)]
STARTDATE = date(2, 1, 1)
STEADY_STATE_TIMESTEP = 10000.
# constants for the model parameters
PARAM_SAMPLES = 100000
PARAM_COUNT = 45
PARAM_F = '45f'

class ModelRunner(object):
    """
    This class is responsible for calling the actual Yasso07 modeldata.
    It converts the data in the UI into the form that can be passed
    to the model
    """

    def __init__(self, parfile):
        """
        Constructor.
        """
        self.parfile = parfile

    def compute_steady_state(self, modeldata):
        """
        Solves the steady state for the system given the constant infall
        """
        self.simulation = False
        self.md = modeldata
        self.steady_state = numpy.empty(shape=(0,6), dtype=numpy.float32)
        self.timemap = defaultdict(list)
        samplesize = self.md.sample_size
        timesteps = 1
        self.timestep_length = STEADY_STATE_TIMESTEP
        self.curr_yr_ind = 0
        self.ml_run = True
        self.infall = {}
        self.initial_mode = 'zero'
        timemsg = None
        with open(self.parfile, 'rb') as self.f:
            for j in range(samplesize):
                self.draw = True
                self._predict_steady_state(j)
                self.ml_run = False
        self._steadystate2initial()
        return self.ss_result

    def run_model(self, modeldata):
        self.simulation = True
        self.md = modeldata
        self.c_stock = numpy.empty(shape=(0,9), dtype=numpy.float32)
        self.c_change = numpy.empty(shape=(0,9), dtype=numpy.float32)
        self.co2_yield = numpy.empty(shape=(0,3), dtype=numpy.float32)
        self.timemap = defaultdict(list)
        samplesize = self.md.sample_size
        msg = "Simulating %d samples for %d timesteps" % (samplesize,
                                                    self.md.simulation_length)
        progress = ProgressDialog(title="Simulation", message=msg,
                                  max=samplesize, show_time=True,
                                  can_cancel=True)
        progress.open()
        timesteps = self.md.simulation_length
        self.timestep_length = self.md.timestep_length
        self.curr_yr_ind = 0
        self.ml_run = True
        self.infall = {}
        self.initial_mode = self.md.initial_mode
        if self.initial_mode=='steady state':
            self.initial_def = self.md.steady_state
        else:
            self.initial_def = self.md.initial_litter
        timemsg = None
        with open(self.parfile, 'rb') as self.f:
            for j in range(samplesize):
                (cont, skip) = progress.update(j)
                if not cont or skip:
                    break
                self.draw = True
                for k in range(timesteps):
                    self._predict_timestep(j, k)
                self.ml_run = False
        self._fill_moment_results()
        progress.update(samplesize)
        if timemsg is not None:
            error(timemsg, title='Error handling timesteps',
                  buttons=['OK'])
        return self.c_stock, self.c_change, self.co2_yield

    def _add_c_stock_result(self, sample, timestep, sc, endstate):
        """
        Adds model result to the C stock

        res -- model results augmented with timestep, iteration and
               sizeclass data
        """
        cs = self.c_stock
        # if sizeclass is non-zero, all the components are added together
        # to get the mass of wood
        if sc > 0:
            totalom = endstate.sum()
            woody = totalom
        else:
            totalom = endstate.sum()
            woody = 0.0
        res = numpy.concatenate(([float(sample), float(timestep), totalom,
                                  woody], endstate))
        res.shape = (1, 9)
        # find out whether there are already results for this timestep and
        # iteration
        criterium = (cs[:,0]==res[0,0]) & (cs[:,1]==res[0,1])
        target = numpy.where(criterium)[0]
        if len(target) == 0:
            self.c_stock = numpy.append(cs, res, axis=0)
        else:
            # if there are, add the new results to the existing ones
            self.c_stock[target[0],2:] = numpy.add(cs[target[0],2:], res[0,2:])

    def _add_steady_state_result(self, sc, endstate):
        """
        Adds model result to the C stock

        res -- model results augmented with timestep, iteration and
               sizeclass data
        """
        res = numpy.concatenate(([float(sc)], endstate))
        res.shape = (1, 6)
        self.steady_state= numpy.append(self.steady_state, res, axis=0)

    def _calculate_c_change(self, s, ts):
        """
        The change of mass per component during the timestep

        s -- sample ordinal
        ts -- timestep ordinal
        """
        cc = self.c_change
        cs = self.c_stock
        criterium = (cs[:,0]==s) & (cs[:,1]==ts)
        nowtarget = numpy.where(criterium)[0]
        criterium = (cs[:,0]==s) & (cs[:,1]==ts-1)
        prevtarget = numpy.where(criterium)[0]
        if len(nowtarget) > 0 and len(prevtarget)>0:
            stepinf = numpy.array([[s, ts, 0., 0., 0., 0., 0., 0., 0.]],
                                  dtype=numpy.float32)
            self.c_change = numpy.append(cc, stepinf, axis=0)
            self.c_change[-1, 2:] = cs[nowtarget, 2:] - cs[prevtarget, 2:]

    def _calculate_co2_yield(self, s, ts):
        """
        The yield of CO2 during the timestep

        s -- sample ordinal
        ts -- timestep ordinal
        """
        cs = self.c_stock
        cy = self.co2_yield
        stepinf = numpy.array([[s, ts, 0.]], dtype=numpy.float32)
        self.co2_yield = numpy.append(cy, stepinf, axis=0)
        # total organic matter at index 3
        criterium = (cs[:,0]==s) & (cs[:,1]==ts)
        rowind = numpy.where(criterium)[0]
        if len(rowind)>0:
            atend = cs[rowind[0], 3]
            self.co2_yield[-1, 2] = self.ts_initial + self.ts_infall - atend

    def _construct_climate(self, timestep):
        """
        From the different ui options, creates a unified climate description
        (type, start month, duration, temperature, rainfall, amplitude)
        """
        cl = {}
        now = self._get_now(timestep)
        if now==-1:
            return -1
        cl['start month'] = now.month
        if self.md.duration_unit == 'month':
            if self.simulation:
                yeardur = self.timestep_length / 12.
            else:
                yeardur = 1. / 12.
        elif self.md.duration_unit == 'year':
            if self.simulation:
                yeardur = self.timestep_length
            else:
                yeardur = 1.
        if self.simulation:
            cl['duration'] = yeardur
        else:
            cl['duration'] = STEADY_STATE_TIMESTEP
        if self.md.climate_mode == 'constant yearly':
            cl['rain'] = self.md.constant_climate.annual_rainfall
            cl['temp'] = self.md.constant_climate.mean_temperature
            cl['amplitude'] = self.md.constant_climate.variation_amplitude
        elif self.md.climate_mode == 'monthly':
            cl = self._construct_monthly_climate(cl, now.month, yeardur * 12.)
        elif self.md.climate_mode == 'yearly':
            cl = self._construct_yearly_climate(cl, now.month, now.year,yeardur)
        return cl

    def _construct_monthly_climate(self, cl, sm, dur):
        """
        Summarizes the monthly climate data into rain, temp and amplitude
        given the start month and duration

        cl -- climate dictionary
        sm -- start month
        dur -- timestep duration in months
        """
        if dur >= 12:
            months = range(0,12)
        else:
            em = sm + int(dur)
            if em > 12:
                overflow = em - 12
                months = range(sm,12) + range(0,overflow)
            else:
                months = range(sm-1, em-1)
        rain = 0.0
        temp = 0.0
        maxtemp = 0.0
        mintemp = 0.0
        for m in months:
            mtemp = self.md.monthly_climate[m].temperature
            temp += mtemp
            if mtemp < mintemp: mintemp = mtemp
            if mtemp > maxtemp: maxtemp = mtemp
            rain = self.md.monthly_climate[m].rainfall
        cl['rain'] = rain / len(months)
        cl['temp'] = temp / len(months)
        cl['amplitude'] = (maxtemp - mintemp) / 2.0
        return cl

    def _construct_yearly_climate(self, cl, sm, sy, dur):
        """
        Summarizes the yearly climate data into rain, temp and amplitude
        given the start month, start year and duration. Rotates the yearly
        climate definition round if shorter than the simulation length.

        cl -- climate dictionary
        sm -- start month
        sy -- start year
        dur -- timestep duration in years
        """
        weight = 1.0
        firstyearweight = (13. - sm) / 12.
        lastyearweight = 1.0 - firstyearweight
        rain = 0.0
        temp = 0.0
        ampl = 0.0
        years = range(sy, sy + int(dur))
        addyear = True
        # the following handles the case when simulation timeste
        # is in months but climate in years
        if len(years)==0:
            years = [0]
            firstyearweight = 1.0
            if (sm + self.timestep_length)<12:
                addyear = False
        for ind in range(len(years)):
            if self.curr_yr_ind > len(self.md.yearly_climate) - 1:
                self.curr_yr_ind = 0
            cy = self.md.yearly_climate[self.curr_yr_ind]
            if ind == 0:
                weight = firstyearweight
            elif ind == len(years) - 1:
                weight = lastyearweight
            else:
                weight = 1.0
            temp += weight * cy.mean_temperature
            rain += weight * cy.annual_rainfall
            ampl += weight * cy.variation_amplitude
            if addyear:
                self.curr_yr_ind +=1
        # backs one year back, if the last weight was less than 1
        if weight < 1.0 and addyear:
            self.curr_yr_ind -= 1
            if self.curr_yr_ind < 0:
                self.curr_yr_ind = len(self.md.yearly_climate) - 1
        cl['rain'] = rain / len(years)
        cl['temp'] = temp / len(years)
        cl['amplitude'] = ampl / len(years)
        return cl

    def __create_input(self, timestep):
        """
        Sums up the non-woody inital states and inputs into a single
        initial state and input. Matches the woody inital states and
        inputs by size class.
        """
        self.litter = {}
        if timestep == 0:
            self.initial = {}
            if self.initial_mode!='zero':
                self._define_components(self.initial_def, self.initial)
        if self.md.litter_mode == 'constant yearly':
            self._define_components(self.md.constant_litter, self.litter)
        else:
            timeind = self._map_timestep2timeind(timestep)
            if self.md.litter_mode=='monthly':
                infdata = self.md.monthly_litter
            elif self.md.litter_mode=='yearly':
                infdata = self.md.yearly_litter
            self._define_components(infdata, self.litter, tsind=timeind)
        self._fill_input()

    def _define_components(self, fromme, tome, tsind=None):
        """
        Adds the component specification to list to be passed to the model

        fromme -- the component specification from the ui
        tome -- the list on its way to the model
        tsind -- indices if the components are taken from a timeseries
        """
        sizeclasses = defaultdict(list)
        if tsind is None:
            for i in range(len(fromme)):
                sizeclasses[fromme[i].size_class].append(i)
        else:
            for i in tsind:
                sizeclasses[fromme[i].size_class].append(i)
        for sc in sizeclasses:
            m, m_std, a, a_std, w, w_std = (0., 0., 0., 0., 0., 0.)
            e, e_std, n, n_std, h, h_std = (0., 0., 0., 0., 0., 0.)
            for ind in sizeclasses[sc]:
                litter = fromme[ind]
                mass = litter.mass
                m += mass
                a += mass * litter.acid
                w += mass * litter.water
                e += mass * litter.ethanol
                n += mass * litter.non_soluble
                h += mass * litter.humus
                m_std += mass * litter.mass_std
                a_std += mass * litter.acid_std
                w_std += mass * litter.water_std
                e_std += mass * litter.ethanol_std
                n_std += mass * litter.non_soluble_std
                h_std += mass * litter.humus_std
            tome[sc] = [m , m_std / m, a / m, a_std / m, w / m, w_std / m,
                        e / m, e_std / m, n / m, n_std / m, h / m, h_std / m]

    def _draw_from_distr(self, values, pairs, randomize):
        """
        Draw a sample from the normal distribution based on the mean and std
        pairs

        values -- a vector containing mean and standard deviation pairs
        pairs -- how many pairs the vector contains
        randomize -- boolean for really drawing a random sample instead of
                  using the maximum likelihood values
        """
        # sample size one less than pairs specification as pairs contain
        # the total mass and component percentages. These are transformed
        # into component masses
        sample = [None for i in range(len(pairs)-1)]
        for i in range(len(pairs)):
            vs = pairs[i]
            mean = values[2*i]
            std = values[2*i+1]
            if std>0.0 and randomize:
                samplemean = random.gauss(mean, std)
            else:
                samplemean = mean
            if vs[0] == 'mass':
                samplemass = samplemean
                remainingmass = samplemean
            elif vs[0] != 'water':
                compmass = samplemass * samplemean
                sample[vs[1]] = compmass
                remainingmass -= compmass
            elif vs[0] == 'water':
                waterind = i
        sample[pairs[waterind][1]] = remainingmass
        return sample

    def _endstate2initial(self, sizeclass, endstate):
        """
        Transfers the endstate masses to the initial state description of
        masses and percentages with standard deviations. Std set to zero.
        """
        mass = endstate.sum()
        acid = endstate[0] / mass
        water = endstate[1] / mass
        ethanol = endstate[2] / mass
        nonsoluble = endstate[3] / mass
        humus = endstate[4] / mass
        self.initial[sizeclass] = [mass, 0., acid, 0., water, 0., ethanol, 0.,
                                   nonsoluble, 0., humus, 0.]

    def _fill_input(self):
        """
        Makes sure that both the initial state and litter input have the same
        size classes
        """
        for sc in self.initial:
            if sc not in self.litter:
                self.litter[sc] = [0., 0., 0., 0., 0., 0.,
                                   0., 0., 0., 0., 0., 0.]
        for sc in self.litter:
            if sc not in self.initial:
                self.initial[sc] = [0., 0., 0., 0., 0., 0.,
                                    0., 0., 0., 0., 0., 0.]

    def _fill_moment_results(self):
        """
        Fills the result arrays used for storing the calculated moments
         common format: time, mean, mode, var, skewness, kurtosis,
                        95% confidence lower limit, 95% upper limit
        """
        toprocess = [('stock_tom', self.c_stock, 2),
                     ('stock_woody', self.c_stock, 3),
                     ('stock_acid', self.c_stock, 4),
                     ('stock_water', self.c_stock, 5),
                     ('stock_ethanol',  self.c_stock, 6),
                     ('stock_non_soluble', self.c_stock, 7),
                     ('stock_humus', self.c_stock, 8),
                     ('change_tom', self.c_change, 2),
                     ('change_woody', self.c_change, 3),
                     ('change_acid', self.c_change, 4),
                     ('change_water', self.c_change, 5),
                     ('change_ethanol', self.c_change, 6),
                     ('change_non_soluble', self.c_change, 7),
                     ('change_humus', self.c_change, 8),
                     ('co2', self.co2_yield, 2)]
        for (resto, dataarr, dataind) in toprocess:
            # filter time steps
            ts = numpy.unique(dataarr[:,1])
            # extract data for the timestep
            for timestep in ts:
                ind = numpy.where(dataarr[:,1]==timestep)
                mean = stats.mean(dataarr[ind[0], dataind])
                mode = stats.mode(dataarr[ind[0], dataind])
                var = stats.var(dataarr[ind[0], dataind])
                skew = stats.skew(dataarr[ind[0], dataind])
                kurtosis = stats.kurtosis(dataarr[ind[0], dataind])
                if var>0.0:
                    sd2 = 2 * math.sqrt(var)
                else:
                    sd2 = var
                res = [[timestep, mean, mode[0], var, skew, kurtosis,
                       mean - sd2, mean + sd2]]
                if resto=='stock_tom':
                    self.md.stock_tom = numpy.append(self.md.stock_tom,
                                                     res, axis=0)
                elif resto=='stock_woody':
                    self.md.stock_woody = numpy.append(self.md.stock_woody,
                                                       res, axis=0)
                elif resto=='stock_acid':
                    self.md.stock_acid = numpy.append(self.md.stock_acid,
                                                      res, axis=0)
                elif resto=='stock_water':
                    self.md.stock_water = numpy.append(self.md.stock_water,
                                                       res, axis=0)
                elif resto=='stock_ethanol':
                    self.md.stock_ethanol = numpy.append(self.md.stock_ethanol,
                                                         res, axis=0)
                elif resto=='stock_non_soluble':
                    self.md.stock_non_soluble= numpy.append(
                                        self.md.stock_non_soluble, res, axis=0)
                elif resto=='stock_humus':
                    self.md.stock_humus = numpy.append(self.md.stock_humus,
                                                       res, axis=0)
                elif resto=='change_tom':
                    self.md.change_tom = numpy.append(self.md.change_tom,
                                                      res, axis=0)
                elif resto=='change_woody':
                    self.md.change_woody = numpy.append(self.md.change_woody,
                                                        res, axis=0)
                elif resto=='change_acid':
                    self.md.change_acid = numpy.append(self.md.change_acid,
                                                       res, axis=0)
                elif resto=='change_water':
                    self.md.change_water = numpy.append(self.md.change_water,
                                                        res, axis=0)
                elif resto=='change_ethanol':
                    self.md.change_ethanol = numpy.append(
                                            self.md.change_ethanol, res, axis=0)
                elif resto=='change_non_soluble':
                    self.md.change_non_soluble=numpy.append(
                                        self.md.change_non_soluble, res, axis=0)
                elif resto=='change_humus':
                    self.md.change_humus = numpy.append(self.md.change_humus,
                                                        res, axis=0)
                elif resto=='co2':
                    self.md.co2 = numpy.append(self.md.co2, res, axis=0)


    def _get_now(self, timestep):
        """
        Uses a fixed simulation start date for calculating the value date
        for each timestep
        """
        rd = relativedelta
        start = STARTDATE
        try:
            if self.md.duration_unit == 'month':
                now = start + rd(months=timestep*self.timestep_length)
            elif self.md.duration_unit == 'year':
                now = start + rd(years=timestep*self.timestep_length)
        except ValueError:
            now = -1
        return now

    def _map_timestep2timeind(self, timestep):
        """
        Convert the timestep index to the nearest time defined in the litter
        timeseries array

        timestep -- ordinal number of the simulation run timestep
        """
        if not self.simulation:
            # for steady state computation include year 0 or first 12 months
            if self.md.litter_mode=='monthly':
                incl = range(1, 13)
                infall = self.md.monthly_litter
            elif self.md.litter_mode=='yearly':
                incl = [0]
                infall = self.md.yearly_litter
            for ind in range(len(infall)):
                if infall[ind].timestep in incl:
                    self.timemap[timestep].append(ind)
            if timestep not in self.timemap and self.md.litter_mode=='yearly':
                # if no year 0 specification, use the one for year 1
                for ind in range(len(infall)):
                    if infall[ind].timestep==1:
                        self.timemap[timestep].append(ind)
        if self.simulation and timestep not in self.timemap:
            # now for the simulation run
            now = self._get_now(timestep)
            if self.md.duration_unit=='month':
                dur = relativedelta(months=self.timestep_length)
            elif self.md.duration_unit=='year':
                dur = relativedelta(years=self.timestep_length)
            end = now + dur - relativedelta(days=1)
            if self.md.litter_mode=='monthly':
                inputdur = relativedelta(months=1)
                infall = self.md.monthly_litter
            elif self.md.litter_mode=='yearly':
                inputdur = relativedelta(years=1)
                infall = self.md.yearly_litter
            # the first mont/year will have index number 1, hence deduce 1 m/y
            start = STARTDATE - inputdur
            for ind in range(len(infall)):
                relamount = int(infall[ind].timestep)
                if self.md.litter_mode=='monthly':
                    inputdate = start + relativedelta(months=relamount)
                else:
                    inputdate = start + relativedelta(years=relamount)
                if inputdate>=now and inputdate<=end:
                    self.timemap[timestep].append(ind)
        if timestep not in self.timemap:
            self.timemap[timestep] = []
        return self.timemap[timestep]

    def _predict(self, sc, initial, litter, climate):
        """
        Processes the input data before calling the model and then
        runs the model

        sc -- non-woody / size of the woody material modelled
        initial -- system state at the beginning of the timestep
        litter -- litter input for the timestep
        climate -- climate conditions for the timestep
        draw -- should the values be drawn from the distribution or not
        """
        # model parameters
        if self.ml_run:
            # maximum likelihood estimates for the model parameters
            self.f.seek(0, 0)
            packed = self.f.read(4*PARAM_COUNT)
            self.param = struct.unpack(PARAM_F, packed)
        elif self.draw:
            which = random.randint(1, PARAM_SAMPLES - 1)
            pos = which * PARAM_COUNT * 4
            self.f.seek(pos, 0)
            packed = self.f.read(4*PARAM_COUNT)
            self.param = struct.unpack(PARAM_F, packed)
        # and mean values for the initial state and input
        if self.ml_run:
            initial = self._draw_from_distr(initial, VALUESPEC, False)
            self.infall[sc] = self._draw_from_distr(litter, VALUESPEC, False)
        elif self.draw:
            initial = self._draw_from_distr(initial, VALUESPEC, True)
            self.infall[sc] = self._draw_from_distr(litter, VALUESPEC, True)
        else:
            # initial values drawn randomly only for the "draw" run
            # i.e. for the first run after maximum likelihood run
            initial = self._draw_from_distr(initial, VALUESPEC, False)
            if self.md.litter_mode!='constant yearly':
                # if litter input is a timeseries, drawn at each step
                # for constant input the values drawn at the beginning used
                self.infall[sc] = self._draw_from_distr(litter, VALUESPEC,
                                                        True)
        # climate
        na = numpy.array
        f32 = numpy.float32
        par = na(self.param, dtype=f32)
        dur = climate['duration']
        init = na(initial, dtype=f32)
        # convert input to yearly input in all cases
        if not self.simulation or self.md.litter_mode=='constant yearly':
            inf = na(self.infall[sc], dtype=f32)
        else:
            inf = na(self.infall[sc], dtype=f32) / dur
        cl = na([climate['temp'], climate['rain'], climate['amplitude']],
                dtype=f32)
        endstate = y07.yasso.mod5c(par, dur, cl, init, inf, sc)
        self.ts_initial += sum(initial)
        self.ts_infall += sum(self.infall[sc])
        return init, endstate

    def _predict_timestep(self, sample, timestep):
        """
        Loops over all the size classes for the given sample and timestep
        """
        climate = self._construct_climate(timestep)
        if climate==-1:
            timemsg = "Simulation extends too far into the future."\
                      " Couldn't allocate inputs to all timesteps"
            return
        self.ts_initial = 0.0
        self.ts_infall = 0.0
        self.__create_input(timestep)
        for sizeclass in self.initial:
            initial, endstate = self._predict(sizeclass,
                                              self.initial[sizeclass],
                                              self.litter[sizeclass], climate)
            if timestep==0:
                self._add_c_stock_result(sample, timestep, sizeclass, initial)
            self._add_c_stock_result(sample, timestep+1, sizeclass, endstate)
            self._endstate2initial(sizeclass, endstate)
            self.draw = False
        self._calculate_c_change(sample, timestep+1)
        self._calculate_co2_yield(sample, timestep+1)

    def _predict_steady_state(self, sample):
        """
        Makes a single prediction for the steady state for each sizeclass
        """
        climate = self._construct_climate(0)
        self.ts_initial = 0.0
        self.ts_infall = 0.0
        self.__create_input(0)
        for sizeclass in self.initial:
            initial, endstate = self._predict(sizeclass,
                                              self.initial[sizeclass],
                                              self.litter[sizeclass], climate)
            self._add_steady_state_result(sizeclass, endstate)
            self.draw = False

    def _steadystate2initial(self):
        """
        Transfers the endstate masses to the initial state description of
        masses and percentages with standard deviations. Std set to zero.
        """
        self.ss_result = []
        ss = self.steady_state
        sizeclasses = numpy.unique(ss[:,0])
        for sc in sizeclasses:
            criterium = (ss[:,0]==sc)
            target = numpy.where(criterium)[0]
            div = len(target)
            masses = [ss[t, 1:].sum() for t in target]
            mass_sum = sum(masses)
            m = mass_sum / div
            m_std = self._std(masses)
            acids = ss[target, 1] / masses
            a = acids.sum() / div
            a_std = self._std(acids)
            waters = ss[target, 2] / masses
            w = waters.sum() / div
            w_std = self._std(waters)
            ethanols = ss[target, 3] / masses
            e = ethanols.sum() / div
            e_std = self._std(ethanols)
            nonsolubles = ss[target, 4] / masses
            n = nonsolubles.sum() / div
            n_std = self._std(nonsolubles)
            humuses = ss[target, 5] / masses
            h = humuses.sum() / div
            h_std = self._std(humuses)
            self.ss_result.append([m, m_std, a, a_std, w, w_std,
                                   e, e_std, n, n_std, h, h_std, sc])

    def _std(self, data):
        """
        Computes the standard deviation
        """
        var = stats.var(data)
        if var>0.0:
            sd = math.sqrt(var)
        else:
            sd = 0.0
        return sd
