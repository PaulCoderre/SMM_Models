#!/bin/bash

module restore scimods
source /home/paulc600/scimods/bin/activate

python ./data/data_calibrate_prms.py

