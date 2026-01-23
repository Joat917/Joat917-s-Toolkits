# SCDACH说明文档

SCDACH 全称是 schedule and achievements manager 。

---

## 目的

本项目目的有三：

1. 制作一个**好看的**事件管理器，每天复盘当日的时间分配；
2. 记录每天是否完成某些特殊任务（早八、早六、熄灯前睡觉等），并在**好看的**日历上显示出来；
3. 每周复盘当周的时间分配，并制作成**好看的**海报。

本项目由XQShia提出需求，并由本人一人写完全部代码和本说明文档。

---

## 使用

运行`mainmenu.py`，进入事件管理器或者在日历上查看特殊任务完成情况。

运行`posterer.py`，在控制台中选择达成的成就并输出为海报。


---

## 依赖

本项目使用Python语言和tkinter实现，并强制要求Python版本不低于3.10。此外需要以下第三方库：

```
openpyxl==3.1.2
borax==4.1.1
numpy==1.23.0
Pillow==10.0.1
pillow-heif==0.13.0
opencv-python==4.6.0.66
opencv-contrib-python==4.9.0.80
```

\**第三方库的版本仅供参考*

另外，本项目依赖tkinter在Windows系统中的某些特性函数，可能不能在其它操作系统上正确运行。

---

## 结构

本项目包含以下9个代码文件：

```
achmReader.py
calendarA.py
eventEditor.py
labelCalendar.py
mainmenu.py
posterer.py
schdReader.py
timesetter.py
tkwindow.py
```

以及以下3个数据文件

```
achievements.xlsx
logfile.dat.xz (optional)
readme.md
```

代码文件的依赖关系如下：

``` mermaid
graph TD
a(achmReader.py)
c(calendarA.py)
e(eventEditor.py)
l(labelCalendar.py)
m(mainmenu.py)
p(posterer.py)
s(schReader.py)
tm(timesetter.py)
tk(tkwindow.py)
s-->l
s-->e
tk-->c
tk-->e
tk-->tm
tm-->e
tk-->m
c-->l
e-->m
l-->m
a-->p
```

以下是这些文件的详细说明：

#### achmReader

该代码读取数据文件`achievements.xlsx`中的内容，并分类展示出来。

`(class)Achievement`：一个成就。包含“类别”、“名称”、“稀有度”、“描述”四个属性。

`(class)AchvmReader`：读取数据文件，并将结果存储在其`content`属性中。

#### posterer

该代码用于生成海报，暂未完成。

#### tkwindow

该代码实现了以下功能：

1. 定义了**好看的**tk窗口，按住**好看的**标题栏拖动窗口，并为该窗口配备**好看的**最小/大化按钮和**好看的**关闭按钮。
2. 定义了**好看的**按钮、**好看的**勾选框和**好看的**单选菜单。
3. 定义了**好看的**滚动条。
4. 实时监控对象的销毁，避免和减缓内存泄露。

包括如下11个类：

`(class)ColorUtils`：提供HSV和RGB色彩空间的相互转换，并提供了使颜色变暗的静态方法。这是抽象类，不能实例化。

`(class)TKWindow`：构造一个**好看的**tk窗口，可以容纳其它组件。在关闭时销毁包含其中的其它组件对象。

`(class)TKTray`：最小化的tk窗口，不能容纳任何其它组件。恢复原窗口或者关闭原窗口时销毁自己。

`(class)TKPrompt`：在屏幕下方产生**好看的**文本提示，一段时间后淡出并销毁自己。该类还提供了静态方法，把文本转化为透明背景的PIL图片。

`(class)TKButton`：构造一个**好看的**按钮。

`(class)TKCheckBox`：构造一个**好看的**勾选框。

`(class)TKMultiSelect`：构造一个**好看的**单选菜单。

`(class)WDPs`：收集所有组件和窗口的销毁信息，每隔1秒打印在控制台。

`(class)Scroller`：支持鼠标滚轮、包含**好看的**滑槽的**好看的**滚动条容器组件。

`(class)ScrollerControlBar`：一个**好看的**滚动条滑槽。

`(class)ScrollerWidget`：所有其它组件盛放到该容器中，该容器盛放在滚动条容器中并随之滚动。

#### calendarA

提供了公历转农历的办法，并制作日历。

包含以下3个函数和5个类：

`(function)get_lunar_info`：公历转农历。农历信息被存放在一个字典中。

`(function)get_lunar_info_calender`：公历转农历，并把所有信息整合在一个短字符串中以供日历显示。

`(function)zigzag`：一个数学意义上的函数。在输入达到lowest时取到0，达到highest时取到1，并以period为周期。

`(class)DateDisplay`：给定自己在网格中的位置，显示单个日期。

`(class)DatesDisplay`：给定年月，显示本月全部的日期。

`(class)WeekCaptionDisplay`：给定列号，显示本列的星期。

`(class)WeekCaptionDisplays`：显示全部星期。

`(class)MonthCaptionDisplays`：显示年月和改变年月的按钮组，同时构造日历中的其它全部组件。

#### schReader

定义了事件，同时实现了存取事件的文件管理器。

包含以下7个类：

`(class)ByteStream`：顺序取出和拼接字节串。本类在某些条件下可用于操作字符串。

`(class)CompressedData`：给定若干文件的文件名和文件内容（字节流对象），将这些文件打包压缩并存储为单个文件。当给定这种文件时，将其解压分离还原为原文件名和文件内容。

`(class)LogInfo`：最基本的事件对象，包含时间和内容。

`(class)LogFile`：对一系列LogInfo事件的打包压缩，打包时按月份分类。

`(class)SchdEvent`：更加详细的事件对象。可以和LogInfo相互转化，进而存储。

`(class)Inverse`：比较伪函数，适用于不支持负号的可比较对象。当objA小于objB时有Inverse(objA)大于Inverse(objB)，反之亦然。

`(class)TimeLine`：时间线对象。把大量事件平铺在一个一维时间轴上，并表示为一些首尾相接的线段。

2个枚举对象：

`(Enum)EventType`：事件类型。

`(Enum)LabelType`：标签类型，包含在事件中。

5个函数/字典：

`(const)eventTypeTranslator`：一个字典，包含事件类型对应的中文名称。

`(function)event2color`：记录事件类型对应的颜色。

`(function)label2color`：记录标签类型对应的颜色。

`(function)showObj`：打印某一个对象的所有属性和方法到控制台

`(function)testfor`：在输入参数不相等时报错。

#### timesetter

一个用于选取时间的组件。包含1个类：`(class)TimeSetter`

#### labelCalendar

读取事件的标签，并按照是否拥有标签给日历上色。

包含以下1个函数和2个类：

`(function)getDatesMon`：判断这个月里有哪些天达成了目标成就。

`(class)CalendarRenderer`：给定一个标签，弹出窗口显示达成该标签的日历。

`(class)CalendarStarter`：一个组件，按下其中的按钮能够弹出对应标签的日历。

#### eventEditor

不仅可视化，而且**好看的**事件编辑器。

包含以下5个类：

`(class)TimeLineButton` ：为时间线中一条首尾相接的线段提供可视化。时间线在schReader中定义。

`(class)TimeLineDisplay` ：显示一条时间线中所有首尾相接的线段。

`(class)LabelSelectorDisplay` ：一个组件，包含多个勾选框。用于挑选事件拥有的标签。

`(class)EventEditorDisplay` ：一个组件，包含一个滚动条，以及滚动条内所有的组件。提供向滚动条中添加和移除组件的方法。由于滚动条内组件和事件绑定，这相当于编辑事件管理器。如果在未保存时尝试删除该对象，会弹出窗口提示是否保存。

`(class)EventEditorWindow` ：一个窗口，包含日期显示和调整按钮、保存按钮和提取按钮、时间线显示、绑定事件的滚动条。

#### mainmenu

在根窗口中的主菜单，可以弹出事件编辑器或者标签日历。包含1个函数：`(function)mainmenu`

---

## 致谢

Aminous ama seemy norse

