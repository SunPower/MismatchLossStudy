# MismatchLossStudy
Mismatch Loss study using PVMismatch

# First steps 
Create Conda environment using the included .yml file

Make sure get_flash_data.py from the core module MismatchLossStudy can read your flash test results file and has headers as expected by the get_flash_data module.

See generate_flash_data.py module for an example on how the flash test data should look like. Same script can be modified to generate flash test distributions if the mean and scale of various parameters required are known.

# STC calculations 
To run Monte Carlo simulations for STC mismatch calculations -  run_mismatchloss_study.py

# Annual Loss calculations
To run one simulation of annual energy loss use run_annual_energy_mismatch.py

To run full Monte Carlo for annual energy loss, use run_annual.sh 

