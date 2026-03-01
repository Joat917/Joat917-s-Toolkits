# 一个类似IDLE的代码编辑器，随时执行单行或多行Python代码
import code
import sys
import os
import threading

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) # import patch

class InlineCalculator(code.InteractiveConsole):
    NAMEX = "namex" # 试图用UniTex渲染'namex'字符串时使用的结果
    def __init__(self):
        super().__init__()
        sys.ps1 = ">>> "
        sys.ps2 = "... "
        for command in [
            'import os', 
            'import sys', 
            'import math',
            'import cmath',
            'import random',
            'import time',
            'from datetime import date, datetime, timedelta',
            'import fractions',
            'from fractions import Fraction', 
            'import decimal', 
            'from decimal import Decimal',
            'import collections', 
            'import itertools',
            'import re', 
            'import json', 
            'import base64', 
            'import hashlib',
            'original_pow = pow',
            'from math import *', 
            'from builtins import *', 

            f'os.chdir({os.path.abspath(os.path.expanduser("~"))!r})', 

            'from PIL import Image, ImageDraw, ImageFont',
            'from pyperclip import copy, paste', 
            'import prettytable' if self.has_lib("prettytable") else '',
            'from prettytable import PrettyTable' if self.has_lib("prettytable") else '',

            # 后台线程导入启动较慢的库，减少启动卡顿
            'import threading',
            'threading.Thread(target=lambda:exec("import numpy as np",globals()),daemon=True).start()' if self.has_lib("numpy") else '',
            'threading.Thread(target=lambda:exec("import pandas as pd",globals()),daemon=True).start()' if self.has_lib("pandas") else '', 
            'threading.Thread(target=lambda:exec("import sympy as sp",globals()),daemon=True).start()' if self.has_lib("sympy") else '', 
            'threading.Thread(target=lambda:exec("import matplotlib.pyplot as plt",globals()),daemon=True).start()' if self.has_lib("matplotlib") else '',
            'threading.Thread(target=lambda:exec("from unitex_jsrunner import convert as unitex",globals()),daemon=True).start()' if self.has_lib("execjs") else 'print("Warning: UniTex is not available because execjs is not installed.")',
            'threading.Thread(target=lambda:exec("os.system(\\"title Inline Calculator\\")",globals()),daemon=True).start()',
        ]:
            self.push(command)

        threading.Thread(target=self.set_namex, daemon=True).start()

    def has_lib(self, libname):
        import importlib.util
        return importlib.util.find_spec(libname) is not None

        
    def set_namex(self):
        from basic_settings import SETTINGS
        import base64
        try:
            with open(SETTINGS.namexfilepath, 'r', encoding='utf-8') as f:
                new_namex = base64.a85decode(f.read().strip().encode()).decode()
                if new_namex:
                    self.NAMEX = new_namex
            # for arg in sys.argv[1:]:
            #     if arg.startswith('--namex='):
            #         new_namex = base64.a85decode(arg[len('--namex='):].strip().encode()).decode()
            #         if new_namex:
            #             self.NAMEX = new_namex
        except Exception:
            # import traceback
            # traceback.print_exc()
            pass


    def interact(self):
        print("Inline Calculator (like IDLE).")
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
                        expr=line[2:]
                        if expr=='namex':
                            expr=self.NAMEX
                        self.push(f'copy(_:=unitex({expr!r}));_')
                    else:
                        expr=line[1:]
                        if expr=='namex':
                            expr=self.NAMEX
                        self.push(f'unitex({expr!r})')
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