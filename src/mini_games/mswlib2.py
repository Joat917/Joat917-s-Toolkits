"""
扫雷游戏基本代码。
"""

import numpy as np
from math import gcd, comb
import time
import itertools

class MineField:
    "雷场：用于存储雷区的布局和状态的基本结构。不包含任何游戏逻辑。"
    def __init__(self, height:int, width:int, num_mines:int, seed=None):
        """
        初始化雷场，记录初始数据，但是不放置雷

        Args:
            height (int): 雷场的高度
            width (int): 雷场的宽度
            num_mines (int): 雷的数量
            seed: 随机数种子
        """
        self.height = height
        self.width = width
        self.num_mines = num_mines
        self.seed=seed
        self.rng=np.random.Generator(np.random.PCG64(seed))

        self.field = np.zeros((height, width), dtype=np.int8)
        """
        field是一个二维数组，表示雷区和数字。
        0表示空白，1~8表示周围雷的数量，9~17表示雷。
        """

        self.revealed = np.zeros((height, width), dtype=np.int8)
        """
        revealed是一个二维数组，表示每个格子的状态。
        0表示未翻开，1表示已翻开，2表示标记为雷，4表示标记为问号。
        """

    @property
    def num_cells(self):
        """
        返回雷区的总格子数量
        """
        return self.height * self.width

    def all_indices(self):
        """
        依次给出雷区中所有格子的索引

        Yields:
            tuple: (row, col) 格子的索引
        """
        for row in range(self.height):
            for col in range(self.width):
                yield (row, col)

    def all_neighbors(self, pos:tuple[int,int]):
        """
        给出指定格子周围的所有格子的索引

        Args:
            pos (tuple): (row, col) 指定格子的索引

        Yields:
            tuple: (neighbor_row, neighbor_col) 周围格子的索引
        """
        row, col = pos
        for dr,dc in [(1,0),(1,1),(0,1),(-1,1),(-1,0),(-1,-1),(0,-1),(1,-1)]:
            neighbor_row = row + dr
            neighbor_col = col + dc
            if 0 <= neighbor_row < self.height and 0 <= neighbor_col < self.width:
                yield (neighbor_row, neighbor_col)

    def place_mines(self):
        """
        清空雷区，然后随机放置雷，并更新周围格子的数字。
        不会放置在已经翻开的格子上。
        """
        return self.place_mines_quick() or self.place_mines_safe()

    def place_mines_quick(self):
        """
        随机放置雷。内存高效，尤其对于翻开格子不多的情况。但是有小概率失败。

        Returns:
            bool: 是否成功放置所有雷
        """
        # 清空雷区
        self.field.fill(0)

        placed = 0
        for loop in range(2*self.num_mines):  # 尝试2倍雷数次
            if placed >= self.num_mines:
                return placed == self.num_mines
            # 随机选择一个格子
            row = self.rng.integers(0, self.height)
            col = self.rng.integers(0, self.width)
            pos = row,col
            if self.revealed[pos] == 0 and self.field[pos] < 9:  # 只考虑未翻开的格子，并且该格子没有雷
                self.field[pos] = 9  # 放置雷
                placed += 1
                # 更新周围格子的数字
                for pos2 in self.all_neighbors(pos):
                    self.field[pos2] += 1
        return placed == self.num_mines  # 返回是否成功放置所有雷


    def place_mines_safe(self):
        """
        随机放置雷。保证只要可以成功，必定成功。
        """
        # 清空雷区
        self.field.fill(0)

        # 获得所有空地
        empty_cell_indices = []
        for pos in self.all_indices():
            if self.revealed[pos] == 0:  # 只考虑未翻开的格子
                empty_cell_indices.append(pos)

        # 随机选择放置雷的格子
        if len(empty_cell_indices) < self.num_mines:
            raise ValueError("空地不足以放置所有雷。")
        chosen_indices = self.rng.choice(len(empty_cell_indices), self.num_mines)
        
        # 放置雷
        for index in chosen_indices:
            pos = empty_cell_indices[index]
            self.field[pos] = 9  # 放置雷
            # 更新周围格子的数字
            for pos2 in self.all_neighbors(pos):
                self.field[pos2] += 1
        return

    def reveal_cell(self, pos:tuple[int,int]):
        """
        翻开指定格子，并返回翻开的格子数量。
        如果翻开的是雷，返回-1。
        如果翻开的是空白格子，会递归翻开周围的空白格子。

        Args:
            pos (tuple): (row, col) 指定格子的索引

        Returns:
            int: 翻开的格子数量，或者-1表示翻开的是雷
        """
        # 如果已经翻开，直接返回0
        if self.revealed[pos]:
            return 0
        # 如果已经标记，原则上不能翻开
        if self.revealed[pos]==2:
            return 0

        # 翻开
        self.revealed[pos] = 1

        # 如果是雷，返回-1
        if self.field[pos] >= 9:
            return -1

        # 如果不是空白，返回1
        if self.field[pos] > 0:
            return 1

        # 如果是空白，递归翻开周围的格子
        count = 1
        for pos2 in self.all_neighbors(pos):
            assert not self.is_mine(pos2), f"空地{pos}周围的格子{pos2}是雷"
            count += self.reveal_cell(pos2)
        return count

    def mark_cell(self, pos:tuple[int,int]):
        """
        标记指定格子为雷，或者取消标记。
        如果已经翻开，不能标记。

        Args:
            pos (tuple): (row, col) 指定格子的索引

        Returns:
            int: 标记数量的变化
        """
        if self.revealed[pos] == 0:
            self.revealed[pos] = 2  # 标记为雷
            return 1
        elif self.revealed[pos] == 2:
            self.revealed[pos] = 0  # 取消标记
            return -1
        return 0  # 已翻开的格子不能标记

    def reveal_neighbors(self, pos:tuple[int,int]):
        """
        翻开指定格子周围的格子。
        如果周围标记的雷数量等于该格子的数字，才会翻开周围的格子。

        Args:
            pos (tuple): (row, col) 指定格子的索引

        Returns:
            int: 翻开的格子数量，或者-1表示翻开的是雷
        """
        if self.revealed[pos] != 1:
            return 0  # 只有已翻开的格子才可以使用这个功能

        # 计算周围标记的雷数量
        marked_mines = sum(1 for pos2 in self.all_neighbors(pos) if self.revealed[pos2] == 2)

        # 如果标记的雷数量不等于该格子的数字，不能翻开周围的格子
        if marked_mines != self.field[pos]:
            return 0

        # 翻开周围的格子
        count = 0
        found_mine = False
        for pos2 in self.all_neighbors(pos):
            result = self.reveal_cell(pos2)
            if result == -1:
                found_mine = True
                count += 1  # 仍然计数翻开的格子数量
            else:
                count += result
        
        # 如果翻开的是雷，返回-1
        if found_mine:
            return -1
        else:
            return count

    def copy(self):
        """
        返回一个雷场的副本。

        Returns:
            MineField: 雷场的副本
        """
        new_field = MineField(self.height, self.width, self.num_mines)
        new_field.field = self.field.copy()
        new_field.revealed = self.revealed.copy()
        return new_field

    def copy_to(self, other):
        """
        将当前雷场的内容覆写到另一个雷场中。

        Args:
            other (MineField): 目标雷场
        """
        if not isinstance(other, MineField):
            raise TypeError("目标必须是MineField类型。")
        if self.height != other.height or self.width != other.width or self.num_mines != other.num_mines:
            raise ValueError("雷场尺寸或雷数不匹配，无法复制。")
        other.field[:] = self.field
        other.revealed[:] = self.revealed

    # 辅助方法
    def is_mine(self, pos):
        return bool(self.field[pos] >= 9)

    def is_flag(self, pos):
        return bool(self.revealed[pos] == 2)

    def is_exposed(self, pos):
        return bool(self.revealed[pos] == 1)

    def is_covered(self, pos):
        return bool(self.revealed[pos] != 1)

    def is_grass(self, pos):
        return bool(self.revealed[pos] == 0)

    def get_exposed_number(self, pos):
        if not self.is_exposed(pos):
            raise ValueError("Chosen position is not exposed")
        return min(self.field[pos], 9)

    def is_safe(self):
        # 判断是否所有已翻开的格子都是安全的（没有雷）
        for pos in self.all_indices():
            if self.is_exposed(pos) and self.is_mine(pos):
                return False
        return True

    def is_victory(self):
        # 判断是否胜利
        for pos in self.all_indices():
            if self.is_mine(pos)^self.is_covered(pos):
                return False
        return True

    def to_string(self, ascii_only=False):
        out = " |"
        # 制作表头
        out += "|".join("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"[:self.width])
        out += "\n"

        if ascii_only:
            covered_cell = "?"
            flag_cell = "F"
            mine_cell = "X"
            other_cell = '!'
        else:
            covered_cell = "█"
            flag_cell = "⚑"
            mine_cell = "✹"
            other_cell = '·'

        for row in range(self.height):
            # 制作行头
            try:
                line = ["123456789abcdefghijklmnopqrstuvwxyz"[row]]
            except IndexError:
                line = []
            # 读取这一行的数据
            for col in range(self.width):
                if self.is_grass((row, col)):
                    line.append(covered_cell)
                elif self.is_flag((row, col)):
                    line.append(flag_cell)
                elif self.is_mine((row, col)):
                    line.append(mine_cell)
                elif self.get_exposed_number((row, col)) == 0:
                    line.append(' ')
                elif 1 <= self.get_exposed_number((row, col)) <= 8:
                    line.append(str(self.get_exposed_number((row, col))))
                else:
                    line.append(other_cell)

            out += "|".join(line) + "\n"
        return out


class MineGame:
    "扫雷游戏：包含游戏逻辑和状态。"
    def __init__(self, height:int, width:int, num_mines:int, seed=None):
        """
        初始化扫雷游戏，创建一个雷场。

        Args:
            height (int): 雷场的高度
            width (int): 雷场的宽度
            num_mines (int): 雷的数量
            seed: 随机数种子
        """
        self.minefield = MineField(height, width, num_mines, seed=seed)
        self.game_over = False # 游戏是否结束，包括输赢
        self.victory = False # 游戏是否胜利
        self.initialized = False  # 是否已经初始化雷区
        self.unrevealed_count = self.minefield.num_cells  # 未翻开的格子数量
        self.actions_count = 0  # 玩家操作次数
        self.marked_count = 0  # 玩家标记的雷数量
        self.detector = MineDetector(self.minefield)

    def reset(self):
        """
        重置游戏，清空雷场和状态。
        """
        self.minefield = MineField(
            self.minefield.height, self.minefield.width, 
            self.minefield.num_mines, 
            self.minefield.seed+1 if self.minefield.seed is not None else None
        )
        self.detector = MineDetector(self.minefield)
        self.game_over = False
        self.victory = False
        self.initialized = False
        self.unrevealed_count = self.minefield.num_cells
        self.actions_count = 0
        self.marked_count = 0

    def reveal_cell(self, pos:tuple[int,int]):
        """
        翻开指定格子，并更新游戏状态。
        如果未初始化，会先初始化雷区，保证第一次翻开的格子不是雷。
        """
        if self.game_over or self.victory:
            return False

        if not self.initialized:
            self.minefield.revealed.fill(0)  # 清空翻开状态
            # 硬翻开点击位置
            self.minefield.revealed[pos] = 1
            # 硬翻开周围
            for pos2 in self.minefield.all_neighbors(pos):
                self.minefield.revealed[pos2] = 1
            # 放置雷
            self.minefield.place_mines()

            # 合上刚才翻开的格子
            self.minefield.revealed[pos] = 0
            for pos2 in self.minefield.all_neighbors(pos):
                self.minefield.revealed[pos2] = 0
            # 标记已经初始化
            self.initialized = True
            # 重新打开点击位置（继续下面的代码）
        
        count = self.minefield.reveal_cell(pos)
        self.actions_count += 1

        if count == -1:
            self.game_over = True
            self.victory = False
        else:
            self.unrevealed_count -= count
            if self.unrevealed_count == self.minefield.num_mines:
                self.victory = True
                self.game_over = True
        return count!=0

    def mark_cell(self, pos:tuple[int,int]):
        """
        标记指定格子为雷，或者取消标记。
        """
        if self.game_over or self.victory:
            return False
        
        change = self.minefield.mark_cell(pos)
        if change != 0:
            self.actions_count += 1
            self.marked_count += change
        return change!=0

    def reveal_neighbors(self, pos:tuple[int,int]):
        """
        翻开指定格子周围的格子，并更新游戏状态。
        """
        if self.game_over or self.victory:
            return False
        
        count = self.minefield.reveal_neighbors(pos)
        self.actions_count += 1

        if count == -1:
            self.game_over = True
            self.victory = False
        else:
            self.unrevealed_count -= count
            if self.unrevealed_count == self.minefield.num_mines:
                self.victory = True
                self.game_over = True
        return count!=0

    def to_string(self):
        """
        将游戏状态转换为字符串，适合直接在控制台中显示
        """
        lines = []
        for row in range(self.minefield.height):
            line = []
            for col in range(self.minefield.width):
                pos = (row, col)
                if self.minefield.revealed[pos] == 0:
                    line.append('.')
                elif self.minefield.revealed[pos] == 1:
                    if self.minefield.field[pos] >= 9:
                        line.append('*')
                    else:
                        line.append(str(self.minefield.field[pos]))
                elif self.minefield.revealed[pos] == 2:
                    line.append('F')
                elif self.minefield.revealed[pos] == 4:
                    line.append('?')
            lines.append(' '.join(line))
        # 追加统计信息
        lines.append(f"Step: {self.actions_count}")
        lines.append(f"Mine: {self.minefield.num_mines - self.marked_count}")

        prog_denominator = self.minefield.num_cells - self.minefield.num_mines
        prog_numerator = self.minefield.num_cells - self.unrevealed_count
        prog_percentage = int(prog_numerator / prog_denominator * 100)
        prog_percentage = min(max(prog_percentage, 0), 100)  # 限制在0~100之间
        lines.append(f"Prog: {prog_numerator}/{prog_denominator} ({prog_percentage}%)")
        
        lines.append(f"Stat {'Win' if self.victory else 'Lose' if self.game_over else 'Playing'}")

        return '\n'.join(lines)


class MineDetector:
    "提供辅助功能"
    def __init__(self, minefield:MineField):
        self.minefield = minefield
        self.minefield_snapshot = minefield.copy() # 保存雷区的快照，用于差异分析

        # 缓存
        self.known_mines = np.zeros(minefield.field.shape, dtype=np.int8)
        self.known_empty = np.zeros(minefield.field.shape, dtype=np.int8)
        self.effective_unrevealed_cells = np.zeros(minefield.field.shape, dtype=np.int8) # 不是已知雷，也不是已知空格，但周围有已知数字的未翻开格子
        self.effective_numbers = {}  # 有效数字，位置到数字的映射

        self._probabilities = np.full(minefield.field.shape, np.nan, dtype=np.float32)  # 概率，位置到概率的映射
        self._solver = None
        self._x_map = None

        self._buffer_all_solutions = []

    def get_diff(self):
        """
        获取当前雷区与快照的差异。忽略标记状态，只关注新翻开的格子。
        """
        differences = []
        for pos in self.minefield.all_indices():
            if self.minefield_snapshot.is_covered(pos) and self.minefield.is_exposed(pos):
                differences.append(pos)
        return differences

    def update_snapshot(self):
        """
        更新快照为当前雷区的状态。
        """
        self.minefield.copy_to(self.minefield_snapshot)

    def update_known_cells(self, differences:list):
        """
        更新缓存
        """
        for pos in differences:
            assert self.minefield.is_exposed(pos), "差异列表中的格子必须是已翻开的。"
            number = self.minefield.get_exposed_number(pos)
            # 更新已知mines和已知empty
            if self.minefield.is_mine(pos):
                self._set_to_mine(pos)
            else:
                self._set_to_empty(pos)
                # 记录数字
                if number > 0:
                    self.effective_numbers[pos] = number

            # 更新有效未翻开格子
            self.effective_unrevealed_cells[pos] = 0
            if number==0:
                continue # 空地周围不存在格子
            for pos2 in self.minefield.all_neighbors(pos):
                if not self.known_mines[pos2] and not self.known_empty[pos2]:
                    self.effective_unrevealed_cells[pos2] = 1

        # 更新有效数字，去掉无效数字
        for pos in list(self.effective_numbers.keys()):
            # 检查周围是否还有有效未翻开格子
            has_effective_unrevealed = False
            for pos2 in self.minefield.all_neighbors(pos):
                if self.effective_unrevealed_cells[pos2]:
                    has_effective_unrevealed = True
                    break
            if not has_effective_unrevealed:
                # 如果没有，该数字不再有效，删去
                self.effective_numbers.pop(pos)

    def _set_to_empty(self, cell):
        """
        将指定的格子标记为已知空格，并从有效未翻开格子中移除。
        如果这些格子已经被标记为已知雷，则会抛出异常。
        """
        if self.minefield.is_mine(cell):
            raise RuntimeError(f"指定的格子是雷，但是正在标记为空格: {cell}")
        if self.known_mines[cell]:
            raise ValueError(f"指定的格子已经被标记为已知雷: {cell}")
        self.effective_unrevealed_cells[cell] = 0
        self.known_empty[cell] = 1

    def _set_to_mine(self, cell):
        """
        将指定的格子标记为已知雷，并从有效未翻开格子中移除。
        """
        if not self.minefield.is_mine(cell):
            raise RuntimeError(f"指定的格子不是雷，但是正在标记为雷: {cell}")
        if self.known_empty[cell]:
            raise ValueError(f"指定的格子已经被标记为已知空格: {cell}")
        self.effective_unrevealed_cells[cell] = 0
        self.known_mines[cell] = 1

    def get_constraints(self):
        """
        获取约束条件列表，每个约束条件是一个二元组，包含格子列表和对应的雷数。
        """
        constraints = set()
        for pos, number in self.effective_numbers.items():
            uncertain_cells = []
            mines_count = 0
            for pos2 in self.minefield.all_neighbors(pos):
                if self.minefield.revealed[pos2] == 1 or self.known_empty[pos2]:
                    continue
                if self.known_mines[pos2]:
                    mines_count += 1
                    continue
                uncertain_cells.append(pos2)
            assert len(uncertain_cells)>0, "有效数字周围必须有未确定的格子。"
            constraints.add((tuple(sorted(uncertain_cells)), number - mines_count))
        return constraints

    def get_additional_constraint(self):
        """
        计算总雷数带来的限制。返回一个二元组，表示所有变量之和需要处于的范围。
        """
        remaining_mines = self.minefield.num_mines - np.count_nonzero(self.known_mines)
        unexposed_cells = self.minefield.num_cells - np.count_nonzero(self.known_empty|self.known_mines|self.effective_unrevealed_cells)
        return max(0,remaining_mines-unexposed_cells), min(remaining_mines, np.count_nonzero(self.effective_unrevealed_cells))

    @staticmethod
    def constraint_to_matrix_form(constraints):
        """
        将约束表示为增广矩阵的形式，但不化简。

        Args:
            constraints (set): 约束条件集合，每个约束条件是一个二元组，包含格子列表和对应的雷数。

        Returns:
            tuple: (matrix, cells) 其中 matrix 是增广矩阵，cells 是索引到格子的映射列表。
        """
        constraints_sorted = sorted(constraints, key=lambda x: (len(x[0]), x[1])) # 约束少的优先，雷数少的优先
        cell_to_index = {}
        output_cells = []
        for cells, _ in constraints_sorted:
            for cell in cells:
                if cell not in cell_to_index:
                    cell_to_index[cell] = len(cell_to_index)
                    output_cells.append(cell)
        cells_count = len(cell_to_index)

        # 构建增广矩阵
        matrix = np.zeros((len(constraints), cells_count + 1), dtype=np.int8)
        for row_index, (cells, mine_count) in enumerate(constraints_sorted):
            for cell in cells:
                col_index = cell_to_index[cell]
                matrix[row_index, col_index] = 1
            matrix[row_index, -1] = mine_count

        return matrix, output_cells

    def refresh(self):
        """刷新自身，以匹配minefield的状态"""
        # 获取差异
        diff = self.get_diff()
        if not diff:
            return False
        self._buffer_all_solutions.clear()
        # 根据翻开的情况更新
        self.update_known_cells(diff)
        # 获得当下约束
        constraints = self.get_constraints()
        s_range = self.get_additional_constraint()

        # 求解约束
        matrix, x_map = self.constraint_to_matrix_form(constraints)
        self._solver = ZeroOneSolver(matrix)
        self._x_map = x_map
        self._solver.simplify_full()
        certain_solution = self._solver.certain_solutions

        # 应用得到的解
        for i, cell in enumerate(x_map):
            if i not in certain_solution:
                continue
            if certain_solution[i] == 1:
                self._set_to_mine(cell)
            elif certain_solution[i] == 0:
                self._set_to_empty(cell)

        # 计算完成
        self.update_snapshot()
        return True

    # lazy-loaded probability
    @property
    def probabilities(self):
        # 应用概率
        if self._solver is None:
            return self._probabilities
        # _, probabilities = self._solver.solve()
        number_of_solutions, probabilities = self._solver.try_probabilities()
        assert number_of_solutions > 0, "没有可行解"
        # print(number_of_solutions)
        # print(self._solver.matrix, len(probabilities), len(self._x_map))
        self._probabilities.fill(np.nan)
        mines_left = self.minefield.num_mines - np.count_nonzero(self.known_mines)
        mines_need_total = mines_left
        for i, cell in enumerate(self._x_map):
            if np.isfinite(probabilities[i]):
                self._probabilities[cell] = probabilities[i]
                mines_left -= probabilities[i]

        # 如果发现mines_left小于0或大于mines_need_total，重新求解
        if mines_left < 0 or mines_left > mines_need_total:
            _solutions = []
            mat_orig = self._solver.matrix_orig
            for mines_left in range(0, mines_need_total+1):
                try:
                    mat = np.concatenate([mat_orig, [
                        [1]*(mat_orig.shape[1]-1) + [mines_need_total-mines_left]
                    ]], axis=0)  # 强制约束总数等于上限
                    self._solver = ZeroOneSolver(mat)
                    _solutions.append(self._solver.try_probabilities())
                except ValueError:
                    continue
            
            n_sum, probabilities = ZeroOneSolver.merge_probabilities(_solutions)
            if n_sum>0:
                for i, cell in enumerate(self._x_map):
                    if np.isfinite(probabilities[i]):
                        self._probabilities[cell] = probabilities[i]
            else:
                # 忽略，使用默认求解策略，尽管确实有问题
                pass

        # 填充其它格子
        unexposed_mines = []
        for cell in self.minefield.all_indices():
            if self.known_mines[cell]:
                self._probabilities[cell]=1
            elif self.known_empty[cell]:
                self._probabilities[cell]=0
            elif not self.effective_unrevealed_cells[cell]:
                unexposed_mines.append(cell)
        for cell in unexposed_mines:
            self._probabilities[cell] = mines_left / len(unexposed_mines)

        self._solver = None
        self._x_map = None
        return self._probabilities

    def reset(self):
        self.minefield_snapshot = MineField(self.minefield.height, self.minefield.width, self.minefield.num_mines, seed=self.minefield.seed)
        self.known_mines.fill(0)
        self.known_empty.fill(0)
        self.effective_unrevealed_cells.fill(0)
        self.effective_numbers.clear()
        self._probabilities.fill(np.nan)
        self._solver = None
        self._x_map = None


class DisjointSet:
    __slots__ = ['p']
    def __init__(self, n):
        self.p={i:i for i in range(n)}
    def find(self, x):
        if self.p[x]!=x:
            self.p[x]=self.find(self.p[x])
        return self.p[x]
    def union(self, xs):
        roots = [self.find(x) for x in xs]
        root = min(roots)
        for r in roots:
            self.p[r]=root
    def groups(self):
        group_dict={}
        for i in self.p.keys():
            group_dict.setdefault(self.find(i), []).append(i)
        return list(group_dict.values())

class NoSolution(Exception):
    pass

class ZeroOneSolver:
    print_debug_info = 0
    def __init__(self, matrix, i2v=None):
        """
        求解Ax=b，x的每个元素必须取0或1。

        Args:
            matrix: 增广矩阵(A|b)
            i2v: 可选，原始变量下标到矩阵列指标的映射
        """
        self.matrix = matrix
        self.matrix_orig = matrix.copy()

        num_vars = matrix.shape[1]-1
        if i2v is not None:
            self.x_mapping_v2i = {i2v[i]:i for i in range(num_vars)}  # 原始变量下标到目前矩阵列指标的映射
            # 检查下标是否完全
            _lacking_index = []
            for i in range(num_vars):
                if i not in i2v:
                    _lacking_index.append(i)
            if _lacking_index:
                raise ValueError(f"i2v缺少变量下标: {_lacking_index}")
        else:
            self.x_mapping_v2i = {i:i for i in range(num_vars)}  # 原始变量下标到目前矩阵列指标的映射
        self.x_mapping_i2v = {v: k for k, v in self.x_mapping_v2i.items()} # 矩阵列指标到原始变量下表的映射

        self.certain_solutions = {} # var: 0/1，表示确定的解
        self.probabilities = {} # var: float，表示概率解

    @staticmethod
    def _var_index_to_var_name(index):
        "将变量索引转换为变量名"
        if 0 <= index < 26:
            return chr(97 + index)  # a-z
        elif index < 26*27:
            return chr(97 + index // 26) + chr(97 + index % 26)  # aa-zz
        else:
            return f"x{index}"  # x702, x703, ...

    @classmethod
    def _equation_to_string(cls, equation, i2v, sep=' '):
        """
        将单个等式转换为字符串。

        Args:
            equation (np.ndarray): 单个等式的系数和常数项
            i2v (dict): 原始变量下标到矩阵列指标的映射
            sep (str): 变量和系数之间的分隔符，默认为空格

        Returns:
            str: 等式的字符串表示
        """
        if isinstance(equation, np.ndarray):
            if not equation.ndim == 1:
                raise ValueError("输入必须是一维数组")
        elif not isinstance(equation, (list, tuple)):
            raise TypeError(f"输入必须是列表或元组, got {type(equation)}")
        if not isinstance(i2v, dict):
            raise TypeError("i2v必须是字典")

        var_count = len(equation) - 1
        terms = [] # (varname, coeff)
        for col in range(var_count):
            coeff = equation[col]
            if coeff != 0:
                terms.append((cls._var_index_to_var_name(i2v[col]), coeff))
        rhs = equation[-1]
        if len(terms)==0:
            return f"0 = {rhs}"

        line = ""
        if terms[0][1]==1:
            line += terms[0][0]
        elif terms[0][1]==-1:
            line += "-" + terms[0][0]
        else:
            line += f"{terms[0][1]}{sep}{terms[0][0]}"
        for varname, coeff in terms[1:]:
            if coeff==1:
                line += f" + {varname}"
            elif coeff==-1:
                line += f" - {varname}"
            elif coeff<0:
                line += f" - {-coeff}{sep}{varname}"
            elif coeff>0:
                line += f" + {coeff}{sep}{varname}"
        line += f" = {rhs}"
        return line

    def _eq2s(self, row_index:int):
        "简写：将指定行的等式转换为字符串"
        return self._equation_to_string(self.matrix[row_index], self.x_mapping_i2v)

    @classmethod
    def matrix_to_string(cls, matrix, i2v=None):
        """
        将约束的增广矩阵形式转换为字符串，便于调试和查看。

        Args:
            matrix (np.ndarray): 增广矩阵
            i2v (dict): 可选，原始变量下标到矩阵列指标的映射
        Returns:
            str: 约束的字符串表示
        """
        if matrix.shape[0]==0:
            return "[No constraint]"
        var_count = matrix.shape[1] - 1
        if var_count==0:
            return f"0 = {matrix[0, -1]}"

        if i2v is None:
            i2v = {i:i for i in range(var_count)} 
        
        lines = []
        for row in range(matrix.shape[0]):
            lines.append(cls._equation_to_string(matrix[row], i2v))
        return '\n'.join(lines)

    def to_string(self):
        # check
        _lacking_index = []
        for i in range(self.matrix.shape[1]-1):
            if i not in self.x_mapping_i2v:
                _lacking_index.append(i)
        if _lacking_index:
            raise ValueError(f"在{self.matrix.shape[1]-1}个变量中，缺少变量下标: {_lacking_index}: {self.x_mapping_i2v}")
        #
        return self.matrix_to_string(self.matrix, self.x_mapping_i2v)

    def simplify_0(self):
        # 清除所有全0行，然后将所有行约去最小公因数
        matrix = self.matrix
        # 依次遍历每一行
        row_index=0
        while row_index < matrix.shape[0]:
            if np.count_nonzero(matrix[row_index,:-1])==0:
                # 如果当前行是全零行，移动到最后
                if not matrix[row_index,-1]==0:
                    raise NoSolution("全零行的右端必须为0")
                matrix[[row_index,-1],:] = matrix[[-1,row_index],:] # 将全零行交换到最后
                matrix = matrix[:-1,:] # 删除最后一行
            else:
                # 将当前行的所有系数约去最小公因数
                coeffs = matrix[row_index,:-1]
                nonzero_coeffs_abs = [abs(x) for x in coeffs if x!=0]
                factor = gcd(*nonzero_coeffs_abs)
                if factor>1:
                    matrix[row_index,:] //= factor
                # 如果系数之和小于0，让系数之和大于0
                if np.sum(coeffs) < 0:
                    matrix[row_index,:] *= -1
                
                row_index += 1

        self.matrix = matrix
        return

    def simplify_1(self):
        # 先将矩阵按照非零系数个数递增排列，然后尽可能减少非零系数个数
        matrix = self.matrix
        changed = False # 是否成功消去一行的元素
        # 排序
        nonzero_counts = np.count_nonzero(matrix[:,:-1], axis=1)
        sorted_indices = np.argsort(nonzero_counts)
        matrix = matrix[sorted_indices,:]
        # 尝试消去多余的约束
        for row_index in range(matrix.shape[0]-1):
            current_coeffs = matrix[row_index,:-1]
            current_nonzero_indices = np.nonzero(current_coeffs)[0]
            for other_row_index in range(row_index+1, matrix.shape[0]):
                other_coeffs = matrix[other_row_index,:-1]
                other_nonzero_count = np.count_nonzero(other_coeffs)
                # 遍历所有的current_nonzero_indices，尝试消元
                for col_index in current_nonzero_indices:
                    if other_coeffs[col_index] == 0:
                        # 消元系数为0，毫无意义
                        continue
                    # 计算消元系数
                    factor = other_coeffs[col_index] // current_coeffs[col_index]
                    if abs(other_coeffs[col_index]) % abs(current_coeffs[col_index]) != 0:
                        # 不能整除，无法消元
                        continue
                    # 尝试消元
                    new_other_coeffs = other_coeffs - factor * current_coeffs
                    new_other_nonzero_count = np.count_nonzero(new_other_coeffs)
                    if (
                        new_other_nonzero_count < other_nonzero_count or # 变量个数变少了
                        new_other_nonzero_count == other_nonzero_count and # 变量个数不变，但是等式右侧变成了0
                        matrix[other_row_index,-1]!=0 and
                        matrix[other_row_index,-1]-factor*matrix[row_index,-1] == 0
                    ):
                        # 消元成功，更新该行
                        matrix[other_row_index] -= factor * matrix[row_index]
                        other_coeffs = new_other_coeffs
                        other_nonzero_count = new_other_nonzero_count
                        changed = True
                        # 允许继续更新该行
        self.matrix = matrix
        # 此后可能会出现新的全零行，需要继续消元
        return changed

    def _delete_cols(self, idxes):
        if not idxes:
            return
        idxes_set = set(idxes)
        idxes = sorted(idxes_set)

        # if self.print_debug_info:
        #     print(f"Deleting: {', '.join(self._var_index_to_var_name(self.x_mapping_i2v[i]) for i in idxes)}")
        #     print("Before Deletion:")
        #     print(self.to_string())
        #     # print("Deleting Variables: ")
        #     # for old_ind in idxes:
        #     #     var = self.x_mapping_i2v[old_ind]
        #     #     x = self.certain_solutions[var]
        #     #     print(f"  {self._var_index_to_var_name(var)} = {x}")
        
        # 给出指标映射
        new_indices = np.arange(self.matrix.shape[1]-1)
        old_indices_ = [i for i in new_indices if i not in idxes_set]
        old_indices = np.array(old_indices_, dtype=np.int32)
        new_indices = new_indices[:len(old_indices)]

        # 变量映射
        new_vars = [self.x_mapping_i2v[i] for i in old_indices]

        # 将待删除的列归零，维持等式自洽
        for old_ind in idxes:
            x = self.certain_solutions[self.x_mapping_i2v[old_ind]]
            if x==0:
                continue
            self.matrix[:,-1] -= self.matrix[:,old_ind]
            self.matrix[:,old_ind] = 0

        # 删除矩阵的第idx列
        new_matrix = np.zeros((self.matrix.shape[0], self.matrix.shape[1]-len(idxes)), dtype=self.matrix.dtype)
        for new_ind, old_ind in enumerate(old_indices):
            new_matrix[:, new_ind] = self.matrix[:, old_ind]
        new_matrix[:,-1] = self.matrix[:,-1]

        # 更新矩阵
        self.matrix = new_matrix
        
        # 更新v2i和i2v
        self.x_mapping_v2i={} # 不用clear，直接开新的字典
        self.x_mapping_i2v={}
        for new_ind, var in enumerate(new_vars):
            self.x_mapping_v2i[var] = new_ind
            self.x_mapping_i2v[new_ind] = var

        # 化简
        self.simplify_0()

        # if self.print_debug_info:
        #     print("After Deletion:")
        #     print(self.to_string())

    def _set_certain_solution(self, col2val:dict):
        # 设置确定解，并从矩阵中删除这些列
        for col, val in col2val.items():
            var = self.x_mapping_i2v[col]
            self.certain_solutions[var] = val
        # 删除这些列
        self._delete_cols(list(col2val.keys()))

    def get_solution_a(self):
        # 求出显然解：方程左侧只有一个非零系数
        new_solutions = {} # col: val
        for row_index in range(self.matrix.shape[0]):
            coeffs = self.matrix[row_index,:-1]
            rhs = self.matrix[row_index,-1]
            
            nonzero_indices = np.nonzero(coeffs)[0]
            if len(nonzero_indices) != 1:
                continue

            col_index = nonzero_indices[0]
            coeff = coeffs[col_index]
            if rhs==0:
                new_solutions[col_index] = 0
            elif rhs==coeff:
                new_solutions[col_index] = 1
            else:
                raise NoSolution(f"单变量方程 {self._eq2s(row_index)} 无0/1解。")
        self._set_certain_solution(new_solutions)
        return len(new_solutions) > 0

    def get_solution_b(self):
        # 求出特殊解：方程左侧只有两个非零系数，且可以解出这两个变量
        new_solutions = {} # col: val
        for row_index in range(self.matrix.shape[0]):
            coeffs = self.matrix[row_index,:-1]
            rhs = self.matrix[row_index,-1]
            
            nonzero_indices = np.nonzero(coeffs)[0]
            if len(nonzero_indices) != 2:
                continue

            cola = nonzero_indices[0]
            colb = nonzero_indices[1]
            coeffa = coeffs[cola]
            coeffb = coeffs[colb]

            # 同号
            if coeffa * coeffb > 0:
                if rhs==0:
                    # ax+by=0 => x=y=0
                    new_solutions[cola] = 0
                    new_solutions[colb] = 0
                elif rhs==coeffa+coeffb:
                    # ax+by=a+b => x=y=1
                    new_solutions[cola] = 1
                    new_solutions[colb] = 1
                elif rhs==coeffa!=coeffb:
                    # ax+by=a => x=1,y=0
                    new_solutions[cola] = 1
                    new_solutions[colb] = 0
                elif rhs==coeffb!=coeffa:
                    # ax+by=b => x=0,y=1
                    new_solutions[cola] = 0
                    new_solutions[colb] = 1
                elif coeffa!=coeffb or rhs!=coeffa:
                    raise NoSolution(f"同号双变量方程 {self._eq2s(row_index)} 无0/1解。")
            # 异号
            else:
                if rhs==coeffa:
                    # ax-cy=a => x=1,y=0
                    new_solutions[cola] = 1
                    new_solutions[colb] = 0
                elif rhs==coeffb:
                    # ax-cy=-c => x=0,y=1
                    new_solutions[cola] = 0
                    new_solutions[colb] = 1
                elif coeffa+coeffb!=0: # a!=c
                    if rhs==0:
                        # ax-cy=0 => x=y=0
                        new_solutions[cola] = 0
                        new_solutions[colb] = 0
                    elif rhs==coeffa+coeffb:
                        # ax-cy=a-c => x=y=1
                        new_solutions[cola] = 1
                        new_solutions[colb] = 1
                    else:
                        raise NoSolution(f"异号双变量方程 {self._eq2s(row_index)} 无0/1解。")
                elif rhs!=0:
                    # a=c and ax-cy!=0 => 无解
                    raise NoSolution(f"异号双变量方程 {self._eq2s(row_index)} 无0/1解。")
        self._set_certain_solution(new_solutions)
        return len(new_solutions) > 0

    def get_solution_c(self):
        # 求解当系数全部同号，且等式右侧等于0或系数和的情况。
        new_solutions = {} # col: val
        for row_index in range(self.matrix.shape[0]):
            coeffs = self.matrix[row_index,:-1]
            rhs = self.matrix[row_index,-1]
            nonzero_indices = np.nonzero(coeffs)[0]
            # 检查系数的符号
            all_same_sign = True
            for i in range(len(nonzero_indices)-1):
                if coeffs[nonzero_indices[i]] * coeffs[nonzero_indices[i+1]] < 0:
                    all_same_sign = False
                    break
            if not all_same_sign:
                continue
            if rhs==0:
                for col_index in nonzero_indices:
                    new_solutions[col_index] = 0
            elif rhs==np.sum(coeffs[nonzero_indices]):
                for col_index in nonzero_indices:
                    new_solutions[col_index] = 1
        self._set_certain_solution(new_solutions)
        return len(new_solutions) > 0

    @staticmethod
    def decompose_matrix(matrix):
        if not isinstance(matrix, np.ndarray):
            raise TypeError("输入必须是numpy数组")
        if matrix.ndim != 2:
            raise ValueError("输入必须是二维数组")
        
        # 将矩阵分解为互不相交的子矩阵
        if matrix.shape[0]==0 or matrix.shape[1]<=1:
            return [matrix]

        ds = DisjointSet(matrix.shape[1]-1)
        for row_index in range(matrix.shape[0]):
            coeffs = matrix[row_index,:-1]
            nonzero_indices = np.nonzero(coeffs)[0]
            if len(nonzero_indices) > 1:
                ds.union(nonzero_indices)
        
        result = []
        for component in ds.groups():
            submatrix = []
            for row_index in range(matrix.shape[0]):
                coeffs = matrix[row_index][component]
                rhs = matrix[row_index][-1]
                if np.count_nonzero(coeffs) > 0:
                    submatrix.append(np.concatenate([coeffs, [rhs]]))
            result.append(np.array(submatrix, dtype=matrix.dtype))
        return result

    def decompose(self):
        "将自身分解为多个独立的子问题"
        if self.matrix.shape[0]==0 or self.matrix.shape[1]<=1:
            return [self]

        ds = DisjointSet(self.matrix.shape[1]-1)
        for row_index in range(self.matrix.shape[0]):
            coeffs = self.matrix[row_index,:-1]
            nonzero_indices = np.nonzero(coeffs)[0]
            if len(nonzero_indices) > 1:
                ds.union(nonzero_indices)

        result = []
        groups = ds.groups()
        if len(groups) == 1:
            return [self]

        for component in groups:
            submatrix = []
            for row_index in range(self.matrix.shape[0]):
                coeffs = self.matrix[row_index][component]
                rhs = self.matrix[row_index][-1]
                if np.count_nonzero(coeffs) > 0:
                    submatrix.append(np.concatenate([coeffs, [rhs]]))
            result.append(ZeroOneSolver(
                np.array(submatrix, dtype=self.matrix.dtype), 
                i2v={i:self.x_mapping_i2v[component[i]] for i in range(len(component))}
            ))
        return result

    def _construct_full_probabilities(self, old_probabilities:dict):
        "将确定解信息加入概率数组，并检查概率数组是否完整"
        if not isinstance(old_probabilities, dict):
            raise TypeError(f"old_probabilities必须是字典, got {type(old_probabilities)}")
        probabilities = old_probabilities.copy()
        for var, val in self.certain_solutions.items():
            probabilities[var] = val
        lacking_vars = []
        for var in self.x_mapping_v2i.keys():
            if var not in probabilities:
                lacking_vars.append(var)
                probabilities[var] = np.nan
        if lacking_vars:
            raise ValueError(f"概率数组缺少变量: {','.join([self._var_index_to_var_name(v) for v in lacking_vars])}")
        return probabilities

    def _construct_no_solution_probabilities(self):
        "构造无解的概率数组"
        probabilities = {}
        for var in self.x_mapping_v2i.keys():
            probabilities[var] = 0.5
        return probabilities

    def try_probabilities(self):
        """
        通过设置试探解的方法，给出解的总个数，以及每个位置的概率

        Returns:
            tuple[int, dict]: 返回可行解的数量和概率分布字典，其中字典的键是原始变量下标，值是该变量取1的概率。
        """
        try:
            self.simplify_full()
        except NoSolution:
            all_vars = list(v for v in self.x_mapping_v2i.keys() if v not in self.certain_solutions)
            return 0, self._construct_no_solution_probabilities()

        if self.matrix.shape[1]<=1:
            # 没有变量，直接返回当前确定解
            return 1, self._construct_full_probabilities({})
        if self.matrix.shape[0]==0:
            # 没有约束，所有解都是可行的
            all_vars = list(v for v in self.x_mapping_v2i.keys() if v not in self.certain_solutions)
            return 2**len(all_vars), self._construct_full_probabilities({v:0.5 for v in all_vars})

        # 如果只有一个约束，直接求解
        if self.matrix.shape[0]==1:
            result = self._solve_single_equation(self.matrix[0,:-1], self.matrix[0,-1], self.x_mapping_i2v)
            if result[0]==0:
                return 0, self._construct_no_solution_probabilities()
            return result[0], self._construct_full_probabilities(result[1])
        
        # 分离耦合的变量
        subproblems = self.decompose()
        if len(subproblems) > 1:
            if self.print_debug_info:
                print(f"Decomposed into {len(subproblems)} subproblems.")
                print("Original:")
                print(self.to_string())
                for i, solver in enumerate(subproblems):
                    print(f"Subproblem {i}/{len(subproblems)}:")
                    print(solver.to_string())
                print()
            # 如果分解后有多个子问题，递归求解
            try:
                results = [subproblem.try_probabilities() for subproblem in subproblems]
                total_solutions = 1
                total_probabilities = {}
                for r in results:
                    total_solutions *= r[0]
                    total_probabilities.update(r[1])
                return total_solutions, self._construct_full_probabilities(total_probabilities)
            except NoSolution:
                all_vars = list(v for v in self.x_mapping_v2i.keys() if v not in self.certain_solutions)
                return 0, self._construct_no_solution_probabilities()
            return
        
        # 找到参与约束数量最多的变量，下一个指标是这些约束涉及的所有变量之和要尽可能少
        constraint_count = np.zeros(self.matrix.shape[1]-1, dtype=np.int32)
        constraint_vars_count = np.zeros_like(constraint_count)
        for row_index in range(self.matrix.shape[0]):
            coeffs = self.matrix[row_index,:-1]
            nonzero_indices = np.nonzero(coeffs)[0]
            for col_index in nonzero_indices:
                constraint_count[col_index] += 1
                constraint_vars_count[col_index] += len(nonzero_indices)
        # 选择参与约束最多的变量
        max_constraint_idx = 0
        max_constraint_number = constraint_count[max_constraint_idx]
        for idx in range(1, len(constraint_count)):
            if constraint_count[idx] > max_constraint_number or (
                constraint_count[idx] == max_constraint_number and
                constraint_vars_count[idx] < constraint_vars_count[max_constraint_idx]
            ):
                max_constraint_idx = idx
                max_constraint_number = constraint_count[max_constraint_idx]

        # 如果所有方程解耦，这应当已经在上文的分解中被处理了
        if max_constraint_number <= 1:
            raise ValueError("How?")
        if self.print_debug_info:
            print(f"Trying variable {self._var_index_to_var_name(self.x_mapping_i2v[max_constraint_idx])}, affecting {max_constraint_number} constraints.")

        _solutions = [] # (number, probabilities)
        # 尝试该变量取为0或者1
        for guess_val in (0,1):
            # 引入新的约束
            new_matrix = np.concatenate([self.matrix, [
                [int(i==max_constraint_idx) for i in range(self.matrix.shape[1]-1)] + [guess_val]
            ]], axis=0)
            # 构造子问题
            new_solver = ZeroOneSolver(new_matrix, i2v=self.x_mapping_i2v.copy())
            # 求解该问题
            try:
                new_solution_number, new_solution = new_solver.try_probabilities()
                # 在问题的解中加入确定解
                new_solution.update({self.x_mapping_i2v[max_constraint_idx]: guess_val})
                # 记录该分支
                _solutions.append((new_solution_number, new_solution))
                if self.print_debug_info:
                    print(f"Found {new_solution_number} solutions with {self._var_index_to_var_name(self.x_mapping_i2v[max_constraint_idx])}={guess_val}.")
            except NoSolution:
                # 这种情况无解
                if self.print_debug_info:
                    print(f"No Solution with {self._var_index_to_var_name(self.x_mapping_i2v[max_constraint_idx])}={guess_val}.")
                pass
        # 合并两个子问题的解
        n=sum(s[0] for s in _solutions)
        if n==0:
            return n, self._construct_no_solution_probabilities()
        n, p = ZeroOneSolver.merge_probabilities(_solutions)
        return n, self._construct_full_probabilities(p)

    def try_all_solutions(self, seed=None):
        """
        遍历所有可能的解

        Yields:
            dict: 每个解的字典表示，其中键是原始变量下标，值是该变量的取值（0或1）。
        """ 
        try:
            self.simplify_full()
        except NoSolution:
            return

        # 通过设置试探解的方法，寻找所有的解
        if self.matrix.shape[1]<=1:
            # 没有变量，直接返回当前确定解
            yield self._construct_full_probabilities({})
            return

        # 初始化随机数生成器
        if isinstance(seed, np.random.Generator):
            rng = seed
        elif seed is not None:
            rng = np.random.Generator(np.random.PCG64(seed))
        else:
            rng = np.random.Generator(np.random.get_bit_generator())
        
        if self.matrix.shape[0]==0:
            # 没有约束，所有解都是可行的
            _uncertain_vars = [v for v in self.x_mapping_v2i.keys() if v not in self.certain_solutions]
            # 随机化变量顺序和0/1的输出顺序
            rng.shuffle(_uncertain_vars)
            _random_mask = rng.integers(0, 2, size=len(_uncertain_vars), dtype=np.int8)
            # 遍历所有的0-1组合
            for i in range(2**len(_uncertain_vars)):
                _solution = self.certain_solutions.copy()
                for j, idx in enumerate(_uncertain_vars):
                    _solution[idx] = ((i >> j) & 1) ^ _random_mask[j]
                yield self._construct_full_probabilities(_solution)
            return

        # 分解为子问题
        subproblems = self.decompose()
        if len(subproblems) > 1:
            if self.print_debug_info:
                print(f"Decomposed into {len(subproblems)} subproblems.")
                print("Original:")
                print(self.to_string())
                for i, solver in enumerate(subproblems):
                    print(f"Subproblem {i}/{len(subproblems)}:")
                    print(solver.to_string())
                print()
            # 如果分解后有多个子问题，递归求解。最终解是它们的组合。
            try:
                for solutions in itertools.product(*[sp.try_all_solutions(rng) for sp in subproblems]):
                    combined_solution = self.certain_solutions.copy()
                    for sol in solutions:
                        combined_solution.update(sol)
                    yield self._construct_full_probabilities(combined_solution)
                return
            except NoSolution:
                return
            return

        # 找到参与约束数量最多的变量，下一个指标是这些约束涉及的所有变量之和要尽可能少
        constraint_count = np.zeros(self.matrix.shape[1]-1, dtype=np.int32)
        constraint_vars_count = np.zeros_like(constraint_count)
        for row_index in range(self.matrix.shape[0]):
            coeffs = self.matrix[row_index,:-1]
            nonzero_indices = np.nonzero(coeffs)[0]
            for col_index in nonzero_indices:
                constraint_count[col_index] += 1
                constraint_vars_count[col_index] += len(nonzero_indices)
        # 选择参与约束最多的变量
        _max_constraint_key = None
        max_constraint_idxes = []
        for idx in range(len(constraint_count)):
            _key = (constraint_count[idx], -constraint_vars_count[idx])
            if _max_constraint_key is None or _key > _max_constraint_key:
                _max_constraint_key = _key
                max_constraint_idxes = [idx]
            elif _key == _max_constraint_key:
                max_constraint_idxes.append(idx)
        max_constraint_idx = rng.choice(max_constraint_idxes)

        # 尝试该变量取为0或者1
        for guess_val in ((0,1) if rng.random()<0.5 else (1,0)):
            # 引入新的约束
            new_matrix = np.concatenate([self.matrix, [
                [int(i==max_constraint_idx) for i in range(self.matrix.shape[1]-1)] + [guess_val]
            ]], axis=0)
            # 构造子问题
            new_solver = ZeroOneSolver(new_matrix, i2v=self.x_mapping_i2v)
            # 求解该问题
            try:
                for solution in new_solver.try_all_solutions(rng):
                    solution[self.x_mapping_i2v[max_constraint_idx]] = guess_val
                    yield self._construct_full_probabilities(solution)
            except NoSolution:
                # 这种情况无解
                pass
        return

    def simplify_full(self):
        "完全化简该系统，得到绝大多数确定的解"
        if self.print_debug_info:
            _before_simplification = self.to_string()

        changed = False
        loop_flag = True
        while loop_flag:
            loop_flag = False
            b0 = self.simplify_0()
            b1 = self.simplify_1()
            loop_flag |= b1
            changed |= b0 or b1
        # 使用简单方法求解
        loop_flag = True
        while loop_flag:
            loop_flag = False
            loop_flag |= self.get_solution_a()
            loop_flag |= self.get_solution_b()
            loop_flag |= self.get_solution_c()
            changed |= loop_flag

        if self.print_debug_info:
            if changed:
                print("Before Simplification:")
                print(_before_simplification)
                print("After Simplification:")
                print(self.to_string())
            else:
                print("Simplification did not change the system.")
                print(self.to_string())

        return changed

    @staticmethod
    def _solve_single_equation(coeffs, rhs, i2v=None):
        """
        求解单个方程的所有解，计算解的总个数，并计算每个变量为1的概率。

        Args:
            coeffs (np.ndarray): 方程的系数数组。
            rhs (int): 方程的右端值。
            i2v (dict, optional): 可选，原始变量下标到矩阵列指标的映射。

        Returns:
            tuple[int, dict]: 返回可行解的数量和概率分布字典，其中字典的键是原始变量下标，值是该变量取1的概率。
        """
        if i2v is None:
            i2v = {i:i for i in range(len(coeffs))}
        
        if ZeroOneSolver.print_debug_info:
            old_print_debug_info = ZeroOneSolver.print_debug_info
            ZeroOneSolver.print_debug_info = 0
            result = ZeroOneSolver._solve_single_equation(coeffs, rhs, i2v)
            ZeroOneSolver.print_debug_info = old_print_debug_info

            print(f"Solved single equation: {coeffs} = {rhs}")
            print(f"Number of solutions: {result[0]}")
            print(f"Probabilities: ")
            for v, p in result[1].items():
                print(f"  {ZeroOneSolver._var_index_to_var_name(v)}: {p}")
            return result

        def no_solution():
            return 0, {v:1/2 for v in i2v.values()}

        # 平凡单解
        if len(coeffs)==0:
            return int(rhs==0), {}
        if len(coeffs)==1:
            coeff = coeffs[0]
            if rhs==0:
                return 1, {i2v[0]: 0}
            elif rhs==coeff:
                return 1, {i2v[0]: 1}
            else:
                return 0, {i2v[0]: 0}

        # 存在0
        zero_indices = np.where(coeffs==0)[0]
        if len(zero_indices)>0:
            nonzero_indices = np.where(coeffs!=0)[0]
            num, probabilities_new = ZeroOneSolver._solve_single_equation(coeffs[nonzero_indices], rhs, i2v)
            probabilities = {}
            for i, idx in enumerate(nonzero_indices):
                probabilities[i2v[idx]] = probabilities_new[i]
            for idx in zero_indices:
                probabilities[i2v[idx]] = 1/2
            return num*2**len(zero_indices), probabilities

        # 全部相等
        if len(set(coeffs))==1:
            coeff = coeffs[0]
            if rhs%coeff!=0:
                return no_solution()
            rhs//=coeff
            if rhs>len(coeffs) or rhs<0:
                return no_solution()
            # print(f"All equal coefficients: {coeffs}, rhs={rhs}, number of solutions={comb(len(coeffs), rhs)}")
            return comb(len(coeffs), rhs), {i2v[i]: rhs/len(coeffs) for i in range(len(coeffs))}

        coeffs_with_indices = list(enumerate(coeffs))
        coeffs_with_indices_sorted = sorted(coeffs_with_indices, key=lambda x:(-abs(x[1]),x[1]>0))
        new_i2v = {j:i2v[coeffs_with_indices_sorted[j][0]] for j in range(len(coeffs))}
        np0 = ZeroOneSolver._solve_single_equation(coeffs[1:], rhs, new_i2v)
        np1 = ZeroOneSolver._solve_single_equation(coeffs[1:], rhs-coeffs[0], new_i2v)
        return ZeroOneSolver.merge_probabilities((np0, np1))

    @staticmethod
    def merge_probabilities(probs:list[tuple[int, dict]]):
        """
        合并多个概率分布
        """
        if len(probs)==0:
            raise ValueError("不能合并空气")
        if len(probs)==1:
            return probs[0]

        # 擦屁股
        probs_orig = probs
        probs = [(num, prob) for num, prob in probs if num>0]
        if len(probs)==0:
            return max(probs_orig, key=lambda x:-len(x[1])) # 返回长度最大的概率分布
        if len(probs)==1:
            return probs[0] # 只有一个非零解，直接返回

        dict_lengths = [len(prob) for _, prob in probs]
        if len(set(dict_lengths))>1:
            raise ValueError(f"概率分布的长度不一致: {dict_lengths} of {probs}")
        total_solutions = 0
        all_keys = set(probs[0][1].keys())
        total_probabilities = {}
        for num, prob in probs:
            if num==0:
                continue
            total_solutions += num
            for k,v in prob.items():
                if k not in all_keys:
                    raise ValueError(f"概率分布的键不一致: {k} 在 {prob} 中，但不在 {probs[0][1]} 中")
                if not 0<=v<=1:
                    raise ValueError(f"概率分布的值不在[0,1]范围内: {v} 在 {prob} 中")
                total_probabilities[k] = total_probabilities.get(k, 0) + num*v
        return total_solutions, {k: v/total_solutions for k, v in total_probabilities.items()}

class MineFieldSafe(MineField):
    """在点击的时候尝试重新布局，只要可以不踩雷就把雷搬走"""
    def __init__(self, height, width, num_mines):
        super().__init__(height, width, num_mines)
        self.detector = MineDetector(self)

    def reveal_cell(self, pos):
        # 如果已经翻开，直接返回0
        if self.revealed[pos]:
            return 0
        # 如果已经标记，原则上不能翻开
        if self.revealed[pos]==2:
            return 0
        if not self.field[pos]>=9:
            # 如果不是雷，直接翻开
            return super().reveal_cell(pos)
        # 如果是雷
        self.detector.refresh()
        if self.detector.known_mines[pos]:
            # 如果已经确定是雷，无法重新排布
            # print(f"Cell ({row}, {col}) is known to be a mine. Cannot rearrange.")
            return super().reveal_cell(pos)

        # 如果pos和已有信息完全无关，直接重新排布这些未知位置
        uninformed_cells = set()
        for cell in self.all_indices():
            if not self.detector.known_mines[cell] and not self.detector.known_empty[cell] and not self.detector.effective_unrevealed_cells[cell]:
                uninformed_cells.add(cell)
        if pos in uninformed_cells:
            mines_count_uninformed = sum(self.field[cell]>=9 for cell in uninformed_cells)
            uninformed_cells_without_target = uninformed_cells - {pos}
            if len(uninformed_cells_without_target) >= mines_count_uninformed:
                # 可以重新排布
                canditates = list(uninformed_cells_without_target)
                new_allocated_mines = set()
                while len(new_allocated_mines) < mines_count_uninformed:
                    new_allocated_mines.add(canditates.pop(self.rng.integers(len(canditates))))
                new_field = np.zeros_like(self.field)
                for cell in self.all_indices():
                    if cell not in uninformed_cells and self.field[cell]>=9 or cell in new_allocated_mines:
                        new_field[cell] = 9
                        for neighbor in self.all_neighbors(cell):
                            new_field[neighbor] += 1
                assert np.sum(new_field>=9) == self.num_mines, f"重新排布后雷的数量不正确：{np.sum(new_field>=9)} != {self.num_mines}"
                self.field = new_field
                return super().reveal_cell(pos)
        
        # 尝试求解使得 pos 不是雷的布局
        self.detector.update_known_cells(self.detector.get_diff())
        constraints = self.detector.get_constraints()
        matrix, cells = self.detector.constraint_to_matrix_form(constraints)
        # 添加一个额外约束
        matrix=np.concatenate([matrix, [[cells[i]==pos for i in range(len(cells))]+[0]]], axis=0)
        # 求解
        solver = ZeroOneSolver(matrix)
        for solution in solver.try_all_solutions():
            mine_list = []
            # add solutions
            for i, cell in enumerate(cells):
                if solution[i]==1:
                    mine_list.append(cell)
                else:
                    assert solution[i]==0, f"Invalid solution value {solution[i]} for cell {cell}"
            # add known mines
            for cell in self.all_indices():
                if self.detector.known_mines[cell]:
                    mine_list.append(cell)
            # print(mine_list)
            assert len(mine_list) >= np.count_nonzero(self.detector.known_mines), "Solution must include all known mines"
            if len(mine_list) > self.num_mines:
                # print(f"Too many mines in solution: already has {len(mine_list)}, total {self.num_mines}")
                continue
            if len(mine_list) + len(uninformed_cells) < self.num_mines:
                # print(f"Not enough mines in solution: already has {len(mine_list)}, uninformed cells {len(uninformed_cells)}, total {self.num_mines}")
                continue
            # 补全mine_list
            candidates = list(uninformed_cells)
            while len(mine_list) < self.num_mines:
                mine_list.append(candidates.pop(self.rng.integers(len(candidates))))
            new_field = np.zeros_like(self.field)
            for cell in mine_list:
                new_field[cell] = 9
                for cell in self.all_neighbors(cell):
                    new_field[cell] += 1
            # 最后检查
            consistent = True
            for cell in self.all_indices():
                if self.revealed[cell]!=1:
                    continue
                if new_field[cell] != self.field[cell]:
                    consistent = False
                    # print(f"Inconsistent revealed cell at {cell}: old={self.field[cell]}, new={new_field[cell]}")
                    break
            if consistent:
                self.field = new_field
                return super().reveal_cell(pos)
        # print(f"No valid rearrangement found to avoid mine at ({row}, {col}).")
        # 如果没有可行解，直接翻开
        return super().reveal_cell(pos)


class MineGameSafe(MineGame):
    def __init__(self, height, width, num_mines):
        super().__init__(height, width, num_mines)
        self.minefield = MineFieldSafe(height, width, num_mines)
        self.detector = self.minefield.detector


def run_console_game():
    game = MineGame(9, 9, 10)
    while not game.game_over:
        print(game.to_string())
        action = input("Enter action (r row col / m row col / n row col): ")
        parts = action.split()
        if len(parts) != 3:
            print("Invalid input. Please enter action and coordinates.")
            continue
        cmd, row_str, col_str = parts
        try:
            row = int(row_str)
            col = int(col_str)
        except ValueError:
            print("Invalid coordinates. Please enter integers.")
            continue
        pos = (row, col)
        if cmd == 'r':
            game.reveal_cell(pos)
        elif cmd == 'm':
            game.mark_cell(pos)
        elif cmd == 'n':
            game.reveal_neighbors(pos)
        else:
            print("Unknown command. Use 'r' to reveal, 'm' to mark, 'n' to reveal neighbors.")
    
    print(game.to_string())


def run_single_game(height, width, mines, interactive=False):
    game = MineGame(height, width, mines)
    detector = game.detector
    game.reveal_cell(((game.minefield.height-1)//2, (game.minefield.width-1)//2))
    while not game.game_over:
        detector.refresh()

        new_known_mines=[]
        new_known_empty=[]
        for cell in game.minefield.all_indices():
            if detector.known_mines[cell] and game.minefield.revealed[cell]!=2:
                new_known_mines.append(cell)
            elif detector.known_empty[cell] and game.minefield.revealed[cell]!=1:
                new_known_empty.append(cell)

        if interactive:
            print(game.to_string())
            print("Known mines:", new_known_mines)
            print("Known empty:", new_known_empty)
            
            if not new_known_empty and not new_known_mines:
                print("Current Equations:")
                print(ZeroOneSolver.matrix_to_string(detector._solver.matrix_orig))
                print("Current Probabilities:")
                for cell in game.minefield.all_indices():
                    if detector.effective_unrevealed_cells[cell]:
                        prob = float(detector.probabilities[cell])
                        print(f"{cell}: {prob:.2%}")
            
                input("Press Enter to continue...")

        if not new_known_mines and not new_known_empty:
            # 没有新的确定解，选择概率最小的格子翻开
            candidates = []
            for cell in game.minefield.all_indices():
                if game.minefield.revealed[cell]==0:
                    candidates.append(cell)
            candidates.sort(key=lambda cell: float(detector.probabilities[cell]))
            if candidates:
                game.reveal_cell(candidates[0])
            else:
                break
        
        for pos in new_known_mines:
            game.mark_cell(pos)
        for pos in new_known_empty:
            game.reveal_cell(pos)

    if interactive:
        print(game.to_string())
    
    return {
        "victory": game.victory,
        "progress": game.minefield.num_cells - game.unrevealed_count, 
        "progress_total": game.minefield.num_cells - game.minefield.num_mines,
        "marked": game.marked_count,
        "marked_total": game.minefield.num_mines
    }



def run_batch(height, width, mines, repeat, save):
    import tqdm
    import multiprocessing as mp

    pool = mp.Pool()
    pbar = tqdm.tqdm(range(repeat))
    tasks = []
    def callback(result):
        pbar.update()
        with open(save, 'a') as f:
            f.write(f"{height}x{width}-{mines}:{'W' if result['victory'] else 'L'},progress={result['progress']}/{result['progress_total']},marked={result['marked']}/{result['marked_total']}\n")
    
    for _ in range(repeat):
        tasks.append(pool.apply_async(run_single_game, args=(height, width, mines), callback=callback))

    for task in tasks:
        task.wait()


def test_safegame():
    game = MineGameSafe(16, 30, 99)
    game.reveal_cell(((game.minefield.height-1)//2, (game.minefield.width-1)//2))
    while not game.game_over:
        print(game.to_string())
        game.detector.refresh()
        revealed = False
        # 专门找有雷的格子翻开
        for cell in game.minefield.all_indices():
            if game.minefield.field[cell]<9:
                continue
            if game.detector.effective_unrevealed_cells[cell]:
                input(f"Revealing cell {cell} which is a mine. Press Enter to continue...")
                game.reveal_cell(cell)
                revealed = True
                break
        if revealed:
            continue
        # 找不到就随便翻
        all_indices_shuffled = list(game.minefield.all_indices())
        np.random.shuffle(all_indices_shuffled)
        for cell in all_indices_shuffled:
            if not game.detector.known_mines[cell] and game.minefield.revealed[cell]==0:
                input(f"Revealing cell {cell}. Press Enter to continue...")
                game.reveal_cell(cell)
                break
        if revealed:
            continue

    print(game.to_string())


def main_save_batch(difficulty = "expert"):
    run_batch(
        16, 30, 99, 
        100, "run_batch_expert.txt"
    )
    with open(f"run_batch_{difficulty}.txt", 'r') as f:
        lines = f.readlines()
    lines = [line for line in lines if line.strip()]
    wins = sum(1 for line in lines if line.split(':')[1].startswith('W'))
    print(f"Wining rate ({difficulty}):{wins}/{len(lines)}={wins/len(lines)*100:.2f}%")

