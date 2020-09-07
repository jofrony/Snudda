#!/bin/bash -l


# !!! OBS, you need to point to the right directory which contains network!!!
#JOBDIR=TegnerRun.${SLURM_JOBID}
SNUDDA_DIR=/cfs/klemming/nobackup/${USER:0:1}/$USER/Snudda/snudda
DATA=$SNUDDA_DIR/data

JOBDIR=$SNUDDA_DIR/../networks/TegnerRun.900154


if [ $SLURM_PROCID -gt 0 ]; then
	mock_string="Not main process"

else

    echo ">>> Input: "`date`

    snudda input ${JOBDIR} --input ../data/config/input-tinytest-v5org-strongerFS-short2.5s.json --time 2.5


    echo "JOB END "`date` start_time_network_connect.txt

fi


