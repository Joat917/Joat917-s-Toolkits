"""
本代码将在一个固定的方形空间内绘制雷洛三角形，并让它贴着方形空间的内壁旋转
"""

import numpy as np
import matplotlib.pyplot as plt

def reuleaux_triangle(radius=1, point_per_arc=100):
    """
    绘制一个标准的正向摆放的雷洛三角形
    :param radius: 雷洛三角形的边长
    :param point_per_arc: 每条弧线上的点数
    :return: 雷洛三角形的参数曲线
    """
    vertices = np.array([
        [0, radius/np.sqrt(3)],
        [-radius/2, -radius/(2*np.sqrt(3))],
        [radius/2, -radius/(2*np.sqrt(3))]
    ])
    angle_ranges = [
        np.linspace(-2*np.pi/3, -np.pi/3, point_per_arc),
        np.linspace(0, np.pi/3, point_per_arc),
        np.linspace(2*np.pi/3, np.pi, point_per_arc)
    ]
    points = np.concatenate([
        vertices[i] + radius * np.array([np.cos(angle_ranges[i]), np.sin(angle_ranges[i])]).T
        for i in range(3)
    ])
    return points

def reuleaux_triangle_rotated(theta, radius=1, point_per_arc=100):
    """
    绘制一个旋转摆放的雷洛三角形
    :param theta: 旋转角度（弧度，逆时针）
    :param radius: 雷洛三角形的边长
    :param point_per_arc: 每条弧线上的点数
    :return: 雷洛三角形的参数曲线
    """
    points = reuleaux_triangle(radius, point_per_arc)
    rotation_matrix = np.array([
        [np.cos(theta), -np.sin(theta)],
        [np.sin(theta), np.cos(theta)]
    ])
    rotated_points = points @ rotation_matrix.T

    vertices = np.array([
        [0, radius/np.sqrt(3)],
        [-radius/2, -radius/(2*np.sqrt(3))],
        [radius/2, -radius/(2*np.sqrt(3))]
    ]) @ rotation_matrix.T
    vertices = [tuple(v) for v in vertices]

    vertices.sort(key=lambda v:v[1])
    anchor_x = vertices[1][0] # 中间点的x坐标
    center_x = anchor_x - radius/2 if anchor_x > 0 else anchor_x + radius/2 # 方框中心x坐标，相当于从中间点水平移动radius/2
    
    vertices.sort(key=lambda v:v[0])
    anchor_y = vertices[1][1] # 中间点的y坐标
    center_y = anchor_y - radius/2 if anchor_y > 0 else anchor_y + radius/2 # 方框中心y坐标，相当于从中间点垂直移动radius/2

    translated_points = rotated_points - np.array([center_x, center_y]) # 让雷洛三角形贴着方框内壁
    return translated_points

if __name__ == "__main__":
    radius = 2
    half_radius = radius / 2
    point_per_arc = 100

    def update(theta):
        plt.clf()
        # square = np.array([
        #     [-half_radius, -half_radius],
        #     [half_radius, -half_radius],
        #     [half_radius, half_radius],
        #     [-half_radius, half_radius],
        #     [-half_radius, -half_radius]
        # ])
        # plt.plot(square[:,0], square[:,1], 'k-')
        points = reuleaux_triangle_rotated(theta, radius, point_per_arc)
        plt.plot(points[:,0], points[:,1], 'b-')
        plt.xlim(-half_radius, half_radius)
        plt.ylim(-half_radius, half_radius)
        plt.gca().set_aspect('equal', adjustable='box')
        plt.pause(0.02)

    plt.ion()
    for i in range(10000):
        theta = i * 0.04
        update(theta)
    plt.ioff()
    plt.show()
