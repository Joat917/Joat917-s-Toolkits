from random import randint
from math import log2

ALL_ANSWERS = [[i, j, k, l] for i in range(10) for j in range(
    10) for k in range(10) for l in range(10)]


def numcompare(digits1: list[int], digits2: list[int]) -> tuple[int]:
    # [1,2,3,4]&[2,3,3,5]->((A=)1, (B=)2)
    compared = [False]*4

    A = 0
    for i in range(4):
        if digits1[i] == digits2[i]:
            A += 1
            compared[i] = True

    count1 = [0]*10
    count2 = [0]*10
    for i in range(4):
        if not compared[i]:
            count1[digits1[i]] += 1
            count2[digits2[i]] += 1
    B = 0
    for i in range(10):
        B += min(count1[i], count2[i])

    return (A, B)


class NumGuess:
    def __init__(self):
        self.answer = [randint(0, 9) for i in range(4)]
        self.guesstime = 0
        self.guesshistory = []  # [[2,3,3,5]->(1,2) pairs]
        # print("GameStart")

    def guess(self, string):
        if len(string) != 4:
            print('illegal input: length not 4')
            return

        inp = []
        for dig in string:
            try:
                inp.append(int(dig))
            except:
                print(f'illegal input: {dig} not a number')
                return

        result = numcompare(self.answer, inp)
        self.guesshistory.append((inp, result))
        self.guesstime += 1
        return result

    def __add__(self, val: str) -> str:
        result = self.guess(val)
        if result is None:
            return ""
        out = ""
        out += f"Your Guess: {val}\n"
        out += f"Correct Digit Correct Place(CDCP): {result[0]}\n"
        out += f"Correct Digit Wrong Place(CDWP): {result[1]}\n"
        return out

    def __repr__(self):
        out = ""
        out += "Guess(5,5) object\n"

        if self.guesshistory:
            out += "History: \n"
            for item in self.guesshistory:
                out += "".join([str(i) for i in item[0]])
                out += f": CDCP-{item[1][0]}; CDWP-{item[1][1]}\n"

        out += "Answer: "
        for i in self.answer:
            out += str(i)

        out += "\nGuessTime: %i\n" % self.guesstime
        return out


class Attack:
    def __init__(self) -> None:
        self.history = []
        self.possibles = ALL_ANSWERS+[]

        pass

    def addinfo(self, guess: str, A: int, B: int):
        if len(guess) != 4:
            print('illegal input: length not 4')
            return
        inp = []
        for dig in guess:
            try:
                inp.append(int(dig))
            except:
                print(f'illegal input: {dig} not a number')
                return

        self.history.append((inp, (A, B)))

        new_possibles = []
        for opt in self.possibles:
            if numcompare(opt, inp) == (A, B):
                new_possibles.append(opt)
        self.possibles = new_possibles
        return

    def getnextmove(self):
        statics = []  # (opt, index) pairs
        for opt in self.possibles:
            results = {}
            for poss in self.possibles:
                result = numcompare(poss, opt)
                if result in results:
                    results[result] += 1
                else:
                    results[result] = 1

            index = 0
            for value in results.values():
                index += log2(value)

            statics.append((opt, index))

        maxindex = max([i[1] for i in statics])

        suggested = []
        for i in statics:
            if i[1] == maxindex:
                suggested.append(i[0])

        return suggested

    def request(self):
        self.addinfo(input("Your guess:"), int(
            input("CDCP:")), int(input("CDWP:")))
        print(self.getnextmove())


def main():
    a = Attack()
    while True:
        a.request()
        print("possible answer number: ", len(a.possibles))


while True:
    try:
        main()
    except Exception:
        __import__('traceback').print_exc()
        input(":(\n")
