#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 15 14:05:12 2018

@author: cchaudhari

System level Mismatch calculator for PV systems
"""
import os
import pandas as pd
import numpy as np
import random
random.seed(666)
from pvmismatch import PVcell, PVconstants, PVmodule, PVstring, PVsystem
from get_flash_data import get_flash_data

from scipy import stats

pvconstants = PVconstants(npts=1001)

def get_nS(invSize, nM):
    """
    Get number of Strings in a PV system
    :param invSize: Inverter Power kW
    :param nM: Number of Modules per string
    :return: Number of strings in the system
    """
    nS = int(np.floor(invSize / (nM * 327.)))
    if nS < 1:
        nS = 1
    return nS

def get_nM(df_flash_data, sysV):
    """
    Get number of Modules in a PV string
    :param sysV: System Voltage (600|1000|1500V)
    :return: max number of modules per string
    """
    pv = df_flash_data['pvmods_obj'][0]
    pv.setTemps(0+273.15)
    Vabsmax = pv.Voc.sum()
    return int(np.floor(sysV/Vabsmax))

def get_scale(numMods, numStrings):
    """
    Get scale of the PV system
    :return:<str>:: Scale of the system
    """
    if numStrings <= 5:
        system_scale = 'Residential'
    elif (numStrings > 5) and (numStrings <= 20):
        system_scale = 'Commercial'
    elif numStrings > 20:
        system_scale = 'Utility'
    return system_scale

def get_sum_pmp(pvsys):
    pvmods_all = np.ravel(pvsys.pvmods)
    # TODO: change the x.Pmod.max() to a proper interpolation of Pmp for better accuracy
    return np.sum([x.Pmod.max() for x in pvmods_all])

def get_param_stats(pvsys):
    #pvmods_all = np.ravel(pvsys.pvmods)
    r = {}
    for i, pvstr in enumerate(pvsys.pvstrs):
        s = {}
        pvmods = np.ravel(pvstr.pvmods)
        s['vmp_p50'] = np.percentile([x.Vmod[x.Pmod.argmax()] for x in pvmods], 0.5)
        s['vmp_std'] = np.std([x.Vmod[x.Pmod.argmax()] for x in pvmods])
        s['imp_p50'] = np.percentile([x.Imod[x.Pmod.argmax()] for x in pvmods], 0.5)
        s['imp_std'] = np.std([x.Imod[x.Pmod.argmax()] for x in pvmods])
        r[i] = s
    return r

def get_pvsystem_random(df_flash_data, numMods, numStrings):
    pvstr_list = []
    indices = []
    for strnum in range(numStrings):
        rand_grp = df_flash_data['pvmods_obj'].sample(numMods)
        indices.append(rand_grp.index.values)
        pvstr = PVstring(numberMods=numMods, pvmods=rand_grp.values, pvconst=pvconstants)
        pvstr_list.append(pvstr)
    pvsys = PVsystem(numberStrs=numStrings, pvstrs=pvstr_list, pvconst=pvconstants)
    return pvsys, indices

def get_temp_var(size, sig=0.02, mu=0):
    """
    get variance to be applied to temperatures in the pv string
    :param size: number of temperature modifiers
    :param sig: 1 sigma of temperature variance across the PV string
    :param mu: bias if any
    :return: list of temperature modifiers
    """
    if size == 1:
        return stats.norm.rvs(loc=mu, scale=sig, size=size)[0]
    else:
        return stats.norm.rvs(loc=mu, scale=sig, size=size)

def run_model(df_flash_data, numMods=8, numStrings=3, num_trials= 1000, temp_var = None):
    """
    run Mismatch Calculator for a given configuration of PV system (numStrings x numMods) for a given number of trials.
    Each trial consists of a random walk of Monte Carlo simulation where the PV modules used in the PV system are chosen
    at random from the collection of flash test data

    :param df_r:dataframe:: Dataframe containing flash test data and fitted models for each PV module in the dataset
    :param numMods:int:: number of modules in series
    :param numStrings:int:: number of strings in parallel
    :param num_trials:int:: number of trials in the Monte Carlo simulation
    :param temp_var:float:: fraction of temperature variance
    :return: Dataframe of mismatch loss results
    """
    system_scale = get_scale(numMods, numStrings)
    result_dict = {}
    key_flash_power = 'pmp'

    model_power_vector = []
    model_power_vector_max = []
    sum_pmpmod_vector = []
    pvsys_param_vector =[]
    indices_vector = []

    for trial in range(num_trials): # Monte Carlo Simulation
        # choose randomly from collection of PV modules models to build strings
        pvsys, pvmod_indices = get_pvsystem_random(df_flash_data, numMods, numStrings)
        pvsys_param_vector.append(get_param_stats(pvsys))
        indices_vector.append(pvmod_indices)
        # build PV system using the strings
        model_power_vector.append(pvsys.Pmp)
        model_power_vector_max.append(pvsys.Psys.max())
        sum_pmpmod_vector.append(get_sum_pmp(pvsys))

    result_dict['system_scale']= [system_scale] * num_trials  # for i in range(num_trials)]
    result_dict['numStrings']  = [numStrings] * num_trials  # for i in range(num_trials)]
    result_dict['numMods']     = [numMods] * num_trials  # for i in range(num_trials)]
    result_dict['trial']       = range(num_trials)
    result_dict['ref_power']   = sum_pmpmod_vector
    result_dict['model_power'] = model_power_vector
    result_dict['model_power_max'] = model_power_vector_max
    result_dict['stats'] = pvsys_param_vector

    df_result = pd.DataFrame(result_dict)
    df_result['mismatch_loss'] = (df_result['model_power'] - df_result['ref_power'])*100/df_result['ref_power']
    df_result['mismatch_loss_pmax'] = (df_result['model_power_max'] - df_result['ref_power'])*100/df_result['ref_power']
    df_result['indices'] = indices_vector

    if not os.path.exists('results'):
        os.mkdir('results')

    model_run_fname = 'results/%s_%dx%d.csv'%(system_scale, numStrings, numMods)
    df_result.to_csv(model_run_fname)
    return df_result

#def run_energy_mismatch_model(df_flash_data, numMods=10, numStrings=2, num_trials= 100):
    """
    Get energy mismatch for a TMY file
    :param df_flash_data:
    :type df_flash_data:
    :param numMods:
    :type numMods:
    :param numStrings:
    :type numStrings:
    :param num_trials:
    :type num_trials:
    :return:
    :rtype:
    """

def show_mismatch_best_worst_case(df_stc):
    a = df_stc.loc[df_stc.mismatch_loss.idxmin()] # high mismatch loss
    b = df_stc.loc[df_stc.mismatch_loss.idxmax()] # low mismatch loss
    df_a = [ df_flash_data.loc[a.indices[i]][['imp1','vmp1','pmp1']] for i in range(3)]
    df_b = [ df_flash_data.loc[b.indices[i]][['imp1','vmp1','pmp1']] for i in range(3)]

    pvmods_a = [ df_flash_data.loc[a.indices[i]]['pvmods_obj'] for i in range(3)]
    pvmods_b = [ df_flash_data.loc[b.indices[i]]['pvmods_obj'] for i in range(3)]

    a_pmp = [df_a[i].pmp1.values for i in range(3)]
    b_pmp = [df_b[i].pmp1.values for i in range(3)]

    a_vmp = [df_a[i].vmp1.values for i in range(3)]
    b_vmp = [df_b[i].vmp1.values for i in range(3)]

    a_imp = [df_a[i].imp1.values for i in range(3)]
    b_imp = [df_b[i].imp1.values for i in range(3)]

    pvstrs_list_a,pvstrs_list_b = [],[]
    for i in range(3):
        pvstrs_list_a.append( PVstring(numberMods=8, pvmods=pvmods_a[i].values, pvconst=pvconstants))
        pvstrs_list_b.append( PVstring(numberMods=8, pvmods=pvmods_b[i].values, pvconst=pvconstants))

    pvsys_a = PVsystem(numberStrs=3, pvstrs=pvstrs_list_a, pvconst=pvconstants)
    pvsys_b = PVsystem(numberStrs=3, pvstrs=pvstrs_list_b, pvconst=pvconstants)

    plt.figure()
    fig, ax = plt.subplots(1,2, sharey=True, sharex=True)
    for pstr in pvstrs_list_a:
        ax[0].plot(pstr.Istring, pstr.Pstring, 'o-')
    ax[0].set_ylim([0,3000])
    ax[0].set_title('high mismatch loss PV system %f'%(a['mismatch_loss']))

    for pstr in pvstrs_list_b:
        ax[1].plot(pstr.Istring, pstr.Pstring, 'o-')
    ax[1].set_ylim([0,3000])
    ax[1].set_title('low mismatch loss PV system %f'%(b['mismatch_loss']))
    plt.suptitle('PI curve for PV strings for %s'%tech)

def show_flash_data(df_flash_data):
	plt.figure()
	pmp = df_flash_data[df_flash_data['pmp1']>327]['pmp1']
	pmp.hist(bins=50)
	plt.grid(True)
	plt.axvline(327, color='red')
	plt.xlabel('Pmp(W)')
	plt.title(r'$Distribution\ of\ P_{mpmod}\ -\ (Population\ size=%d)$'%(len(pmp)))
#%%
if __name__ == '__main__':
    from matplotlib import pyplot as plt
    tech = 'TEST'

    directory = os.path.join('~','repo','MismatchLossStudy','data')
    if os.path.exists(directory):
        pass
    else:
        os.makedirs(directory)

    fname = directory + '/flash_test_results.csv'
    df_flash_data = get_flash_data(fname)

    df_flash_data.to_pickle('../data/%s.pkl'%(tech))

    # run Mismatch Model
    df_stc = run_model(df_flash_data, numMods=8, numStrings=3, num_trials=50)

    # Show flash data Pmp distribution
    show_flash_data(df_flash_data)
	# Show mismatch loss on individual strings
    show_mismatch_best_worst_case(df_stc)
