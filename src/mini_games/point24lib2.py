"""
24点游戏的求解器
"""

from itertools import permutations, product
from math import isclose, nan, isfinite, prod
from collections import deque

class TreeNode:
    "运算树的节点"
    PRIORITY={'+':1, '-':1, '*':2, '/':2} # 运算符优先级
    def __init__(self, value:str, left:'TreeNode|int|None'=None, right:'TreeNode|int|None'=None):
        """
        Args:
            value (str): 节点的值，表示运算符
            left (TreeNode|int|None): 左子节点或数字
            right (TreeNode|int|None): 右子节点或数字
        """
        if not value in self.PRIORITY:
            raise ValueError("value must be one of '+', '-', '*', '/'")
        self.value=value
        self.left=left
        self.right=right

    def preorder(self):
        "前序遍历生成器"
        yield self
        if isinstance(self.left, TreeNode):
            yield from self.left.preorder()
        if isinstance(self.right, TreeNode):
            yield from self.right.preorder()

    def inorder(self):
        "中序遍历生成器"
        if isinstance(self.left, TreeNode):
            yield from self.left.inorder()
        yield self
        if isinstance(self.right, TreeNode):
            yield from self.right.inorder()

    def postorder(self):
        "后序遍历生成器"
        if isinstance(self.left, TreeNode):
            yield from self.left.postorder()
        if isinstance(self.right, TreeNode):
            yield from self.right.postorder()
        yield self

    def all_numbers(self):
        "输出所有数字"
        if isinstance(self.left, TreeNode):
            yield from self.left.all_numbers()
        else:
            yield self.left
        if isinstance(self.right, TreeNode):
            yield from self.right.all_numbers()
        else:
            yield self.right

    def __repr__(self):
        if self.right is None:
            if self.left is None:
                return f"TreeNode({repr(self.value)})"
            else:
                return f"TreeNode({repr(self.value)}, {repr(self.left)})"
        if self.left is None:
            return f"TreeNode({repr(self.value)}, right={repr(self.right)})"
        return f"TreeNode({repr(self.value)}, {repr(self.left)}, {repr(self.right)})"
    
    def __str__(self):
        left_expr = str(self.left) if not isinstance(self.left, TreeNode) else str(self.left)
        right_expr = str(self.right) if not isinstance(self.right, TreeNode) else str(self.right)

        need_left_parentheses = isinstance(self.left, TreeNode) and self.PRIORITY[self.value]>self.PRIORITY[self.left.value]
        need_right_parentheses = isinstance(self.right, TreeNode) and self.PRIORITY[self.value]>=self.PRIORITY[self.right.value]

        left_expr = f"({left_expr})" if need_left_parentheses else left_expr
        right_expr = f"({right_expr})" if need_right_parentheses else right_expr

        return f"{left_expr}{self.value}{right_expr}"
    
    def __eq__(self, other):
        if not isinstance(other, TreeNode):
            return False
        return self.value==other.value and self.left==other.left and self.right==other.right
    
    @staticmethod
    def assess(node:'TreeNode|int|float')->tuple:
        """评估节点的复杂度，用于化简表达式树时排序节点

        Args:
            node (TreeNode|int|float): 节点

        Returns:
            tuple: 评估结果，复杂度越高的节点返回值越大
        """
        if isinstance(node, TreeNode):
            parenthesis_count = str(node).count('(') # 括号数量是首要的复杂度指标
            node_count = sum(1 for _ in node.preorder())  # 节点总数其次
            numbers = tuple(node.all_numbers()) # 数字大小作为最后的复杂度指标
        else:
            # 对于数字：
            parenthesis_count = 0
            node_count = 1
            numbers = (node,)
        return (parenthesis_count, node_count, *numbers)

    def copy(self):
        left_copy = self.left.copy() if isinstance(self.left, TreeNode) else self.left
        right_copy = self.right.copy() if isinstance(self.right, TreeNode) else self.right
        return TreeNode(self.value, left_copy, right_copy)
    
    def evaluate(self, throw=False):
        """
        计算表达式树的值。

        Args:
            throw (bool, optional): 是否在除以零时抛出异常，默认为False
        """
        try:
            return eval(str(self))
        except Exception as e:
            if throw:
                raise e
            else:
                return nan

    def simplify(self):
        """
        利用交换律和结合律化简表达式树。
        """
        if isinstance(self.left, TreeNode):
            self.left.simplify()
        # 对于每一个连加减或者连乘除表达式，要求加/乘在先、减/除在后，而且要求右节点必须为数字，不能是同优先级的子树。
        # 化简连加表达式为仅左子树存在括号的形式
        if self.value=='+':
            if isinstance(self.right, TreeNode) and self.right.value=='+':
                # a+(b+c) -> (a+b)+c
                a = self.left
                b = self.right.left
                c = self.right.right
                a,b,c = sorted((a,b,c), key=TreeNode.assess)
                self.left = TreeNode('+', a, b)
                self.right = c
            elif isinstance(self.right, TreeNode) and self.right.value=='-':
                # a+(b-c) -> (a+b)-c
                a = self.left
                b = self.right.left
                c = self.right.right
                a,b = sorted((a,b), key=TreeNode.assess)
                self.value='-'
                self.left = TreeNode('+', a, b)
                self.right = c
        if self.value=='-':
            if isinstance(self.right, TreeNode) and self.right.value=='+':
                # a-(b+c) -> (a-b)-c
                a = self.left
                b = self.right.left
                c = self.right.right
                b,c = sorted((b,c), key=TreeNode.assess)
                self.left = TreeNode('-', a, b)
                self.right = c
            elif isinstance(self.right, TreeNode) and self.right.value=='-':
                # a-(b-c) -> (a+c)-b
                a = self.left
                b = self.right.left
                c = self.right.right
                a,c = sorted((a,c), key=TreeNode.assess)
                self.value='-'
                self.left = TreeNode('+', a, c)
                self.right = b
        # 化简连乘表达式
        if self.value=='*':
            if isinstance(self.right, TreeNode) and self.right.value=='*':
                # a*(b*c) -> (a*b)*c
                a = self.left
                b = self.right.left
                c = self.right.right
                a,b,c = sorted((a,b,c), key=TreeNode.assess)
                self.left = TreeNode('*', a, b)
                self.right = c
            elif isinstance(self.right, TreeNode) and self.right.value=='/':
                # a*(b/c) -> (a*b)/c
                a = self.left
                b = self.right.left
                c = self.right.right
                a,b = sorted((a,b), key=TreeNode.assess)
                self.value='/'
                self.left = TreeNode('*', a, b)
                self.right = c
        if self.value=='/':
            if isinstance(self.right, TreeNode) and self.right.value=='*':
                # a/(b*c) -> (a/b)/c
                a = self.left
                b = self.right.left
                c = self.right.right
                b,c = sorted((b,c), key=TreeNode.assess)
                self.left = TreeNode('/', a, b)
                self.right = c
            elif isinstance(self.right, TreeNode) and self.right.value=='/':
                # a/(b/c) -> (a*c)/b
                a = self.left
                b = self.right.left
                c = self.right.right
                a,c = sorted((a,c), key=TreeNode.assess)
                self.value='/'
                self.left = TreeNode('*', a, c)
                self.right = b
        
        if isinstance(self.right, TreeNode):
            self.right.simplify()
        
        # 对于全加减表达式，获取全部加数，排序后重新构建表达式树
        if self.value in ('+', '-'):
            # 获取全部加数
            tree_nodes = deque([self])
            addends = deque()
            subtrahends = deque()
            while isinstance(tree_nodes[0], TreeNode) and tree_nodes[0].value in ('+', '-'):
                if tree_nodes[0].value == '+':
                    addends.appendleft(tree_nodes[0].right)
                else:
                    subtrahends.appendleft(tree_nodes[0].right)
                tree_nodes.appendleft(tree_nodes[0].left)
            addends.appendleft(tree_nodes.popleft())

            # 排序加数
            addends = deque(sorted(addends, key=TreeNode.assess))
            subtrahends = deque(sorted(subtrahends, key=TreeNode.assess))

            # 重新构建表达式树
            current_node = tree_nodes.popleft()
            current_node.left = addends.popleft()
            while addends:
                current_node.value = '+'
                current_node.right = addends.popleft()
                current_node = tree_nodes.popleft() if tree_nodes else None
            while subtrahends:
                current_node.value = '-'
                current_node.right = subtrahends.popleft()
                current_node = tree_nodes.popleft() if tree_nodes else None

            assert not tree_nodes and not addends and not subtrahends
        # 对于全乘除表达式，获取全部乘数，排序后重新构建表达式树
        elif self.value in ('*', '/'):
            # 获取全部乘数
            tree_nodes = deque([self])
            multipliers = deque()
            divisors = deque()
            while isinstance(tree_nodes[0], TreeNode) and tree_nodes[0].value in ('*', '/'):
                if tree_nodes[0].value == '*':
                    multipliers.appendleft(tree_nodes[0].right)
                else:
                    divisors.appendleft(tree_nodes[0].right)
                tree_nodes.appendleft(tree_nodes[0].left)
            multipliers.appendleft(tree_nodes.popleft())

            # 排序乘数
            multipliers = deque(sorted(multipliers, key=TreeNode.assess))
            divisors = deque(sorted(divisors, key=TreeNode.assess))
            # 重新构建表达式树
            current_node = tree_nodes.popleft()
            current_node.left = multipliers.popleft()
            while multipliers:
                current_node.value = '*'
                current_node.right = multipliers.popleft()
                current_node = tree_nodes.popleft() if tree_nodes else None
            while divisors:
                current_node.value = '/'
                current_node.right = divisors.popleft()
                current_node = tree_nodes.popleft() if tree_nodes else None
            assert not tree_nodes and not multipliers and not divisors
            
        return self
    
    def is_fully_simplified(self):
        """
        检查表达式树是否已经无法再化简。

        Returns:
            bool: 如果无法再化简则返回True，否则返回False
        """
        return str(self) == str(self.copy().simplify())
        
    
    def full_simplify(self):    
        """
        重复调用simplify直到无法再化简为止。
        """
        previous_str = ""
        current_str = str(self)
        while previous_str != current_str:
            self.simplify()
            previous_str = current_str
            current_str = str(self)
        return self


_TREE_BUILDER_CACHE={} # 表达式树生成器缓存
def build_trees(node_count:int):
    """
    构建所有可能的表达式树结构。包括运算符，但是不包括数字。

    Args:
        node_count (int): 运算符数量

    Yields:
        TreeNode: 表达式树
    """
    if node_count == 0:
        yield None
        return
    if node_count in _TREE_BUILDER_CACHE:
        for tree in _TREE_BUILDER_CACHE[node_count]:
            yield tree.copy()
        return

    results = []
    for left_count in range(node_count):
        right_count = node_count - 1 - left_count
        for left_subtree in build_trees(left_count):
            for right_subtree in build_trees(right_count):
                for operator in ['+', '-', '*', '/']:
                    treenode = TreeNode(operator, left_subtree, right_subtree)
                    results.append(treenode)
                    yield treenode
    _TREE_BUILDER_CACHE[node_count] = tuple(results)
    

def set_numbers(tree:TreeNode, numbers:tuple)->TreeNode:
    """
    在表达式树中填入数字。将会覆写表达式树中的所有叶子节点。

    Args:
        tree (TreeNode): 表达式树
        numbers (tuple): 数字元组

    Returns:
        TreeNode: 填入数字后的表达式树
    """
    numbers_list = deque(numbers)
    for node in tree.preorder():
        if not isinstance(node.left, TreeNode):
            node.left = numbers_list.popleft()
        if not isinstance(node.right, TreeNode):
            node.right = numbers_list.popleft()
    return tree


def find_solutions(numbers:tuple, target:int=24, simpilified:bool=True, unique:bool=True):
    """
    查找给定数字能组成的所有表达式树，使其值等于目标值。

    Args:
        numbers (tuple): 数字元组
        target (int, optional): 目标值，默认为24
        simpilified (bool, optional): 是否返回化简后的表达式树，默认为True

    Yields:
        TreeNode: 满足条件的表达式树
    """
    visited=set()
    for tree in build_trees(len(numbers)-1):
        for num_permutation in permutations(numbers):
            tree_with_numbers = set_numbers(tree, num_permutation)
            value = tree_with_numbers.evaluate(throw=False)
            if not isclose(value, target):
                continue
            if simpilified and not tree_with_numbers.is_fully_simplified():
                continue
            result_tree = tree_with_numbers.copy()
            if unique:
                tree_str = str(result_tree)
                if tree_str in visited:
                    continue
                visited.add(tree_str)
            yield result_tree

def has_solution(numbers:tuple, target:int=24)->bool:
    """
    检查给定数字能否组成表达式树，使其值等于目标值。

    Args:
        numbers (tuple): 数字元组
        target (int, optional): 目标值，默认为24

    Returns:
        bool: 如果存在满足条件的表达式树则返回True，否则返回False
    """
    for node in find_solutions(numbers, target, simpilified=False, unique=False):
        return True
    return False

def has_solution_lite(numbers:tuple[int, int, int, int], target:int=24)->bool:
    """
    检查由四个数字组成的表达式能否等于目标值。
    """
    a,b,c,d = numbers
    def eval_with_catch(text):
        try:
            return eval(text)
        except Exception:
            return nan
    for i in "+-*/":
        for j in "+-*/":
            for k in "+-*/":
                text = f"(%i%s%i)%s(%i%s%i)" % (a, i, b, j, c, k, d)
                if isclose(eval_with_catch(text), target): return True
                text = f"(%i%s%i)%s(%i%s%i)" % (a, i, c, j, b, k, d)
                if isclose(eval_with_catch(text), target): return True
                text = f"(%i%s%i)%s(%i%s%i)" % (a, i, d, j, b, k, c)
                if isclose(eval_with_catch(text), target): return True
                for p, q, r, s in permutations([a, b, c, d], 4):
                    text = "((%i%s%i)%s%i)%s%i" % (p, i, q, j, r, k, s)
                    if isclose(eval_with_catch(text), target): return True
                    text = "(%i%s(%i%s%i))%s%i" % (p, i, q, j, r, k, s)
                    if isclose(eval_with_catch(text), target): return True
                    text = "%i%s((%i%s%i)%s%i)" % (p, i, q, j, r, k, s)
                    if isclose(eval_with_catch(text), target): return True
                    text = "%i%s(%i%s(%i%s%i))" % (p, i, q, j, r, k, s)
                    if isclose(eval_with_catch(text), target): return True
    return False


class DifficultyAssessor:
    """
    24点游戏难度评估器
    """
    def __init__(self, target:int=24):
        self.target=target
        self.factors_of_target = [i for i in range(2, target) if target % i == 0]
        self.factor_pairs = [(i, target // i) for i in self.factors_of_target if i <= target // i]

    def assess_solution(self, solution:TreeNode):
        # 评估单个解的难度

        # 是否是纯加减，或者唯一乘除项为1
        PURE_ADDSUB = True
        for node in solution.preorder():
            if node.value=='*':
                if not ( node.left==1 or node.right==1 ):
                    PURE_ADDSUB = False
                    break
            if node.value=='/':
                if not ( node.right==1 or node.left==node.right):
                    PURE_ADDSUB = False
                    break
        
        # 是否是纯乘法，或者唯一除项为1
        PURE_MULT = True
        for node in solution.preorder():
            if node.value=='+' or node.value=='-':
                PURE_MULT = False
                break
            if node.value=='/':
                if not ( node.right==1 ):
                    PURE_MULT = False
                    break

        # 最后一步是否含有非平凡的乘法
        LAST_MULT = {pair:False for pair in self.factor_pairs}
        if solution.value=='*':
            # 获取所有乘数
            multipliers = deque()
            tree_nodes = deque([solution])
            while isinstance(tree_nodes[0], TreeNode) and tree_nodes[0].value=='*':
                multipliers.appendleft(tree_nodes[0].right)
                tree_nodes.appendleft(tree_nodes[0].left)
            multipliers.appendleft(tree_nodes.popleft())
            # 获取乘数的全部可能组合
            for comb in product((True, False), repeat=len(multipliers)):
                selected = [ multipliers[i] for i in range(len(multipliers)) if comb[i] ]
                selected = [ val.evaluate(throw=False) if isinstance(val, TreeNode) else val for val in selected ]
                if not selected:
                    continue
                prod_selected = prod(selected)
                for factor_pair in self.factor_pairs:
                    if prod_selected == factor_pair[0] or prod_selected == factor_pair[1]:
                        LAST_MULT[factor_pair] = True

        LAST_DIV_CONST = False # 最后一步是否是除数为常数的除法
        LAST_DIV_VAR = False # 最后一步是否是除数不为常数的除法（难度增加）
        if solution.value=='/':
            if not isinstance(solution.right, TreeNode):
                LAST_DIV_CONST = True
            else:
                LAST_DIV_VAR = True
        
        # 每一个子树的值
        subtree_values = set()
        for node in solution.preorder():
            val = node.evaluate(throw=False)
            try:
                if isfinite(val):
                    subtree_values.add(val)
            except Exception:
                pass
        # 如果含有很大的数字，或者含有非整数，难度增加
        HAS_LARGE = any( val > self.target for val in subtree_values )
        HAS_NONINT = any( not isclose(val, round(val)) for val in subtree_values )

        return {
            'PURE_ADDSUB': PURE_ADDSUB,
            'PURE_MULT': PURE_MULT,
            'LAST_MULT': LAST_MULT, 
            'LAST_DIV_CONST': LAST_DIV_CONST,
            'LAST_DIV_VAR': LAST_DIV_VAR,
            'HAS_LARGE': HAS_LARGE and not PURE_ADDSUB and not PURE_MULT,
            'HAS_NONINT': HAS_NONINT
        }

    def assess(self, numbers:tuple, all_unique_solutions:list=None)->dict:
        if all_unique_solutions is None:
            all_unique_solutions = list(find_solutions(numbers, self.target, simpilified=True, unique=True))
        HAS_PURE_ADDSUB = False
        HAS_PURE_MULT = False
        HAS_LAST_MULT = {pair:False for pair in self.factor_pairs}
        REQUIRES_LAST_DIV_CONST = True
        REQUIRES_LAST_DIV_VAR = True
        REQUIRES_LARGE = True
        REQUIRES_NONINT = True

        for solution in all_unique_solutions:
            assessment = self.assess_solution(solution)
            if assessment['PURE_ADDSUB']:
                HAS_PURE_ADDSUB = True
            if assessment['PURE_MULT']:
                HAS_PURE_MULT = True
            for pair in self.factor_pairs:
                if assessment['LAST_MULT'][pair]:
                    HAS_LAST_MULT[pair] = True
            if not assessment['LAST_DIV_CONST']:
                REQUIRES_LAST_DIV_CONST = False
            if not assessment['LAST_DIV_VAR']:
                REQUIRES_LAST_DIV_VAR = False
            if not assessment['HAS_LARGE']:
                REQUIRES_LARGE = False
            if not assessment['HAS_NONINT']:
                REQUIRES_NONINT = False
        
        
        return {
            'HAS_PURE_ADDSUB': HAS_PURE_ADDSUB,
            'HAS_PURE_MULT': HAS_PURE_MULT,
            'HAS_LAST_MULT': HAS_LAST_MULT,
            'REQUIRES_LAST_DIV_CONST': REQUIRES_LAST_DIV_CONST,
            'REQUIRES_LAST_DIV_VAR': REQUIRES_LAST_DIV_VAR,
            'REQUIRES_LARGE': REQUIRES_LARGE,
            'REQUIRES_NONINT': REQUIRES_NONINT
        }



if __name__=="__main__":
    # for i in range(2,7):
    #     print(len(list(build_trees(i))))
    # A151403: https://oeis.org/A151403

    import tqdm
    import json

    all_numbers_with_solutions = []
    for numbers in tqdm.tqdm(product(range(1, 14), repeat=4), total=13**4):
        if not all(numbers[i] <= numbers[i+1] for i in range(3)):
            continue
        if has_solution(numbers, 24):
            all_numbers_with_solutions.append(numbers)
    with open("point24_all_numbers_with_solutions.json", "w") as f:
        json.dump(all_numbers_with_solutions, f, indent=4)
    print(len(all_numbers_with_solutions))

    assessment_counts = {
        'HAS_PURE_ADDSUB': [],
        'HAS_PURE_MULT': [],
        'HAS_LAST_MULT': {(i, 24//i): [] for i in range(2, 13) if 24 % i == 0},
        'REQUIRES_LAST_DIV_CONST': [],
        'REQUIRES_LAST_DIV_VAR': [],
        'REQUIRES_LARGE': [],
        'REQUIRES_NONINT': [], 
        'NONE_OF_ABOVE': []
    }
    assessor = DifficultyAssessor(24)
    for numbers in tqdm.tqdm(all_numbers_with_solutions):
        assessment = assessor.assess(numbers)
        for key in assessment:
            if key == 'HAS_LAST_MULT':
                for pair in assessment[key]:
                    if assessment[key][pair]:
                        assessment_counts[key][pair].append(numbers)
            else:
                if assessment[key]:
                    assessment_counts[key].append(numbers)
        if not any( assessment[key] if key != 'HAS_LAST_MULT' else any(assessment[key].values()) for key in assessment ):
            assessment_counts['NONE_OF_ABOVE'].append(numbers)
    with open("point24_difficulty_assessment.json", "w") as f:
        json.dump(assessment_counts, f, indent=4)

