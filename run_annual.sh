#!/bin/bash
j=0
for i in {1..200}; # 200 is the number of monte carlo simulations
do
      j=$((i%70)) # replace 70 with number of Cores available on your machine
      if [ $j -eq 0 ]; then
	  wait;
	  sleep 3;
	  echo "just finished batch of $i"
      else
          # ~/anaconda3/envs/PVMIS27/bin/python run_annual_energy_mismatch.py 8 3 E20 $i &
          ~/anaconda3/envs/PVMIS27/bin/python run_annual_energy_mismatch.py $1 $2 $3 $i &
         
      fi
done


