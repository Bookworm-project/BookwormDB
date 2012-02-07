#!/bin/bash 
# 
#$ -cwd 
#$ -j y 
#$ -S /bin/bash 
#$ -M bschmidt@seas.harvard.edu


python jstorParser.py
