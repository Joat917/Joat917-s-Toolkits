import tkinter as tk
from time import sleep
from copy import deepcopy
from point24lib2 import find_solutions

class InputWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Input Window")
        self.text0 = tk.Label(
            self.window, text="Input four positive numbers: ")
        self.text0.grid(column=0, row=0)
        self.entry1 = tk.Entry(self.window)
        self.entry1.grid(column=0, row=1)
        self.entry2 = tk.Entry(self.window)
        self.entry2.grid(column=0, row=2)
        self.entry3 = tk.Entry(self.window)
        self.entry3.grid(column=0, row=3)
        self.entry4 = tk.Entry(self.window)
        self.entry4.grid(column=0, row=4)
        self.button = tk.Button(
            self.window, text="Calculate", command=calculate)
        self.button.grid(column=0, row=5)
        self.window.update()

    def getinput(self):
        global a, b, c, d
        try:
            a = abs(int(eval(self.entry1.get())))
            b = abs(int(eval(self.entry2.get())))
            c = abs(int(eval(self.entry3.get())))
            d = abs(int(eval(self.entry4.get())))
            return 1
        except Exception as exc:
            import traceback
            error_popup(traceback.format_exc())
            return 0


def error_popup(exc):
    errwin = tk.Tk()
    errwin.title("Error! ")
    errtext = tk.Label(errwin, text=str(exc))
    errtext.grid(column=0, row=0)
    errbutton = tk.Button(errwin, text="Accept", command=errwin.destroy)
    errbutton.grid(column=0, row=1)
    errwin.update()


def calculate():
    ret = inp.getinput()
    if not ret:
        return
    window = tk.Tk()
    window.title("Output Window")
    text0 = tk.Label(
        window, text="(%i), (%i), (%i), (%i) -> 24" % (a, b, c, d))
    text0.grid(column=0, row=0)
    try:
        solutions = list(find_solutions([a, b, c, d], 24, simpilified=True))
    except Exception as exc:
        import traceback
        error_popup(traceback.format_exc())
        return
    if not solutions:
        text_string = "No solution"
    else:
        LENGTH_PER_SOLUTION = 17
        SOLUTIONS_PER_LINE = 6
        text_string = '\n'.join('\t'.join(
            str(sol).ljust(LENGTH_PER_SOLUTION) 
            for sol in solutions[i:i+SOLUTIONS_PER_LINE]
        ) for i in range(0, len(solutions), SOLUTIONS_PER_LINE))

    text1 = tk.Label(window, text=text_string)
    text1.grid(column=0, row=1)

    button = tk.Button(window, text="Accept", command=window.destroy)
    button.grid(column=0, row=2)
    window.update()


if __name__ == "__main__":
    inp = InputWindow()
    tk.mainloop()
