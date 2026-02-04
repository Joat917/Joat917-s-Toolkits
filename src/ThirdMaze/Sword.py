from BaseImport import *


class Sword:
    image = Im.open(MediaPath/"Sword.png").convert("RGBA")
    icon = None

    def __init__(self):
        pass

    @classmethod
    def geticon(cls):
        if cls.icon is not None:
            return cls.icon
        else:
            _t = cls.image.resize((38, 38))
            cls.icon = Im.new('RGBA', ITEMBAR_SIZE[1])
            cls.icon.paste(_t, (10, 12), _t.getchannel('A'))
            return cls.icon

    @classmethod
    def use(cls, main, attack_value=5):
        rolepos = main.role.position
        enemies = main.Enemy.__iter__()
        maze = main.maze
        neighbors = maze.neighbors(*rolepos)
        for enemy in enemies:
            if enemy.position in neighbors:
                enemy.hurt(attack_value)
