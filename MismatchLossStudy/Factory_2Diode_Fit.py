import os
import sys
# from pvmismatch.pvmismatch_lib import *
from pvmismatch import PVcell, PVconstants, PVmodule, PVstring, PVsystem, pvmodule

from pvmismatch.contrib import gen_coeffs
import pandas as pd
import numpy as np


def read_data(filename, tech, how_many_rows=None):
	"""
	Get dataframe of flash test results from the excel spreadsheet

	:param filename: Full path of factory flash data excel spreadsheet
	:type filename: str
	:param tech: String of module technology, currently just 'E' or 'P'
	:type tech: str
	:return: DataFrame of factory data along with the number of cells in series and in parallel for the module type
	:rtype: dataframe
	"""

	if tech == 'E':
		sheetname = 'E20 WW3 VT1'
		bin_ = [-0.03, 0.05]
		nameplate = 327
		nseries = 96
		npar = 1
	elif tech == 'P':
		sheetname = 'P17 WW3 VTP1'
		bin_ = [0, 0.05]
		nameplate = 360
		nseries = 82
		npar = 6
	df_r = pd.read_excel(filename, sheetname)
	df = df_r[['Power', 'VmpMOd', 'VocMod', 'ImpMod', 'IscMod', 'Shunt', 'Rs', 'C']]
	df.columns = ['pmp', 'vmp', 'voc', 'imp', 'isc', 'rsh', 'rs', 'tc']
	df = df[(df.pmp > nameplate * (1 + bin_[0])) & (df.pmp < nameplate * (1 + bin_[1]))]
	if how_many_rows is None:
		return df, nseries, npar
	else:
		return df.head(how_many_rows), nseries, npar


def pmax(volt, curr):
	"""
	Find Pmp (MPP) from IV dataset (not used)
	:param volt:
	:type volt:
	:param curr:
	:type curr:
	:return:
	:rtype:
	"""
	power = curr * volt
	mpp = np.argmax(power)
	while (len(volt) - mpp) < 2:
		mpp -= 1
	P = power[mpp - 1:mpp + 2]
	V = volt[mpp - 1:mpp + 2]
	I = curr[mpp - 1:mpp + 2]
	# calculate derivative dP/dV using central difference
	dP = np.diff(P, axis=0)  # size is (2, 1)
	dV = np.diff(V, axis=0)  # size is (2, 1)
	Pv = dP / dV  # size is (2, 1)
	# dP/dV is central difference at midpoints,
	Vmid = (V[1:] + V[:-1]) / 2.0  # size is (2, 1)
	Imid = (I[1:] + I[:-1]) / 2.0  # size is (2, 1)
	# interpolate to find Vmp
	Vmp = (-Pv[0] * np.diff(Vmid, axis=0) / np.diff(Pv, axis=0) + Vmid[0]).item()
	Imp = (-Pv[0] * np.diff(Imid, axis=0) / np.diff(Pv, axis=0) + Imid[0]).item()
	# calculate max power at Pv = 0
	Pmp = Imp * Vmp
	return Vmp, Imp, Pmp


def factory_fit(filename, tech, how_many_rows=None):
	"""
	Fit factory dataset with 2 diode model using the datapoints - Voc, Vmp, Imp, Isc
	:param filename: Full path of factory flash data excel spreadsheet
	:type filename:
	:param tech: String of module technology, currently just 'E' or 'P'
	:type tech:
	:return: DataFrame consisting of factory flash data along with 2-Diode fit values
	:rtype:
	"""

	df, ncells, npar = read_data(filename, tech, how_many_rows)
	isat1, isat2, rs, rsh, imp1, vmp1, pmp1, pvm_list = [], [], [], [], [], [], [], []
	x0 = (2.25e-11, 1.5e-6, 4.e-3, 10.0)
	x1 = (2.25e-11, 6.5e-7, 3e-2, 24)

	for i, row in df.iterrows():
		try:
			if tech == 'E':
				mod = pvmodule.STD96
			elif tech == 'P':
				mod = pvmodule.PCT492

			if tech == 'P' and row.imp > 8.3:
				x, sol = gen_coeffs.gen_two_diode(row.isc, row.voc, row.imp, row.vmp, ncells, npar, 25., method='lm',
												  x0=x1)
			else:
				x, sol = gen_coeffs.gen_two_diode(row.isc, row.voc, row.imp, row.vmp, ncells, npar, 25., method='lm',
												  x0=x0)
			pvc = PVcell(Rs=x[2], Rsh=x[3], Isat1_T0=x[0], Isat2_T0=x[1], Isc0_T0=row.isc / npar, pvconst=pvconstants)
			pvm = PVmodule(mod, pvcells=pvc, pvconst=pvconstants)
			vmp, imp, pmp = pmax(pvm.Vmod, pvm.Imod)

			isat1.append(x[0])
			isat2.append(x[1])
			rs.append(x[2] * ncells)
			rsh.append(x[3] * ncells)
			imp1.append(imp)
			vmp1.append(vmp)
			pmp1.append(pmp)
			pvm_list.append(pvm)

		except Exception as e:
			print('Exception at %d' % (i) + str(e))
			isat1.append(None)
			isat2.append(None)
			rs.append(None)
			rsh.append(None)
			imp1.append(None)
			vmp1.append(None)
			pmp1.append(None)
			pvm_list.append(None)
			pass

		print(tech, i, pmp)

	df['isat1'] = isat1
	df['isat2'] = isat2
	df['rs1'] = rs
	df['rsh1'] = rsh
	df['imp1'] = imp1
	df['vmp1'] = vmp1
	df['pmp1'] = pmp1
	df['pvmods_obj'] = pvm_list
	return df


def show_flash_data():
	plt.figure()
	plt.subplot(121)

	pickle_fname = 'data/E20.pkl'
	# pickle_fname = 'data/P17.pkl'

	if os.path.exists(pickle_fname):
		print('pickle exits... ' + pickle_fname)
		df_flash_data = pd.read_pickle(pickle_fname)
	else:
		df_flash_data = factory_fit(filename, 'E')
		df_flash_data.to_pickle(pickle_fname)

	ref = 'pmp'
	model = 'pmp1'
	resid = (df_flash_data[model] - df_flash_data[ref]) * 100 / df_flash_data[ref]

	df_flash_data = df_flash_data[resid > resid.quantile(0.05)]
	df_flash_data = df_flash_data[resid < resid.quantile(0.95)]

	plt.hist(df_flash_data[ref], bins=50, label='flash', alpha=0.5)
	plt.hist(df_flash_data[model], bins=50, label='model', alpha=0.5)
	plt.title('IBC')
	plt.legend()

	plt.subplot(122)
	# pickle_fname = 'data/E20.pkl'
	pickle_fname = 'data/P17.pkl'

	if os.path.exists(pickle_fname):
		print('pickle exits... ' + pickle_fname)
		df_flash_data = pd.read_pickle(pickle_fname)
	else:
		df_flash_data = factory_fit(filename, 'P')
		df_flash_data.to_pickle(pickle_fname)

	ref = 'pmp'
	model = 'pmp1'
	resid = (df_flash_data[model] - df_flash_data[ref]) * 100 / df_flash_data[ref]
	df_flash_data = df_flash_data[resid > resid.quantile(0.05)]
	df_flash_data = df_flash_data[resid < resid.quantile(0.95)]

	plt.hist(df_flash_data[ref], bins=50, label='flash', alpha=0.5)
	plt.hist(df_flash_data[model], bins=50, label='model', alpha=0.5)
	plt.legend()
	plt.title('Non IBC')


if __name__ == '__main__':
	tech = 'E'
	npts = 1001
	pvconstants = PVconstants(npts=npts)
	# Example of how to run this code
	filename = '/Users/cchaudhari/repo/MismatchLossStudy/data/Data Generator Master Query.xlsx'
	df_flash_data = factory_fit(filename, tech, 100)
	if tech == 'E':
		df_flash_data.to_pickle(tech + '20_%d.pkl'%(npts))
	elif tech == 'P':
		df_flash_data.to_pickle(tech + '17_%d.pkl'%(npts))

# df_p = factory_fit(filename, 'P')
# df_p.to_pickle('../data/P17.pkl')

"""
	from matplotlib import pyplot as plt

	##
	#%%
	plt.figure()
	plt.plot(df_flash_data.pmp, df_flash_data.pmp1, '.')
	plt.figure()
	plt.plot(df_e.imp,df_e.imp1, '.')
	plt.figure()
	plt.plot(df_e.vmp,df_e.vmp1, '.')


##
	ref = 'vmp'
	model= 'vmp1'

	resid = ( df_p[ref] - df_p[model])*100/df_p.pmp
	plt.figure()
	plt.plot(df_p[ref], resid, '.')
	plt.xlabel('Pmp_flash (W)')
	plt.ylabel('(Pmp_flash-Pmp_model)/Pmp_flash (%)')
	plt.grid(True)
	#plt.text(327, np.median(resid), 'median error = %f pct'%(np.median(resid)))

	plt.figure()
	plt.hist(resid)
"""
