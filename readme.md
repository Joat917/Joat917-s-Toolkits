<!-- omit from toc -->
# Joat917's Toolkit

<!-- omit from toc -->
## 目录

- [简介](#简介)
- [安装依赖](#安装依赖)
- [项目结构](#项目结构)
  - [Basic-Settings](#basic-settings)
  - [Main-Widgets](#main-widgets)
  - [Common-Utilities](#common-utilities)
  - [Small-Tools](#small-tools)
  - [Mini-Games](#mini-games)


## 简介

我(Joat917)的工具箱。整理并集成了我自2023年以来撰写的几乎全部代码项目，并将它们打包成了一个实用的工具箱入口。

包括：

- 极常用工具，如命令行计算器、剪贴板格式管理器、LaTeX-to-Unicode转换器、Python/C运行器等；（私人定制版中，可以快捷复制姓名中的生僻字）
- 辅助工具，如键盘监视与显示器、秒表、连点器、文本数量统计、文件二进制查看器、日历等；
- 小游戏，如半自动扫雷、球面扫雷，全自动飞行棋、破解版24点、破解版猜数、半自动数字华容道；
<!-- - 科学演示工具，如Ising模型全家桶、傅里叶光学变换、Reuleaux三角可视化、二维相流可视化、混沌蝴蝶可视化、混沌摆桌面摆件等。 -->
- 尝用功能：BPM探测器、Quine生成器、代码最小化工具、乱码生成和解码工具、整数分析工具、列竖式草稿纸计算工具等。
- 快捷键指南。

此项目中包括的很多代码都源自于历史项目，或已经完成，或只写到一半便失去了维护的机会。为了兼容工具箱的功能，我将这些代码进行了适当的修改。

本项目的客户为我自己，原则上不考虑他人的需求。自己用得爽就完了！

## 安装依赖

**重要**：*本项目只支持Windows，不支持其它操作系统！*

本项目在Python版本不低于3.13的环境中可以正常运行，在更低版本的Python中不保证可以运行。如果你没有安装Python，请至 https://www.python.org/downloads 安装最新版本的Python。

在项目根目录中执行命令`pip install -r requirements.txt`，即可安装所有所需依赖库。

直接运行`src/main.pyw`文件，启动本工具箱。

本项目的部分功能依赖于gcc和ffmpeg。

安装GCC：前往 https://github.com/niXman/mingw-builds-binaries/releases ，下载合适版本的文件（如遇选择困难，建议安装x86_64-posix-ucrt版本），然后解压到本地目录，将`bin`目录添加到系统环境变量。

安装FFmpeg：前往 https://www.gyan.dev/ffmpeg/builds/#release-builds ，下载release builds下面latest release中的第一个压缩包，解压到本地目录，然后将`bin`目录添加到系统环境变量。

本项目需要用到的快捷键必须在PowerToys中设置。请先从微软商店中安装PowerToys，然后按照你的喜好调整PowerToys中的快捷键设置和按键映射。你只需要保证F13-F22按键可以在键盘上按下，并将无用的Copilot键(Win+LShift+F23)映射到F24。

## 项目结构

<!-- 2026.2.15更新 -->

```
Joat917-s-Toolkit
├─assets
│  ├─flightchess
│  ├─numguess
│  └─thirdmaze
│      ├─dll
│      └─img
└─src
    ├─basic_settings
    ├─common_utilities
    ├─FSTimer
    ├─main_widgets
    ├─mini_games
    ├─musical_lite
    ├─phys_demo
    ├─ScdAch
    ├─small_tools
    └─ThirdMaze
```

### Basic-Settings

这个包导入了本项目依赖的所有外部库，同时定义了设置类，管理和控制所有的全局变量。

### Main-Widgets

定义了工具箱的主窗口和一些通用组件，如自定义菜单、键盘监听器、渐隐弹窗等。

- `main_window.py`：实现了工具箱的主窗口类`MainWindow`。该类综合了工具箱的一些基础功能，实现了主窗口的显示和控制，但是不包括内部布局。同时还定义了背景类`BackgroundWidget`和主菜单管理器类`TrayIconWidget`，它们可以通过主窗口类访问。
- `popup_window.py`：实现了信息弹窗、是否弹窗和渐隐弹窗。通过向主窗口的message队列发送字符串，即可显示为渐隐弹窗。
- `keyboard_listener.py`：基于`pynput`实现的键盘监听器，监控全局键盘事件，在按键按下和松开时在主线程中调用回调函数。主窗口的`_globalHotkeyHandler`函数就是这个监听器的回调函数。
- `custom_menu.py`：`CustomMenu`类定义了一个更好看的菜单，作为`QMenu`的平替。
- `switch_widgets.py`：实现了滑块开关组件`SwitchButton`和文本圆角按钮组件`PushButton`。它们被点击的时候调用所绑定的回调函数。
- `widget_box.py`：定义了纯文本组件`PlainText`和分区布局组件（也就是盒子）`WidgetBox`。所有的文本、滑块、按钮都装在盒子里，盒子放在主窗口中。
- `start_check.py`：实现了一个特殊类`CheckStarted`，这是一个上下文管理器，通过维护锁文件，保证同一时刻同一用户只有一个工具箱实例在运行。（多个用户同时登陆同一台电脑的情况下，每个用户都可以运行一个工具箱实例）

此包依赖于`basic_settings`包与在`basic_settings`中导入的第三方库。此外，`start_check.py`依赖本包中的`ConfirmationPopup`类；`main_window.py`依赖本包中的`CustomMenu`、`KeyboardListener`和`FadingPopup`三个类。

值得注意的是，本包中的`MainWindow`类的实例化还依赖于`common_utilities`包中的`DropRunner`和`ClipboardWidget`类，尽管`common_utilities`包的实现依赖于本包。

### Common-Utilities

这个包定义了工具箱的*内置*功能。这些功能
1. 在工具箱的主窗口中以独立组件的形式呈现，因而具有丰富的交互性。
2. 依赖于`main_widgets`包中实现的组件，也依赖于`basic_settings`包中`Settings`类中定义的全局变量。

- `clipboard_widget.py`：基于`win32clipboard`实现，包含剪贴板格式管理器组件`ClipboardWidget`，和获取剪贴板内容详情的的多个函数。
- `drop_runner.py`：向*主窗口*拖入python或C文件时，运行该文件。在调试模式下，运行结束后命令行窗口将保持开启。其它模块可以通过主窗口的`droprunner`属性访问`run()`和`run_Ccode()`这两个函数，从而实现在工具箱内运行Python或C代码的功能。
- `keyboard_displayer.py`：在屏幕右下角实时显示当前按下的键盘按键。通过主窗口的键盘监听器实现。
- `clickclick_clicker.py`：一个非常普通的连点器。通过`pynput`控制鼠标，并从主窗口的键盘监听器获取全局按键输入。
- `stop_watch.py`：屏幕左下角显示的数码管秒表。通过右键菜单或者快捷键控制，循环开始、停止、重置。
- `chaotic_pendulum.py`：混沌摆桌面摆件。通过使用RK45方法数值求解混沌摆系统满足的欧拉-拉格朗日方程并线性插值，实时显示该系统随时间演化后的状态。~~（该摆件并不依赖于`basic_settings`中导入的第三方库和全局变量，但是确实以独立组件的形式呈现在主窗口中，因此被放在了这个包里。）~~ 该组件在之后可能被剥离，并作为一个相对独立的功能放在`phys_demo`包中。

### Small-Tools

实现了一些实用或者好玩的功能。它们相对独立，不依赖于`basic_settings`包中导入的第三方库和全局变量，但是可能依赖于没有在`basic_settings`包中导入的另外的第三方库。但即使没有安装这些依赖库，除了相关功能无法使用之外，工具箱的其它功能也不会受到影响。

- `clipboard_reader.py`：在一个独立的窗口中显示剪贴板内的所有格式和对应的数据。基于`win32clipboard`和`PyQt5`实现。
- `inline_calculator.py`：在命令行中运行的交互式计算器。这是一个基于`code`模块实现了一个Python交互式解释器，并预导入了一些内置库和第三方库，可以便捷地进行剪贴板操作、命令行操作。
- `word_counter.py`：字数统计。
- `hex_quickview.py`：文件二进制查看器。
- `qrcode_scanner.py`：扫描图片中的二维码。
- `script_generator.py`：脚本生成器，记录一段时间的所有键盘操作为一个Python脚本。依赖于`pynput`和`pyautogui`。
- `quinify_quine.py`：在一个Python脚本内插入一个函数`quinified()`，该函数在调用后返回这个脚本自身，而且不涉及任何魔法变量（禁止使用__file__或__code__）。值得一提的是，这个文件本身就是一个Quine。
- `gushen_coder.py`：乱码生成和解码工具。~~（如果乱码包含了全部原始数据，那么我愿称之为古神语；不过正宗的古神语需要文本生成音频然后倒放再识别文字）~~
- `custompyminify.py`：调用`python_minifier`将Python脚本最小化。
- `unitex_jsrunner.py`：使用`execjs`直接执行`UniTex.js`，将LaTeX表达式转换为Unicode字符串。`UniTex.js`内嵌于该Python代码文件中。
- `small_tools_widgets.py`：所有工具在主窗口中的入口。InlineCalculator因为比较常用，单独放在一个盒子中，其它工具放在另一个盒子中。一些工具会试图从剪贴板中获取运行所需的参数。

### Mini-Games

曾经写过的小游戏。所有游戏都基于`pygame`实现。

... 
