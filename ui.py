#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from enthought.traits.api import *
from enthought.traits.ui.api import *
from enthought.traits.ui.menu import *

from collections import defaultdict
from datetime import date
from dateutil.relativedelta import relativedelta

from yassodata import YassoModel
from modelcall import ModelRunner
import y6c

class YassoController(Controller):
    """
    Controller and the default View for the Yasso07 program
    """

    view = View(VGroup(Item(name='initial_mode', style='custom'),
                       Item('initial_litter',
                            enabled_when='initial_mode=="non zero"'),
                       label='Initial condition'
                      ),
                VGroup(Item('litter_mode', style='custom'),
                       Item('constant_litter',
                            enabled_when='litter_mode=="constant"'),
                       Item('timeseries_litter',
                            enabled_when='litter_mode=="timeseries"'),
                       label='Litter input'
                      ),
                VGroup(Item('climate_mode', style='custom'),
                       Group(Item('object.constant_climate.annual_rainfall'),
                             Item('object.constant_climate.mean_temperature'),
                             Item('object.constant_climate.variation_amplitude'),
                             label='Constant climate',
                             show_border=True,
                             enabled_when='climate_mode=="constant"'),
                       Item('monthly_climate',
                            enabled_when='climate_mode=="monthly"'),
                       Item('yearly_climate',
                            enabled_when='climate_mode=="yearly"'),
                       label='Climate'
                      ),
                VGroup(Item('sample_size'),
                       Item('duration_unit', style='custom'),
                       Item('timestep'),
                       Item('simulation_length'),
                       label='Model run'
                      ),
                title     = 'Yasso 07',
                id        = 'simosol.yasso07',
                dock      = 'horizontal',
                resizable = True,
                buttons   = NoButtons
                )

    def __init__(self):
        self.predictor = None
        self.timemap = defaultdict(list)
        self.c_stock = numpy.empty(shape=(0,8), dtype=float)
        self.c_change = numpy.empty(shape=(0,8), dtype=float)
        self.co2_yield = numpy.empty(shape=(0,3), dtype=float)

    def __add_c_stock_result(self, sample, timestep, woody, nonwoody):
        """
        Adds model result to the C stock

        res -- model results augmented with timestep and iteration data
        """
        cs = model.c_stock
        res = numpy.concatenate(([float(sample), float(timestep), woody],
                                 nonwoody))
        res.shape = (1, 8)
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
        cc = self.c_change
        stepinf = numpy.array([[s, ts, 0., 0., 0., 0., 0., 0.]], dtype=float)
        cc = numpy.append(cc, stepinf, axis=0)
        cc[-1, 2:] = cs[s, ts, :] - self.c_ts_initial

    def __calculate_co2_yield(self, s, ts):
        """
        The yield of CO2 during the timestep

        s -- sample ordinal
        ts -- timestep ordinal
        """
        cs = self.c_stock
        cy = self.co2_yield
        stepinf = numpy.array([[s, ts, 0.]], dtype=float)
        cy = numpy.append(cc, stepinf, axis=0)
        ini = sum(self.c_ts_initial)
        infall = sum(self.c_ts_infall)
        atend = sum(cs[s, ts, :])
        cc[-1, 2] = ini + infall - atend

    def __calculate_timesteps(self):
        return int(math.ceil(model.simulation_length / model.timestep))

    def __construct_climate(self, timestep):
        """
        From the different ui options, creates a unified climate description
        (type, start month, duration, temperature, rainfall, amplitude)
        """
        cl = {}
        now = self.__get_now(timestep).month
        cl['start month'] = now.month
        if model.duration_unit == 'month':
            dur = model.timestep / 12.
        elif model.duration_unit == 'year':
            dur = model.timestep
        cl['duration'] = dur
        if model.climate_mode == 'constant':
            cl['rain'] = model.constant_climate.annual_rainfall
            cl['temp'] = model.constant_climate.mean_temperature
            cl['amplitude'] = month.constant_climate.variation_amplitude
        elif model.climate_mode == 'monthly':
            cl = self.__construct_monthly_climate(cl, now.month, dur / 12.)
        elif model.climate_mode == 'yearly':
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
            mtemp = model.monthly_climate[m].temperature
            temp += mtemp
            if mtemp < mintemp: mintemp = mtemp
            if mtepm > maxtemp: maxtemp = mtemp
            rain = model.monthly_climate[m].rainfall
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
            for cy in model.yearly_climate:
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
            if model.initial_mode == 'non zero':
                self.__define_components(model.initial_litter, self.initial)
        if model.litter_mode == 'constant':
            self.__define_components(model.constant_litter, self.litter)
        else:
            timeind = self.__map_timestep2timeind(timestep)
            self.__define_components(model.timeseries_litter, self.litter,
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
            if model.duration_unit == 'month' and
               self.litter_input_resolution == 'year':
                   div = model.timestep/12.
            else:
                div = 1.
            tome[sc] = [m / div, m_std, a / div, a_std, w / div, w_std,
                        e / div, e_std, n / div, n_std, h / div, h_std]

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
        s = model.start_month.split('/')
        start = date(int(s[1]), int(s[0]), 1)
        if model.duration_unit == 'month':
            now = start + relativedelta(months=timestep)
        elif model.duration_unit == 'year':
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
            for i in range(len(model.timeseries_litter)):
                ltime = model.timeseries_litter[i].time.split('/')
                if len(ltime) == 1:
                    lmonth = None
                    lyear = int(ltime[0])
                    self.litter_input_resolution = 'year'
                else:
                    lmonth = int(ltime[0])
                    lyear = int(ltime[1])
                    self.litter_input_resolution = 'month'
                if model.duration_unit == 'month' and now.year == lyear:
                    if lmonth is not None:
                        if now.month == lmonth:
                            self.timemap[timestep].append(i)
                    else:
                        self.litter_input_resolution = 'year'
                        self.timemap[timestep].append(i)
                elif model.duration_unit == 'year' and now.year == lyear:
                    self.timemap[timestep].append(i)
        return self.timemap[timestep]

    def __predict(self, initial, litter, climate):
        if self.predictor is None:
            self.predictor = ModelRunner(model.timestep)
        init, infall, endstate = self.predictor.predict(initial, litter,
                                                        climate, self.ml_run)
        woody = endstate[0]
        nonwoody = endstate[1:]
        sizeclass = infall[-1]
        infall = infall[:-1]
        if sizeclass > 0.0:
            # for woody components, the different chemical components in
            # inital state and infall are just added together
            self.c_ts_initial[0] += sum(init)
            self.c_ts_infall[0] += sum(infall)
        else:
            # for non woody components the chemical component masses are
            # stored separately
            self.c_ts_initial[1:] = numpy.add(self.c_ts_initial[1:], init)
            self.c_ts_infall[1:] = numpy.add(self.c_ts_infall[1:], infall)
        return woody, nonwoody

    def __process_next_nw_init(self, mode, nonwoody=None):
        if mode == 'init':
            self.next_nw_init = numpy.array([0., 0., 0., 0., 0.], dtype=float)
        elif mode == 'add':
            self.next_nw_init += nonwoody
        elif mode == 'copy2initial':
            nonwoody = self.next_nw_init
            totmass = sum(nonwoody)
            self.initial[0.0] = [totmass, 0.,
                                 nonwoody[0] / totmass, 0.,
                                 nonwoody[1] / totmass, 0.,
                                 nonwoody[2] / totmass, 0.,
                                 nonwoody[3] / totmass, 0.,
                                 nonwoody[4] / totmass, 0.]

    def run_model(self):
        timesteps = self.__calculate_timesteps()
        for j in range(model.sample_size):
            self.ml_run = True
            for k in range(timesteps):
                self.c_ts_initial = numpy.zeros(6)
                self.c_ts_infall = numpy.zeros(6)
                self.__create_input(k)
                self.__process_next_nonwoody_init('init', k)
                for sizeclass in self.initial:
                    climate = self.__construct_climate(k)
                    woody, nonwoody = self.__predict(self.initial[sizeclass],
                                                self.litter[sizeclass], climate)
                    if sizeclass > 0.0:
                        # woody output as the initial state woody mass for the
                        # next timestep for this size class
                        self.initial[sizeclass][0] = woody
                    self.__process_nonwoody_initial('add', nonwoody)
                    self.__add_c_stock_result(j, k, woody, nonwoody)
                    self.ml_run = False
                self.__process_next_nonwoody_init('copy2initial')
                self.__calculate_c_change(j, k)
                self.__calculate_co2_yield(j, k)

yasso = YassoController(model=YassoModel())

if __name__ == '__main__':
    yasso.configure_traits()
