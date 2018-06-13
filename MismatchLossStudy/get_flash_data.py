# -*- coding: utf-8 -*-
"""
Created on Mon Jan 15 14:05:12 2018

@author: cchaudhari

Get flash data from flash test results

headers = [pmp, vmp, voc, imp, isc]

"""
import os
from pvmismatch import PVcell, PVconstants, PVmodule, PVstring, PVsystem, pvmodule
from pvmismatch.contrib import gen_coeffs
import pandas as pd
import numpy as np

pvconstants = PVconstants(npts=1001)

def get_flash_data(flash_test_results_fname):
	"""
	Load flash test results and make PVmodule objects after generating 2 diode model coefficients

	:param flash_test_results_fname: filename
									 input parameters from flash tests [pmp, vmp, voc, imp, isc]
	:type flash_test_results_fname: string
	:return: dataframe PVMismatch pvmodule objects (including original flash test data)
	:rtype: dataframe
	"""

	# initial estimate for (isat1, isat2, rs, rsh)
	print('Make sure this is correct : initial Estimate for (isat1, isat2, rs, rsh)')
	x0 = (2.25e-11, 1.5e-6, 4.e-3, 10.0)
	print(x0)

	df = pd.read_csv(flash_test_results_fname)

	isat1, isat2, rs, rsh, imp1, vmp1, pmp1, pvm_list = [], [], [], [], [], [], [], []

	for i, row in df.iterrows():
		try:
			# standard module layout from PVMismatch
			mod = pvmodule.STD96
			ncells = 96
			npar = 1

			x, sol = gen_coeffs.gen_two_diode(row.isc, row.voc, row.imp, row.vmp, ncells, npar, 25., method='lm', x0=x0)
			pvc = PVcell(Rs=x[2], Rsh=x[3], Isat1_T0=x[0], Isat2_T0=x[1], Isc0_T0=row.isc / npar, pvconst=pvconstants)
			pvm = PVmodule(mod, pvcells=pvc, pvconst=pvconstants)
			vmp, imp, pmp = (pvm.Vmod[pvm.Pmod.argmax()], pvm.Imod[pvm.Pmod.argmax()], pvm.Pmod.max())

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

		#print(i, pmp)

	df['isat1'] = isat1 # 1 suffix for the parameters after the fit
	df['isat2'] = isat2
	df['rs1'] = rs
	df['rsh1'] = rsh
	df['imp1'] = imp1
	df['vmp1'] = vmp1
	df['pmp1'] = pmp1
	df['pvmods_obj'] = pvm_list
	return df

if __name__ == '__main__':
	tech = 'TEST'
	# Show mismatch loss on individual strings
	directory = os.path.join('~','repo','MismatchLossStudy','data')
	fname = directory + '/fictional_flash_test_results.csv'
	df = get_flash_data(fname)
	df.to_pickle(directory + '/%s.pkl'%(tech))