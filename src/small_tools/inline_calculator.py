# 一个类似IDLE的代码编辑器，随时执行单行或多行Python代码
import code
import sys
import os
import threading
import traceback
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import BufferControl

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))) # import patch


class MultiLineConsole:
    def __init__(self, locals=None):
        self.locals = locals or {"__name__": "__console__", "__doc__": None}

    def is_complete(self, text):
        try:
            return code.compile_command(text, "<console>", "single") is not None
        except Exception:
            return False

    def push(self, text):
        try:
            compiled = code.compile_command(text, "<console>", "single")
        except Exception:
            return
        if compiled is not None:
            try:
                exec(compiled, self.locals)
            except SystemExit:
                raise
            except Exception:
                traceback.print_exc()

    def _get_line_prefix(self, lineno, before_previous):
        return sys.ps1 if lineno == 0 else sys.ps2

    def interact(self, banner=None, exitmsg=None):
        if banner: print(banner)
        kb = KeyBindings()
        @kb.add(Keys.Enter)
        def _(e):
            t = e.current_buffer.text
            if not t.strip() or self.is_complete(t):
                e.app.exit(result=t)
            else:
                e.current_buffer.insert_text("\n")
        @kb.add(Keys.Tab)
        def _(e):
            e.current_buffer.insert_text("    ")
        @kb.add(Keys.Up)
        def _(e):
            b = e.current_buffer
            if b.document.cursor_position_row == 0:
                history_strings = list(history.get_strings())
                if history_strings and history_index[0] < len(history_strings):
                    history_index[0] += 1
                    b.text = history_strings[-history_index[0]]
                    b.cursor_position = 0
        @kb.add(Keys.Down)
        def _(e):
            b = e.current_buffer
            if b.document.cursor_position_row == b.document.line_count - 1:
                history_strings = list(history.get_strings())
                if history_index[0] > 0:
                    history_index[0] -= 1
                    if history_index[0] == 0:
                        b.text = ""
                    else:
                        b.text = history_strings[-history_index[0]]
                    b.cursor_position = 0
        @kb.add("c-j")
        def _(e):
            e.current_buffer.insert_text("\n")
        history = InMemoryHistory()
        history_index = [0]
        buffer = Buffer(multiline=True, history=history)
        control = BufferControl(buffer=buffer)
        window = Window(content=control, get_line_prefix=self._get_line_prefix)
        layout = Layout(window)
        layout.focus(window)
        while True:
            try:
                app = Application(
                    layout=layout,
                    key_bindings=kb,
                    full_screen=False,
                    mouse_support=False
                )
                text = app.run()
            except (EOFError, KeyboardInterrupt):
                break
            if text and text.strip():
                self.push(text)
                history.append_string(text)
            buffer.reset()
        if exitmsg: print(exitmsg)


class InlineCalculator(MultiLineConsole):
    NAMEX = "namex" # 试图用UniTex渲染'namex'字符串时使用的结果
    BANNER = "Inline Calculator (like IDLE). \nTry 'help()' for help, EOF to exit."

    def __init__(self):
        super().__init__()
        self._scipy_imported = False
        self.buffer = [] # don't set this when using code.InteractiveConsole

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
            'threading.Thread(target=lambda:exec("from why import whyRunner as why",globals()),daemon=True).start()',

            ('sci='
             'lambda:exec("'
             'import scipy\\n'
             'from scipy.constants import *\\n'
             'from scipy.stats import linregress, norm, chi2\\n'
             'from scipy.optimize import minimize, curve_fit\\n'
             'from scipy.interpolate import interp1d, CubicSpline\\n'
             'from scipy.integrate import quad, solve_ivp, RK45, BDF, odeint\\n'
             'del sci'
             '",globals())'
             '') if self.has_lib("scipy") else '',
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
            with open(SETTINGS.paths.namexfilepath, 'r', encoding='utf-8') as f:
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

    def _post_push(self, line):
        # print('[Debug] Executing line:', line)
        ret = super().push(line)
        if not self._scipy_imported and 'scipy' in sys.modules:
            self._scipy_imported = True
            print("Warning: KeyboardInterrupt collapses the program once scipy is imported.")
        return ret

    def is_complete(self, text):
        if text.startswith('%') or text.startswith('!') or text.startswith('$') or text.startswith('?'):
            return True
        return super().is_complete(text)

    def push(self, line:str):
        if not self.buffer:
            if line.startswith('%') or line.startswith('!'):
                ret = os.system(line[1:])
                return self._post_push(f"_ = {ret}")
            if line.startswith('$'):
                if line.startswith('$$'):
                    expr=line[2:]
                    if expr=='namex':
                        expr=self.NAMEX
                    return self._post_push(f'copy(_:=unitex({expr!r}));_')
                else:
                    expr=line[1:]
                    if expr=='namex':
                        expr=self.NAMEX
                    return self._post_push(f'unitex({expr!r})')
            if line.startswith('?'):
                expr = line[1:].strip()
                if not expr:
                    print("New features:\n- Prefix '$' to evaluate UniTex expression.\n- Prefix '$$' to copy UniTex expression to clipboard.\n- Prefix '%' or '!' to run shell commands.\n- Use copy() and paste() to interact with clipboard. \nFor more information, use help().")
                    return False
                else:
                    if all(c=='?' for c in expr):
                        # easter egg
                        import random
                        if expr=='??':
                            print('そんなことに何の意味があるんですか？')
                        else:
                            print(''.join(random.choice('???¿')*random.randint(10,60) for _ in expr))
                    elif expr[0]=='?':
                        while expr[0]=='?':
                            expr=expr[1:]
                        return self._post_push(f"help({expr})")
                    else:
                        if expr in self.locals:
                            return self._post_push(f"help({expr})")
                        else:
                            return self._post_push(f"help({repr(expr)})")
                return False
        return self._post_push(line)


if __name__ == "__main__":
    calc = InlineCalculator()
    calc.interact(banner=InlineCalculator.BANNER)
