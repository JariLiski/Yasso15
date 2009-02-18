#!/usr/bin/env python
# -*- coding: utf-8 -*-

DISTDIR = 'yasso-0.1a2'
import shutil
from bbfreeze import Freezer

f = Freezer(DISTDIR)
f.addScript("../yasso.py", gui_only=False)
f.include_py = True
f()    # starts the freezing process
# copy the neeeded data files to the distribution dir
shutil.copy('../yasso_param.txt', DISTDIR+'/')
shutil.copy('../demo_input.txt', DISTDIR+'/')
