import tkinter as tk
from time import sleep
from copy import deepcopy

# tkinter


class Inp:
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
            raiseerror(exc)
            return 0


def raiseerror(exc):
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
    go()

    text1 = tk.Label(window, text=output_to_text(out))
    text1.grid(column=0, row=1)

    button = tk.Button(window, text="Accept", command=window.destroy)
    button.grid(column=0, row=2)
    window.update()


def output_to_text(out):
    if not out:
        return "No solution"
    t = 0
    L = 6
    M = 17
    output = ""
    out = [str(i)+" "*(M-len(str(i))) for i in out]
    while out[L*t: L*t+L]:
        output += "\t".join(out[L*t: L*t+L])
        output += "\n"
        t += 1
    return output

# logics


priority = {'+-*/'[i]: [1, 1, 2, 2][i] for i in range(4)}


class Tree:
    def __init__(self, left=None, right=None) -> None:
        self.operator = None
        self.left = deepcopy(left)
        self.right = deepcopy(right)
        self.number = None

    def __eq__(self, other: object) -> bool:
        if other is None:
            # print(f"Warning: to tell tree({self})==None")
            return False
        return self.left == other.left\
            and self.right == other.right\
            and self.operator == other.operator\
            and self.number == other.number

    def post(self, operator: str) -> bool:
        if self.left is not None and self.left.post(operator):
            return True
        if self.right is not None and self.right.post(operator):
            return True
        if self.operator is None:
            self.operator = operator
            return True
        else:
            return False

    def fill(self, number: int) -> bool:
        if self.left is None:
            self.left = EndPoint(number)
            return True
        else:
            if self.left.fill(number):
                return True
        if self.right is None:
            self.right = EndPoint(number)
            return True
        else:
            if self.right.fill(number):
                return True
        return False

    def value(self):
        if self.left is None or self.right is None or self.operator is None:
            raise ValueError
        else:
            return eval(f"{self.left.value()}"+self.operator+f"{self.right.value()}")

    def __str__(self) -> str:
        if type(self.left) is Tree:
            if priority[self.left.operator] >= priority[self.operator]:
                leftstr = str(self.left)
            else:
                leftstr = "("+str(self.left)+")"
        else:
            leftstr = str(self.left)

        if type(self.right) is Tree:
            if priority[self.right.operator] > priority[self.operator]:
                rightstr = str(self.right)
            else:
                rightstr = "("+str(self.right)+")"
        else:
            rightstr = str(self.right)

        out = leftstr+str(self.operator)+rightstr
        return out


class EndPoint:
    def __init__(self, number: int) -> None:
        self.number = number
        self.left = None
        self.right = None
        self.operator = None

    def __eq__(self, other: object) -> bool:
        if other is None:
            # print(f"Warning: to tell endpoint({self})==None")
            return False
        return self.left == other.left\
            and self.right == other.right\
            and self.operator == other.operator\
            and self.number == other.number

    def post(self, operator: str) -> bool:
        return False

    def fill(self, number: int) -> bool:
        return False

    def value(self):
        return self.number

    def __str__(self) -> str:
        return str(self.number)


def fullarrange(*obj):
    if len(obj) == 0:
        return []
    elif len(obj) == 1:
        return [[obj[0]]]

    prev = fullarrange(*(list(obj)[1:]))
    ins = obj[0]
    out = []

    for lis in prev:
        for i in range(len(obj)):
            temp = deepcopy(lis)
            temp.insert(i, ins)
            if temp not in out:
                out.append(temp)

    return out


def fullpick(num=3, *objs) -> list:
    if num == 0:
        return []
    elif num == 1:
        return [[i] for i in objs]
    else:
        prev = fullpick(num-1, *objs)
        return [[i]+case for i in objs for case in prev]


FullTrees = {}


def fulltrees(num=3) -> list:
    if num in FullTrees:
        return FullTrees[num]
    if num == 0:
        return [None]
    elif num == 1:
        FullTrees[1] = [Tree()]
        return [Tree()]

    out = []
    for i in range(num):
        j = num-1-i
        for left in fulltrees(i):
            for right in fulltrees(j):
                out.append(Tree(left, right))

    FullTrees[num] = out

    return out


def isStandard(tree) -> bool:
    if type(tree) is EndPoint:
        return True
    if tree.left is not None:
        if not isStandard(tree.left):
            return False
    if tree.right is not None:
        if not isStandard(tree.right):
            return False

    if tree.operator in ['+', '*']:
        if type(tree.left) is EndPoint\
                and type(tree.right) is EndPoint:
            if tree.left.number <= tree.right.number:
                pass
            else:
                return False

    if tree.operator in ['+', '-']:
        if tree.right.operator is not None:
            if tree.right.operator in ["+", '-']:
                return False

    elif tree.operator in ['*', '/']:
        if tree.right.operator is not None:
            if tree.right.operator in ["*", '/']:
                return False

    # (a+b)+c
    if tree.operator in ['+', '*'] and type(tree.right) is EndPoint:
        if type(tree.left) is Tree and tree.left.operator == tree.operator:
            if not tree.left.right.number < tree.right.number:
                return False

    return True


def go():
    global out
    altree = fulltrees()
    alnum = fullarrange(a, b, c, d)
    aloperator = fullpick(3, *'+-*/')
    out = []

    for tree in altree:
        for nums in alnum:

            temp1 = deepcopy(tree)
            for num in nums:
                temp1.fill(num)
            for operators in aloperator:

                temp2 = deepcopy(temp1)
                for operator in operators:
                    temp2.post(operator)
                try:
                    # if temp2.value() == 24:
                    if eval(str(temp2)) == 24:
                        to_add = True
                        for i in out:
                            if i == temp2:
                                to_add = False
                                break
                        if to_add:
                            out.append(temp2)
                except:
                    pass

    i = 0
    while i < len(out):
        tree = out[i]
        if not isStandard(tree):
            out.remove(tree)
        else:
            i += 1


def attack(a, b, c, d):
    altree = fulltrees()
    alnum = fullarrange(a, b, c, d)
    aloperator = fullpick(3, *'+-*/')
    out = []

    for tree in altree:
        for nums in alnum:

            temp1 = deepcopy(tree)
            for num in nums:
                temp1.fill(num)
            for operators in aloperator:

                temp2 = deepcopy(temp1)
                for operator in operators:
                    temp2.post(operator)
                try:
                    # if temp2.value() == 24:
                    if eval(str(temp2)) == 24:
                        to_add = True
                        for i in out:
                            if i == temp2:
                                to_add = False
                                break
                        if to_add:
                            out.append(temp2)
                except:
                    pass

    i = 0
    while i < len(out):
        tree = out[i]
        if not isStandard(tree):
            out.remove(tree)
        else:
            i += 1

    return ([str(i) for i in out])


if __name__ == "__main__":
    inp = Inp()
    tk.mainloop()
