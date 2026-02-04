import ctypes
from random import randint
from BaseImport import MediaPath, SavePath


def generate(size, seed=None, filename=None):
    if size not in [20, 35, 50, 100, 200]:
        raise ValueError(f"size {size} not supported")
    if seed is None:
        seed = randint(0, (1 << 32)-1)
    if filename is None:
        filename = f"Maze_size{size}_seed{seed}.thirdmaze"

    filename_full = SavePath/filename
    filename_char_p = ctypes.create_string_buffer(filename_full.encode(), len(filename_full)+1)
    cdll = ctypes.CDLL(MediaPath/f"Maze22dll_size{size}.dll", winmode=0)
    cdll.calculate(ctypes.c_uint(seed), filename_char_p)
    try:
        open(filename_full, 'rb').close()
    except FileNotFoundError:
        raise RuntimeError("Generation Completed, but file not found")
