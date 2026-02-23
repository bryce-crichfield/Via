#!/bin/bash

# Disable screen blanking
xset s off
xset -dpms
xset s noblank

# Hide cursor
unclutter -idle 0.1 &

# Run your app (this replaces the window manager)
cd /home/pi/via
exec /home/pi/via/venv/bin/python3 main.py