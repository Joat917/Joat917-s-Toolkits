"""
新版本的计时记录文件和老版本不兼容。
格式：(F)(S)(T)(0x02,version)-(l3)-(b3+)-(b2+)
"""


def deflate_v2(content):
    tm, ls = eval(content)  # tm是起始时间，ls是计时详情，[(累计时间，间隔时间，类型)]
    OFFSET = 1689153536  # 只用4位保存时间，但是减去这个数字。不会是负数。
    tm = round(tm-OFFSET, 2)
    ls = ls[1:]  # 丢掉最开始的[(0,0,0)]

    ls2 = [tm]  # ls2是包含所有浮点数据的列表。
    ls3 = []  # ls3是包含所有状态有关的数据的列表。
    for tup in ls:
        ls2.append(round(tup[1], 2))  # 只记录间隔时间，不记录累计时间。节省空间。
        ls3.append(tup[2])  # 记录状态。

    # 把ls2数据列表转化为文本tx2
    tx2 = ""
    for num in ls2:
        if type(num) == float and str(num)[:2] == "0.":
            tx2 += str(num)[1:]  # 纯小数不存储最开头的0
        else:
            tx2 += str(num)
        tx2 += ","
    tx2 = tx2[:-1]  # 舍去最后的那个逗号

    # 字符替换：0~9->0~9; .->a; ,->b。使用十二进制进行数据存储。
    i2 = tx2.replace('.', 'a')
    i2 = i2.replace(',', 'b')
    i2 = int(i2, 12)

    # 直接把l3中的所有数字连起来，使用3进制进行存储。
    i3 = ''.join([str(j) for j in ls3])
    i3 = int(i3, 3)

    # 记录i2和i3的长度，其中i3最大不超过255bytes
    l3 = 0
    _i = i3+0
    while _i:
        _i >>= 8
        l3 += 1
    l2 = 0
    _i = i2+0
    while _i:
        _i >>= 8
        l2 += 1
    if l3 >= 256:
        raise RuntimeError("l3 too big to store")

    # 转换为字节
    b2 = i2.to_bytes(l2, 'big')
    b3 = i3.to_bytes(l3, 'big')

    return b'FST\x02'+l3.to_bytes(1, 'big')+b3+b2

from filepathpatch import DataPath

with open(DataPath/'TimerRecord.txt', 'r') as file:
    content = file.read()

outbyte = deflate_v2(content)
# 起名字
while True:
    filename = input("Write your Target(notSource) file name:")
    try:
        open(DataPath/filename, "rb")
        print("file already exist!")
    except FileNotFoundError:
        break
    except Exception as e:
        print(e)

with open(DataPath/filename, "wb") as file:
    file.write(outbyte)
