from PIL import Image, ImageDraw
import numpy as np

# 基本設定
WIDTH = 4096
STROKE_WIDTH = 48
BACKGROUND = (0, 0, 0, 0)  # 透明
WHITE = (255, 255, 255, 255)  # 白
BLACK = (0, 0, 0, 255)  # 黒
STROKE = WHITE
D = 512+128

SCALE = 1024

A = 0.25

HEIGHT = int(D + A*SCALE + STROKE_WIDTH) * 2

# キャンバスの作成
image = Image.new('RGBA', (WIDTH, HEIGHT), BACKGROUND)
draw = ImageDraw.Draw(image)

x_points = np.linspace(-2, 2, 100)

# -2 ~ -1 は直線、-1 ~ 0 は放物線、0 ~ 1 は放物線、1 ~ 2 は直線

y_points = np.zeros_like(x_points)
for i, x in enumerate(x_points):
    if x < -1:
        y_points[i] = A
    elif x < 0:
        y_points[i] = -A * (x + 1) ** 2 + A
    elif x < 1:
        y_points[i] = A * (x - 1) ** 2 - A
    else:
        y_points[i] = -A

x_points = x_points * SCALE + (WIDTH/2)
y_points = -y_points * SCALE + (HEIGHT/2)

draw.line(list(zip(x_points, y_points + D)), fill=STROKE, width=STROKE_WIDTH, joint='curve')
draw.line(list(zip(x_points, y_points - D)), fill=STROKE, width=STROKE_WIDTH, joint='curve')

# フェルミ準位の線を追加（半透明の白）
FERMI_STROKE = STROKE[:3] + (128,)
draw.line([(0, HEIGHT/2), (WIDTH, HEIGHT/2)], fill=FERMI_STROKE, width=STROKE_WIDTH)

# 画像の保存
image.save('pn_junction_band.png')
