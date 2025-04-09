#!/bin/bash
source /home/user/Desktop/petbot3.11/bin/activate
python3 /home/user/Desktop/petbot3.11/src/move/main.py &
python3 /home/user/Desktop/petbot3.11/src/see/detection.py &
wait
