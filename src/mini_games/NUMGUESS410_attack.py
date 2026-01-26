from math import log2
# import pickle
import time
import os


def _numcompare(digits1: tuple[int], digits2: tuple[int]) -> tuple[int]:
    # [1,2,3,4]&[2,3,3,5]->((A=)1, (B=)2)
    same_in_place = [digits1[i]==digits2[i] for i in range(4)]
    A = sum(same_in_place)

    count1 = [sum(d==i for d,ex in zip(digits1, same_in_place) if not ex) for i in range(10)]
    count2 = [sum(d==i for d,ex in zip(digits2, same_in_place) if not ex) for i in range(10)]
    B = sum(min(cnt1, cnt2) for cnt1, cnt2 in zip(count1, count2))

    return (A, B)


def numcompare_buffered(digits1: tuple[int], digits2: tuple[int]) -> tuple[int]:
    if digits1 < digits2:
        return ALL_ANSWERS_BUFFERED[(digits1, digits2)]
    elif digits1 > digits2:
        return ALL_ANSWERS_BUFFERED[(digits2, digits1)]
    else:
        return (4, 0)


class GameAttack:
    def __init__(self) -> None:
        self.history = []
        self.possible_answers = ALL_ANSWERS.copy()
        self.possible_answers = self.answer_sort(self.possible_answers)

    def answer_sort(self, answers: list[tuple[int]])-> list[tuple[int]]:
        return sorted(answers, key=lambda x: ((x not in self.possible_answers), tuple(i if i else 10 for i in x)))

    def add_record(self, guess: tuple[int], A: int, B: int):
        self.history.append((guess, (A, B)))
        self.possible_answers = [ans for ans in self.possible_answers if numcompare(ans, guess) == (A, B)]
        self.possible_answers = self.answer_sort(self.possible_answers)

    def get_next_move(self):
        # 假如选择了opt，结果信息熵变为了多少
        statistics = [] # (opt, entropy)
        _start_time = time.process_time()
        for opt in ALL_ANSWERS:
            if time.process_time() - _start_time > 30:
                raise TimeoutError("Computation took too long, aborting.")
            result_counts = {}
            for poss in self.possible_answers:
                result = numcompare(poss, opt)
                result_counts[result] = result_counts.get(result, 0) + 1
            entropy = sum(count * log2(count) for count in result_counts.values() if count > 0)
            statistics.append((opt, entropy))
        min_entropy = min(statistics, key=lambda x: x[1])[1]
        candidates = [opt for opt, ent in statistics if ent == min_entropy]
        
        return self.answer_sort(candidates)

    def get_next_move_within_results(self):
        statistics = [] # (opt, entropy)
        for opt in self.possible_answers:
            result_counts = {}
            for poss in self.possible_answers:
                result = numcompare(poss, opt)
                result_counts[result] = result_counts.get(result, 0) + 1

            entropy = sum(count * log2(count) for count in result_counts.values() if count > 0)
            statistics.append((opt, entropy))

        min_entropy = min(statistics, key=lambda x: x[1])[1]
        candidates = [opt for opt, ent in statistics if ent == min_entropy]
        
        return self.answer_sort(candidates)


class GameAttackUI(GameAttack):
    def get_input(self):
        while True:
            try:
                guess = tuple(int(i) for i in input("Enter your guess (4 digits): "))
                assert len(guess) == 4 and all(0 <= d <= 9 for d in guess)
            except EOFError:
                raise
            except Exception:
                print("Invalid input. Please enter 4 digits (0-9).")
                continue
            break
        while True:
            try:
                A = int(input("Enter number of CDCP: "))
                B = int(input("Enter number of CDWP: "))
                assert 0 <= A <= 4 and 0 <= B <= 4 and A + B <= 4
            except Exception:
                print("Invalid input. Please enter valid counts for A and B.")
                continue
            break
        return guess, A, B
    
    def format_answer(self, answer: tuple[int]) -> str:
        return ''.join(str(d) for d in answer)
    
    def format_answers(self, answers: list[tuple[int]]) -> str:
        if len(answers) <=20:
            return ', '.join(self.format_answer(ans) for ans in answers)
        else:
            return self.format_answers(answers[:20]) + f', ...(total {len(answers)})'
        
    def _get_suggested_firstmove_1(self):
        results = []
        for candidate in self.possible_answers:
            if not len(set(candidate))==4:
                continue
            results.append(candidate)
        return results
    
    def _get_suggested_firstmove_2(self):
        guess = self.history[0][0]
        assert self.history[0][1] == (0, 2)
        results = [] # should be: Recommended next guesses (only possible answers): 2546, 2547, 2548, 2549, 2540, 2563, 2573, 2583, 2593, 2503, 2645, 2647, 2648, 2649, 2640, 2653, 2673, 2683, 2693, 2603, ...(total 360)
        for candidate in self.possible_answers:
            if not len(set(candidate))==4:
                continue
            common_digits = set(guess) & set(candidate)
            places_of_common_digits = [candidate.index(d) for d in common_digits]
            if common_digits & {guess[i] for i in places_of_common_digits}:
                continue
            results.append(candidate)
        return results
    
    def _get_suggested_firstmove_3(self):
        guess = tuple(self.history[0][0])
        assert self.history[0][1] == (0, 1)
        repeated_digit = [d for d in guess if guess.count(d) > 1][0]
        places_of_individual_digits = [guess.index(d) for d in guess if d != repeated_digit]
        results = [] # should be: Recommended next guesses (only possible answers): 4516, 4517, 4518, 4519, 4510, 4526, 4527, 4528, 4529, 4520, 4561, 4562, 4571, 4572, 4581, 4582, 4591, 4592, 4501, 4502, ...(total 840)
        for candidate in self.possible_answers:
            if repeated_digit in candidate:
                continue
            if not len(set(candidate))==4:
                continue
            if set(guess) & {candidate[i] for i in places_of_individual_digits}:
                continue
            results.append(candidate)
        return results
    
    def mainloop(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Welcome to the Number Guessing Game Attack Tool!")
        # 硬编码的初始推荐，算出该推荐需要跑骇人的一个半小时代码
        print("Recommended next guesses (including non-possible answers): 1234, 1235, 1236, 1237, 1238, 1239, 1230, 1243, 1245, 1246, 1247, 1248, 1249, 1240, 1253, 1254, 1256, 1257, 1258, 1259, ...(total 5040)")
        print("Recommended next guesses (only possible answers): 1234, 1235, 1236, 1237, 1238, 1239, 1230, 1243, 1245, 1246, 1247, 1248, 1249, 1240, 1253, 1254, 1256, 1257, 1258, 1259, ...(total 5040)")
        while True:
            guess, A, B = self.get_input()
            self.add_record(guess, A, B)
            print(f"\nPossible answers remaining: {len(self.possible_answers)}")

            # 对于一些常见的情况打表
            if len(self.history)==1 and self.history[0][1]==(0,0):
                print("Recommended next guesses:", self.format_answers(self._get_suggested_firstmove_1()))
                continue
            elif len(self.history)==1 and len(set(self.history[0][0]))==4:
                if len(self.possible_answers) == 3048 and self.history[0][1]==(0,1):
                    print("Recommended next guesses (only possible answers):", self.format_answers(self._get_suggested_firstmove_1()))
                    continue
                elif len(self.possible_answers) == 1896 and self.history[0][1]==(0,2):
                    print("Recommended next guesses (only possible answers):", self.format_answers(self._get_suggested_firstmove_2()))
                    continue
                elif len(self.possible_answers) == 1372 and self.history[0][1]==(1,0):
                    print("Recommended next guesses (only possible answers):", self.format_answers(self._get_suggested_firstmove_1()))
                    continue
                elif len(self.possible_answers) == 1296 and self.history[0][1]==(0,0):
                    print("Recommended next guesses (only possible answers):", self.format_answers(self._get_suggested_firstmove_1()))
                    continue
                elif len(self.possible_answers) == 1260 and self.history[0][1]==(1,1):
                    print("Recommended next guesses (only possible answers):", self.format_answers(self._get_suggested_firstmove_1()))
                    continue
            elif len(self.history)==1 and len(set(self.history[0][0]))==3:
                if len(self.possible_answers) == 3052 and self.history[0][1]==(0,1):
                    print("Recommended next guesses (only possible answers):", self.format_answers(self._get_suggested_firstmove_3()))
                    continue
                elif len(self.possible_answers) == 2401 and self.history[0][1]==(0,0):
                    print("Recommended next guesses (only possible answers):", self.format_answers(self._get_suggested_firstmove_1()))
                    continue
      
            if len(self.possible_answers) == 0:
                print("No answers possible.")
                input("Good Luck!")
                return
            elif len(self.possible_answers)==1:
                print("The answer is:", self.format_answers(self.possible_answers))
                input("Have fun!")
                return 
            elif len(self.possible_answers)==2:
                print("The answers are:", self.format_answers(self.possible_answers))
                input("Try one of them and good luck!")
                return
            if len(self.possible_answers) <= 20:
                print("Possible answers:", self.format_answers(self.possible_answers))
            next_moves = self.get_next_move_within_results()
            print("Recommended next guesses (only possible answers):", self.format_answers(next_moves))
            try:
                if len(self.possible_answers) > 128:
                    raise RuntimeError("Skipping full search due to large number of possible answers.")
                next_moves = self.get_next_move()
                print("Recommended next guesses (including non-possible answers):", self.format_answers(next_moves))
            except (TimeoutError, RuntimeError):
                pass


ALL_ANSWERS = [(i,j,k,l) for i in range(10) for j in range(10) for k in range(10) for l in range(10)]

# print("Initializing  buffering numcompare results...")
# try:
#     with open('numguess_attack_buffer.pkl', 'rb') as f:
#         ALL_ANSWERS_BUFFERED = pickle.load(f)
# except FileNotFoundError:
#     import tqdm
#     pbar = tqdm.tqdm(total=len(ALL_ANSWERS)*(len(ALL_ANSWERS)-1)//2, desc="Buffering numcompare results")
#     ALL_ANSWERS_BUFFERED = {}
#     for a in ALL_ANSWERS:
#         for b in ALL_ANSWERS:
#             if a < b:
#                 ALL_ANSWERS_BUFFERED[(a, b)] = _numcompare(a, b)
#                 pbar.update(1)
#     pbar.close()
#     with open('numguess_attack_buffer.pkl', 'wb') as f:
#         pickle.dump(ALL_ANSWERS_BUFFERED, f)

# numcompare = numcompare_buffered
numcompare = _numcompare


if __name__ == "__main__":
    while True:
        try:
            game = GameAttackUI()
            game.mainloop()
        except EOFError:
            continue
        except KeyboardInterrupt:
            try:
                print()
                input("Press Ctrl+C again to exit, or Enter to restart the game.")
            except KeyboardInterrupt:
                raise SystemExit
