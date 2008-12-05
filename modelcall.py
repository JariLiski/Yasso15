#!/usr/bin/env python
# -*- coding: utf-8 -*-


    # model input data structures
    a_parameters = Array(dtype=float, shape=(44,))
    t_timestep = Range(low=1.0/12.0)
    cl_climate = Array(dtype=float, shape=(3,))
    k_woody_ind = Enum([1,2]) # 1 = non woody, 2 = woody
    init_condition = Array(dtype=float, shape=(6,))
    inf_input = Array(dtype=float, shape=(6,))
    cc_composition = Array(dtype=float, shape=(6,))
    # model output data structure
    model_result = Array(dtype=float, shape=(6,))
