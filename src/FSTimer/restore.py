def restore_v2(content: bytes):
    OFFSET = 1689153536
    if content[:4] != b'FST\x02':
        raise RuntimeError("Invalid file type")
    content = content[4:]
    # 还原i2和i3
    l3 = content[0]
    content = content[1:]
    i3 = int.from_bytes(content[:l3], 'big')
    i2 = int.from_bytes(content[l3:], 'big')

    # 提取出i2(十二进制)和i3(三进制)
    dc2 = '0123456789.,'
    tx2 = ''
    while i2:
        tx2 = dc2[i2 % 12]+tx2
        i2 //= 12

    ls3 = []
    while i3:
        ls3.insert(0, i3 % 3)
        i3 //= 3

    # 还原ls2
    ls2 = eval(f"[{tx2}]")

    # ls3的开头很有可能是0，因此需要补0
    while len(ls2)-len(ls3) > 1:
        ls3.insert(0, 0)

    # 还原tm和ls
    tm = ls2[0]+OFFSET
    ls = [(0, 0, 0)]
    for i in range(len(ls2)-1):
        ls.append((ls[-1][0]+ls2[i+1], ls2[i+1], ls3[i]))

    # 还原原文件
    return str([tm, ls])


from filepathpatch import DataPath

# 打开目标文件
while True:
    filename = input("Write your source file name:")
    try:
        open(DataPath/filename, "rb")
        break
    except FileNotFoundError:
        print("file not found!")
    except Exception as e:
        print(e)

with open(DataPath/filename, "rb") as file:
    byte0 = file.read()
try:
    content = restore_v2(byte0)
except Exception as e:
    __import__("traceback").print_exc()
    input()

# 打开目标文件
_obtain_filename = False
filename = "TimerRecord.txt"
try:
    open(DataPath/filename, "rb").close()
    _obtain_filename = True
except FileNotFoundError:
    _obtain_filename = False
except Exception as e:
    _obtain_filename = True
while _obtain_filename:
    filename = input("Write your target file name:")
    if len(filename) < 4 or filename[-4:] != ".txt":
        filename += ".txt"
    try:
        open(DataPath/filename, "rb")
        print("file exists!")
    except FileNotFoundError:
        break
    except Exception as e:
        print(e)

with open(DataPath/filename, "w") as file:
    file.write(content)
