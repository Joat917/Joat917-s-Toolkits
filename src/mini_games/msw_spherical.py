"""
基于PyGame伪3D的球面扫雷。

使用说明：
1. 鼠标左键和右键进行扫雷。
2. 左键双击翻开周围的格子。
3. 右键空白格子高亮与之相邻的格子。
4. 左键拖动调整视角。
5. 滚轮缩放视角。
6. 按R键重置游戏。

小技巧：
1. 拖动鼠标只能平行移动球面，不能在屏幕内旋转。如果需要旋转，请拖动屏幕画圈，圈越大转过的角度越大。
2. 当发现多个格子相较于一点，但不确定其中的两个格子是否真的相邻，你需要把鼠标置于翻开的格子上按住右键。
3. 游戏结束后需要手动按下R键，注意输入法要调为英文。不建议关闭重开，否则要等很久。
4. 可以任意修改本文件最后一行num_points和num_mines的值。

注意：
打开游戏可能需要很长时间的加载，因为scipy.minimize非常慢。

By Joat917 at 2026-2-25, AI assisted
"""

import os, sys
import numpy as np
import networkx as nx
from scipy.spatial import SphericalVoronoi
from scipy.optimize import minimize

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame

class SphericalGeometry:
    def __init__(self, num_points:int, radius=1.0):
        self.radius = radius
        self.points_center = self.generate_random_points_sphere(num_points, radius=self.radius) # 在球面上生成均匀分布的点，作为雷区的中心
        self.points_center = self.optimize_points_on_sphere(self.points_center, radius=self.radius) # 优化点的位置，使其在球面上更均匀分布

        self.voronoi = SphericalVoronoi(self.points_center, radius=self.radius) # 计算球面上的Voronoi图
        self.voronoi.sort_vertices_of_regions() # 对每个Voronoi区域的顶点进行排序，确保它们按顺时针或逆时针顺序排列
        self.num_points = len(self.points_center)

        _vertices = []
        for region in self.voronoi.regions:
            _vertices.append([self.voronoi.vertices[idx] for idx in region if idx != -1])
        self.vertices = tuple(_vertices) # 每个Voronoi区域的顶点坐标列表，作为雷区的边界

        self.graph = nx.Graph() # 构建雷区的邻接关系图
        # 如果两个Voronoi区存在公共边界，即它们存在至少两个（一个不够）公共顶点，则认为它们是相邻的
        for i, region_i in enumerate(self.voronoi.regions):
            for j, region_j in enumerate(self.voronoi.regions):
                if i >= j:
                    continue
                region_intersection = set(region_i) & set(region_j)
                region_intersection.discard(-1)
                if len(region_intersection) >= 2:
                    self.graph.add_edge(i, j)

    @staticmethod
    def generate_random_points_sphere(n_points, radius=1.0, perturbation=0.05, rng=None):
        """
        使用Fibonacci球面采样算法生成在球面上均匀分布的点，并进行扰动。
        """
        rng = rng if rng is not None else np.random.default_rng()
        indices = np.arange(0, n_points, dtype=float) + 0.5
        phi = np.arccos(1 - 2*indices/n_points)
        theta = np.pi * (1 + 5**0.5) * indices
        points = np.stack((np.cos(theta) * np.sin(phi), np.sin(theta) * np.sin(phi), np.cos(phi)), axis=-1) * radius
        points += rng.normal(scale=perturbation*radius, size=points.shape) # 添加小的随机扰动，避免完全规则的分布
        return points

    @staticmethod
    def optimize_points_on_sphere(points, radius=1.0, iterations=10_000):
        """
        优化点的位置使其在球面上更均匀分布
        """
        n_points = len(points)
        def energy(pts):
            pts = pts.reshape((n_points, 3))
            pts /= np.linalg.norm(pts, axis=1, keepdims=True) * radius # 投影回球面
            e = 0.0
            for i in range(n_points):
                for j in range(i+1, n_points):
                    dist = np.linalg.norm(pts[i] - pts[j])
                    if dist > 1e-10:
                        e += 1.0 / dist
            return e
        
        result = minimize(energy, points.flatten(), bounds=[(-radius, radius)]*(n_points*3), options={'maxiter': iterations}, tol=1e-3)
        optimized_points = result.x.reshape((n_points, 3))
        # 将优化后的点投影回球面
        optimized_points /= np.linalg.norm(optimized_points, axis=1, keepdims=True)
        optimized_points *= radius
        return optimized_points


    @staticmethod
    def cut_polygon_by_plane(polygon, plane_point, plane_normal, threshold=0.1):
        """
        将多边形切割成两部分，返回在平面上方的部分为一个新的多边形。如果不存在在平面上方的部分，返回None。
        """
        point_sides = np.dot(polygon - plane_point, plane_normal)
        new_polygon = []
        for i in range(-1,len(polygon)-1):
            p1, p2 = polygon[i], polygon[i+1]
            s1, s2 = point_sides[i], point_sides[i+1]
            s1-=threshold
            s2-=threshold
            if s1 >= 0:
                new_polygon.append(p1)
            if s1*s2 < 0:
                t = s1 / (s1 - s2)
                intersection = p1 + t * (p2 - p1)
                new_polygon.append(intersection)
        if len(new_polygon)<3:
            return None
        return np.array(new_polygon)
    
    @staticmethod
    def point_in_polygon(point, polygon):
        """
        判断一个点是否在多边形内。假设多边形是凸的。
        """
        if polygon is None:
            return False
        n = len(polygon)
        edges = [(polygon[i], polygon[i+1]) for i in range(-1,len(polygon)-1)]
        sides = [np.cross(edge[1]-edge[0], point-edge[0]) for edge in edges]
        return all(s >= 0 for s in sides) or all(s <= 0 for s in sides)
        
    
class MineField:
    def __init__(self, geometry:SphericalGeometry, num_mines:int, rng=None):
        """
        Args:
            geometry: 球面几何对象，包含雷区的顶点和邻接关系
            num_mines: 雷的数量
            forbidden_indices: 不允许放置雷的雷区索引集合，通常是玩家当前所在的雷区及其邻接雷区，以确保玩家不会一开始就踩雷
            seed: 随机数种子
        """
        self.geometry = geometry
        self.num_mines = num_mines
        self.rng = rng if rng is not None else np.random.default_rng()
        self.blocks = [MineBlock(self, i) for i in range(geometry.num_points)] # 创建每个雷区对应的MineBlock对象，包含其状态和属性

    def place_mines(self, forbidden_indices:set):
        self.mines = set(self.rng.choice([i for i in range(self.geometry.num_points) if i not in forbidden_indices], size=self.num_mines, replace=False))
        for block in self.blocks:
            block.place_mine()

    def is_mine(self, region_index:int) -> bool:
        return region_index in self.mines
    
    def check_win(self) -> bool:
        return all((block.is_revealed or block.is_mine) for block in self.blocks) # The player wins if all non-mine blocks are revealed and all mine blocks are either revealed or flagged.
    
    def check_lose(self) -> bool:
        return any(block.is_revealed and block.is_mine for block in self.blocks) # The player loses if any mine block is revealed.
    

class MineBlock:
    def __init__(self, minefield:MineField, region_index:int):
        self.minefield = minefield
        self.geometry = minefield.geometry
        self.region_index = region_index
        self.vertices = self.geometry.vertices[region_index] # 雷区的顶点坐标列表
        self.is_revealed = False
        self.is_flagged = False
        self._font = None
        self.current_polygon_vertices = None
        self.number_color = (255, 255, 255)
        self.temperarily_highlight = False

    @property
    def font(self):
        if self._font is None:
            self._font = pygame.font.SysFont(None, 24)
        return self._font

    def place_mine(self):
        self.is_mine = self.minefield.is_mine(self.region_index)
        self.adjacent_mines = sum(1 for neighbor in self.geometry.graph.neighbors(self.region_index) if self.minefield.is_mine(neighbor)) # 计算相邻雷区中雷的数量
        NUMBER_COLOR = {
            1: (0, 0, 255, 255),
            2: (0, 128, 0, 255),
            3: (255, 0, 0, 255),
            4: (0, 0, 128, 255),
            5: (128, 0, 0, 255),
            6: (0, 128, 128, 255),
            7: (0, 0, 0, 255),
            8: (128, 128, 128, 255),
        }
        self.number_color = NUMBER_COLOR.get(self.adjacent_mines, (128, 128, 128, 255))[:3]

    def reveal(self):
        if self.is_revealed or self.is_flagged:
            return
        self.is_revealed = True
        if self.adjacent_mines == 0 and not self.is_mine:
            for neighbor in self.geometry.graph.neighbors(self.region_index):
                self.minefield.blocks[neighbor].reveal()
    
    def toggle_flag(self):
        if self.is_revealed:
            return
        self.is_flagged = not self.is_flagged

    def blit(self, surface, camera_angle, camera_zoom):
        """
        在给定的surface上渲染当前雷区块。
        
        Args:
            surface: PyGame的Surface对象，表示要渲染的画布
            camera_angle: 当前摄像机的朝向。必须是三维正交矩阵，每一列分别代表摄像机的右向量、上向量和前向量（指向摄像机）
            camera_zoom: 当前摄像机的缩放级别
        """

        # Get color of the block based on its state
        if self.temperarily_highlight:
            color = (0, 200, 200)
            self.temperarily_highlight = False
        elif self.is_revealed:
            color = (200, 200, 200) if not self.is_mine else (255, 0, 0)
        else:
            color = (100, 100, 100) if not self.is_flagged else (255, 255, 0)

        screen_center = np.array(surface.get_size()) / 2

        # Project vertices to 2D screen coordinates
        cut_vertices = SphericalGeometry.cut_polygon_by_plane(self.vertices, plane_point=np.array([0,0,0]), plane_normal=camera_angle[:,2])
        if cut_vertices is not None:
            projected = cut_vertices @ camera_angle[:,:2] * camera_zoom + screen_center
            pygame.draw.polygon(surface, color, projected)
            self.current_polygon_vertices = projected
            pygame.draw.polygon(surface, (0, 0, 0), projected, width=1) # Draw border
            # If revealed and has adjacent mines, draw the number
            if self.is_revealed and self.adjacent_mines > 0 and not self.is_mine:
                center_projected = self.geometry.points_center[self.region_index] @ camera_angle[:,:2] * camera_zoom + screen_center
                text = self.font.render(str(self.adjacent_mines), True, self.number_color)
                text_rect = text.get_rect(center=center_projected.astype(int))
                surface.blit(text, text_rect)
        else:
            self.current_polygon_vertices = None
        
        
    def is_point_inside(self, point_2d):
        """
        判断一个2D点是否在当前雷区块的投影区域内。
        
        Args:
            point_2d: 以像素为单位的2D点坐标，表示鼠标点击位置
        
        Returns:
            bool: 如果点在雷区块内返回True，否则返回False
        """
        if self.current_polygon_vertices is None:
            return False
        return SphericalGeometry.point_in_polygon(point_2d, self.current_polygon_vertices)
    
class MineSweeperGame:
    def __init__(self, num_points:int, num_mines:int, seed=None):
        self.geometry = SphericalGeometry(num_points)
        self.num_mines = num_mines
        self.camera_angle = np.eye(3) # 初始摄像机朝向，右向量、上向量、前向量
        self.camera_zoom = 200.0
        self.rng = np.random.default_rng(seed)
        self.reset()

    def reset(self):
        self.minefield = MineField(self.geometry, num_mines=self.num_mines, rng=self.rng)
        self.mine_placed = False
        self.gameovered = False
        self.won = False

    def click_block(self, block:MineBlock, right_click=False, double_click=False):
        # if debug:
        print(f"Clicked block {block.region_index}, right_click={right_click}, double_click={double_click}")
        if self.gameovered:
            return
        if not self.mine_placed:
            forbidden = set([block.region_index]) | set(self.geometry.graph.neighbors(block.region_index))
            self.minefield.place_mines(forbidden_indices=forbidden)
            self.mine_placed = True
        if right_click:
            block.toggle_flag()
        elif double_click:
            if block.is_revealed and block.adjacent_mines > 0:
                flagged_neighbors = sum(1 for neighbor in self.geometry.graph.neighbors(block.region_index) if self.minefield.blocks[neighbor].is_flagged)
                if flagged_neighbors == block.adjacent_mines:
                    for neighbor in self.geometry.graph.neighbors(block.region_index):
                        if not self.minefield.blocks[neighbor].is_flagged:
                            self.click_block(self.minefield.blocks[neighbor], right_click=False, double_click=False)
        else:
            block.reveal()
        self.won = self.minefield.check_win()
        self.gameovered = self.won or self.minefield.check_lose()

    def move_camera(self, dx, dy):
        """
        拖动摄像机旋转。
        """
        rotation_vector = np.array([dy, -dx, 0],dtype=np.float64)
        angle = np.linalg.norm(rotation_vector)
        if angle<1e-3:
            return False
        rotation_vector/=angle
        angle/=self.camera_zoom
        cross_matrix = np.array([
            [0, -rotation_vector[2], rotation_vector[1]],
            [rotation_vector[2], 0, -rotation_vector[0]],
            [-rotation_vector[1], rotation_vector[0], 0]
        ])
        rotation_matrix = np.eye(3) + np.sin(angle)*cross_matrix + (1-np.cos(angle))*(cross_matrix @ cross_matrix)
        self.camera_angle = self.camera_angle @ rotation_matrix
        return True

    def get_block_at_point(self, point_2d):
        for block in self.minefield.blocks:
            if block.is_point_inside(point_2d):
                return block
        return None
    
    def mainloop(self):
        pygame.init()
        pygame.display.set_caption("Spherical Minesweeper")
        screen = pygame.display.set_mode((800, 600))
        clock = pygame.time.Clock()

        dragging = False
        last_mouse_pos = None
        last_mouse_times = (-10, 0)
        # dragging = True
        # last_mouse_pos = pygame.mouse.get_pos()
        # camera_moved = True

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # 左键点击
                        dragging = True
                        last_mouse_pos = event.pos
                        last_mouse_times = last_mouse_times[1], pygame.time.get_ticks()
                        camera_moved = False
                    elif event.button == 3: # 右键点击
                        block = self.get_block_at_point(event.pos)
                        if block is not None:
                            self.click_block(block, right_click=True)
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        dragging = False
                        if not camera_moved:
                            block = self.get_block_at_point(event.pos)
                            if block is not None:
                                self.click_block(block, double_click=(last_mouse_times[1]-last_mouse_times[0] < 400))
                        else:
                            camera_moved = False
                elif event.type == pygame.MOUSEWHEEL:
                    if event.y > 0:
                        self.camera_zoom *= 1.1
                    else:
                        self.camera_zoom /= 1.1
                elif event.type == pygame.MOUSEMOTION and dragging:
                    dx = event.pos[0] - last_mouse_pos[0]
                    dy = event.pos[1] - last_mouse_pos[1]
                    camera_moved|=self.move_camera(dx, dy)
                    last_mouse_pos = event.pos
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.reset()
                    elif event.key == pygame.K_EQUALS:
                        self.camera_zoom *= 1.5
                    elif event.key == pygame.K_MINUS:
                        self.camera_zoom /= 1.5

            screen.fill((0, 0, 0))

            if pygame.mouse.get_pressed()[2]:
                block = self.get_block_at_point(pygame.mouse.get_pos())
                if block is not None and block.is_revealed:
                    for neighbor in self.geometry.graph.neighbors(block.region_index):
                        self.minefield.blocks[neighbor].temperarily_highlight = True
            for block in self.minefield.blocks:
                block.blit(screen, self.camera_angle, self.camera_zoom)
            
            if self.gameovered:
                font = pygame.font.SysFont(None, 48)
                text = font.render("You Win!" if self.won else "Game Over", True, (255, 255, 255))
                text_rect = text.get_rect(center=(400, 300))
                screen.blit(text, text_rect)

            pygame.display.flip()
            clock.tick(60)


if __name__ == "__main__":
    game = MineSweeperGame(num_points=100, num_mines=20)
    game.mainloop()

