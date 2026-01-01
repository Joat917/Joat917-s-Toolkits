import os
import sys
import time
import datetime
import math
import collections

import threading
import queue
import win32com.client
import subprocess
import pynput
import psutil

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'
os.chdir(os.path.dirname(__file__))

FONT_NAME = "STXINWEI"

