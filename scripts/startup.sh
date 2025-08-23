#!/bin/sh

rm -f /tmp/.X0-lock

# Run Xvfb on dispaly 0.
Xvfb :0 -screen 0 1280x720x16 &

# Run fluxbox windows manager on display 0.
fluxbox -display :0 &

# Run x11vnc on display 0
x11vnc -display :0 -forever -usepw &

# Add delay
sleep 5

# Run python script
python test.py
