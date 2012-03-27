#!/bin/bash
#
#$ -cwd
#$ -j y
#$ -S /bin/bash
#$ -M neva@seas.harvard.edu
#$ -o runcode.out

python ImportNewLibrary.py