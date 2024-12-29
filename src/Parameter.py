# coding=utf-8
from queue import Queue
from threading import Lock

# Global
RUN_FLAG = None
MODEL_CONFIG = None
SYSTEM_CONFIG = None
IMAGE_PIXMAP = None
DRAW_COORDINATE = None
SUB_IMAGE = None