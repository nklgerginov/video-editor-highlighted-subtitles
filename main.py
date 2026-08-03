#!/usr/bin/env python3
import sys
import os

project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from ui.main_window import main

if __name__ == "__main__":
    main()