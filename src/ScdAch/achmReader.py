"""
用一个简单的方式读取achievements.xlsx中的内容。
注：相较于原始的ScdAch项目稍作修改，以适配本项目的结构。
"""

import openpyxl
import os

ALPHABET = ''.join(map(chr, range(65, 91)))


class Forever:
    def __init__(self) -> None:
        self.i = 0
        pass

    def __iter__(self):
        return self

    def __next__(self):
        o = self.i
        self.i += 1
        return o


class Achievement:
    def __init__(self, typName: str, name: str, rarity: str, description: str) -> None:
        self.typName = typName
        self.name = name
        self.rarity = rarity
        self.description = description
        return

    def __repr__(self):
        return 'Achievement'+repr((self.typName, self.name, self.rarity, self.description))

    def __eq__(self, other):
        return isinstance(other, Achievement) and self.typName == other.typName \
            and self.name == other.name and self.rarity == other.rarity \
            and self.description == other.description

    def __hash__(self):
        return hash(repr(self))


class AchvmReader:
    def __init__(self) -> None:
        self.wb = openpyxl.open(
            os.path.abspath(os.path.dirname(__file__), "../../assets/achievements.xlsx"), 
            read_only=True
        )
        ws = self.wb["Sheet0"]
        sheetNames = self.readSheet(ws)['CONTENTS']
        self.contents = {}
        for _n in sheetNames:
            self.contents[_n] = _l = []
            cont = self.readSheet(self.wb[_n])
            for i in range(len(cont['NAME'])):
                _l.append(Achievement(_n, cont['NAME'][i],
                                      cont['RARITY'][i], cont['DESCRIPTION'][i]))
        self.wb.close()
        return

    @staticmethod
    def readSheet(sheet: openpyxl.worksheet._read_only.ReadOnlyWorksheet):
        out = {}
        for col in range(sheet.max_column):
            out[sheet[ALPHABET[col]+'1'].value] = _l = []
            for row in range(1, sheet.max_row):
                _l.append(sheet[ALPHABET[col]+str(row+1)].value)
        return out


if __name__ == "__main__":
    print(AchvmReader().contents)
