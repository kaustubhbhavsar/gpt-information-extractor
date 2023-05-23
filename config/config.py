import os
from pathlib import Path


# Directories
BASE_DIR = Path(os.path.abspath(__file__)).parent.parent.absolute()
DATA_DIR = Path(BASE_DIR, "data")
LOG_DIR = Path(DATA_DIR, "log")