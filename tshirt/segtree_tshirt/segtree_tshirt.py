# flake8: noqa E501

import math
from PIL import Image, ImageDraw

# 画像のサイズと背景色を指定
width = 4000
height = 4000
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

NODE_COLOR = WHITE
LINE_COLOR = WHITE

# NODE_RADIUS = 30
# ARC_WIDTH = 60
NODE_RADIUS = 120
ARC_WIDTH = 240
LINE_NEXT_DEPTH_WIDTH = ARC_WIDTH

DISTANCE = 400

center_x = width // 2
center_y = height // 2

# 画像オブジェクトを作成
img = Image.new("RGBA", (width, height), (0, 0, 0, 0))

# ImageDrawオブジェクトを作成
draw = ImageDraw.Draw(img)


# 描画関数
def draw_line_circle(cx, cy, radius, color=BLACK):
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=color)


def draw_circle(cx, cy, radius, color=LINE_COLOR):
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=color)


def draw_arc(cx, cy, radius, start_angle, end_angle, line_width, color=LINE_COLOR):
    draw.arc((cx - radius, cy - radius, cx + radius, cy + radius), start=start_angle, end=end_angle, width=line_width, fill=color)

# メイン


def depth_to_radius(depth):
    return depth * DISTANCE


def getNodePos(depth, angle) -> tuple[float, float]:
    return (
        center_x + depth_to_radius(depth)*math.cos(math.radians(angle)),
        center_y + depth_to_radius(depth)*math.sin(math.radians(angle)),
    )


def draw_node(depth, angle, color):
    draw_circle(*getNodePos(depth, angle), NODE_RADIUS, color=color)


def draw_line_to_next_depth(depth, angle, color):
    draw.line((getNodePos(depth, angle) + getNodePos(depth+1, angle)), width=LINE_NEXT_DEPTH_WIDTH+1, fill=color)


def draw_arc_between_nodes(depth, angle_from, angle_to, color):
    draw_arc(center_x, center_y, depth_to_radius(depth)+(ARC_WIDTH//2), angle_from, angle_to, line_width=ARC_WIDTH+1, color=color)


DRAW_TASKS = []
COLOR_LEVEL = 255



def segtree():
    # nodes = [3, 15, 9, 10, 1, 16, 5, 8, 7, 14, 11, 2, 13, 12, 4, 6]
    # nodes = list(range(1,16+1))
    nodes = [
        10,14,
        6,3,
        2,5,
        4,1,
        13,9,
        16,15,
        12,8,
        7,11,
    ]
    import random
    random.seed(2)
    # random.shuffle(nodes)
    nodes = [(node, 360 + 360/len(nodes)*(i-0.5-3)) for i, node in enumerate(nodes)]
    depth = 4
    while depth:
        next_nodes = []
        for i in range(0, len(nodes), 2):
            a_color, a_angle = nodes[i]
            b_color, b_angle = nodes[i+1]
            half_angle = (a_angle + b_angle) / 2
            DRAW_TASKS.append((draw_node, depth, a_angle, (255, 255, 255, a_color * 16)))
            DRAW_TASKS.append((draw_node, depth, b_angle, (255, 255, 255, b_color * 16)))
            if a_color < b_color:
                DRAW_TASKS.append((draw_arc_between_nodes, depth, a_angle, half_angle, (255, 255, 255, a_color * 16)))
                DRAW_TASKS.append((draw_arc_between_nodes, depth, half_angle, b_angle, (255, 255, 255, b_color * 16)))
            else:
                DRAW_TASKS.append((draw_arc_between_nodes, depth, a_angle, half_angle, (255, 255, 255, a_color * 16)))
                DRAW_TASKS.append((draw_arc_between_nodes, depth, half_angle, b_angle, (255, 255, 255, b_color * 16)))
            max_color = max(a_color, b_color)
            DRAW_TASKS.append((draw_node, depth, half_angle, (255, 255, 255, max_color * 16)))
            DRAW_TASKS.append((draw_line_to_next_depth, depth-1, half_angle, (255, 255, 255, max_color * 16)))
            next_nodes.append((max_color, half_angle))
            
        nodes = next_nodes
        depth -= 1

segtree()

def dfs(depth: int, angle: float):
    global COLOR_LEVEL
    DRAW_TASKS.append((draw_node, depth, angle, (255,)*3 + (COLOR_LEVEL,)))
    if depth < 4:
        DRAW_TASKS.append((draw_line_to_next_depth, depth, angle, (255,)*3 + (COLOR_LEVEL,)))
        next_node_count = 2<<(depth + 1)
        next_angle_p = angle + (360/next_node_count)
        next_angle_n = angle - (360/next_node_count)
        DRAW_TASKS.append((draw_node, depth+1, angle, (255,)*3 + (COLOR_LEVEL,)))
        DRAW_TASKS.append((draw_arc_between_nodes, depth+1, angle, next_angle_p, (255,)*3 + (COLOR_LEVEL,)))
        dfs(depth+1, next_angle_p)
        DRAW_TASKS.append((draw_arc_between_nodes, depth+1, next_angle_n, angle, (255,)*3 + (COLOR_LEVEL,)))
        dfs(depth+1, next_angle_n)
    else:
        COLOR_LEVEL -= 15


# dfs(0, 90)

# DRAW_TASKS.reverse()
for i in range(len(DRAW_TASKS)):
    color = round((i+1) / len(DRAW_TASKS) * 255)
    DRAW_TASKS[i][0](*DRAW_TASKS[i][1:])



# for i in range(1, 3+1):
#     draw_line_circle(center_x, center_y, i*DISTANCE)



# 画像を表示
img.show()

# 画像を保存
img.save("segtree.png")
