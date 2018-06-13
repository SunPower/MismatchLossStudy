#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 15 14:05:12 2018

@author: cchaudhari

Annual Energy Mismatch Loss calculator
"""
import sys
import os
PID = os.getpid()
import random
#random.seed(PID)
from pvmismatch import PVcell, PVconstants, PVmodule, PVstring, PVsystem
pvconstants = PVconstants(npts=1001)
from matplotlib import pyplot as plt
import pandas as pd
import numpy as np
from MismatchLossStudy.mismatch_model import get_nM, get_nS, get_scale, get_sum_pmp, get_pvsystem_random

def get_hourly_energy(pvsys, irr, temp):
	pvsys.setTemps(temp + 273.15)
	pvsys.setSuns(irr/1000.0)
	return pvsys.Pmp, get_sum_pmp(pvsys)

def run_annual_energy_sim(pvsys, df_tmy, tech, sim_id):
	"""
	For a given PVsys config, run annual energy calculations and return energy mismatch loss
	:param pvsys: PVSystem built using PVMismatch
	:type pvsys: object
	:param df_tmy: Dataframe containing TMY3 data
	:type df_tmy: dataframe
	:return: annual energy mismatch loss results dictionary
	:rtype: dict
	"""
	result_list = []
	for row in df_tmy.iterrows():
		irr = row[1][irr_key]
		temp = row[1][temp_key]
		dt = row[1]['Date (MM/DD/YYYY)']
		tm = row[1]['Time (HH:MM)']

		sysP, sumP = get_hourly_energy(pvsys, irr, temp)
		mml = (sysP-sumP)*100/sumP
		res_dict = {'date':dt, 'time':tm, 'Irr':irr, 'Temp':temp, 'sysP':sysP, 'sumP':sumP, 'hourly_mismatch_loss':mml}
		print(res_dict)
		result_list.append(res_dict)
	df_r = pd.DataFrame(result_list)
	res_dir = 'results_annual'
	if not os.path.exists(res_dir):
		os.mkdir(res_dir)
	model_run_fname =  res_dir + '/annenergysim_%s_%s_%dx%d_%d.csv'%(tech, system_scale, numMods, numStrings, sim_id)
	energy_mml = (df_r['sysP'].sum() - df_r['sumP'].sum()) *100/ df_r['sumP'].sum()
	res_dict = {'tech' : tech, 'sim_id' : sim_id,'sys_scale': system_scale, 'numMods': numMods, 'numStrings' : numStrings, 'energy_mml' : energy_mml }
	df_to_write = pd.DataFrame([res_dict])
	df_to_write.to_csv(model_run_fname)
	return res_dict

# TODO: Convert GHI to POA
irr_key='GHI (W/m^2)'
# TODO: Convert Dry-bulb to Module temperature for better accuracy
temp_key='Dry-bulb (C)'

if __name__ == '__main__':
	"""
	Note: 
		Arguments to the executable script are : <numMods> <numStrings> <technology> <unique integer for seed>
		Each script instance is a process for one simulation
		Use run_annual.sh shell script to start multiple simulations in parallel
	"""
	args = sys.argv
	if len(args) < 2:
		numMods= 8
		numStrings = 3
		tech = 'TEST'
		sim_id = PID
	else:
		numMods = int(args[1])
		numStrings = int(args[2])
		tech = args[3]
		sim_id = int(args[4])

	df_tmy = pd.read_csv('../data/TMY3_Tucson.csv', skiprows=1)
	df_tmy = df_tmy[df_tmy[irr_key]>0]

	df_flash_data = pd.read_pickle('data/%s.pkl'%(tech))
	ref = 'pmp'
	model = 'pmp1'

	# filter flash data where modeled Pmp and recorded Pmp are close
	df_flash_data['resid'] = (df_flash_data[model] - df_flash_data[ref])*100/df_flash_data[ref]
	df_flash_data = df_flash_data[df_flash_data['resid'] > df_flash_data['resid'].quantile(0.05)]
	df_flash_data = df_flash_data[df_flash_data['resid'] < df_flash_data['resid'].quantile(0.95)]

	# Configure a PVSystem object to be fed to the monte carlo simulation as input
	pvsys = get_pvsystem_random(df_flash_data, numMods, numStrings)

	# run Monte Carlo simulation
	r = run_annual_energy_sim(pvsys, df_tmy, tech, sim_id)
	print(r)
