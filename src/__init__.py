# Copyright (c) kerem.ai. All Rights Reserved.

import os
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# Suppress GDAL loggers
os.environ["CPL_LOG"] = "/dev/null"  # disable GDAL’s own log file
os.environ["CPL_DEBUG"] = "OFF"  # no GDAL debug output
os.environ["GDAL_PAM_ENABLED"] = "NO"  # optional: stop GDAL auxiliary writes

# Import the modules
from . import utils
from .downloader import AlphaEarthDownloader
from .visualizer import EarthEngineVisualizer

__all__ = [
    "utils",
    "AlphaEarthDownloader",
    "EarthEngineVisualizer",
]
