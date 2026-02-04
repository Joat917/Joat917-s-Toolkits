import numpy as np
from PIL import Image, ImageDraw

class Grid:
    """
    一个抽象网格类。可以用于表示任意维度任意形状的拓扑格点。（平直空间，暂时没有实现坐标卡）
    """
    def __init__(self, n_dim=2, neighbor_num=4):
        self.point_coords = np.zeros((0, n_dim), dtype=np.float64)  # 存储格点坐标的数组
        self.adjacency_array = np.zeros((0, neighbor_num), dtype=np.int32)  # 存储邻接关系的数组
        self.activated = np.ones((0,), dtype=bool)  # 存储格点激活状态的数组
        self.adjacency_array.fill(-1)  # -1表示无邻居
        self.n_dim = n_dim  # 网格的维度
        self.neighbor_num = neighbor_num  # 每个格点的邻居数量

    def save(self, filepath, **params):
        np.savez_compressed(
            filepath, 
            point_coords=self.point_coords,
            adjacency_array=self.adjacency_array,
            activated=self.activated, 
            **params
        )
    
    @classmethod
    def load(cls, filepath):
        data = np.load(filepath)
        grid = cls(n_dim=data['point_coords'].shape[1], neighbor_num=data['adjacency_array'].shape[1])
        grid.point_coords = data['point_coords']
        grid.adjacency_array = data['adjacency_array']
        grid.activated = data['activated']
        return grid

        
class TwoDGrid(Grid):
    def __init__(self, neighbor_num=4):
        super().__init__(n_dim=2, neighbor_num=neighbor_num)
        self.image_unit = None # PIL.Image对象，L格式，表示一个单元的图像的掩码图。
        self.image_unit_size = None # float，表示坐标系中单位长度对应的像素大小

    def get_image_unit(self, coord=None):
        return self.image_unit

    def paint(self):
        if not self.image_unit or not self.image_unit_size:
            raise ValueError("Image unit or image unit size not set.")
        min_coords = np.min(self.point_coords, axis=0)
        max_coords = np.max(self.point_coords, axis=0)
        def coord_to_pixel(coord):
            return ((coord - min_coords) * self.image_unit_size).round().astype(np.int32)
        img_size = coord_to_pixel(max_coords) + np.array(self.image_unit.size, dtype=np.int32)
        img = Image.new("LA", tuple(img_size), (0, 255))
        for i,coord in enumerate(self.point_coords):
            if not self.activated[i]:
                continue
            pixel_pos = coord_to_pixel(coord)
            mask = self.get_image_unit(coord)
            img.paste(mask, tuple(pixel_pos), mask)
        return img


class SquareGrid(TwoDGrid):
    def __init__(self, width, height, image_unit_size=10.0):
        super().__init__(neighbor_num=4)
        self.width = width
        self.height = height
        self.image_unit_size = image_unit_size
        self.image_unit = Image.new("L", (int(image_unit_size), int(image_unit_size)), 255)
        for i in range(width):
            for j in range(height):
                self.point_coords = np.vstack([self.point_coords, np.array([i, j], dtype=np.float64)])
        self.adjacency_array = -np.ones((width * height, 4), dtype=np.int32)
        self.activated = np.ones((width * height,), dtype=bool)
        for i in range(width):
            for j in range(height):
                idx = i * height + j
                if i > 0:
                    self.adjacency_array[idx][0] = (i - 1) * height + j  # left
                if i < width - 1:
                    self.adjacency_array[idx][1] = (i + 1) * height + j  # right
                if j > 0:
                    self.adjacency_array[idx][2] = i * height + (j - 1)  # up
                if j < height - 1:
                    self.adjacency_array[idx][3] = i * height + (j + 1)  # down

    def paint(self):
        img = super().paint()
        draw = ImageDraw.Draw(img)
        min_coords = np.min(self.point_coords, axis=0)
        max_coords = np.max(self.point_coords, axis=0)
        def coord_to_pixel(coord):
            return ((coord - min_coords) * self.image_unit_size).round().astype(np.int32)
        # 在交叉点上绘制菱形负片
        for i in range(self.width - 1):
            for j in range(self.height - 1):
                idx_00 = i * self.height + j
                idx_01 = i * self.height + (j + 1)
                idx_10 = (i + 1) * self.height + j
                idx_11 = (i + 1) * self.height + (j + 1)
                if not self.activated[idx_00] and not self.activated[idx_11] or not self.activated[idx_01] and not self.activated[idx_10]:
                    p1 = coord_to_pixel(np.array([i + 0.5, j], dtype=np.float64)+0.5)
                    p2 = coord_to_pixel(np.array([i + 1, j + 0.5], dtype=np.float64)+0.5)
                    p3 = coord_to_pixel(np.array([i + 0.5, j + 1], dtype=np.float64)+0.5)
                    p4 = coord_to_pixel(np.array([i, j + 0.5], dtype=np.float64)+0.5)
                    draw.polygon([tuple(p1), tuple(p2), tuple(p3), tuple(p4)], fill=(0, 255))
        return img

class DiagnalSquareGrid(TwoDGrid):
    def __init__(self, width, height, image_unit_size=10.0):
        super().__init__(neighbor_num=8)
        self.width = width
        self.height = height
        self.image_unit_size = image_unit_size
        self.image_unit = Image.new("L", (int(image_unit_size), int(image_unit_size)), 255)
        for i in range(width):
            for j in range(height):
                self.point_coords = np.vstack([self.point_coords, np.array([i, j], dtype=np.float64)])
        self.adjacency_array = -np.ones((width * height, 8), dtype=np.int32)
        self.activated = np.ones((width * height,), dtype=bool)
        for i in range(width):
            for j in range(height):
                idx = i * height + j
                if i > 0:
                    self.adjacency_array[idx][0] = (i - 1) * height + j  # left
                if i < width - 1:
                    self.adjacency_array[idx][1] = (i + 1) * height + j  # right
                if j > 0:
                    self.adjacency_array[idx][2] = i * height + (j - 1)  # up
                if j < height - 1:
                    self.adjacency_array[idx][3] = i * height + (j + 1)  # down
                if i > 0 and j > 0:
                    self.adjacency_array[idx][4] = (i - 1) * height + (j - 1)  # up-left
                if i < width - 1 and j > 0:
                    self.adjacency_array[idx][5] = (i + 1) * height + (j - 1)  # up-right
                if i > 0 and j < height - 1:
                    self.adjacency_array[idx][6] = (i - 1) * height + (j + 1)  # down-left
                if i < width - 1 and j < height - 1:
                    self.adjacency_array[idx][7] = (i + 1) * height + (j + 1)  # down-right
    
    def paint(self):
        img = super().paint()
        draw = ImageDraw.Draw(img)
        min_coords = np.min(self.point_coords, axis=0)
        max_coords = np.max(self.point_coords, axis=0)
        def coord_to_pixel(coord):
            return ((coord - min_coords) * self.image_unit_size).round().astype(np.int32)
        # 在交叉点上绘制菱形
        for i in range(self.width - 1):
            for j in range(self.height - 1):
                idx_00 = i * self.height + j
                idx_01 = i * self.height + (j + 1)
                idx_10 = (i + 1) * self.height + j
                idx_11 = (i + 1) * self.height + (j + 1)
                if self.activated[idx_00] and self.activated[idx_11] or self.activated[idx_01] and self.activated[idx_10]:
                    p1 = coord_to_pixel(np.array([i + 0.5, j], dtype=np.float64)+0.5)
                    p2 = coord_to_pixel(np.array([i + 1, j + 0.5], dtype=np.float64)+0.5)
                    p3 = coord_to_pixel(np.array([i + 0.5, j + 1], dtype=np.float64)+0.5)
                    p4 = coord_to_pixel(np.array([i, j + 0.5], dtype=np.float64)+0.5)
                    draw.polygon([tuple(p1), tuple(p2), tuple(p3), tuple(p4)], fill=(255, 255))
        return img
                    

class HexagonGrid(TwoDGrid):
    def __init__(self, size, image_unit_size=10.0):
        super().__init__(neighbor_num=6)
        self.size=size
        self.image_unit_size = image_unit_size
        self.image_unit = Image.new('L', (round(image_unit_size), round(image_unit_size*(2*3**-.5))), 0)
        ImageDraw.Draw(self.image_unit).polygon([
            (image_unit_size/2, 0),
            (image_unit_size, image_unit_size*3**-.5/2),
            (image_unit_size, image_unit_size*(3*3**-.5/2)),
            (image_unit_size/2, image_unit_size*(2*3**-.5)),
            (0, image_unit_size*(3*3**-.5/2)),
            (0, image_unit_size*3**-.5/2)
        ], fill=255)  # 一个竖直摆放的正六边形单元

        # 生成网格，在斜角坐标系中。
        # xi轴沿着水平方向，eta轴沿着120度方向。
        # 这样，在第一象限和第三象限内都是平行四边形，但是第二四象限就是（等边）三角形。
        xi_eta_to_index = {}
        point_coords_list = []
        for xi in range(-size, size+1):
            if xi>=0:
                eta_range = range(-size+xi, size+1)
            else:
                eta_range = range(-size, size+xi+1)
            for eta in eta_range:
                index = len(point_coords_list)
                point_coords_list.append((
                    xi - 0.5 * eta,
                    (3**0.5)/2 * eta
                ))
                xi_eta_to_index[(xi, eta)] = index
        self.point_coords = np.array(point_coords_list, dtype=np.float64)
        # 生成邻接关系
        self.adjacency_array = -np.ones((len(self.point_coords), 6), dtype=np.int32)
        for (xi, eta), index in xi_eta_to_index.items():
            neighbors = [
                (xi - 1, eta),     # left
                (xi + 1, eta),     # right
                (xi - 1, eta - 1), # down-left
                (xi, eta - 1),     # down-right
                (xi, eta + 1),     # up-left
                (xi + 1, eta + 1)  # up-right
            ]
            for n_idx, (n_xi, n_eta) in enumerate(neighbors):
                if (n_xi, n_eta) in xi_eta_to_index:
                    self.adjacency_array[index][n_idx] = xi_eta_to_index[(n_xi, n_eta)]
        
        self.activated = np.ones((len(self.point_coords),), dtype=bool)

class TriangularGrid(TwoDGrid):
    def __init__(self, size, image_unit_size=10.0):
        super().__init__(neighbor_num=3)
        self.size=size
        self.image_unit_size = image_unit_size
        self.image_unit = Image.new('L', (round(image_unit_size), round(image_unit_size*(3**0.5)/2)), 0)
        ImageDraw.Draw(self.image_unit).polygon([
            (image_unit_size/2, 0),
            (image_unit_size, image_unit_size*(3**0.5)/2),
            (0, image_unit_size*(3**0.5)/2)
        ], fill=255) # 一个向上的三角
        self.image_unit_inverted = self.image_unit.rotate(180) # 一个向下的三角

        point_coords_list = []
        xy_to_index_map = {}
        # 使用横纵尺度不同的直角坐标系，x轴刻度大小为1/2，y轴刻度大小为sqrt(3)/4且y只能取为奇数
        # x的取值范围：如果size=3，那么在y=1处（水平主轴上方第一层），上三角所在位置的x为(-5,-3,-1,1,3,5)。
        # y的取值范围：在x=2*size-1时y取+-1；如果x很大，x每减少1，y的上限和下限都会扩张2；最大y值为2*size-1。
        for x in range(-(2*size-1), 2*size):
            y_lim = min(4*size-1-2*abs(x), 2*size-1)
            for y in range(-y_lim, y_lim+1, 2):
                index = len(point_coords_list)
                point_coords_list.append((x/2, (3**0.5)/4*y))
                xy_to_index_map[(x, y)] = index
        self.point_coords = np.array(point_coords_list, dtype=np.float64)

        # 生成邻接关系
        self.adjacency_array = -np.ones((len(self.point_coords), 3), dtype=np.int32)
        for (x, y), index in xy_to_index_map.items():
            if not (x ^ (y>>1)) & 1:
                neighbors = [
                    (x - 1, y),     # down-left
                    (x + 1, y),     # down-right
                    (x,     y + 2)  # up
                ]
            else:
                neighbors = [
                    (x - 1, y),     # up-left
                    (x + 1, y),     # up-right
                    (x,     y - 2)  # down
                ]
            for n_idx, (n_x, n_y) in enumerate(neighbors):
                if (n_x, n_y) in xy_to_index_map:
                    self.adjacency_array[index][n_idx] = xy_to_index_map[(n_x, n_y)]
        
        self.activated = np.ones((len(self.point_coords),), dtype=bool)

    def get_image_unit(self, coord):
        x, y = coord
        x_int = round(x * 2)
        y_int = round(y * 4 / (3**0.5))
        inverted = (x_int ^ (y_int>>1)) & 1 # 由于图像中的y坐标向下，和xy坐标系相反，所以这里需要取反（去掉not）
        return self.image_unit_inverted if inverted else self.image_unit
        


def makemaze(grid:Grid, start_pos:int, seed=None):
    rng = np.random.Generator(np.random.PCG64(seed))
    grid.activated[:] = False
    stack = [start_pos]
    last_dict = {start_pos:-1}
    while stack:
        # 尝试挖去当前节点
        current = stack.pop()
        last = last_dict[current]
        # 如果挖去后形成了新的通路，那么别挖
        if any(grid.activated[neighbor] for neighbor in grid.adjacency_array[current] if neighbor>=0 and neighbor!=last):
            continue
        grid.activated[current] = True
        # 将邻居节点加入栈中
        neighbors = [n for n in grid.adjacency_array[current] if n>=0 and not grid.activated[n] and n not in last_dict]
        rng.shuffle(neighbors)
        for n in neighbors:
            stack.append(n)
            last_dict[n] = current
        
    return grid


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--type', type=str, default='square', choices=['square', 'diagnal_square', 'hexagon', 'triangular'])
    parser.add_argument('--size', type=int, default=10, help='Size of the grid.')
    parser.add_argument('--unit_size', type=float, default=20.0, help='Size of each unit in pixels.')
    parser.add_argument('--output', type=str, default='maze.png', help='Output image file path.')
    parser.add_argument('--seed', type=int, default=None, help='Random seed for maze generation.')
    args = parser.parse_args()
    if args.type == 'square':
        grid = SquareGrid(args.size, args.size, args.unit_size)
    elif args.type == 'diagnal_square':
        grid = DiagnalSquareGrid(args.size, args.size, args.unit_size)
    elif args.type == 'hexagon':
        grid = HexagonGrid(args.size, args.unit_size)
    elif args.type == 'triangular':
        grid = TriangularGrid(args.size, args.unit_size)
    else:
        raise ValueError("Unknown grid type.")
    makemaze(grid, start_pos=0, seed=args.seed)
    img = grid.paint()
    img.save(args.output)
    