#!/usr/bin/env python
# -*- coding: utf-8 -*-

import y07
import numpy
import math
from datetime import date
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import random
from scipy.stats import stats
from enthought.pyface.api import ProgressDialog

PARAMFILE = 'yasso_param.txt'
# the order in which data comes in (defined by list index) and in which
# it should passed to the model (defined in the tuple)
VALUESPEC = [('mass', None), ('acid', 0), ('water', 1), ('ethanol', 2),
             ('non_soluble', 3), ('humus', 4)]
STARTDATE = date(2000, 1, 1)

class ModelRunner(object):
    """
    This class is responsible for calling the actual Yasso07 modeldata.
    It converts the data in the UI into the form that can be passed
    to the model
    """

    def __init__(self):
        """
        Constructor.
        """
        f = open(PARAMFILE)
        first = [float(val) for val in f.readline().split()]
        parr = numpy.array([first])
        parr.shape = (1, len(first))
        #for line in f:
        #    data = [float(val) for val in line.split()]
        #    parr = numpy.append(parr, [data], axis=0)
        self._model_param = parr
        f.close()

    def run_model(self, modeldata):
        self.md = modeldata
        self.timemap = defaultdict(list)
        samplesize = self.md.sample_size
        msg = "Simulating %d samples for %d timesteps" % (samplesize,
                                                    self.md.simulation_length)
        progress = ProgressDialog(title="Simulation",
                                  message=msg,
                                  max=samplesize, show_time=True,
                                  can_cancel=True)
        progress.open()
        timesteps = self._calculate_timesteps()
        self.curr_yr_ind = 0
        for j in range(samplesize):
            (cont, skip) = progress.update(j)
            if not cont or skip:
                break
            self.ml_run = True
            self.draw = True
            for k in range(timesteps):
                climate = self._construct_climate(k)
                self.ts_initial = 0.0
                self.ts_infall = 0.0
                self.__create_input(k)
                for sizeclass in self.initial:
                    endstate = self._predict(sizeclass,
                                              self.initial[sizeclass],
                                              self.litter[sizeclass],
                                              climate)
                    self._add_c_stock_result(j, k, sizeclass, endstate)
                    self._endstate2initial(sizeclass, endstate)
                if not self.ml_run:
                    # first run is the maximum likelihood run, on the next
                    # we draw the random sample, and on the next runs use it
                    self.draw = False
                self._calculate_c_change(j, k)
                self._calculate_co2_yield(j, k)
            self.ml_run = False
        self._fill_moment_results()
        progress.update(samplesize)

    def _add_c_stock_result(self, sample, timestep, sc, endstate):
        """
        Adds model result to the C stock

        res -- model results augmented with timestep, iteration and
               sizeclass data
        """
        cs = self.md.c_stock
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
            self.md.c_stock = numpy.append(cs, res, axis=0)
        else:
            # if there are, add the new results to the existing ones
            self.md.c_stock[target[0],2:] = numpy.add(cs[target[0],2:], res[0,2:])

    def _calculate_c_change(self, s, ts):
        """
        The change of mass per component during the timestep

        s -- sample ordinal
        ts -- timestep ordinal
        """
        cc = self.md.c_change
        cs = self.md.c_stock
        criterium = (cs[:,0]==s) & (cs[:,1]==ts)
        nowtarget = numpy.where(criterium)[0]
        criterium = (cs[:,0]==s) & (cs[:,1]==ts-1)
        prevtarget = numpy.where(criterium)[0]
        if len(nowtarget) > 0 and len(prevtarget)>0:
            stepinf = numpy.array([[s, ts, 0., 0., 0., 0., 0., 0., 0.]],
                                  dtype=numpy.float32)
            self.md.c_change = numpy.append(cc, stepinf, axis=0)
            self.md.c_change[-1, 2:] = cs[nowtarget, 2:] - cs[prevtarget, 2:]

    def _calculate_co2_yield(self, s, ts):
        """
        The yield of CO2 during the timestep

        s -- sample ordinal
        ts -- timestep ordinal
        """
        cs = self.md.c_stock
        cy = self.md.co2_yield
        stepinf = numpy.array([[s, ts, 0.]], dtype=numpy.float32)
        self.md.co2_yield = numpy.append(cy, stepinf, axis=0)
        # total organic matter at index 3
        criterium = (cs[:,0]==s) & (cs[:,1]==ts)
        rowind = numpy.where(criterium)[0]
        atend = cs[rowind[0], 3]
        self.md.co2_yield[-1, 2] = self.ts_initial + self.ts_infall - atend

    def _calculate_timesteps(self):
        sl = self.md.simulation_length
        tl = self.md.timestep_length
        return int(math.ceil(sl/tl))

    def _construct_climate(self, timestep):
        """
        From the different ui options, creates a unified climate description
        (type, start month, duration, temperature, rainfall, amplitude)
        """
        cl = {}
        now = self._get_now(timestep)
        cl['start month'] = now.month
        if self.md.duration_unit == 'month':
            yeardur = self.md.timestep_length / 12.
        elif self.md.duration_unit == 'year':
            yeardur = self.md.timestep_length
        cl['duration'] = yeardur
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
            self.curr_yr_ind +=1
        # backs one year back, if the last weight was less than 1
        if weight < 1.0:
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
            if self.md.initial_mode == 'non zero':
                self._define_components(self.md.initial_litter, self.initial)
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
            a = a / m
            w = w / m
            e = e / m
            n = n / m
            h = h / m
            a_std = a_std / m
            w_std = w_std / m
            e_std = e_std / m
            n_std = n_std / m
            h_std = h_std / m
            if self.md.duration_unit == 'month' and \
               self.md.litter_mode == 'yearly':
                div = self.md.timestep_length / 12.
            else:
                div = 1.
            tome[sc] = [m / div, m_std, a / div, a_std, w / div, w_std,
                        e / div, e_std, n / div, n_std, h / div, h_std]

    def _draw_from_distr(self, values, pairs, ml):
        """
        Draw a sample from the normal distribution based on the mean and std
        pairs

        values -- a vector containing mean and standard deviation pairs
        pairs -- how many pairs the vector contains
        ml -- boolean for using the maximum likelihood values
        """
        # sample size one less than pairs specification as pairs contain
        # the total mass and component percentages. These are transformed
        # into component masses
        sample = [None for i in range(len(pairs)-1)]
        for i in range(len(pairs)):
            vs = pairs[i]
            mean = values[2*i]
            std = values[2*i+1]
            if std > 0.0 and not ml:
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
        md = self.md
        toprocess = [('stock_tom', md.c_stock, 2),
                     ('stock_woody', md.c_stock, 3),
                     ('stock_acid', md.c_stock, 4),
                     ('stock_water', md.c_stock, 5),
                     ('stock_ethanol',  md.c_stock, 6),
                     ('stock_non_soluble', md.c_stock, 7),
                     ('stock_humus', md.c_stock, 8),
                     ('change_tom', md.c_change, 2),
                     ('change_woody', md.c_change, 3),
                     ('change_acid', md.c_change, 4),
                     ('change_water', md.c_change, 5),
                     ('change_ethanol', md.c_change, 6),
                     ('change_non_soluble', md.c_change, 7),
                     ('change_humus', md.c_change, 8),
                     ('co2', md.co2_yield, 2)]
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
                sd2 = 2 * math.sqrt(var)
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
        Uses a fixed simulation start date for calculating the month
        for each timestep
        """
        rd = relativedelta
        start = STARTDATE
        if self.md.duration_unit == 'month':
            now = start + rd(months=timestep*self.md.timestep_length)
        elif self.md.duration_unit == 'year':
            now = start + rd(years=timestep*self.md.timestep_length)
        return now

    def _map_timestep2timeind(self, timestep):
        """
        Convert the timestep index to the nearest time defined in the litter
        timeseries array

        timestep -- ordinal number of the simulation run timestep
        """
        if timestep not in self.timemap:
            now = self._get_now(timestep)
            if self.md.duration_unit=='month':
                dur = relativedelta(months=self.md.timestep_length)
            elif self.md.duration_unit=='year':
                dur = relativedelta(years=self.md.timestep_length)
            end = now + dur - relativedelta(days=1)
            if self.md.litter_mode=='monthly':
                inputdur = relativedelta(months=1)
                inputdate = STARTDATE
                for ind in range(len(self.md.monthly_litter)):
                    if inputdate>=now and inputdate<=end:
                        self.timemap[timestep].append(ind)
                    inputdate += inputdur
            elif self.md.litter_mode=='yearly':
                inputdur = relativedelta(years=1)
                inputdate = STARTDATE
                for ind in range(len(self.md.yearly_litter)):
                    if inputdate>=now and inputdate<=end:
                        self.timemap[timestep].append(ind)
                    inputdate += inputdur
        if timestep not in self.timemap:
            self.timemap[timestep] = []
        return self.timemap[timestep]

    def _predict(self, sc, initial, litter, climate):
        """
        processes the input data before calling the model and then
        runs the model
        sc -- non-woody / size of the woody material modelled
        initial -- system state at the beginning of the timestep
        litter -- litter input for the timestep
        climate -- climate conditions for the timestep
        draw -- should the values be drawn from the distribution or not
        """
        # model parameters
        if self.ml_run:
            self.infall = {}
            # maximum likelihood estimates for the model parameters
            self.param = self._model_param[0,:]
        elif self.draw:
            pind = random.randint(0, self._model_param.shape[0]-1)
            self.param = self._model_param[pind,:]
        # and mean values for the initial state and input
        if self.ml_run:
            initial = self._draw_from_distr(initial, VALUESPEC, True)
            self.infall[sc] = self._draw_from_distr(litter, VALUESPEC, True)
        elif self.draw:
            initial = self._draw_from_distr(initial, VALUESPEC, False)
            self.infall[sc] = self._draw_from_distr(litter, VALUESPEC, False)
        else:
            # initial values drawn randomly only for the "draw" run
            # i.e. for the first run after maximum likelihood run
            initial = self._draw_from_distr(initial, VALUESPEC, True)
            if self.md.litter_mode!='constant yearly':
                # if litter input is a timeseries, drawn at each step
                # for constant input the values drawn at the beginning used
                self.infall[sc] = self._draw_from_distr(litter, VALUESPEC,
                                                         False)
        # climate
        na = numpy.array
        f32 = numpy.float64
        par = na(self.param, dtype=f32)
        dur = climate['duration']
        init = na(initial, dtype=f32)
        # convert input to yearly input in all cases
        if self.md.litter_mode=='constant yearly':
            inf = na(self.infall[sc], dtype=f32)
        else:
            inf = na(self.infall[sc], dtype=f32) / dur
        cl = na([climate['temp'], climate['rain'], climate['amplitude']],
                dtype=f32)
        endstate = y07.yasso.mod5c(par, dur, cl, init, inf, sc)
        print "*****************"
        print "par:", par
        print "dur:", dur
        print "cl:", cl
        print "init:", init
        print "inf, sc:", inf, sc
        print "result:", endstate
        self.ts_initial += sum(initial)
        self.ts_infall += sum(self.infall[sc])
        return endstate

