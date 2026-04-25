import random

def why(n=None):
    """
    Original code by MATLAB
    WHY    Provides succinct answers to almost any question.
       WHY, by itself, provides a random answer.
       WHY(N) provides the N-th answer.
       Please embellish or modify this function to suit your own tastes.

       Copyright 1984-2014 The MathWorks, Inc.
    """
    dflt = None
    if n is not None:
        dflt = random.getstate()
        random.seed(n)
    choice = random.randint(1, 10)
    if choice == 1:
        a = special_case()
    elif choice in {2, 3, 4}:
        a = phrase()
    else: 
        a = sentence()
    a = a[0].upper() + a[1:]
    print(a)
    if n is not None:
        random.setstate(dflt)


# ------------------

def special_case():
    choice = random.randint(1, 12)
    match choice:
        case 1:
            return 'why not?'
        case 2:
            return "don't ask!"
        case 3:
            return "it's your karma."
        case 4:
            return 'stupid question!'
        case 5:
            return 'how should I know?'
        case 6:
            return 'can you rephrase that?'
        case 7:
            return 'it should be obvious.'
        case 8:
            return 'the devil made me do it.'
        case 9:
            return 'the computer did it.'
        case 10:
            return 'the customer is always right.'
        case 11:
            return 'in the beginning, God created the heavens and the earth...'
        case 12:
            return "don't you have something better to do?"


def phrase():
    choice = random.randint(1, 3)
    match choice:
        case 1:
            return f"for the {nouned_verb()} {prepositional_phrase()}."
        case 2:
            return f"to {present_verb()} {object_()}."
        case 3:
            return f"because {sentence()}"


def preposition():
    choice = random.randint(1, 2)
    match choice:
        case 1:
            return 'of'
        case 2:
            return 'from'


def prepositional_phrase():
    choice = random.randint(1, 3)
    match choice:
        case 1:
            return f"{preposition()} {article()} {noun_phrase()}"
        case 2:
            return f"{preposition()} {proper_noun()}"
        case 3:
            return f"{preposition()} {accusative_pronoun()}"


def sentence():
    return f"{subject()} {predicate()}."


def subject():
    choice = random.randint(1, 4)
    match choice:
        case 1:
            return proper_noun()
        case 2:
            return nominative_pronoun()
        case _:
            return f"{article()} {noun_phrase()}"


def proper_noun():
    choice = random.randint(1, 12)
    match choice:
        case 1:
            return 'Cleve'
        case 2:
            return 'Jack'
        case 3:
            return 'Bill'
        case 4:
            return 'Joe'
        case 5:
            return 'Pete'
        case 6:
            return 'Loren'
        case 7:
            return 'Damian'
        case 8:
            return 'Barney'
        case 9:
            return 'Nausheen'
        case 10:
            return 'Mary Ann'
        case 11:
            return 'Penny'
        case 12:
            return 'Mara'


def noun_phrase():
    choice = random.randint(1, 4)
    match choice:
        case 1:
            return noun()
        case 2:
            return f"{adjective_phrase()} {noun_phrase()}"
        case _:
            return f"{adjective_phrase()} {noun()}"


def noun():
    choice = random.randint(1, 6)
    match choice:
        case 1:
            return 'mathematician'
        case 2:
            return 'programmer'
        case 3:
            return 'system manager'
        case 4:
            return 'engineer'
        case 5:
            return 'hamster'
        case 6:
            return 'kid'


def nominative_pronoun():
    choice = random.randint(1, 5)
    match choice:
        case 1:
            return 'I'
        case 2:
            return 'you'
        case 3:
            return 'he'
        case 4:
            return 'she'
        case 5:
            return 'they'


def accusative_pronoun():
    choice = random.randint(1, 4)
    match choice:
        case 1:
            return 'me'
        case 2:
            return 'all'
        case 3:
            return 'her'
        case 4:
            return 'him'


def nouned_verb():
    choice = random.randint(1, 2)
    match choice:
        case 1:
            return 'love'
        case 2:
            return 'approval'


def adjective_phrase():
    choice = random.randint(1, 6)
    match choice:
        case 1 | 2 | 3:
            return adjective()
        case 4 | 5:
            return f"{adjective_phrase()} and {adjective_phrase()}"
        case 6:
            return f"{adverb()} {adjective()}"


def adverb():
    choice = random.randint(1, 3)
    match choice:
        case 1:
            return 'very'
        case 2:
            return 'not very'
        case 3:
            return 'not excessively'


def adjective():
    choice = random.randint(1, 7)
    match choice:
        case 1:
            return 'tall'
        case 2:
            return 'bald'
        case 3:
            return 'young'
        case 4:
            return 'smart'
        case 5:
            return 'rich'
        case 6:
            return 'terrified'
        case 7:
            return 'good'


def article():
    choice = random.randint(1, 3)
    match choice:
        case 1:
            return 'the'
        case 2:
            return 'some'
        case 3:
            return 'a'


def predicate():
    choice = random.randint(1, 3)
    match choice:
        case 1:
            return f"{transitive_verb()} {object_()}"
        case _: 
            return intransitive_verb()


def present_verb():
    choice = random.randint(1, 3)
    match choice:
        case 1:
            return 'fool'
        case 2:
            return 'please'
        case 3:
            return 'satisfy'


def transitive_verb():
    choice = random.randint(1, 10)
    match choice:
        case 1:
            return 'threatened'
        case 2:
            return 'told'
        case 3:
            return 'asked'
        case 4:
            return 'helped'
        case _: 
            return 'obeyed'


def intransitive_verb():
    choice = random.randint(1, 6)
    match choice:
        case 1:
            return 'insisted on it'
        case 2:
            return 'suggested it'
        case 3:
            return 'told me to'
        case 4:
            return 'wanted it'
        case 5:
            return 'knew it was a good idea'
        case 6:
            return 'wanted it that way'


def object_():
    choice = random.randint(1, 10)
    match choice:
        case 1:
            return accusative_pronoun()
        case _: 
            return f"{article()} {noun_phrase()}"


# ----------------------

class _WhyRunner:
    def __repr__(self):
        choice = random.randint(1, 10)
        if choice == 1:
            a = special_case()
        elif choice in {2, 3, 4}:
            a = phrase()
        else: 
            a = sentence()
        a = a[0].upper() + a[1:]
        print(a,end='')
        return ''
    def __call__(self, n=None):
        why(n)
whyRunner = _WhyRunner()
