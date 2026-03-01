import os
import numpy as np
import tqdm

cache_dir = 'cache_non_fractal.npz'

if not os.path.exists(cache_dir):
    point_count = 2_000 # 每一个r值模拟多少个点
    r_count = 3_000 # r值的个数
    iteration_round = 1000
    r_values = np.linspace(3, 4, r_count)
    r_values_expanded = np.broadcast_to(r_values[:, np.newaxis], (r_count, point_count))
    data_buf = np.linspace(0, 1, point_count)[np.newaxis, :].repeat(r_count, axis=0)

    for _rnd in tqdm.tqdm(range(iteration_round)):
        data_buf *= r_values_expanded * (1 - data_buf)
    
    for _r_idx in range(r_count):
        data_buf[_r_idx, :].sort()
    
    np.savez_compressed(cache_dir, r_values_expanded=r_values_expanded.astype(np.float32), data_buf_asint=(data_buf*65535).astype(np.uint16))
else:
    cache = np.load(cache_dir)
    r_values_expanded = cache['r_values_expanded']
    data_buf = cache['data_buf_asint'].astype(np.float32) / 65535.0

import matplotlib.pyplot as plt
plt.figure(figsize=(10, 6))
r_trivial = np.linspace(0, 3, 1000)
x_trivial = np.where(r_trivial < 1, 0, 1-1/r_trivial)
plt.scatter(r_trivial, x_trivial, s=0.1, color='black')
plt.scatter(r_values_expanded, data_buf[:, :], s=0.1, color='black')
plt.title('Bifurcation Diagram')
plt.xlabel('r')
plt.ylabel('x')
plt.xlim(0, 4)
plt.ylim(0, 1)
plt.grid()
plt.tight_layout()
plt.show()
    
