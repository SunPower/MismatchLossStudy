"""
Created on Mon Jan 15 14:05:12 2018

@author: cchaudhari

Show annual energy loss due to mismatch results
"""
import pandas as pd
from matplotlib import pyplot as plt
import os

fnames = os.listdir('results_annual')

def get_annual_mismatch_df(tech='TEST', nS=3, nM=8):
	df_list = []
	for f in fnames:
		if tech in f:
			if '%dx%d'%(nM, nS) in f:
				df = pd.read_csv('results/' + f)
				df_list.append(df)
	df_master = pd.concat(df_list)
	return df_master

tech= 'TEST'
nS = 3
nM = 8
df_master = get_annual_mismatch_df(tech, nS, nM)

plt.figure()
plt.subplot(121)
n, bins, p = plt.hist(df_master['energy_mml'], alpha = 0.5)
# plt.title('Annual Energy Mismatch Loss for Tucson, AZ (IBC technology)')
plt.xlabel('% Annual energy mismatch loss')
p50 = df_master['energy_mml'].quantile(0.5)
p95 = df_master['energy_mml'].quantile(0.05)
print(tech, nS, nM, p50, p95)
plt.axvline(p50, color='green', alpha=0.5)
plt.axvline(p95, color='red', alpha=0.5)
plt.text(-0.18, n.max()*0.7, 'IBC', color='red', size=14)
plt.text(-0.18, n.max()*0.5, 'p50=%.3f%%'%(p50), color='red',size=14)
plt.text(-0.18, n.max()*0.3, r'$N_s=%d\ x\ N_m=%d$'%(nS, nM), color='red', size=14)
plt.grid(True)

plt.suptitle('Annual Energy Mismatch Loss for Tucson, AZ (TMY3)')