import pandas as pd
import numpy as np
import os

loc = {
				 'imp': 5.98,
				 'isc': 6.46,
				 'pmp': 327,
				 'vmp': 54.7,
				 'voc': 64.9}

scale = {
				'imp': 0.02,
				'isc': 0.015,
				'pmp': 2.0,
				'vmp': 0.4,
				'voc': 0.075}

size = 100
df = pd.DataFrame(index=range(size))

f = lambda k :  np.random.normal(loc=loc[k], scale=scale[k] , size=size)

for k in scale.keys():
	df[k] = f(k)
directory = os.path.join('~','repo','MismatchLossStudy','data')

df.to_csv(directory + '/fictional_flash_test_results.csv')