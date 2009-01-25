#!/usr/bin/env python
# -*- coding: utf-8 -*-

from numpy import array, float32
from datetime import date
import random
from y07 import yasso

PARAMFILE = 'mc5_y07_a01.data'
# the order in which data comes in (defined by list index) and in which
# it should passed to the model (defined in the tuple)
VALUESPEC = [('mass', None), ('acid', 0), ('water', 1), ('ethanol', 2),
             ('non_soluble', 3), ('humus', 4)]

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
        for line in f:
            data = [float(val) for val in line]
            parr = numpy.append(parr, [data])
        self._model_param = parr
        f.close()

    def run_model(self, modeldata):
        timesteps = self.__calculate_timesteps()
        for j in range(modeldata.sample_size):
            self.ml_run = True
            self.draw = True
            for k in range(timesteps):
                climate = self.__construct_climate(k)
                self.ts_initial = 0.0
                self.ts_infall = 0.0
                self.__create_input(k)
                for sizeclass in self.initial:
                    endstate = self.__predict(sizeclass,
                                              self.initial[sizeclass],
                                              self.litter[sizeclass],
                                              climate)
                self.__add_c_stock_result(j, k, endstate)
                if not self.ml_run:
                    # first run is the maximum likelihood run, on the next
                    # we draw the random sample, and on the next runs use it
                    self.draw = False
                self.ml_run = False
                self.__calculate_c_change(j, k)
                self.__calculate_co2_yield(j, k)

    def __add_c_stock_result(self, sample, timestep, sc, endstate):
        """
        Adds model result to the C stock

        res -- model results augmented with timestep, iteration and
               sizeclass data
        """
        cs = modeldata.c_stock
        # if sizeclass is non-zero, all the components are added together
        # to get the mass of wood
        if sc > 0:
            totalom, woody = sum(endstate)
        else:
            totalom = sum(endstate)
            woody = 0.0
        res = numpy.concatenate(([float(sample), float(timestep), totalom,
                                  woody], endstate))
        res.shape = (1, 9)
        # find out whether there are already results for this timestep and
        # iteration
        criterium = (cs[:,0]==res[0,0]) & (cs[:,1]==res[0,1])
        target = numpy.where(criterium)[0]
        if len(target) == 0:
            cs = numpy.append(cs, res, axis=0)
        else:
            # if there are, add the new results to the existing ones
            cs[target[0],2:] = numpy.add(cs[target[0],2:], res[0,2:])

    def __calculate_c_change(self, s, ts):
        """
        The change of mass per component during the timestep

        s -- sample ordinal
        ts -- timestep ordinal
        """
        cc = modeldata.c_change
        cs = modeldata.c_stock
        criterium = (cs[:,0]==s) & (cs[:,1]==ts)
        nowtarget = numpy.where(criterium)[0]
        criterium = (cs[:,0]==s) & (cs[:,1]==ts-1)
        prevtarget = numpy.where(criterium)[0]
        if len(target) > 0:
            stepinf = numpy.array([[s, ts, 0., 0., 0., 0., 0., 0., 0.]],
                                  dtype=numpy.float32)
            cc = numpy.append(cc, stepinf, axis=0)
            cc[-1, 2:] = cs[nowtarget, 2:] - cs[prevtarget, 2:]

    def __calculate_co2_yield(self, s, ts):
        """
        The yield of CO2 during the timestep

        s -- sample ordinal
        ts -- timestep ordinal
        """
        cs = modeldata.c_stock
        cy = modeldata.co2_yield
        stepinf = numpy.array([[s, ts, 0.]], dtype=numpy.float32)
        cy = numpy.append(cc, stepinf, axis=0)
        # total organic matter at index 3
        atend = cs[s, ts, 3]
        cc[-1, 2] = self.ts_initial + self.ts_infall - atend

    def __calculate_timesteps(self):
        return int(math.ceil(modeldata.simulation_length / modeldata.timestep))

    def __construct_climate(self, timestep):
        """
        From the different ui options, creates a unified climate description
        (type, start month, duration, temperature, rainfall, amplitude)
        """
        cl = {}
        now = self.__get_now(timestep).month
        cl['start month'] = now.month
        if modeldata.duration_unit == 'month':
            dur = modeldata.timestep / 12.
        elif modeldata.duration_unit == 'year':
            dur = modeldata.timestep
        cl['duration'] = dur
        if modeldata.climate_mode == 'constant':
            cl['rain'] = modeldata.constant_climate.annual_rainfall
            cl['temp'] = modeldata.constant_climate.mean_temperature
            cl['amplitude'] = month.constant_climate.variation_amplitude
        elif modeldata.climate_mode == 'monthly':
            cl = self.__construct_monthly_climate(cl, now.month, dur / 12.)
        elif modeldata.climate_mode == 'yearly':
            cl = self.__construct_yearly_climate(cl, now.month, now.year, dur)
        return cl

    def __construct_monthly_climate(self, cl, sm, dur):
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
            em = sm + int(dur * 12)
            if em > 12:
                overflow = em - 12
                months = range(sm,12) + range(0,overflow)
            else:
                months = range(sm-1, em-1)
        rain = 0.0
        temp = 0.0
        maxtemp, mintemp = 0.0
        for m in months:
            mtemp = modeldata.monthly_climate[m].temperature
            temp += mtemp
            if mtemp < mintemp: mintemp = mtemp
            if mtepm > maxtemp: maxtemp = mtemp
            rain = modeldata.monthly_climate[m].rainfall
        cl['rain'] = rain / len(months)
        cl['temp'] = temp / len(months)
        cl['amplitude'] = (maxtemp - mintemp) / 2.0
        return cl

    def __construct_yearly_climate(self, cl, sm, sy, dur):
        """
        Summarizes the yearly climate data into rain, temp and amplitude
        given the start month, start year and duration

        cl -- climate dictionary
        sm -- start month
        sy -- start year
        dur -- timestep duration in years
        """
        firstyearweight = (13. - sm) / 12.
        lastyearweight = 1.0 - firstyearweight
        rain = 0.0
        temp = 0.0
        ampl = 0.0
        years = range(sy, sy + int(dur))
        for ind in range(len(years)):
            for cy in modeldata.yearly_climate:
                if cy.year == years[ind]:
                    if ind == 0:
                        weight = firstyearweight
                    elif ind == len(years) - 1:
                        weight = lastyearweight
                    else:
                        weight = 1.0
                    temp += weight * cy.mean_temperature
                    rain += weight * cy.annual_rainfall
                    ampl += weight * cy.variation_amplitude
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
        if timestep == 0:
            if modeldata.initial_mode == 'non zero':
                self.__define_components(modeldata.initial_litter, self.initial)
        if modeldata.litter_mode == 'constant':
            self.__define_components(modeldata.constant_litter, self.litter)
        else:
            timeind = self.__map_timestep2timeind(timestep)
            self.__define_components(modeldata.timeseries_litter, self.litter,
                                     ind=timeind)
        self.__fill_input()

    def __define_components(self, fromme, tome, ind=None):
        """
        Adds the component specification to list to be passed to the model

        fromme -- the component specification from the ui
        tome -- the list on its way to the model
        ind -- indices if the components are taken from a timeseries
        """
        tome = {}
        sizeclasses = defaultdict(list)
        if ind is None:
            for i in range(len(fromme)):
                sizeclasses[fromme[i].size_class].append(i)
        else:
            for i in ind:
                sizeclasses[fromme[i].litter.sizeclass].append(i)
        for sc in sizeclasses:
            m, m_std, a, a_std, w, w_std = (0., 0., 0., 0., 0., 0.)
            e, e_std, n, w_std, h, h_std = (0., 0., 0., 0., 0., 0.)
            for ind in sizeclasses[sc]:
                if ind is None:
                    litter = fromme[ind]
                else:
                    litter = fromme[ind].litter
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
            if modeldata.duration_unit == 'month' and \
               self.litter_input_resolution == 'year':
                   div = modeldata.timestep/12.
            else:
                div = 1.
            tome[sc] = [m / div, m_std, a / div, a_std, w / div, w_std,
                        e / div, e_std, n / div, n_std, h / div, h_std]

    def __draw_from_distr(self, values, pairs, ml):
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
            mean = values[i]
            std = values[i+1]
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

    def __fill_input(self):
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

    def __get_now(self, timestep):
        s = modeldata.start_month.split('/')
        start = date(int(s[1]), int(s[0]), 1)
        if modeldata.duration_unit == 'month':
            now = start + relativedelta(months=timestep)
        elif modeldata.duration_unit == 'year':
            now = start + relativedelta(years=timestep)
        return now

    def __map_timestep2timeind(self, timestep):
        """
        Convert the timestep index to the nearest time defined in the litter
        timeseries array

        timestep -- ordinal number of the simulation run timestep
        """
        if timestep not in self.timemap:
            now = self.__get_now(timestep)
            for i in range(len(modeldata.timeseries_litter)):
                ltime = modeldata.timeseries_litter[i].time.split('/')
                if len(ltime) == 1:
                    lmonth = None
                    lyear = int(ltime[0])
                    self.litter_input_resolution = 'year'
                else:
                    lmonth = int(ltime[0])
                    lyear = int(ltime[1])
                    self.litter_input_resolution = 'month'
                if modeldata.duration_unit == 'month' and now.year == lyear:
                    if lmonth is not None:
                        if now.month == lmonth:
                            self.timemap[timestep].append(i)
                    else:
                        self.litter_input_resolution = 'year'
                        self.timemap[timestep].append(i)
                elif modeldata.duration_unit == 'year' and now.year == lyear:
                    self.timemap[timestep].append(i)
        return self.timemap[timestep]

    def __predict(self, sc, initial, litter, climate):
        """
        processes the input data before calling the model and then
        runs the model
        sc -- non-woody / size of the woody material modelled
        initial -- system state at the beginning of the timestep
        litter -- litter input for the timestep
        climate -- climate conditions for the timestep
        firstrun -- first invocation of the model
        mlrun -- run the model using maximum likelihood estimates
        draw -- should the values be drawn from the distribution or not
        ltype -- litter input type: 'constant' or 'timeseries'
        """
        # model parameters
        if self.mlrun:
            self.infall = {}
            # maximum likelihood estimates for the model parameters
            self.param = self._model_param[0,:]
        elif self.draw:
            pind = random.randint(0, self._model_param.shape[0]-1)
            self.param = self._model_param[pind,:]
        # and mean values for the initial state and input
        if self.mlrun:
            initial = self.__draw_from_distr(initial, VALUESPEC, True)
            self.infall[sc] = self.__draw_from_distr(litter, VALUESPEC, True)
        elif self.draw:
            initial = self.__draw_from_distr(initial, VALUESPEC, False)
            self.infall[sc] = self.__draw_from_distr(litter, VALUESPEC, False)
        else:
            # initial values drawn randomly only for the "draw" run
            # i.e. for the first run after maximum likelihood run
            init = self.__draw_from_distr(initial, VALUESPEC, True)
            if modeldata.litter_model == 'timeseries':
                # if litter input is a timeseries, drawn at each step
                # for constant input the values drawn at the beginning used
                self.infall[sc] = self.__draw_from_distr(litter, VALUESPEC,
                                                         False)
        # climate
        cl = [climate['temp'], climate['rain'], climate['amplitude']]
        endstate = yasso.mod5c(self.param, self.timestep, initial,
                               self.infall[sc], cl, sc)
        self.ts_initial += sum(initial)
        self.ts_infall += sum(self.infall[sc])
        return endstate

