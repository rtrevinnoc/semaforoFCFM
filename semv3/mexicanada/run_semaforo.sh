#!/bin/bash

# Abrir el contador en una nueva terminal
lxterminal -t "Contador" -e "python3 global_counter.py"

# Abrir los scripts de semáforos en nuevas terminales
lxterminal -t "Semáforo 1" -e "python3 sem1.py"
lxterminal -t "Semáforo 2" -e "python3 sem2.py"
lxterminal -t "Semáforo 3" -e "python3 sem3.py"
