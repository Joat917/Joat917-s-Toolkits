"""
用于读取data.dat.xz中有关每日行为安排的信息。
ByteStream提供简单的字节流对象，其中不包含任何类型检查。
CompressedData包装了一种特殊的打包压缩格式，可以通过其extract方法输出为普通文件。
    （Todo：使用tarfile重写此对象以提高兼容性）
LogInfo提供了某一条记录的中间格式。
LogFile提供了一种LogInfo的存储方式，按月份存储和按日期查删记录。
SchdEvent表示一个事件，可以与LogInfo对象相互转化。包含起始时间（日期）、持续时间、类型、标签、备注说明。
TimeLine从起始时间前一个月开始到终止时间的本月，搜索满足条件的目标事件。
"""

import random
import lzma
import os
import time
import datetime
import enum
import json
from itertools import chain
import bisect


class ByteStream:
    "字节流，不做类型检查"

    def __init__(self, src=b""):
        self.data = src

    def peek(self, count=1):
        return self.data[:count]

    def get(self, count=1):
        o, self.data = self.data[:count], self.data[count:]
        return o

    def push(self, cont=b''):
        self.data += cont
        return cont

    def getall(self):
        o = self.data
        self.data = b''
        return o

    def __len__(self):
        return len(self.data)

    def isEmpty(self):
        return len(self.data) == 0


class CompressedData:
    "压缩并存储一系列文件。"

    def __init__(self, fp) -> None:
        self.fp = fp
        if not os.path.exists(fp):
            self.contents = {}
            self.appendix = b''
        else:
            with open(fp, 'rb') as file:
                cnt = ByteStream(lzma.decompress(file.read(), lzma.FORMAT_XZ))
            if not cnt.get(4) == b'SCD\x00':
                raise RuntimeError("Data file with incorrect head")
            count = int.from_bytes(cnt.get(4), 'little')
            name_lengths = []
            for _ in range(count):
                name_lengths.append(int.from_bytes(cnt.get(4), 'little'))
            file_lengths = []
            for _ in range(count):
                file_lengths.append(int.from_bytes(cnt.get(4), 'little'))
            names = []
            for name_length in name_lengths:
                names.append(cnt.get(name_length).decode('utf-8'))
            self.contents = {}
            for name, file_length in zip(names, file_lengths):
                if name not in self.contents:
                    self.contents[name] = cnt.get(file_length)
                else:
                    raise RuntimeError(
                        "Data file with repeated name: {}".format(name))
            self.appendix = cnt.getall()
        self.saved = True
        return

    def save(self):
        data = b'SCD\x00'
        names_bytes = []
        contents = []
        count = 0
        for name, cont in self.contents.items():
            names_bytes.append(name.encode('utf-8'))
            contents.append(cont)
            count += 1
        name_lengths = list(map(len, names_bytes))
        file_lengths = list(map(len, contents))
        data += count.to_bytes(4, 'little')
        for name_length in name_lengths:
            data += name_length.to_bytes(4, 'little')
        for file_length in file_lengths:
            data += file_length.to_bytes(4, 'little')
        for name_byte in names_bytes:
            data += name_byte
        for cont in contents:
            data += cont
        data += self.appendix
        encoded_data = lzma.compress(data, lzma.FORMAT_XZ)
        with open(self.fp, 'wb') as file:
            o = file.write(encoded_data)
            self.saved = True
            return o

    def get(self, name: str):
        try:
            return self.contents[name]
        except KeyError:
            return b''

    def set(self, name: str, content: bytes, non_overlap=True):
        if non_overlap and name in self.contents:
            raise ValueError("name ({}) already exists".format(name))
        if not isinstance(name, str):
            raise TypeError('parameter name must be a string')
        if not isinstance(content, bytes):
            raise TypeError('parameter content must be bytes')
        if len(content) == 0:
            if not non_overlap and name in self.contents:
                self.contents.pop(name)
        else:
            self.contents[name] = content
        self.saved = False

    def add(self, name: str, addition: bytes):
        if not isinstance(name, str):
            raise TypeError('parameter name must be a string')
        if not isinstance(addition, bytes):
            raise TypeError('parameter content must be bytes')
        if len(addition) != 0:
            # self.contents[name] = self.contents.get(name, b'')+addition
            try:
                self.contents[name] += addition
            except KeyError:
                self.contents[name] = addition
            self.saved = False

    def extract(self, target='./sch0_ext/'):
        for name, content in self.contents.items():
            with open(os.path.abspath(os.path.join(target, name)), 'wb') as file:
                file.write(content)


def testfor(a, b):
    if a != b:
        raise ValueError(
            "{} should be {}, but it doesn't.".format(repr(a), repr(b)))


class LogInfo:
    "最基本的事件对象，包含时间和内容。"

    def __init__(self, dt: datetime.datetime, content: str):
        if not isinstance(dt, datetime.datetime) or not isinstance(content, str):
            raise TypeError
        if '\n' in content:
            raise ValueError("line breakers should not exist in log content")
        self.dt = dt
        self.content = content

    @staticmethod
    def fromstr(linetext: str):
        if '\n' in linetext:
            raise ValueError("line breakers should not exist")
        stream = ByteStream(linetext)
        year = int(stream.get(4))
        testfor(stream.get(1), '-')
        month = int(stream.get(2))
        testfor(stream.get(1), '-')
        day = int(stream.get(2))
        testfor(stream.get(1), '-')
        hour = int(stream.get(2))
        testfor(stream.get(1), ':')
        minute = int(stream.get(2))
        testfor(stream.get(1), ':')
        second = int(stream.get(2))
        testfor(stream.get(1), '-')
        dt = datetime.datetime(
            year=year, month=month, day=day,
            hour=hour, minute=minute, second=second)
        cont = stream.getall()
        return LogInfo(dt, cont)

    def __str__(self):
        return '%04d-%02d-%02d-%02d:%02d:%02d-' % (
            self.dt.year, self.dt.month, self.dt.day,
            self.dt.hour, self.dt.minute, self.dt.second)\
            + self.content

    def __repr__(self):
        return 'LogInfo({},{})'.format(repr(self.dt), repr(self.content))

    @staticmethod
    def str2dt(s: str, allow_leftover=False):
        stream = ByteStream(s)
        year = int(stream.get(4))
        testfor(stream.get(1), '-')
        month = int(stream.get(2))
        testfor(stream.get(1), '-')
        day = int(stream.get(2))
        testfor(stream.get(1), '-')
        hour = int(stream.get(2))
        testfor(stream.get(1), ':')
        minute = int(stream.get(2))
        testfor(stream.get(1), ':')
        second = int(stream.get(2))
        if not allow_leftover and not stream.isEmpty():
            raise ValueError("str2datetime: leftover not empty")
        return datetime.datetime(
            year=year, month=month, day=day,
            hour=hour, minute=minute, second=second)

    @staticmethod
    def dt2str(dt: datetime.datetime):
        return '%04d-%02d-%02d-%02d:%02d:%02d' % (
            dt.year, dt.month, dt.day,
            dt.hour, dt.minute, dt.second)


class LogFile(CompressedData):
    "对一系列事件的打包存储"

    def getLogsD(self, date: datetime.date):
        "get all logs in a single day"
        file_name = '%04d-%02d.log' % (date.year, date.month)
        contents = self.get(file_name).decode('utf-8')
        outputs = []
        for line in contents.splitlines():
            try:
                loginfo = LogInfo.fromstr(line)
                if loginfo.dt.year == date.year and loginfo.dt.month == date.month and loginfo.dt.day == date.day:
                    outputs.append(loginfo)
            except Exception:
                pass
        return outputs

    def getLogsM(self, year: int, month: int):
        "get all logs in one month"
        if not isinstance(year, int) or not isinstance(month, int):
            raise TypeError
        file_name = '%04d-%02d.log' % (year, month)
        contents = self.get(file_name).decode('utf-8')
        outputs = []
        for line in contents.splitlines():
            try:
                loginfo = LogInfo.fromstr(line)
                if loginfo.dt.year == year and loginfo.dt.month == month:
                    outputs.append(loginfo)
            except Exception:
                pass
        return outputs

    def getLogsA(self):
        "get all possible logs"
        outputs = []
        for name in self.contents:
            try:
                year = int(name[:4])
                assert name[4] == '-'
                month = int(name[5:7])
                assert name[7:] == '.log'
                outputs += self.getLogsM(year, month)
            except Exception:
                pass
        return outputs

    def setLogsD(self, date: datetime.date, new_logs: list):
        "modify all logs in a single day"
        file_name = '%04d-%02d.log' % (date.year, date.month)
        loglines = []
        old_logs = []
        for loginfo in self.getLogsM(date.year, date.month):
            assert loginfo.dt.year == date.year and loginfo.dt.month == date.month
            if loginfo.dt.day != date.day:
                old_logs.append(loginfo)
        for log in old_logs+new_logs:
            s = str(log)
            assert '\n' not in s
            loglines.append(s)
        contents = '\n'.join(loglines)
        self.set(file_name, contents.encode('utf-8'), False)

    def setLogsM(self, year: int, month: int, new_logs: list):
        "get all logs in one month"
        file_name = '%04d-%02d.log' % (year, month)
        loglines = []
        for log in new_logs:
            assert log.dt.year == year and log.dt.month == month
            s = str(log)
            assert '\n' not in s
            loglines.append(s)
        contents = '\n'.join(loglines)
        self.set(file_name, contents.encode('utf-8'), False)

    def addLog(self, loginfo: LogInfo):
        file_name = '%04d-%02d.log' % (loginfo.dt.year, loginfo.dt.month)
        if file_name in self.contents:
            self.add(file_name, ('\n'+str(loginfo)).encode('utf-8'))
        else:
            self.set(file_name, str(loginfo).encode('utf-8'), non_overlap=True)

    def removeLog(self, loginfo: LogInfo):
        file_name = '%04d-%02d.log' % (loginfo.dt.year, loginfo.dt.month)
        content = self.get(file_name).decode('utf-8')
        lines = content.splitlines()
        # lines=list(filter(lines))
        lines.remove(str(loginfo))
        self.set(file_name, ('\n'.join(lines)).encode('utf-8'), False)


def randomString(n: int):
    "给定长度的随机ASCII字符串"
    return ''.join(map(chr, [random.randint(32, 126) for _ in range(n)]))


@enum.unique
class EventType(enum.Enum):
    SLEEP = 1
    MEAL = 2
    CLASS = 3
    HOMEWORK = 4
    SPORTS = 5
    DORMWORK = 6
    GAME = 7
    UNALLOCATED = 0


@enum.unique
class LabelType(enum.Enum):
    MORN_EIGHT = '早八'
    MORN_SIX = '早六'
    EVE_TEN = '晚十'
    EVE_ELEVEN = '晚十一'
    EVE_TWELVE = '守夜'
    EVE_THREE = '凌晨三点'
    BREAKFAST = '早饭'
    BATH = '洗澡'
    MAKETEA = '泡茶'
    PLAYGROUND = '操场'


eventTypeTranslator = {
    'SLEEP': '睡觉',
    'MEAL': '吃饭',
    'CLASS': '上课',
    'HOMEWORK': '作业',
    'SPORTS': '运动',
    'DORMWORK': '寝务',
    'GAME': '游戏',
    'UNALLOCATED': '???'
}


def event2color(ev):
    match ev:
        case EventType.SLEEP:
            return 0x88, 0x22, 0xff
        case EventType.MEAL:
            return 0xff, 0x99, 0
        case EventType.CLASS:
            return 0xff, 0x55, 0x55
        case EventType.HOMEWORK:
            return 0x55, 0x55, 0xff
        case EventType.SPORTS:
            return 0x88, 0xee, 0
        case EventType.DORMWORK:
            return 0, 0xee, 0xee
        case EventType.GAME:
            return 0, 0x99, 0xff
        case EventType.UNALLOCATED:
            return 0x99, 0x99, 0x99
        case _:
            raise ValueError


def label2color(lb):
    match lb:
        case LabelType.MORN_EIGHT:
            return 0xff, 0xcc, 0x11
        case LabelType.MORN_SIX:
            return 0xff, 0x99, 0x44
        case LabelType.EVE_TEN:
            return 0x99, 0xdd, 0xee
        case LabelType.EVE_ELEVEN:
            return 0, 0xaa, 0xff
        case LabelType.EVE_TWELVE:
            return 0xaa, 0xbb, 0xdd
        case LabelType.EVE_THREE:
            return 0xcc, 0x88, 0xcc
        case LabelType.BREAKFAST:
            return 0xee, 0xee, 0xaa
        case LabelType.BATH:
            return 0xff, 0xaa, 0xcc
        case LabelType.MAKETEA:
            return 0xbb, 0xee, 0x22
        case LabelType.PLAYGROUND:
            return 0x44, 0xdd, 0x77
        case _:
            raise ValueError


def showObj(obj):
    "打印某一个对象的所有属性和方法"
    print('Properties of', repr(obj), ':')
    for key in dir(obj):
        if key[0] != '_':
            print(key, '=', repr(getattr(obj, key)))


class SchdEvent:
    "更加详细的事件对象。可以和LogInfo相互转化，进而存储。"

    def __init__(self, dt_start, dt_end, typ, labl, ps) -> None:
        if isinstance(dt_start, datetime.datetime):
            self.dt_start = dt_start
        elif isinstance(dt_start, str):
            self.dt_start = LogInfo.str2dt(dt_start)
        elif isinstance(dt_start, (int, float)):
            self.dt_start = datetime.datetime.fromtimestamp(dt_start)
        else:
            raise TypeError("argument dt_start must be datetime")
        if isinstance(dt_end, datetime.datetime):
            self.dt_end = dt_end
        elif isinstance(dt_end, str):
            self.dt_end = LogInfo.str2dt(dt_end)
        elif isinstance(dt_end, (int, float)):
            self.dt_end = datetime.datetime.fromtimestamp(dt_end)
        else:
            raise TypeError("argument dt_end must be datetime")
        if self.dt_end <= self.dt_start:
            raise ValueError("dt_start must be earlier than dt_end")
        self.dt_duration = self.dt_end-self.dt_start
        if isinstance(typ, EventType):
            self.typ = typ
        else:
            raise TypeError("argument typ must be EventType")
        try:
            self.labl: frozenset[LabelType]
        except SyntaxError:
            pass
        _labl = []
        for _l in labl:
            if isinstance(_l, LabelType):
                _labl.append(_l)
            else:
                raise ValueError("element of argument labl must be LabelType")
        self.labl = frozenset(_labl)
        if isinstance(ps, str):
            self.ps = ps
        else:
            raise TypeError("argument ps must be string")

    def toLogInfo(self):
        l = []
        l.append(LogInfo.dt2str(self.dt_end))
        l.append(self.typ.name)
        l.append([_t.name for _t in self.labl])
        l.append(self.ps)
        return LogInfo(self.dt_start, json.dumps(l))

    @staticmethod
    def fromLogInfo(li: LogInfo):
        dt_start = li.dt
        inforia = json.loads(li.content)
        dt_end = LogInfo.str2dt(inforia[0])
        typ = EventType._member_map_[inforia[1]]
        labl = [LabelType._member_map_[_n] for _n in inforia[2]]
        ps = inforia[3]
        return SchdEvent(dt_start=dt_start, dt_end=dt_end,
                         typ=typ, labl=labl, ps=ps)

    def __eq__(self, other):
        return isinstance(other, SchdEvent) and \
            other.dt_start == self.dt_start and other.dt_end == self.dt_end \
            and other.typ == self.typ and other.labl == self.labl \
            and other.ps == self.ps

    def __hash__(self) -> int:
        return hash(self.dt_start)+hash(self.dt_end)+hash(self.typ)+hash(self.ps)+hash(self.labl)


class Inverse:
    "比较伪函数，把比较结果反过来。负号的平替。"

    def __init__(self, data):
        self.data = data

    def __lt__(self, other):
        if isinstance(other, Inverse):
            return self.data > other.data
        else:
            return self.data > other

    def __gt__(self, other):
        if isinstance(other, Inverse):
            return self.data < other.data
        else:
            return self.data < other


class TimeLine:
    "时间线对象。把事件打包在一个一维时间轴上显示。"

    def __init__(self, dt_start, dt_end, logfile: LogFile):
        if isinstance(dt_start, datetime.datetime):
            self.dt_start = dt_start
        elif isinstance(dt_start, str):
            self.dt_start = LogInfo.str2dt(dt_start)
        elif isinstance(dt_start, (int, float)):
            self.dt_start = datetime.datetime.fromtimestamp(dt_start)
        else:
            raise TypeError
        if isinstance(dt_end, datetime.datetime):
            self.dt_end = dt_end
        elif isinstance(dt_end, str):
            self.dt_end = LogInfo.str2dt(dt_end)
        elif isinstance(dt_end, (int, float)):
            self.dt_end = datetime.datetime.fromtimestamp(dt_end)
        else:
            raise TypeError
        if self.dt_end <= self.dt_start:
            raise ValueError
        self.dt_duration = self.dt_end-self.dt_start
        self.logfile = logfile
        self.schdEvents = []
        yms = self.getYearMonths(
            (dt_start.year, dt_start.month), (dt_end.year, dt_end.month))
        for ym in chain(yms):
            for ev in self.logfile.getLogsM(*ym):
                # ev:LogInfo
                if ev.dt < self.dt_end:
                    sce = SchdEvent.fromLogInfo(ev)
                    if sce.dt_end > self.dt_start:
                        self.schdEvents.append(sce)
        return

    @staticmethod
    def getYearMonths(ym_start, ym_end):
        assert ym_start <= ym_end

        def ad1(ym):
            if ym[1] >= 12:
                return ym[0]+1, 1
            else:
                return ym[0], ym[1]+1

        def st1(ym):
            if ym[1] <= 1:
                return ym[0]-1, 12
            else:
                return ym[0], ym[1]-1
        o = []
        i = st1(ym_start)
        while i <= ym_end:
            o.append(i)
            i = ad1(i)
        return o

    def getTimeLine(self):
        self.schdEvents: list[SchdEvent]
        scE = sorted(self.schdEvents, key=lambda sc: (
            -sc.typ.value, Inverse(sc.dt_start), sc.dt_end))
        t = []  # ordered list: (start, end, target), non-overlap

        def delap(start_dt, end_dt):
            "给定一个时间区间，去除其中已经被占用的区间，返回剩余部分"
            o = []
            for _start, _end, _ in t:
                if _end >= end_dt:
                    if _start <= start_dt:
                        return o
                    elif _start >= end_dt:
                        o.append((start_dt, end_dt))
                        return o
                    else:
                        o.append((start_dt, _start))
                        return o
                elif _end <= start_dt:
                    continue
                elif _start <= start_dt:
                    start_dt = _end
                else:
                    o.append((start_dt, _start))
                    start_dt = _end
            if start_dt < end_dt:
                o.append((start_dt, end_dt))
            return o

        # 插入事件
        for event in scE:
            for _start, _end in delap(
                    max(self.dt_start, event.dt_start),
                    min(self.dt_end, event.dt_end)):
                bisect.insort(t, (_start, _end, event))

        # 把未被利用的区间设为Unallocated
        if not t:
            t.append((self.dt_start, self.dt_end, None))
        else:
            if t[0][0] > self.dt_start:
                t.insert(0, (self.dt_start, t[0][0], None))
                i = 2
            else:
                i = 1
            while i < len(t):
                if t[i][0] > t[i-1][1]:
                    t.insert(i, (t[i-1][1], t[i][0], None))
                    i += 2
                else:
                    i += 1
            if t[-1][1] < self.dt_end:
                t.append((t[-1][1], self.dt_end, None))
        return t
