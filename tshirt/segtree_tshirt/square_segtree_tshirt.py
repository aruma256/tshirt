# flake8: noqa E501

import math
from PIL import Image, ImageDraw, ImageFont

# 画像のサイズと背景色を指定
IMAGE_WIDTH = 4000
IMAGE_HEIGHT = 2500
SIDE_MARGIN = 200

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

NODE_COLOR = LINE_COLOR = WHITE

NODE_RADIUS = 200
LINE_WIDTH = NODE_RADIUS*2

# 画像オブジェクトを作成
img = Image.new("RGBA", (IMAGE_WIDTH, IMAGE_HEIGHT), (0, 0, 0, 0))

# ImageDrawオブジェクトを作成
draw = ImageDraw.Draw(img)


# 描画関数
def draw_line_circle(cx, cy, radius, color=NODE_COLOR):
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), outline=color)


def draw_circle(cx, cy, radius, color=LINE_COLOR):
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=color)


def getNodePos(depth, i) -> tuple[float, float]:
    node_per_depth = 8
    width = IMAGE_WIDTH - SIDE_MARGIN * 2 - NODE_RADIUS * 2
    x = SIDE_MARGIN + NODE_RADIUS + width * i / (node_per_depth - 1)
    if depth == 0 and i == 0:
        print(x)
    y = SIDE_MARGIN + NODE_RADIUS + depth * width / (node_per_depth - 1)
    return (x, y)


def draw_node(depth, i, value):
    draw_circle(*getNodePos(depth, i), NODE_RADIUS, color=NODE_COLOR+(value,))


def draw_line_between_nodes(depth, i1, i2, value):
    draw.line((getNodePos(depth, i1) + getNodePos(depth, i2)), width=LINE_WIDTH+1, fill=NODE_COLOR+(value,))

# def draw_line_to_next_depth(depth, angle, color):
#     draw.line((getNodePos(depth, angle) + getNodePos(depth+1, angle)), width=LINE_NEXT_DEPTH_WIDTH+1, fill=color)


def segtree():
    values = [3,5,1,1,5,8,1,3]
    for i, value in enumerate(values):
        values[i] = 256//8*value
    for depth in range(4):
        target_range_length = 2**(3-depth)
        for i in range(0, 8, target_range_length):
            max_value = max(values[i:i+target_range_length])
            draw_node(depth, i, max_value)
            if target_range_length > 1:
                draw_node(depth, i+target_range_length-1, max_value)
                draw_line_between_nodes(depth, i, i+target_range_length-1, max_value)


segtree()


CHAR_LINE_WIDTH = 20
SIDE_MARGIN += -10

def draw_logo():
    char_to_paths = {
        "S": [(1, -1), (-1, -1), (-1, 0), (1, 0), (1, 1), (-1, 1)],
        "E": [(1, -1), (-1, -1), (-1, 0), (1, 0), (-1, 0), (-1, 1), (1, 1)],
        "G": [(1, -1), (-1, -1), (-1, 1), (1, 1), (1, 0), (0, 0)],
        "M": [(-1, 1), (-1, -1), (0, 1), (1, -1), (1, 1)],
        "N": [(-1, 1), (-1, -1), (1, 1), (1, -1)],
        "T": [(1, -1), (-1, -1), (0, -1), (0, 1)],
        " ": [],
        "R": [(-1, 1), (-1, -1), (1, -1), (1, 0), (-1, 0), (1, 1)],
    }
    width = IMAGE_WIDTH - SIDE_MARGIN * 2
    CHAR_RADIUS = width / (len("SEGMENT TREE")-0) / 2
    for char_i, c in enumerate("SEGMENT TREE"):
        paths = char_to_paths[c]
        cx = SIDE_MARGIN + width * char_i / (len("SEGMENT TREE")-0) + CHAR_RADIUS
        cy = 2200 - 31
        for path_i in range(len(paths)-1):
            a, b = paths[path_i], paths[path_i+1]
            ax = cx + a[0] * CHAR_RADIUS * 0.8
            ay = cy + a[1] * CHAR_RADIUS * 0.8
            bx = cx + b[0] * CHAR_RADIUS * 0.8
            by = cy + b[1] * CHAR_RADIUS * 0.8
            draw_circle(ax, ay, CHAR_LINE_WIDTH, color=NODE_COLOR+(255,))
            draw_circle(bx, by, CHAR_LINE_WIDTH, color=NODE_COLOR+(255,))
            draw.line(((ax, ay) + (bx, by)), width=CHAR_LINE_WIDTH*2+1, fill=NODE_COLOR+(255,))


draw_logo()


# 画像を表示
img.show()

# 画像を保存
img.save("segtree_white.png")
