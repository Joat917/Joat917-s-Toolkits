from collections import defaultdict

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


def count_words_in_line(line_of_text: str) -> dict[str, list[str]]:
    out = defaultdict(list)
    buf = ''

    def clearBuf():
        nonlocal buf
        if buf:
            pushOut('Latin', buf)
            buf = ''

    def pushOut(typ, cnt):
        out[typ].append(cnt)

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


def dict_combine(*dics):    
    out = defaultdict(list)
    for dic in dics:
        for k, v in dic.items():
            out[k].extend(v)
    return out


def word_counter(text:str):
    word_count = dict_combine(*[count_words_in_line(line) for line in text.splitlines()])
    output = {
        "String Length": len(text),
        "String Byte Length": len(text.encode('utf-8')),
        "Latin Words": len(word_count['Latin']), 
        "Average Latin Word Length": len(''.join(word_count['Latin']))/len(word_count['Latin']) if len(word_count['Latin'])>0 else float('nan'),
        "CJK Characters": len(word_count['CJK']),
        "Punctuations": len(word_count['Punctuation']),
        "Others": len(word_count['Others']),
        "word_count": word_count, 
    }
    output["format_summary"] = (
        "Statistics:\n"
        f"String Length: {output['String Length']}\n"
        f"String Byte Length: {output['String Byte Length']}\n"
        f"Latin Words: {output['Latin Words']}\n"
        +(f" - Average Word Length: {output['Average Latin Word Length']:.2f}\n" if output['Latin Words']>0 else "")
        +f"CJK Characters: {output['CJK Characters']}\n"
        f"Punctuations: {output['Punctuations']}\n"
        f"Others: {output['Others']}\n"
        +(f" - Others contains: {set(word_count['Others'])}\n" if output['Others']>0 else "")
    )
    return output


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


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2:
        print(f"Processing file: {sys.argv[1]}")
        with open(sys.argv[1], 'r') as f:
            text = f.read()
            word_count = word_counter(text)
            print(word_count['format_summary'])
        input("Press Enter to exit...")
    else:
        while True:
            text = getInput()
            print(word_counter(text)['format_summary'])
