#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 15 14:05:12 2018

@author: cchaudhari

System level Mismatch calculator for PV systems (STC)
"""
#%% import necessary libraries
import os
import sys
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from MismatchLossStudy.Factory_2Diode_Fit import factory_fit
from MismatchLossStudy.mismatch_model import get_nM, get_nS, get_scale, run_model
#%%
tech = 'TEST'
df_flash_data = pd.read_pickle('data/%s.pkl'%(tech))
#%% run various num of strings
df_list = []
mismatch_field = 'mismatch_loss'
# System configurations roughly representing 10kW, 100kW, 1000kW
print('starting the STC study ..')
for nS,nM in zip([3,21,139], [8,14,22]):
    df = run_model(df_flash_data, numMods=nM, numStrings=nS, num_trials= 1000)
    df_list.append(df)
    r = [tech, nS,nM,df[mismatch_field].quantile(0.5),df[mismatch_field].quantile(1- 0.95)]
    print(r)
#%% pickle results
d = pd.concat(df_list)
d.to_pickle('data/model_run_%s.pkl'%(tech))