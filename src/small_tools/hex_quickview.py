"""
以二进制格式打开一个文件并以字节为单位给出其内容。
适合查看极大文件的前一小半部分。
"""

def data_displayer():
    """
    一个生成器，输入字节流，输出格式化的十六进制和ASCII表示字符流。
    """
    buf = "          00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F  ASCII\n"
    buf += "          -----------------------------------------------  ----------------\n"
    data = b''
    line_count = 0
    new_data = None
    while True:
        new_data = yield buf
        buf = ''
        if not new_data:
            break
        data += new_data
        while len(data) >= 16:
            chunk = data[:16]
            hex_bytes = ' '.join(f"{byte:02X}" for byte in chunk)
            ascii_bytes = ''.join((chr(byte) if 32 <= byte <= 126 else '.') for byte in chunk)
            line = f"{line_count:08X}  {hex_bytes:<47}  {ascii_bytes}\n"
            buf += line
            line_count += 16
            data = data[16:]
    if data:
        hex_bytes = ' '.join(f"{byte:02X}" for byte in data)
        ascii_bytes = ''.join((chr(byte) if 32 <= byte <= 126 else '.') for byte in data)
        line = f"{line_count:08X}  {hex_bytes:<47}  {ascii_bytes}\n"
        buf += line
    yield buf
    return

def hex_quickview(file_path):
    """
    以交互方式查看文件的十六进制内容。
    """
    import msvcrt
    with open(file_path, 'rb') as f:
        displayer = data_displayer()
        print(displayer.send(None), end='')
        print(displayer.send(f.read(256)), end='')
        while f.peek(1)!=b'':
            key = msvcrt.getch()
            if key in [b' ']:
                chunk = f.read(256)
            elif key in [b'\r']:
                chunk = f.read(16)
            elif key in [b'\x1b', b'q']:
                return
            else:
                continue
            if not chunk:
                break
            output = displayer.send(chunk)
            if output:
                print(output, end='')
    print(displayer.send(None), end='')
    print("          -- End of File --")
    msvcrt.getch()
            
            
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        hex_quickview(input("Enter filepath: "))
    else:
        hex_quickview(sys.argv[1])

