"""
补丁：将数据文件保存在数据目录中，而不是脚本目录中
"""

import os

class _DataPath:
    def __init__(self):
        self.data_dir = os.path.abspath(os.path.join(os.environ['APPDATA'], 'PyScriptX', 'MyToolkits', 'FSTimer'))

    def __truediv__(self, other):
        ret_path = os.path.join(self.data_dir, other)
        os.makedirs(os.path.dirname(ret_path), exist_ok=True)
        return ret_path

DataPath = _DataPath()
