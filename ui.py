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

class YassoController(Controller):
    """
    Controller and the default View for the Yasso07 program3
    """

                            #enabled_when='litter_mode=="constant"',
                            #enabled_when='litter_mode=="timeseries"',
    view = View(VGroup(HGroup(Item(name='initial_mode', style='custom'),
                              spring),
                       Item('initial_litter',
                            enabled_when='initial_mode=="non zero"'),
                       label='Initial condition'
                      ),
                VGroup(HGroup(Item('litter_mode', style='custom'), spring),
                       Item('constant_litter',
                            visible_when='litter_mode=="constant"',
                            show_label=False
                            ),
                       Item('timeseries_litter',
                            visible_when='litter_mode=="timeseries"',
                            show_label=False
                            ),
                       label='Litter input'
                      ),
                VGroup(HGroup(Item('climate_mode', style='custom'), spring),
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
                VGroup(HGroup(Item('sample_size'),spring),
                       HGroup(Item('duration_unit', style='custom'),spring),
                       HGroup(Item('timestep'), spring),
                       HGroup(Item('simulation_length'), spring),
                       HGroup(Item('modelrun_event', show_label=False),
                                   spring),
                       label='Model run',
                      ),
                title     = 'Yasso 07',
                id        = 'simosol.yasso07',
                dock      = 'horizontal',
                resizable = True,
                buttons   = NoButtons
                )

    predictor = None
    timemap = defaultdict(list)

    def controller_modelrun_event_fired(self):
        print 'running model'
        timesteps = self.__calculate_timesteps()
        for j in range(model.sample_size):
            self.ml_run = True
            self.draw = True
            for k in range(timesteps):
                climate = self.__construct_climate(k)
                self.ts_initial = 0.0
                self.ts_infall = 0.0
                self.__create_input(k)
                for sizeclass in self.initial:
                    self.__predict(sizeclass, self.initial[sizeclass],
                                   self.litter[sizeclass], climate)
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
        cs = model.c_stock
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
        cc = model.c_change
        cs = model.c_stock
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
        cs = model.c_stock
        cy = model.co2_yield
        stepinf = numpy.array([[s, ts, 0.]], dtype=numpy.float32)
        cy = numpy.append(cc, stepinf, axis=0)
        # total organic matter at index 3
        atend = cs[s, ts, 3]
        cc[-1, 2] = self.ts_initial + self.ts_infall - atend

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
            if model.duration_unit == 'month' and \
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

    def __predict(self, sizeclass, initial, litter, climate):
        if self.predictor is None:
            self.predictor = ModelRunner(model.timestep)
        init, infall, endstate = self.predictor.predict(sizeclass, initial,
                                        litter, climate, self.ml_run, self.draw,
                                        model.litter_mode)
        self.ts_initial += sum(init)
        self.ts_infall += sum(infall)
        self.__add_c_stock_result(j, k, endstate)

yasso = YassoController(model=YassoModel())

if __name__ == '__main__':
    yasso.configure_traits()
