# import re

CHARACTER_TYPES = [
    'Ascii Letter'
    'Ascii Punctuation'
    'Ascii Control'
    'Latin Letter'
    'CJK Character'
    'SBC Symbols'
    'Others'
]

OUTPUT_TYPES = [
    'Latin'
    'CJK'
    'Punctuation'
    'Others'
]


def tellCharType(c: str):
    i = ord(c)
    if 65 <= i < 91 or 97 <= i < 123:
        return 'Ascii Letter'
    elif 0x20 <= i <= 0x7e:
        return 'Ascii Punctuation'
    elif 0xa0 <= i <= 0xbf:
        return 'SBC Symbols'
    elif i <= 0x9f:
        return 'Ascii Control'
    elif 0xc0 <= i <= 0x2af:
        return 'Latin Letter'
    elif 0x2e80 <= i <= 0x9fff or 0xf900 <= i <= 0xfaff:
        return 'CJK Character'
    elif 0x2000 <= i <= 0x206f or 0x3000 < i <= 0x303f or 0xff00 <= i <= 0xffef:
        return 'SBC Symbols'
    elif 0x2070 <= i <= 0x2bff:
        return 'SBC Symbols'
    else:
        return 'Others'

# pattern=re.compile(r'[^\w ]')


def count_words_in_line(line_of_text: str):
    "return dict[Type: List]"
    out = {}
    buf = ''

    def clearBuf():
        nonlocal buf
        if buf:
            pushOut('Latin', buf)
            buf = ''

    def pushOut(typ, cnt):
        out[typ] = out.get(typ, [])+[cnt]

    for c in line_of_text:
        current_type = tellCharType(c)
        match current_type:
            case 'Ascii Letter':
                buf += c
            case 'Ascii Control':
                clearBuf()
                pushOut('Control', c)
            case 'Ascii Punctuation':
                if buf:
                    if c == "'" and buf == "s":
                        buf = ''
                    else:
                        clearBuf()
                pushOut('Punctuation', c)
            case 'Latin Letter':
                buf += c
            case 'CJK Character':
                clearBuf()
                pushOut('CJK', c)
            case 'SBC Symbols':
                clearBuf()
                pushOut('Punctuation', c)
            case _:
                clearBuf()
                pushOut('Others', c)
    clearBuf()
    return out
    # texted=pattern.sub(' ', line_of_text.strip())
    # out=texted.split()
    # try:
    #     while True:
    #         out.remove('s')
    # except ValueError:
    #     return out


def dict_combine(*dics):
    if len(dics) == 0:
        return {}
    elif len(dics) == 1:
        return dics[0]
    out = {}
    for d in dics:
        for k, v in d.items():
            out[k] = out.get(k, [])
            out[k].extend(v)
    return out


def getInput():
    file_path = input("Enter filepath or text (Ctrl+Z 2End) or 'exit': \n")
    if file_path.lower() == 'exit':
        raise SystemExit
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception:
        out = file_path
        try:
            while True:
                out += '\n'+input().strip()
        except EOFError:
            return out


def main():
    while True:
        text = getInput()
        word_count = dict_combine(*[count_words_in_line(line)
                                  for line in text.splitlines()])

        def get_word_count(typ):
            try:
                return len(word_count[typ])
            except KeyError:
                return 0
        print("Statistics:")
        print("String Length: %i" % len(text))
        print("String Byte Length: %i" % len(text.encode('utf-8')))
        print("Latin Words: %i" % get_word_count('Latin'))
        if get_word_count('Latin'):
            print('- Average Word Length: %.2f' %
                  (len(''.join(word_count['Latin']))/get_word_count('Latin')))
        print("CJK Characters: %i" % get_word_count('CJK'))
        print("Punctuations: %i" % get_word_count('Punctuation'))
        print("Others: %i" % get_word_count('Others'))
        if get_word_count('Others'):
            print('- Others contains: '+str(set(word_count['Others'])))
        print()


if __name__ == "__main__":
    main()
