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
import pyperclip
import win32clipboard
import pywintypes

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

WORKING_DIR = os.path.join(os.environ['APPDATA'], 'PyScriptX', 'MyToolkits')
PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
os.makedirs(WORKING_DIR, exist_ok=True)
os.chdir(WORKING_DIR)

FONT_NAME = "STXINWEI"
ICON_PATH = os.path.abspath(os.path.join(PROJECT_DIR, 'img', 'icon.png'))
