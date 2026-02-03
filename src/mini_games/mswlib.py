"""
一个令人舒适的扫雷游戏基本逻辑代码
"""

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
    def __init__(self, minefield:MineField, seed=None):
        self.minefield = minefield
        self.rng = np.random.Generator(np.random.PCG64(seed=seed))
        self.old_field_cover = np.copy(minefield._cover)
        self.confident_suggestions = np.zeros_like(minefield._cover, dtype=np.int32)  # 0表示无建议，1表示挖开，2表示插旗
        self.probability_suggestions = np.full_like(minefield._cover, fill_value=-1, dtype=np.float32)  # -1表示无建议，0~1表示地雷概率
        self.probabilities_max = self.probability_suggestions.copy()
        self.probabilities_min = self.probability_suggestions.copy()
        self.conflicting_positions = []
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
            # # 求解该线性不定方程组，得到多个线性无关的解
            # # 假设变量个数为N
            # A = np.array(equations, dtype=np.float32)
            # from scipy.linalg import lu, svd
            # from scipy.stats import qmc
            # P, L, U = lu(A[:,:-1])
            # U_rank = np.linalg.matrix_rank(U)
            # U_reduced = U[:U_rank, :]
            # U_svd_U, U_svd_S, U_svd_Vh = svd(U_reduced)
            # null_space_dimension = U.shape[1] - U_rank
            # null_space_basis = U_svd_Vh[U_rank:, :].T  # 每一列是一个基向量，形状为(N, K)，K为零空间维度
            # particular_solution = np.linalg.lstsq(A[:,:-1], A[:,-1], rcond=None)[0] # (N, )
            # # 蒙特卡洛撒点
            # sample_count = 10_000
            # sample_points = qmc.LatinHypercube(d=null_space_dimension, rng=self.rng).random(n=sample_count) # (sample_count, K)
            # sample_point_projected = sample_points @ null_space_basis.T + particular_solution  # (sample_count, N)
            # if soft_total_mine_constraint is not None:
            #     sample_point_projected = sample_point_projected[np.all(sample_point_projected>=soft_total_mine_constraint[0], axis=1) & np.all(sample_point_projected<=soft_total_mine_constraint[1], axis=1)]
            # if sample_point_projected.shape[0] == 0:
            #     return
            # # 计算每个变量为雷的比例
            # for pos, index in positions_to_index.items():
            #     values = sample_point_projected[:, index]
            #     values_clipped = np.clip(values, 0.0, 1.0)
            #     self.probability_suggestions[pos] = np.mean(values_clipped)
            #     self.probabilities_min[pos] = np.min(values_clipped)
            #     self.probabilities_max[pos] = np.max(values_clipped)

            # 更为稳定的做法：迭代算法
            equations = np.array(equations, dtype=np.float64)
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
    def __init__(self, rows, cols, mines, first_click_pos = None, seed=None, timeout=1):
        super().__init__(rows, cols, mines, first_click_pos, seed)
        self.timeout = timeout

    def re_generate(self, no_mine_pos):
        if not self.is_mine(no_mine_pos) or self.is_exposed(no_mine_pos):
            return True  # 该位置本来就不是雷，或者已经翻开，无需重新生成
        
        minefield_copy = MineField(self.rows, self.cols, self.mines, first_click_pos=None)
        minefield_copy._content = np.copy(self._content)
        minefield_copy._cover = np.where(self._cover==1, 1, 0)  # 只保留已翻开的格子状态

        # 先进行确定性分析
        advisor = MineFieldAdvisor(minefield_copy)
        advisor.analyze()
        if advisor.confident_suggestions[no_mine_pos]==2:
            return False # 无法重新生成一个合法的雷区布局
        elif advisor.confident_suggestions[no_mine_pos]==1:
            return True  # 已经安全，无需重新生成

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
            mines_count_in_untouched = len([pos for pos in untouched_positions if minefield_copy.is_mine(pos)]) + 1 # 需要额外放置一个雷
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
                return True

        # 强行让no_mine_pos不是雷，试图找出其它一定是雷的位置
        minefield_copy._content[no_mine_pos] = -9  # 临时标记该位置不是雷
        minefield_copy._cover[no_mine_pos] = 1  # 临时标记该位置已翻开
        advisor.analyze()
        if advisor.conflicting_positions:
            return False  # 无法重新生成一个合法的雷区布局
        
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
                return True
            except RuntimeError:
                return False  # 无法重新生成一个合法的雷区布局

        # print(self)
        # 存在信息的部分
        touched_positions = [
            pos for pos in minefield_copy.all_places() 
            if not minefield_copy.is_exposed(pos)
            and any(minefield_copy.is_exposed(n) for n in minefield_copy.neighbors(pos))
            and pos != no_mine_pos
        ]
        # 如果需要挖的格子在存在信息的部分，
        if any(minefield_copy.is_exposed(n) for n in minefield_copy.neighbors(no_mine_pos)):
            # 找出全部的约束条件
            constraints = []
            position_to_index = {pos: idx for idx, pos in enumerate(touched_positions)}
            for pos in exposed_number_positions:
                if not any(n in touched_positions for n in minefield_copy.neighbors(pos)):
                    continue
                number = minefield_copy.get_exposed_number(pos)
                flagged_count = len([p for p in minefield_copy.neighbors(pos) if p in certain_mine_positions])
                const_term = number - flagged_count
                
                coeffs = np.zeros(len(touched_positions)+1, dtype=np.int32)
                for p in minefield_copy.neighbors(pos):
                    if p in touched_positions:
                        coeffs[position_to_index[p]] = 1
                coeffs[-1] = const_term
                constraints.append(coeffs)

            constraints = np.array(constraints, dtype=np.int32)
            A = constraints[:,:-1]
            b = constraints[:,-1]
            # 找到使得该约束条件成立的一组0-1解
            # TODO: 以下代码不能正常工作，有待修改
            dp = {}
            def backtrack(index, current_assignment):
                if index == len(touched_positions):
                    # 检查约束条件是否满足
                    return np.array_equal(A@current_assignment, b)
                key = (index, tuple(current_assignment))
                if key in dp:
                    return dp[key]
                # 尝试不放置雷
                current_assignment.append(0)
                if backtrack(index+1, current_assignment):
                    dp[key] = True
                    current_assignment.pop()
                    return True
                current_assignment.pop()
                # 尝试放置雷
                current_assignment.append(1)
                if backtrack(index+1, current_assignment):
                    dp[key] = True
                    current_assignment.pop()
                    return True
                current_assignment.pop()
                dp[key] = False
                return False
            assignment = []
            if not backtrack(0, assignment):
                raise RuntimeError("No valid assignment found during re-generation")
            assert len(assignment) == len(touched_positions), "Assignment length mismatch during re-generation; expected: " + str(len(touched_positions)) + ", got: " + str(len(assignment))
            assert constraints @ assignment == np.zeros(len(constraints), dtype=np.int32), "Constraints not satisfied during re-generation"
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

        # 最后的尝试：随机放置剩下的雷，直到符合要求为止
        # print("Re-generating minefield with", len(positions_to_be_changed), "changeable positions and", mines_left, "mines left to place")
        # print(minefield_copy)

        start_time = time.process_time()
        _repeat = 0
        while True:
            _repeat+=1
            if time.process_time() - start_time > self.timeout:
                # print("Re-generation timeout after", self.timeout, "seconds and", _repeat, "attempts")
                return False  # 超时，无法重新生成一个合法的雷区布局
            minefield_copy._content.fill(0)
            # 放置已有的雷
            for pos in certain_mine_positions:
                minefield_copy._content[pos] = 9
            # 随机放置剩下的雷
            selected_positions = self.rng.choice(len(positions_to_be_changed), size=mines_left, replace=False)
            for index in selected_positions:
                pos = positions_to_be_changed[index]
                minefield_copy._content[pos] = 9
            # 计算周围数字
            content_addition_numbers = np.zeros_like(minefield_copy._content)
            for pos in minefield_copy.all_places():
                if minefield_copy.is_mine(pos):
                    for neighbor in minefield_copy.neighbors(pos):
                        content_addition_numbers[neighbor] += 1
            minefield_copy._content += content_addition_numbers
            # 检查是否符合已翻开的格子状态
            valid = True
            for pos in exposed_number_positions:
                if minefield_copy.is_mine(pos):
                    valid = False
                    break
                if minefield_copy.get_exposed_number(pos) != self.get_exposed_number(pos):
                    valid = False
                    break
            if valid:
                break
        # 应用新的布局
        self._content = minefield_copy._content
        return True
    
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
