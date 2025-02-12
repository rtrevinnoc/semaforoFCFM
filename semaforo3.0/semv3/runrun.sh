#!/bin/bash

# Abrir los scripts de semáforos en nuevas terminales
lxterminal -t "Semáforo 1" -e "python sem2.py"
lxterminal -t "Semáforo 2" -e "python semaforoa.py"
lxterminal -t "Semáforo 3" -e "python sem3.py"