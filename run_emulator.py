#!/usr/bin/env python3
"""
NintEmulator - Game Boy Emulator
Single script launcher for the Game Boy emulator

Usage:
    python run_emulator.py [rom_file.gb]

If no ROM file is provided, it will run the built-in Pong game.

Requirements:
    pip install pygame numpy

Controls:
    Arrow Keys: D-Pad
    A: A button
    S: B button
    Enter: Select
    Space: Start
    Escape: Quit
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import pygame
    import numpy as np
except ImportError:
    print("Error: Required dependencies not found!")
    print("Please install them with: pip install pygame numpy")
    sys.exit(1)

try:
    from emulator import main
except ImportError:
    print("Error: Could not import emulator module!")
    print("Make sure all emulator files are in the same directory.")
    sys.exit(1)

if __name__ == "__main__":
    main()
