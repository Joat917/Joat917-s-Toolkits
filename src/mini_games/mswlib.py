"""
一个令人舒适的扫雷游戏基本逻辑代码
"""

import os, sys, ctypes
import numpy as np
import time

class MineField:
    def __init__(self, rows:int, cols:int, mines:int, first_click_pos:tuple[int,int]|None=None, seed=None):
        self.rows = rows
        self.cols = cols
        self.mines = mines
        self.first_click_pos = first_click_pos
        self.seed = seed
        self.rng = np.random.Generator(np.random.PCG64(seed=seed))
        self.ascii_only = False

        if self.mines<=0 or self.mines>self.cols*self.rows-8:
            raise ValueError("Illegal mine count")

        # 表示每个格子下方的内容。0~8表示周围雷的个数，大于等于9表示存在地雷
        self._content = np.zeros((rows, cols), dtype=np.int32)

        # 表示每个格子翻开和标记的情况。0表示未翻开，1表示翻开，2表示插旗，3或以上表示标记问号
        self._cover = np.zeros((rows, cols), dtype=np.int32)

        # 确定雷的位置
        mine_count = 0
        excluded_positions = set() # 不能放置雷的位置
        if first_click_pos is not None:
            excluded_positions.add(tuple(int(x) for x in first_click_pos))
            excluded_positions.update(self.neighbors(first_click_pos))
        continuous_unsuccessful_placements = 0
        
        while mine_count<self.mines:
            random_pos = (int(self.rng.integers(self.rows)), int(self.rng.integers(self.cols)))
            if random_pos in excluded_positions:
                continuous_unsuccessful_placements += 1
                if continuous_unsuccessful_placements > 100:
                    raise RuntimeError("Too few legal mine layout")
                continue
            continuous_unsuccessful_placements = 0
            self._content[random_pos] = 9
            excluded_positions.add(random_pos)
            mine_count += 1

        # 确定周围的数字
        content_addition_numbers = np.zeros_like(self._content)
        for pos in self.all_places():
            if self.is_mine(pos):
                for neighbor in self.neighbors(pos):
                    content_addition_numbers[neighbor] += 1
        self._content += content_addition_numbers

        assert len(np.where(self._content>=9)[0]) == self.mines, "Mine count mismatch"
        assert self.first_click_pos is None or self._content[self.first_click_pos]==0, "First click position is not safe"

    def all_places(self):
        for row in range(self.rows):
            for col in range(self.cols):
                yield row, col

    def neighbors(self, pos):
        row, col = pos
        for r, c in [
            (row-1, col-1), (row-1, col), (row-1, col+1),
            (row, col-1),                 (row, col+1),
            (row+1, col-1), (row+1, col), (row+1, col+1)
        ]:
            if 0<=r<self.rows and 0<=c<self.cols:
                yield int(r), int(c)

    def is_mine(self, pos):
        return self._content[pos] >= 9

    def is_flag(self, pos):
        return self._cover[pos] == 2
    
    def is_exposed(self, pos):
        return self._cover[pos] == 1
    
    def is_covered(self, pos):
        return self._cover[pos] == 0 or self._cover[pos] >= 3
    
    def get_exposed_number(self, pos):
        if not self.is_exposed(pos):
            raise ValueError("Chosen position is not exposed")
        return min(self._content[pos], 9)
    
    def dig(self, pos):
        if self.is_exposed(pos) or self.is_flag(pos):
            return False
        self._cover[pos] = 1
        if self.get_exposed_number(pos) == 0:
            for neighbor in self.neighbors(pos):
                self.dig(neighbor)
        return True
    
    def flag(self, pos, only_on=False):
        if not only_on and self.is_flag(pos):
            self._cover[pos] = 0
            return True
        elif self.is_covered(pos):
            self._cover[pos] = 2
            return True
        return False
    
    def digaround(self, pos):
        if not self.is_exposed(pos):
            return 0
        mines_count = self.get_exposed_number(pos)
        flagged_count = len([p for p in self.neighbors(pos) if self.is_flag(p) or self.is_exposed(p) and self.is_mine(p)])
        ret_val = 0
        if flagged_count>=mines_count:
            for p in self.neighbors(pos):
                if self.is_flag(p) or self.is_exposed(p) and self.is_mine(p):
                    continue
                self.dig(p)
                ret_val += 1
        return ret_val
    
    def flagaround(self, pos):
        ret_val = 0
        for p in self.neighbors(pos):
            if self.is_covered(p):
                self.flag(p)
                ret_val += 1
        return ret_val
    
    def is_safe(self):
        for pos in self.all_places():
            if self.is_exposed(pos) and self.is_mine(pos):
                return False
            if not self.is_exposed(pos) and not self.is_mine(pos):
                return False
        return True
    
    def is_dead(self):
        for pos in self.all_places():
            if self.is_exposed(pos) and self.is_mine(pos):
                return True
        return False
    
    def __str__(self):
        out = " |"
        # 制作表头
        out += "|".join("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"[:self.cols])
        out += "\n"

        if self.ascii_only:
            covered_cell = "?"
            flag_cell = "F"
            mine_cell = "X"
            other_cell = '!'
        else:
            covered_cell = "█"
            flag_cell = "⚑"
            mine_cell = "✹"
            other_cell = '·'

        for row in range(self.rows):
            # 制作行头
            line = ["123456789abcdefghijklmnopqrstuvwxyz"[row]]
            # 读取这一行的数据
            for col in range(self.cols):
                if self.is_covered((row, col)):
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
    
class MineFieldAdvisor:
    def __init__(self, minefield:MineField, seed=None, dense_analysis=True):
        self.minefield = minefield
        self.rng = np.random.Generator(np.random.PCG64(seed=seed))
        self.old_field_cover = np.copy(minefield._cover)
        self.confident_suggestions = np.zeros_like(minefield._cover, dtype=np.int32)  # 0表示无建议，1表示挖开，2表示插旗
        self.probability_suggestions = np.full_like(minefield._cover, fill_value=-1, dtype=np.float32)  # -1表示无建议，0~1表示地雷概率
        self.probabilities_max = self.probability_suggestions.copy()
        self.probabilities_min = self.probability_suggestions.copy()
        self.conflicting_positions = []
        self.dense_analysis = dense_analysis
        pass

    def _needs_recalculation(self):
        return not np.array_equal(self.old_field_cover, self.minefield._cover)

    def analyze(self):
        if not self._needs_recalculation():
            return
        # 初始化
        self.old_field_cover = np.copy(self.minefield._cover)
        self.confident_suggestions.fill(0)
        self.probability_suggestions.fill(-1)
        self.probabilities_max.fill(-1)
        self.probabilities_min.fill(-1)
        self.conflicting_positions.clear()

        # 简单分析：
        # 如果一个已翻开的格子的周围标记的旗子数等于它显示的数字，那么它周围未翻开的格子都可以安全挖开；
        # 如果一个已翻开的格子的周围未翻开的格子数等于它显示的数字减去标记的旗子数，那么这些未翻开的格子都可以插旗
        for pos in self.minefield.all_places():
            if not self.minefield.is_exposed(pos):
                continue
            number = self.minefield.get_exposed_number(pos)
            if not 1<=number<=8:
                continue
            flagged_count = len([p for p in self.minefield.neighbors(pos) if self.minefield.is_flag(p) or self.minefield.is_exposed(p) and self.minefield.is_mine(p)])
            covered_positions = [p for p in self.minefield.neighbors(pos) if self.minefield.is_covered(p)] # 未翻开的格子，不含已经插旗的格子
            covered_count = len(covered_positions)

            if flagged_count == number:
                for p in covered_positions:
                    self.confident_suggestions[p] = 1  # 安全挖开
            elif covered_count == number - flagged_count:
                for p in covered_positions:
                    self.confident_suggestions[p] = 2  # 插旗
            elif flagged_count > number:
                self.conflicting_positions.append(pos)
            elif flagged_count + covered_count < number:
                self.conflicting_positions.append(pos)

        # 概率分析：
        # 得到每个未翻开的格子被地雷占据的概率满足的线性方程组，
        # 然后消去变量后求解该不定方程组，得到约束条件，
        # 最后在整个概率空间中蒙特卡洛撒点，并投影到约束条件超平面上，得到满足该约束条件的比例
        positions_to_index = {}
        for pos in self.minefield.all_places():
            # 如果已经翻开或插旗，就跳过
            if not self.minefield.is_covered(pos):
                continue
            # 如果有确定建议，就跳过
            if self.confident_suggestions[pos] != 0:
                continue
            # 如果周围没有已翻开的格子，就跳过
            if all((not self.minefield.is_exposed(n)) for n in self.minefield.neighbors(pos)):
                continue
            # 如果该格子周围存在错误，则跳过
            if any((n in self.conflicting_positions) for n in self.minefield.neighbors(pos)):
                continue
            positions_to_index[pos] = len(positions_to_index)

        equations = [] # 假设有N个变量，那么该矩阵的形状为(M, N+1)，其中M为方程个数，最后一列为常数项
        for pos in self.minefield.all_places():
            if not self.minefield.is_exposed(pos):
                continue
            if pos in self.conflicting_positions:
                continue
            number = self.minefield.get_exposed_number(pos)
            if not 1<=number<=8:
                continue
            flagged_positions = [p for p in self.minefield.neighbors(pos) if self.minefield.is_flag(p) or self.minefield.is_exposed(p) and self.minefield.is_mine(p) or self.confident_suggestions[p]==2]
            flagged_count = len(flagged_positions)
            covered_positions = [p for p in self.minefield.neighbors(pos) if self.minefield.is_covered(p) and self.confident_suggestions[p]==0]
            coeffs = np.zeros(len(positions_to_index)+1, dtype=np.float32)
            for p in covered_positions:
                if p in positions_to_index:
                    coeffs[positions_to_index[p]] = 1.0
            const_term = number - flagged_count
            coeffs[-1] = const_term
            if np.any(coeffs):
                equations.append(coeffs)

        # 试图使用总雷数作为约束条件
        total_mines_flagged = len([pos for pos in self.minefield.all_places() if self.minefield.is_flag(pos) or self.confident_suggestions[pos]==2 or self.minefield.is_exposed(pos) and self.minefield.is_mine(pos)])
        remaining_mines = self.minefield.mines - total_mines_flagged
        remaining_untouched_positions = [pos for pos in self.minefield.all_places() if self.minefield.is_covered(pos) and all((not self.minefield.is_exposed(n)) for n in self.minefield.neighbors(pos)) and self.confident_suggestions[pos]==0 and pos not in positions_to_index]
        if len(remaining_untouched_positions) == 0:
            coeffs = np.zeros(len(positions_to_index)+1, dtype=np.float32)
            for pos in positions_to_index:
                coeffs[positions_to_index[pos]] = 1.0
            coeffs[-1] = remaining_mines
            equations.append(coeffs)
            soft_total_mine_constraint = None
        else:
            soft_total_mine_constraint = (remaining_mines-len(remaining_untouched_positions), remaining_mines)

        if len(equations) != 0 and len(positions_to_index) != 0:
            # 求解该线性不定方程组，得到多个线性无关的解
            equations = np.array(equations, dtype=np.int32)
            solver = ZeroOneSolver(equations[:,:-1], equations[:,-1])
            if self.dense_analysis:
                all_solutions = np.array(list(solver.get_solutions(timeout=0.2))).astype(np.float64)
            if self.dense_analysis and not solver.timeout_flag and all_solutions.shape and all_solutions.shape[0] > 0:
                # print(f"在总共{len(positions_to_index)}个变量的空间中，存在{len(equations)}个线性约束条件，满足这些约束条件的解共有{len(all_solutions)}个")
                for pos, index in positions_to_index.items():
                    self.probability_suggestions[pos] = np.mean(all_solutions[:, index])
                    self.probabilities_min[pos] = np.min(all_solutions[:, index])
                    self.probabilities_max[pos] = np.max(all_solutions[:, index])
            else:
                # 更为稳定的做法：迭代算法
                equations = equations.astype(np.float64)
                A = equations[:,:-1]
                b = equations[:,-1]
                from scipy.optimize import lsq_linear
                result = lsq_linear(A, b, bounds=(0.0, 1.0))
                solved_probabilities = result.x
                for pos, index in positions_to_index.items():
                    self.probability_suggestions[pos] = solved_probabilities[index]
                    # 由于该方法没有提供不确定性范围，故将最大最小值都设为该值
                    self.probabilities_min[pos] = solved_probabilities[index]
                    self.probabilities_max[pos] = solved_probabilities[index]

        # 补全剩下的格子
        mines_flagged = [pos for pos in self.minefield.all_places() if self.minefield.is_flag(pos) or self.confident_suggestions[pos]==2 or self.minefield.is_exposed(pos) and self.minefield.is_mine(pos)]
        total_mines_flagged = len(mines_flagged)
        total_suggested_mines = sum(self.probability_suggestions[pos] for pos in positions_to_index if self.probability_suggestions[pos]>=0 and (pos not in mines_flagged))
        remaining_mines = self.minefield.mines - total_mines_flagged - total_suggested_mines
        remaining_covered_positions = [pos for pos in self.minefield.all_places() if self.minefield.is_covered(pos) and self.confident_suggestions[pos]==0 and self.probability_suggestions[pos]==-1]
        remaining_covered_count = len(remaining_covered_positions)
        for pos in remaining_covered_positions:
            self.probability_suggestions[pos] = np.clip(remaining_mines / remaining_covered_count, 0.0, 1.0)


class MineFieldNoLosing(MineField):
    def __init__(self, rows, cols, mines, first_click_pos = None, seed=None):
        super().__init__(rows, cols, mines, first_click_pos, seed)

    def re_generate(self, no_mine_pos, verbose=False):
        if not self.is_mine(no_mine_pos) or self.is_exposed(no_mine_pos):
            return True  # 该位置本来就不是雷，或者已经翻开，无需重新生成            
        
        minefield_copy = MineField(self.rows, self.cols, self.mines, first_click_pos=None)
        minefield_copy._content = np.copy(self._content)
        minefield_copy._cover = np.where(self._cover==1, 1, 0)  # 只保留已翻开的格子状态

        # 打印调试信息
        def log(info):
            if not verbose:
                return
            if callable(info):
                info = info()
            print(info)

        # 先进行确定性分析
        advisor = MineFieldAdvisor(minefield_copy, dense_analysis=False)
        advisor.analyze()
        if advisor.conflicting_positions:
            log(f"确定性分析：当前雷区布局存在以下状态冲突：{advisor.conflicting_positions}")
        if advisor.confident_suggestions[no_mine_pos]==2:
            log(f"确定性分析：{no_mine_pos}无可避免为雷")
            return False # 无法重新生成一个合法的雷区布局
        elif advisor.confident_suggestions[no_mine_pos]==1:
            log(f"确定性分析：{no_mine_pos}被认为安全，尽管实际上并不安全")
            return True  # 已经安全，无需重新生成
        else:
            log(lambda:(
                f"确定性分析："
                f"{no_mine_pos}有{advisor.probability_suggestions[no_mine_pos]*100}%的概率是雷。"
                f"在所有未翻开的{sum(1 for pos in minefield_copy.all_places() if not minefield_copy.is_exposed(pos))}个格子中，"
                f"存在{sum(1 for pos in minefield_copy.all_places() if not minefield_copy.is_exposed(pos) and advisor.confident_suggestions[pos]==2)}个确定的雷、"
                f"{sum(1 for pos in minefield_copy.all_places() if not minefield_copy.is_exposed(pos) and advisor.confident_suggestions[pos]==1)}个确定的安全格子，"
                f"以及{sum(1 for pos in minefield_copy.all_places() if not minefield_copy.is_exposed(pos) and advisor.confident_suggestions[pos]==0)}个不确定的格子。"
            ))

        # 存在数字的位置
        exposed_number_positions = [pos for pos in minefield_copy.all_places() if minefield_copy.is_exposed(pos)]
        # 完全没有信息的格子，这些地方可以自由调度
        untouched_positions = [pos for pos in minefield_copy.all_places() 
                               if not minefield_copy.is_exposed(pos)
                               and all((not minefield_copy.is_exposed(n)) for n in minefield_copy.neighbors(pos))
                               and pos != no_mine_pos
                               ]
        # 如果需要挖的格子在完全没有信息的部分，直接洗牌该部分的所有格子即可
        if all((not minefield_copy.is_exposed(n)) for n in minefield_copy.neighbors(no_mine_pos)):
            log(f"无信息分析：目标位置{no_mine_pos}周围没有已翻开的格子")
            mines_count_in_untouched = len([pos for pos in untouched_positions if minefield_copy.is_mine(pos)]) + 1 # 需要额外放置一个雷
            log(f"无信息分析：需要在{len(untouched_positions)}个无信息格子中重新放置{mines_count_in_untouched}个雷")
            if len(untouched_positions) >= mines_count_in_untouched:
                selected_positions = self.rng.choice(len(untouched_positions), size=mines_count_in_untouched, replace=False)
                minefield_copy._content.fill(0)
                # 放置已有的雷
                for pos in self.all_places():
                    if self.is_mine(pos) and pos not in untouched_positions and pos != no_mine_pos:
                        minefield_copy._content[pos] = 9
                # 放置剩下的雷
                for index in selected_positions:
                    pos = untouched_positions[index]
                    minefield_copy._content[pos] = 9
                # 计算周围数字
                content_addition_numbers = np.zeros_like(minefield_copy._content)
                for pos in minefield_copy.all_places():
                    if minefield_copy.is_mine(pos):
                        for neighbor in minefield_copy.neighbors(pos):
                            content_addition_numbers[neighbor] += 1
                minefield_copy._content += content_addition_numbers
                assert len(np.where(minefield_copy._content>=9)[0]) == self.mines, "Mine count mismatch after re-generation; expected: " + str(self.mines) + ", got: " + str(len(np.where(minefield_copy._content>=9)[0]))
                assert all([self.get_exposed_number(pos)==minefield_copy.get_exposed_number(pos) for pos in exposed_number_positions]), "Exposed numbers mismatch after re-generation at " + str(exposed_number_positions) + "; original: " + str([self.get_exposed_number(pos) for pos in exposed_number_positions]) + ", new: " + str([minefield_copy.get_exposed_number(pos) for pos in exposed_number_positions])
                # 应用新的布局
                self._content = minefield_copy._content
                log(f"无信息分析：成功在{len(untouched_positions)}个无信息格子中重新放置{mines_count_in_untouched}个雷")
                return True
            else:
                log(f"无信息分析：无法在{len(untouched_positions)}个无信息格子中重新放置{mines_count_in_untouched}个雷")
        else:
            log(lambda:f"无信息分析：目标位置{no_mine_pos}周围存在{len([n for n in minefield_copy.neighbors(no_mine_pos) if minefield_copy.is_exposed(n)])}个已翻开的格子，不能简单重新放置")
        
        log(lambda:(
            f"无信息分析：在所有{sum(1 for pos in minefield_copy.all_places() if not minefield_copy.is_exposed(pos))}个未翻开的格子中，"
            f"{len(untouched_positions)}个完全没有信息的格子"
            f"（包含{len([pos for pos in untouched_positions if minefield_copy.is_mine(pos)])}个雷），"
            f"以及{len(set(pos2 for pos in exposed_number_positions for pos2 in minefield_copy.neighbors(pos) if not minefield_copy.is_exposed(pos2)))}有信息的格子"
            f"（包含{sum(1 for pos in set(pos2 for pos in exposed_number_positions for pos2 in minefield_copy.neighbors(pos) if not minefield_copy.is_exposed(pos2)) if minefield_copy.is_mine(pos))}）个雷）。"
        ))

        # 强行让no_mine_pos不是雷，试图找出其它一定是雷的位置
        minefield_copy._content[no_mine_pos] = -9  # 临时标记该位置不是雷
        minefield_copy._cover[no_mine_pos] = 1  # 临时标记该位置已翻开
        advisor.analyze()
        if advisor.conflicting_positions:
            log(f"强行尝试：【拒绝计算】强行让{no_mine_pos}不是雷会导致以下格子状态冲突：{advisor.conflicting_positions}")
            return False
        
        # 找出确定是雷的位置
        certain_mine_positions = [
            pos for pos in minefield_copy.all_places()
            if advisor.confident_suggestions[pos]==2
        ]
        # 一定不是雷的位置
        certain_nomine_positions = [
            pos for pos in minefield_copy.all_places()
            if advisor.confident_suggestions[pos]==1
            or minefield_copy.is_exposed(pos)
        ]
        # 可以自由调度的位置
        positions_to_be_changed = [
            pos for pos in minefield_copy.all_places()
            if not minefield_copy.is_exposed(pos)
            and pos not in certain_mine_positions
            and pos not in certain_nomine_positions
        ]
        # 这些自由调度的位置需要分配的雷数
        mines_left = self.mines - len(certain_mine_positions)
        if mines_left < 0 or mines_left > len(positions_to_be_changed):
            return False  # 无法重新生成一个合法的雷区布局
        if mines_left == 0:
            certain_nomine_positions.extend(positions_to_be_changed)
            positions_to_be_changed.clear()
        elif mines_left == len(positions_to_be_changed):
            certain_mine_positions.extend(positions_to_be_changed)
            positions_to_be_changed.clear()
            mines_left = 0

        log(
            f"强行尝试：在强行让{no_mine_pos}不是雷的前提下，"
            f"确定的雷有{len(certain_mine_positions)}个，"
            f"确定安全格子有{len(certain_nomine_positions)}个，"
            f"剩下{len(positions_to_be_changed)}个格子需要重新分配{mines_left}个雷"
        )

        # 没有可以调整位置的空间
        if len(positions_to_be_changed)==0:
            # 直接检查当前布局是否符合要求
            try:
                minefield_copy._content.fill(0)
                for pos in certain_mine_positions:
                    minefield_copy._content[pos] = 9
                if len(certain_mine_positions) != self.mines:
                    raise RuntimeError("Mine count mismatch during re-generation; expected: " + str(self.mines) + ", got: " + str(len(certain_mine_positions)))
                # 计算周围数字
                content_addition_numbers = np.zeros_like(minefield_copy._content)
                for pos in minefield_copy.all_places():
                    if minefield_copy.is_mine(pos):
                        for neighbor in minefield_copy.neighbors(pos):
                            content_addition_numbers[neighbor] += 1
                minefield_copy._content += content_addition_numbers
                for pos in exposed_number_positions:
                    if minefield_copy.is_mine(pos):
                        raise RuntimeError("Mine found in exposed position during re-generation at " + str(pos))
                    if minefield_copy.get_exposed_number(pos) != self.get_exposed_number(pos):
                        raise RuntimeError("Exposed number mismatch during re-generation at " + str(pos) + "; original: " + str(self.get_exposed_number(pos)) + ", new: " + str(minefield_copy.get_exposed_number(pos)))
                # 应用新的布局
                self._content = minefield_copy._content
                log(f"强行尝试：没有调整空间，但是成功生成了合法的雷区布局")
                return True
            except RuntimeError:
                log(f"强行尝试：没有调整空间，无法生成合法的雷区布局")
                return False  # 无法重新生成一个合法的雷区布局

        # 存在信息的部分
        assert minefield_copy.is_exposed(no_mine_pos), "During re-generation, the position to be changed should be treated as exposed; pos: " + str(no_mine_pos)
        touched_positions = [
            pos for pos in minefield_copy.all_places() 
            if not minefield_copy.is_exposed(pos)
            and any(minefield_copy.is_exposed(n) for n in minefield_copy.neighbors(pos))
        ]
        untouched_positions = [
            pos for pos in minefield_copy.all_places() 
            if not minefield_copy.is_exposed(pos)
            and not any(minefield_copy.is_exposed(n) for n in minefield_copy.neighbors(pos))
        ]
        log(f"强行尝试：存在已知信息的格子有{len(touched_positions)}个，需要在满足已存在数字的情况下分配{mines_left-len(untouched_positions)}~{mines_left}个雷")
        mines_to_distribute_range = (max(0, mines_left - len(untouched_positions)), min(mines_left, len(touched_positions)))
        if mines_to_distribute_range[0] > mines_to_distribute_range[1]:
            if mines_left > len(untouched_positions) + len(certain_mine_positions):
                log(f"强行尝试：需要分配的雷数{mines_left}超过了剩余的格子数{len(untouched_positions)+len(certain_mine_positions)}，无法生成合法的雷区布局")
                return False
            else:
                log(f"强行尝试：因为未知原因，无法在{len(touched_positions)}个格子中分配{mines_to_distribute_range[0]}~{mines_to_distribute_range[1]}个雷。")
                return False
                
        # 找出全部的约束条件
        constraints = []
        position_to_index = {pos: idx for idx, pos in enumerate(touched_positions)} # 从格子位置到变量索引的映射
        for pos in exposed_number_positions: # 对每个暴露的数字格子定义一个约束条件
            # 如果该数字格子周围没有需要调整的格子，就跳过
            neighbors_to_be_changed = [n for n in minefield_copy.neighbors(pos) if n in touched_positions]
            if not any(neighbors_to_be_changed):
                continue
            # 获得该数字格子周围的雷数，减去已经确定的雷数，得到剩下的雷数
            number = minefield_copy.get_exposed_number(pos)
            flagged_count = len([p for p in minefield_copy.neighbors(pos) if p in certain_mine_positions])
            const_term = number - flagged_count
            
            # 构造增广矩阵的一行
            coeffs = np.zeros(len(touched_positions)+1, dtype=np.int32)
            for p in neighbors_to_be_changed:
                coeffs[position_to_index[p]] = 1
            coeffs[-1] = const_term
            constraints.append(coeffs)

            log(lambda:f"约束{len(constraints)}：在{pos}周围的{neighbors_to_be_changed}，需要放入{const_term}个雷")

        constraints = np.array(constraints, dtype=np.int32)
        A = constraints[:,:-1]
        b = constraints[:,-1]
        rank_A = np.linalg.matrix_rank(A)
        rank_Ab = np.linalg.matrix_rank(constraints)
        
        log(f"在{A.shape[1]}自由度的空间中，存在{A.shape[0]}个线性约束条件。"
            f"系数矩阵的秩为{rank_A}，增广矩阵的秩为{rank_Ab}，"
            +("存在唯一解" if rank_A==rank_Ab else f"存在{rank_A-rank_Ab}维解空间" if rank_A<rank_Ab else "无解")
        )
        if rank_A > rank_Ab:
            log("强行尝试：约束条件之间存在矛盾，无解")
            return False  # 无法重新生成一个合法的雷区布局
        
        solver = ZeroOneSolver(A, b, verbose=verbose, guess=np.round([advisor.probability_suggestions[pos] for pos in touched_positions]))
        for assignment in solver.get_solutions():
            if not mines_to_distribute_range[0] <= sum(assignment) <= mines_to_distribute_range[1]:
                continue
            log(f"强行尝试：找到一个满足约束条件的解，在{len(touched_positions)}个有信息的格子中分配了{sum(assignment)}个雷，"
                f"剩下{mines_left-sum(assignment)}个雷需要在{len(untouched_positions)}个无信息的格子中分配"
            )
            # 应用该解
            minefield_copy._content.fill(0)
            for idx, pos in enumerate(touched_positions):
                if assignment[idx] == 1:
                    minefield_copy._content[pos] = 9
            for pos in certain_mine_positions:
                minefield_copy._content[pos] = 9
            # - 为剩下的部分分配雷
            mines_left = self.mines - len(certain_mine_positions) - sum(assignment)
            if mines_left < 0 or mines_left > len(untouched_positions):
                return False  # 无法重新生成一个合法的雷区布局
            selected_positions = self.rng.choice(len(untouched_positions), size=mines_left, replace=False)
            for index in selected_positions:
                pos = untouched_positions[index]
                minefield_copy._content[pos] = 9

            # 计算周围数字
            content_addition_numbers = np.zeros_like(minefield_copy._content)
            for pos in minefield_copy.all_places():
                if minefield_copy.is_mine(pos):
                    for neighbor in minefield_copy.neighbors(pos):
                        content_addition_numbers[neighbor] += 1
            minefield_copy._content += content_addition_numbers
            # 检查是否符合已翻开的格子状态
            for pos in exposed_number_positions:   
                if minefield_copy.is_mine(pos):
                    raise RuntimeError("Mine found in exposed position during re-generation at " + str(pos))
                if minefield_copy.get_exposed_number(pos) != self.get_exposed_number(pos):
                    raise RuntimeError("Exposed number mismatch during re-generation at " + str(pos) + "; original: " + str(self.get_exposed_number(pos)) + ", new: " + str(minefield_copy.get_exposed_number(pos)))
            # 应用新的布局
            self._content = minefield_copy._content
            return True
        
        log("强行尝试：无法找到满足约束条件的解")
        return False  # 无法重新生成一个合法的雷区布局

    
    def dig(self, pos):
        if self.is_exposed(pos) or self.is_flag(pos):
            return False
        if self.is_mine(pos):
            self.re_generate(no_mine_pos=pos)
        self._cover[pos] = 1
        if self.get_exposed_number(pos) == 0:
            for neighbor in self.neighbors(pos):
                self.dig(neighbor)
        return True

class ZeroOneSolver:
    "求解线性方程组Ax=b，其中A和x均只包含0和1，且A为稀疏矩阵"
    def __init__(self, A, b, verbose=False, show_pbar=False, guess=None):
        self.A = np.array(A)
        self.b = np.array(b)
        if guess is None:
            self.guess = np.zeros(self.A.shape[1], dtype=np.int32)
        else:
            self.guess = np.array(guess, dtype=np.int32)
        self.verbose = verbose
        self.show_pbar = show_pbar

        if verbose:
            print(self.A.tolist())
            print(self.b.tolist())
        self.vars_to_try = [] # (index, trying_value)构成的栈
        self.current_x = np.zeros(self.A.shape[1], dtype=np.int32)
        self.current_x.fill(-1) # -1表示未赋值，0和1表示已赋值的变量
        self.current_x_assignments = [] # 已经赋值的变量索引列表，用于回溯时撤销赋值

        self.successful_solutions = []
        self.revert_count = 0

        self._set_constraint_dof()
        self.timeout_flag = False
        
    def _try_new_var(self):
        "将一个新的变量入栈"
        for var_index in self.variable_order:
            if var_index not in {x[0] for x in self.vars_to_try} and self.current_x[var_index] == -1:
                if self.verbose:
                    print(f"尝试新变量：{var_index}")
                self.vars_to_try.append((var_index, 1-self.guess[var_index]))
                self.vars_to_try.append((var_index, self.guess[var_index])) # 先尝试猜测值，如果不成功再尝试相反的值
                return True
        return False
            
    def _set_constraint_dof(self):
        "计算每个约束的自由度，该约束中涉及的未赋值变量的所有可能排列组合"
        from math import comb as _comb, prod
        def comb(n, k): return _comb(n, k) if 0<=k<=n else 0
        self.dof_list = [] # 每个约束的自由度
        self.new_dof_list = [] # 每个约束在一个变量被赋值后的自由度
        for constraint_index in range(self.A.shape[0]):
            row = self.A[constraint_index]
            b_value = self.b[constraint_index]
            unassigned_vars = [var_index for var_index in np.argwhere(row).reshape(-1) if self.current_x[var_index] == -1]
            signed_vars = [var_index for var_index in np.argwhere(row).reshape(-1) if self.current_x[var_index] == 1]
            sum_to_assign = b_value - len(signed_vars)

            self.dof_list.append(comb(len(unassigned_vars), sum_to_assign))
            self.new_dof_list.append(max(comb(len(unassigned_vars)-1, sum_to_assign), comb(len(unassigned_vars)-1, sum_to_assign-1)))
        self.variable_order = sorted(range(self.A.shape[1]), key=lambda i: (prod(self.new_dof_list[j]/self.dof_list[j] for j in np.argwhere(self.A[:,i]).reshape(-1) if self.dof_list[j]), -np.sum(self.A[:,i]))) # 先尝试自由度减少较多的约束对应的变量；如果自由度相同，则尝试约束较多的变量
        
            
    def _apply_trying_vars(self):
        "从栈中取出正在尝试的变量，并应用到当前解上"
        if not self.vars_to_try:
            return False
        var_index, trying_value = self.vars_to_try.pop()
        self.current_x[var_index] = trying_value
        self.current_x_assignments.append(var_index)
        return self._apply_constraints()
        
    def _apply_constraints(self):
        # 搜索并应用约束
        changed = True
        while changed:
            self._set_constraint_dof()
            changed = False
            for constraint_index in range(self.A.shape[0]):
                if self.dof_list[constraint_index] >= 1:
                    continue
                # 读取该约束的系数和常数项
                row = self.A[constraint_index]
                b_value = self.b[constraint_index]
                # 计算该约束中已经被赋值为1的变量数量，以及未赋值的变量索引
                sum_assigned = 0
                unassigned_indices = []
                for var_index in np.argwhere(row).reshape(-1):
                    if self.current_x[var_index] == 1:
                        sum_assigned += 1
                    elif self.current_x[var_index] == -1:
                        unassigned_indices.append(var_index)
                if sum_assigned > b_value:
                    if self.verbose:
                        print(f"尝试：{self.current_x}")
                        print(f"约束{constraint_index}不满足：已经赋值为1的变量数量{sum_assigned}超过了常数项{b_value}")
                    return False
                if sum_assigned + len(unassigned_indices) < b_value:
                    if self.verbose:
                        print(f"尝试：{self.current_x}")
                        print(f"约束{constraint_index}不满足：可以赋值为1的变量个数{len(unassigned_indices)}加上现有数值{sum_assigned}无法达到常数项{b_value}")
                    return False
                if not unassigned_indices and sum_assigned != b_value:
                    if self.verbose:
                        print(f"尝试：{self.current_x}")
                        print(f"约束{constraint_index}不满足：没有未赋值的变量，变量和{sum_assigned}不等于常数项{b_value}")
                    return False
            
                sum_to_assign = b_value - sum_assigned
                if sum_assigned == 0:
                    for var_index in unassigned_indices:
                        self.current_x[var_index] = 0
                        self.current_x_assignments.append(var_index)
                    changed = True
                elif sum_to_assign == len(unassigned_indices):
                    for var_index in unassigned_indices:
                        self.current_x[var_index] = 1
                        self.current_x_assignments.append(var_index)
                    changed = True
        return True
    
    def _revert_trying_vars(self):
        "撤销正在尝试的变量的赋值"
        self.revert_count += 1
        while self.current_x_assignments:
            # 撤销导出的变量赋值，直至下一个值得尝试的变量
            var_index = self.current_x_assignments.pop()
            self.current_x[var_index] = -1
            # 如果刚才撤销的变量是下一个要尝试的变量，停止撤销
            if self.vars_to_try and var_index == self.vars_to_try[-1][0]:
                return
    
    def get_solutions(self, timeout=None):
        "生成所有满足约束条件的解"
        import tqdm
        pbar = tqdm.tqdm(desc="Solving...", disable=self.verbose or not self.show_pbar)

        start_time = time.process_time()
        self.timeout_flag = False
        self._apply_constraints()
        self._try_new_var()

        while True:
            if timeout and timeout>0 and time.process_time() - start_time > timeout:
                if self.verbose:
                    print("求解超时，停止搜索")
                self.timeout_flag = True
                return
            pbar.update(1)
            pbar.set_postfix({
                "Assigned": f"{sum(1 for value in self.current_x if value != -1)}/{len(self.current_x)}",
                "stack_size": len(self.vars_to_try),
                "revert_count": self.revert_count,
                "solutions_found": len(self.successful_solutions)
            }, refresh=False)

            if not self.vars_to_try:
                break
            # 导出该变量的赋值，并检查是否满足约束条件
            if not self._apply_trying_vars():
                # 如果不满足约束条件，撤销该变量的赋值，并尝试下一个变量
                self._revert_trying_vars()
                continue
            # 如果没有未赋值分量，输出该解
            if all(value != -1 for value in self.current_x):
                yield self.current_x.copy()
                self.successful_solutions.append(self.current_x.copy())
                # 撤销该变量的赋值，并尝试下一个变量
                self._revert_trying_vars()
                continue
            else:
                self._try_new_var()


class ZeroOneSolverCpp:
    inited = False
    @classmethod
    def _init_lib(cls):
        cpp_file_name = os.path.abspath(os.path.join(os.path.dirname(__file__), "mswlib_zeroonesolver.cpp"))
        if ' ' in cpp_file_name:
            cpp_file_name = f'"{cpp_file_name}"'  # 如果路径中包含空格，需要加引号
        if sys.platform=='win32':
            lib_name = os.path.abspath("mswlib_zeroonesolver.dll")
            if ' ' in lib_name:
                lib_name = f'"{lib_name}"'  # 如果路径中包含空格，需要加引号
            compile_command = f"g++ -O3 -shared -fPIC -o {lib_name} {cpp_file_name}"
        else:
            lib_name = os.path.abspath("mswlib_zeroonesolver.so")
            if ' ' in lib_name:
                lib_name = f'"{lib_name}"'  # 如果路径中包含空格，需要加引号
            compile_command = f"g++ -O3 -shared -fPIC -o {lib_name} {cpp_file_name}"
        os.system(compile_command)
        try:
            assert os.path.exists(lib_name), f"未找到生成的库文件：{lib_name}"
            cls._lib = _lib = ctypes.CDLL(lib_name)
            _lib.create_solver.argtypes = [ctypes.POINTER(ctypes.c_int), 
                                    ctypes.POINTER(ctypes.c_int),
                                    ctypes.POINTER(ctypes.c_int),
                                    ctypes.c_int]
            _lib.create_solver.restype = ctypes.c_void_p

            _lib.get_solutions.argtypes = [ctypes.c_void_p,
                                        ctypes.POINTER(ctypes.c_int),
                                        ctypes.POINTER(ctypes.c_int)]
            _lib.get_solutions.restype = ctypes.POINTER(ctypes.POINTER(ctypes.c_int))
        except Exception as e:
            print(f"无法加载C++求解器库，错误信息：{e}")
            print("将使用Python版本的求解器，性能可能较差")
            _lib = None
        inited = True

    def __init__(self, A, b, **kwargs):
        if not self.__class__.inited:
            self.__class__._init_lib()
        self.A=A=np.array(A, dtype=np.int32)
        self.b=b=np.array(b, dtype=np.int32)
        shape = np.array([A.shape[0], A.shape[1]], dtype=np.int32)
        A_flat = A.flatten().astype(np.int32)
        b_flat = b.astype(np.int32)
        
        # 调用C++函数
        solver = self._lib.create_solver(
            A_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
            shape.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
            b_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_int)),
            len(b_flat)
        )
        
        num_solutions = ctypes.c_int()
        num_vars = ctypes.c_int()
        solutions_ptr = self._lib.get_solutions(solver, 
                                        ctypes.byref(num_solutions),
                                        ctypes.byref(num_vars))
        
        # 转换结果为Python列表
        self.successful_solutions = solutions = []
        for i in range(num_solutions.value):
            sol = [solutions_ptr[i][j] for j in range(num_vars.value)]
            solutions.append(sol)
        
        # 清理
        self._lib.free_solutions(solutions_ptr, num_solutions.value)
        self._lib.delete_solver(solver)

        return solutions
    
    def get_solutions(self, timeout=None):
        return self.successful_solutions

    
    



if __name__ == "__main__":
    # # 测试
    # mf = MineFieldNoLosing(9, 9, 10)
    # advisor = MineFieldAdvisor(mf)
    # while True:
    #     print(mf)
    #     advisor.analyze()
    #     for pos in mf.all_places():
    #         if mf.is_mine(pos) and advisor.confident_suggestions[pos]==0:
    #             mf.dig(pos)
    #             break
    #     else:
    #         print("No more uncertain mines to test")
    #         break
    #     if mf.is_safe() or mf.is_dead():
    #         break
    # print(mf)
    pass
