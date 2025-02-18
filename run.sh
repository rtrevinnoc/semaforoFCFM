#!/bin/bash

#lxterminal -t "Semáforo 1" -e "SERIAL_NUMBER=2526753599 SEMAPHORE_RED=22 SEMAPHORE_YELLOW=27 SEMAPHORE_GREEN=17 python semaphore.py"
#lxterminal -t "Semáforo 2" -e "SERIAL_NUMBER=2526753598 SEMAPHORE_RED=16 SEMAPHORE_YELLOW=24 SEMAPHORE_GREEN=23 python semaphore.py"
#lxterminal -t "Semáforo 3" -e "SERIAL_NUMBER=2526753597 SEMAPHORE_RED=5 SEMAPHORE_YELLOW=19 SEMAPHORE_GREEN=26 python semaphore.py"


SESSION_NAME="SEMAFOROS"

tmux new-session -d -s "$SESSION_NAME"

tmux send-keys -t "$SESSION_NAME".0 "SERIAL_NUMBER=2526753599 SEMAPHORE_RED=22 SEMAPHORE_YELLOW=27 SEMAPHORE_GREEN=17 python semaphore.py" C-m

tmux split-window -h -t "$SESSION_NAME":0

tmux send-keys -t "$SESSION_NAME".1 "SERIAL_NUMBER=2526753598 SEMAPHORE_RED=16 SEMAPHORE_YELLOW=24 SEMAPHORE_GREEN=23 python semaphore.py" C-m

tmux split-window -v -t "$SESSION_NAME":0.1

tmux send-keys -t "$SESSION_NAME".2 "SERIAL_NUMBER=2526753597 SEMAPHORE_RED=5 SEMAPHORE_YELLOW=19 SEMAPHORE_GREEN=26 python semaphore.py" C-m

# Attach to the session
tmux attach -t "$SESSION_NAME"
