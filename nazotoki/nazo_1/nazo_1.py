from math import sqrt
from PIL import Image, ImageDraw

# パラメータ設定（ここだけを変更すれば全体のレイアウトが連動する）
LETTER_WIDTH = 400          # 1文字の横幅（縦は黄金比で導出）
LETTER_GAP = 100            # 文字間の間隔
CORNER_RADIUS = 35          # 角丸半径（三角モードでは三角カットの一辺）
L_CUTOUT_SIZE = CORNER_RADIUS  # Lの右上くり抜きサイズ（意味的に分離）

# "rounded" = 角丸モード / "triangle" = 三角カットモード
CORNER_MODE = "triangle"

TEXT_COLOR = (255, 255, 255, 255)
BACKGROUND_COLOR = (0, 0, 0, 0)

# 導出値
GOLDEN_RATIO = (1 + sqrt(5)) / 2
LETTER_HEIGHT = round(LETTER_WIDTH * GOLDEN_RATIO)
NUM_LETTERS = 4
CANVAS_WIDTH = NUM_LETTERS * LETTER_WIDTH + (NUM_LETTERS - 1) * LETTER_GAP
CANVAS_HEIGHT = LETTER_HEIGHT

img = Image.new('RGBA', (CANVAS_WIDTH, CANVAS_HEIGHT), BACKGROUND_COLOR)
draw = ImageDraw.Draw(img)


def draw_corner_rect(x, y, w, h, corners, fill):
    """corners=(tl, tr, br, bl) で指定した角のみを CORNER_MODE に従って処理した
    長方形を描画する。"""
    tl, tr, br, bl = corners
    r = CORNER_RADIUS
    if CORNER_MODE == "rounded":
        draw.rounded_rectangle(
            [x, y, x + w, y + h],
            radius=r,
            fill=fill,
            corners=(tl, tr, br, bl),
        )
    elif CORNER_MODE == "triangle":
        points = []
        # 左上（左辺上端スタート、時計回り）
        if tl:
            points.append((x, y + r))
            points.append((x + r, y))
        else:
            points.append((x, y))
        # 右上
        if tr:
            points.append((x + w - r, y))
            points.append((x + w, y + r))
        else:
            points.append((x + w, y))
        # 右下
        if br:
            points.append((x + w, y + h - r))
            points.append((x + w - r, y + h))
        else:
            points.append((x + w, y + h))
        # 左下
        if bl:
            points.append((x + r, y + h))
            points.append((x, y + h - r))
        else:
            points.append((x, y + h))
        draw.polygon(points, fill=fill)
    else:
        raise ValueError(f"Unknown CORNER_MODE: {CORNER_MODE}")


def draw_B(x, y):
    """B: Dを縦に2つ並べた形。右辺中央にくぼみができる。"""
    half_h = LETTER_HEIGHT // 2
    draw_corner_rect(x, y, LETTER_WIDTH, half_h,
                     (False, True, True, False), TEXT_COLOR)
    draw_corner_rect(x, y + half_h, LETTER_WIDTH, LETTER_HEIGHT - half_h,
                     (False, True, True, False), TEXT_COLOR)


def draw_O(x, y):
    """O: 4隅すべてを処理した長方形。"""
    draw_corner_rect(x, y, LETTER_WIDTH, LETTER_HEIGHT,
                     (True, True, True, True), TEXT_COLOR)


def draw_L(x, y):
    """L: 長方形の右上を正方形でくり抜いた形（モードに関わらず正方形）。"""
    draw.rectangle(
        [x, y, x + LETTER_WIDTH, y + LETTER_HEIGHT],
        fill=TEXT_COLOR,
    )
    draw.rectangle(
        [x + LETTER_WIDTH - L_CUTOUT_SIZE, y,
         x + LETTER_WIDTH, y + L_CUTOUT_SIZE],
        fill=BACKGROUND_COLOR,
    )


def draw_D(x, y):
    """D: 右上・右下のみを処理した長方形。"""
    draw_corner_rect(x, y, LETTER_WIDTH, LETTER_HEIGHT,
                     (False, True, True, False), TEXT_COLOR)


letter_drawers = [draw_B, draw_O, draw_L, draw_D]
for i, drawer in enumerate(letter_drawers):
    drawer(i * (LETTER_WIDTH + LETTER_GAP), 0)

img.save('nazo_1.png')
print(f'画像を保存しました: nazo_1.png '
      f'({CANVAS_WIDTH} x {CANVAS_HEIGHT} px, mode={CORNER_MODE})')
