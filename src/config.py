import os
from re import M
from pathlib import Path
import json
from yaml import load, dump
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

path_cfg =  'development_config.yml'
cfg = load(open(path_cfg, 'r'), Loader=Loader)

CAMERA_DEVICE = cfg['CAMERA_DEVICE']

def resource_path(relative_path):
    base_path = os.path.abspath("GUI")
    return os.path.join(base_path, relative_path)

MAIN_GUI = resource_path("Main.ui")
SETUP_GUI = resource_path("Setup.ui")