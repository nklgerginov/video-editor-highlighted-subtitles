#!/usr/bin/env python3
import sys
import os
<<<<<<< HEAD

project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

from ui.main_window import main

=======
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)
from ui.main_window import main
>>>>>>> a71566016695e21c407a34efabef2157bae5f31d
if __name__ == "__main__":
    main()
