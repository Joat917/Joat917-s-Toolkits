"""
以二进制格式打开一个文件并以字节为单位给出其内容。
适合查看极大文件的前一小半部分。
"""

def show01(lst, prefix="  ", subcont=" "*16, end=''):
    "以标准格式显示一行自定义内容"
    if len(lst) != 16:
        raise ValueError("In show01: List length not 16 @ "+repr(lst))
    if not all(map(lambda c: type(c) == str, lst)):
        raise ValueError("In show01: Elements not all string @ "+repr(lst))
    if not all(map(lambda c: len(c) == 2, lst)):
        raise ValueError("In show01: Elements not all length 2 @ "+repr(lst))
    if not type(prefix) == str:
        raise ValueError("In show01: Prefix not string @ "+repr(prefix))
    if len(prefix) != 2:
        raise ValueError("In show01: Prefix not length 2 @ "+repr(prefix))
    if not type(subcont) == str:
        raise ValueError("In show01: Subcont not str @ "+repr(subcont))
    if len(subcont) != 16:
        raise ValueError("In show01: Subcont not length 16 @ "+repr(subcont))
    print(prefix+"| "+'  '.join(lst)+" |"+subcont+'|', end=end)


def showSep():
    "显示一行分割线"
    print("  |"+'-'*64+'|'+'-'*16+'|')


def lin2(i: int) -> str:
    "把正整数表示为二字符符号"
    if 0 <= i <= 9:
        return ' '+str(i)
    elif i <= 99:
        return str(i)
    elif i <= 359:
        return chr(i//10+55)+str(i % 10)
    else:
        return '?'+str(i % 10)


def showTit():
    "显示表头"
    show01([lin2(i) for i in range(16)], end='\n')


def hex1d(i):
    if i < 10:
        return chr(i+48)
    else:
        return chr(i+55)


def hex2d(i):
    return hex1d(i >> 4)+hex1d(i & 15)


def asciify(i):
    "尝试把给定整数显示为ascii字符"
    if 33 <= i <= 126:
        return chr(i)
    elif i == 32:
        return ' '#'␣'
    else:
        return ' '


def showLin(lbt, prefix):
    "显示16个字符"
    o = [hex2d(c) for c in lbt]
    q = ''.join(map(asciify, lbt))
    if len(o) < 16:
        q += ' '*(16-len(o))
        o += ['  ']*(16-len(o))
    show01(o, prefix, q)


def showCont(bts, sepCaller=input):
    "给定字节流，输出结果"
    showTit()
    showSep()
    i = 0
    i2 = 16
    while True:
        c = bts[i:i2]
        if not c:
            return
        showLin(c, lin2(i >> 4))
        i = i2
        i2 += 16
        sepCaller()


def showCont2(file, sepCaller=input):
    "给定文件流(通常非常大)，输出结果"
    showTit()
    showSep()
    i = 0
    while True:
        c = file.read(16)
        if not c:
            return
        showLin(c, lin2(i))
        i += 1
        sepCaller()


def main():
    while True:
        try:
            fp = input("fp:=")
            if not fp:
                continue
            if fp[0] == '"' and fp[-1] == '"':
                fp = fp[1:-1]
            with open(fp, 'rb') as file:
                print()
                showCont2(file)
                # ct = file.read()
            # showCont(ct)
        except Exception as exc:
            print("Exception:", exc)


if __name__ == "__main__":
    main()
