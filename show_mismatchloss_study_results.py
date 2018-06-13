#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 15 14:05:12 2018

@author: cchaudhari

Show results of STC mismatch loss study
"""
import pandas as pd
from matplotlib import pyplot as plt
import numpy as np
#%% plot loss and powers distribution
mismatch_field = 'mismatch_loss'
tech = 'TECH'
d = pd.read_pickle('data/model_run_%s.pkl'%(tech))
bins_size = 100
dd = d.groupby(['numMods','numStrings'])

#%%
i = 0
LOW_X = -0.075
kk = [(8,3), (14,21), (22,139)]

fig, ax = plt.subplots(len(kk), 1, sharex=True)
print("nS, nM, p50, p95")
for grp in kk:
	df = dd.get_group(grp)
	nS, nM = df.numStrings.max(),df.numMods.max()
	n, bins, p = ax[i].hist(df[mismatch_field], bins=bins_size, alpha = 0.5, color = 'blue')
	#ax[i].xlabel('Mismatch loss (%)')
	ax[i].set_xlim([LOW_X, 0])
	ax[i].grid(True)
	p50 = np.nanpercentile(df[mismatch_field], 50)
	p95 = np.nanpercentile(df[mismatch_field], 100-95)
	print(','.join([str(round(x,2)) for x in[nS, nM, p50, p95]]))
	ax[i].axvline(p50, color='green', label='p50')
	ax[i].axvline(p95, color='red', alpha=0.3, label='p95')
	ax[i].text(LOW_X, n.max()*0.5, 'p50=%.3f%%'%(p50), color='red', size=10)
	ax[i].text(LOW_X, n.max()*0.3, r'$N_s=%d\ by\ N_m=%d$'%(nS, nM), color='red', size=10)
	i+=1
plt.xlabel('Mismatch loss (%)')
plt.suptitle(r'$Results\ for\ D_{pvmod}\ at\ STC$')
ax[2].legend(loc='best')

