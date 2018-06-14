# MismatchLossStudy
Mismatch Loss study using PVMismatch

# First steps 
Create Conda environment using the included .yml file

# Loading Flash test dataset into the framework
Make sure get_flash_data.py from the core module MismatchLossStudy can read your flash test results file and has headers as expected by the get_flash_data module.

See generate_flash_data.py module for an example on how the flash test data should look like. Same script can be modified to generate flash test distributions if the mean and scale of various parameters required are known.

If comprehensive set of flash test results are available (2 diode model parameters - Rs, Rsh, Isat1, Isat2, Isc0), then instead of using get_flash_data module to generate 2 diode model coefficients , you can directly feed a dataframe of PVMismatch PVmodule objects.

# STC calculations 
To run Monte Carlo simulations for STC mismatch calculations -  run_mismatchloss_study.py

# Annual Loss calculations
To run one simulation of annual energy loss use run_annual_energy_mismatch.py

To run full Monte Carlo for annual energy loss, use run_annual.sh 

You will have to modify the paths in this shell script to suit your environment. 
