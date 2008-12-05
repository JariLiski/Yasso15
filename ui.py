#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from enthought.traits.api import *
from enthought.traits.ui.api import *
from enthought.traits.ui.menu import *

from yassodata import *

class YassoUI(HasTraits):

    view = View(Tabbed(VGroup(Item('initial_state.mode'),
                              Item('initial_state.litter')),
                       VGroup(Item('litter_input.mode'),
                              Item('litter_input.constant'),
                              Item('litter_input.timeseries')),
                       VGroup(Item('climate.mode'),
                              Item('climate.constant'),
                              Item('climate.montly'),
                              Item('climate.yearly')),
                       VGroup(Item('model_run.sample_size'),
                              Item('model_run.duration_unit'),
                              Item('model_run.timestep'),
                              Item('model_run.simulation_length')),
                       id = 'dock_window'
                      ),
                title     = 'Yasso 07',
                id        = 'simosol.yasso07',
                dock      = 'horizontal',
                resizable = True,
                width     = 0.5,
                height    = 0.5,
                buttons   = NoButtons
                )

if __name__ == '__main__':
    initial_state = InitialState()
    litter_input = LitterInput()
    climate = Climate()
    model_run = ModelRun()
    YassoUI().configure_traits(context={'initial_state':initial_state,
                                        'litter_input':litter_input,
                                        'climate':climate,
                                        'model_run':model_run})
