"""
在给定源代码中的指定位置添加一个函数quinified，这个函数返回的就是源代码自身。

在给定源代码中添加一行注释：# quine
注意，注释符号井号需要顶格。
运行这个代码后，原文件的这行注释就会被替换为一个函数。
"""

import re
import os

def quinify(source_code: str):
    m = re.search(r'\n#\s*quine\s*?\n', source_code, re.M)
    if m is not None:
        start, end = m.span()
        start += 1
        end -= 1
    else:
        m = re.search(r'^#\s*quine\s*?\n', source_code, re.M)
        if m is not None:
            start, end = m.span()
            end -= 1
        else:
            m = re.search(r'\n#\s*quine\s*?$', source_code, re.M)
            if m is not None:
                start, end = m.span()
                start += 1
            else:
                m = re.search(r'^#\s*quine\s*?$', source_code, re.M)
                if m is not None:
                    start, end = m.span()
                else:
                    return source_code
    out = source_code[:start]
    out += "def quinified():\n    s = "
    out += repr(source_code[:start].replace('%', '%%')
                + "def quinified():\n    s = %s\n    return s %% repr(s)\n"
                + source_code[end:].replace('%', '%%'))
    out += "\n    return s % repr(s)\n"
    out += source_code[end:]
    return out

def quinified():
    s = '"""\n在给定源代码中的指定位置添加一个函数quinified，这个函数返回的就是源代码自身。\n\n在给定源代码中添加一行注释：# quine\n注意，注释符号井号需要顶格。\n运行这个代码后，原文件的这行注释就会被替换为一个函数。\n"""\n\nimport re\nimport os\n\ndef quinify(source_code: str):\n    m = re.search(r\'\\n#\\s*quine\\s*?\\n\', source_code, re.M)\n    if m is not None:\n        start, end = m.span()\n        start += 1\n        end -= 1\n    else:\n        m = re.search(r\'^#\\s*quine\\s*?\\n\', source_code, re.M)\n        if m is not None:\n            start, end = m.span()\n            end -= 1\n        else:\n            m = re.search(r\'\\n#\\s*quine\\s*?$\', source_code, re.M)\n            if m is not None:\n                start, end = m.span()\n                start += 1\n            else:\n                m = re.search(r\'^#\\s*quine\\s*?$\', source_code, re.M)\n                if m is not None:\n                    start, end = m.span()\n                else:\n                    return source_code\n    out = source_code[:start]\n    out += "def quinified():\\n    s = "\n    out += repr(source_code[:start].replace(\'%%\', \'%%%%\')\n                + "def quinified():\\n    s = %%s\\n    return s %%%% repr(s)\\n"\n                + source_code[end:].replace(\'%%\', \'%%%%\'))\n    out += "\\n    return s %% repr(s)\\n"\n    out += source_code[end:]\n    return out\n\ndef quinified():\n    s = %s\n    return s %% repr(s)\n\n\ndef main():\n    import sys, traceback\n    if len(sys.argv)==2:\n        filename = sys.argv[1]\n    else:\n        filename = None\n    try:\n        while True:\n            if filename is None:\n                try:\n                    filename = input("filename:")\n                except EOFError:\n                    filename = None\n                    continue\n                except Exception as exc:\n                    traceback.print_exc()\n                \n            try:\n                filename = os.path.abspath(filename)\n                print("Reading:", filename)\n                with open(filename, \'r\', encoding=\'utf-8\') as file:\n                    data = file.read()\n            except Exception as exc:\n                traceback.print_exc()\n                filename = None\n                continue\n            \n            try:\n                compile(data)\n            except SyntaxError as exc:\n                traceback.print_exc()\n                filename = None\n                continue\n            except Exception:\n                pass\n\n            try:\n                original_data = data\n                data = quinify(data)\n                if data == original_data:\n                    print("Nothing added. Make sure \'# quine\' is in source code. ")\n            except Exception as exc:\n                traceback.print_exc()\n                filename = None\n                continue\n\n            filename_dir = os.path.dirname(filename)\n            suffix = \'_quine\'\n            suffix_index = 1\n            new_filename_prefix, _ = os.path.splitext(filename)\n            new_filename = new_filename_prefix + suffix + \'.py\'\n            while os.path.exists(new_filename):\n                suffix_index += 1\n                suffix = f\'_quine_{suffix_index}\'\n                new_filename = new_filename_prefix + suffix + \'.py\'\n            \n            try:\n                with open(new_filename, \'w\') as file:\n                    file.write(data)\n                print("Saved to:", new_filename)\n            except Exception as exc:\n                filename = None\n                traceback.print_exc()\n            filename = None\n    except KeyboardInterrupt:\n        return\n    except Exception:\n        traceback.print_exc()\n\n\nif __name__ == "__main__":\n    print(quinified())\n    main()\n'
    return s % repr(s)


def main():
    import sys, traceback
    if len(sys.argv)==2:
        filename = sys.argv[1]
    else:
        filename = None
    try:
        while True:
            if filename is None:
                try:
                    filename = input("filename:")
                except EOFError:
                    filename = None
                    continue
                except Exception as exc:
                    traceback.print_exc()
                
            try:
                filename = os.path.abspath(filename)
                print("Reading:", filename)
                with open(filename, 'r', encoding='utf-8') as file:
                    data = file.read()
            except Exception as exc:
                traceback.print_exc()
                filename = None
                continue
            
            try:
                compile(data)
            except SyntaxError as exc:
                traceback.print_exc()
                filename = None
                continue
            except Exception:
                pass

            try:
                original_data = data
                data = quinify(data)
                if data == original_data:
                    print("Nothing added. Make sure '# quine' is in source code. ")
            except Exception as exc:
                traceback.print_exc()
                filename = None
                continue

            filename_dir = os.path.dirname(filename)
            suffix = '_quine'
            suffix_index = 1
            new_filename_prefix, _ = os.path.splitext(filename)
            new_filename = new_filename_prefix + suffix + '.py'
            while os.path.exists(new_filename):
                suffix_index += 1
                suffix = f'_quine_{suffix_index}'
                new_filename = new_filename_prefix + suffix + '.py'
            
            try:
                with open(new_filename, 'w') as file:
                    file.write(data)
                print("Saved to:", new_filename)
            except Exception as exc:
                filename = None
                traceback.print_exc()
            filename = None
    except KeyboardInterrupt:
        return
    except Exception:
        traceback.print_exc()


if __name__ == "__main__":
    print(quinified())
    main()
