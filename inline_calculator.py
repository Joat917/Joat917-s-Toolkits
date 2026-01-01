# 一个类似IDLE的代码编辑器，随时执行单行或多行Python代码
import code
import sys
import os
from unitex_jsrunner import convert as unitex

class InlineCalculator(code.InteractiveConsole):
    def __init__(self):
        super().__init__()
        sys.ps1 = ">>> "
        sys.ps2 = "... "
        for command in [
            'import math',
            'import cmath',
            'import random',
            'import time',
            'from datetime import datetime, timedelta',
            'from fractions import Fraction',
            'from decimal import Decimal',
            'import collections', 
            'import itertools',
            'import re', 
            'import numpy as np', 
            'import pandas as pd', 
            'import sympy as sp', 
            'import matplotlib.pyplot as plt', 
            'from builtins import *', 
            'original_pow = pow',
            'from math import *', 
            'from PIL import Image, ImageDraw, ImageFont',
            'from unitex_jsrunner import convert as unitex', 
            'from pyperclip import copy, paste', 
            f'__import__("os").chdir({os.path.abspath(os.path.expanduser("~"))!r})'
        ]:
            self.push(command)

    def interact(self):
        print("Inline calculator: Enter expression to evaluate.")
        print("Try 'help()' for help, EOF to exit.")

        more = 0
        _scipy_imported = False
        while True:
            if more:
                prompt = getattr(sys, 'ps2', '... ')
            else:
                prompt = getattr(sys, 'ps1', '>>> ')
            
            try:
                line = input(prompt)
                if more==0 and (line.startswith('%') or line.startswith('!')):
                    ret = os.system(line[1:])
                    self.push(f"_ = {ret}")
                    continue
                if more==0 and line.startswith('$'):
                    if line.startswith('$$'):
                        self.push(f'copy(_:=unitex({line[2:]!r}));_')
                    else:
                        self.push(f'unitex({line[1:]!r})')
                    continue
                if more==0 and line.startswith('?'):
                    expr = line[1:].strip()
                    if not expr:
                        print("New features:\n- Prefix '$' to evaluate UniTex expression.\n- Prefix '$$' to copy UniTex expression to clipboard.\n- Prefix '%' or '!' to run shell commands.\n- Use copy() and paste() to interact with clipboard. \nFor more information, use help().")
                    else:
                        if all(c=='?' for c in expr):
                            # easter egg
                            import random
                            if expr=='??':
                                print('そんなことに何の意味があるんですか？')
                            else:
                                print(''.join(random.choice('???¿')*random.randint(10,60) for _ in expr))
                        else:
                            self.push(f"help({repr(expr)})")
                    continue
                more = self.push(line)
                if not _scipy_imported and 'scipy' in sys.modules:
                    _scipy_imported = True
                    print("Warning: KeyboardInterrupt collapses the program once scipy is imported.")
            except EOFError:
                return
            except KeyboardInterrupt:
                self.write("\nKeyboardInterrupt\n")
                self.resetbuffer()
                more = 0
                continue

if __name__ == "__main__":
    calc = InlineCalculator()
    calc.interact()