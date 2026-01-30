# 各种乱码的生成方式：正确文本--(编码器)-->字节流--(解码器)-->乱码文本--(同一格式编码器)-->乱码文本--(解码器)-->乱码文本

CODER_LISTS = {
    '古文码': ['utf-8', 'gbk'], 
    '口字码': ['gbk', 'utf-8'], 
    '符号码': ['utf-8', 'iso8859-1'], 
    '拼音码': ['gbk', 'iso8859-1'], 
    '问句码': ['utf-8', 'gbk', 'utf-8'], 
    '锟拷码': ['gbk', 'utf-8', 'gbk']
}

def gushen_encode(text:str, method):
    coder = CODER_LISTS[method]
    for i in range(len(coder)-1):
        text = text.encode(coder[i], errors='replace').decode(coder[i+1], errors='replace')
    return text

def gushen_decode(text:str, method):
    coder = CODER_LISTS[method][::-1]
    for i in range(len(coder)-1):
        text = text.encode(coder[i], errors='replace').decode(coder[i+1], errors='replace')
    return text

def print_info(text:str):
    o="原始文本：\n"
    o+=text
    o+='\n\n'
    for method in ['古文码', '口字码', '符号码', '逆符号码', '拼音码', '逆拼音码', '问句码', '锟拷码']:
        o+=method + '：\n'
        if method.startswith('逆'):
            o+=gushen_decode(text, method[1:])
        else:
            o+=gushen_encode(text, method)
        o+='\n\n'
    print(o)


if __name__=="__main__":
    import pyperclip
    text = pyperclip.paste()
    if text and not all(32<=ord(c)<=126 for c in text):
        print_info(text)

    while True:
        print_info(input("原始文本："))
