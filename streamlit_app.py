#!/usr/bin/env python3
"""
Streamlit entry point for League-Stats GUI.

This file serves as the main entry point for Streamlit Cloud deployment.
It simply imports and runs the main GUI application.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Import and run the main GUI app
from stats_visualization.gui_app import *

# Streamlit will automatically run the imported module