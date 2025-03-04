from PIL import Image, ImageDraw

# 基本設定
BASE_SIZE = 4096        # 基本キャンバスサイズ
BORDER_WIDTH = 32       # 線の太さ
MAX_DEPTH = 14         # 最大分割回数

# 派生する設定
MARGIN = BORDER_WIDTH                      # 余白（線の太さと同じ）
CANVAS_SIZE = BASE_SIZE + (MARGIN * 2)     # 最終的なキャンバスサイズ

# 色設定
WHITE = (255, 255, 255, 255)  # 白（完全不透明）
BLACK = (0, 0, 0, 255)        # 黒（完全不透明）
TRANSPARENT = (0, 0, 0, 0)    # 透明

# 描画設定
BACKGROUND_COLOR = TRANSPARENT  # 背景色
STROKE_COLOR = BLACK           # 線の色（WHITE/BLACKを切り替え）

def draw_divisions(x, y, w, h, depth=0):
    """再帰的に分割線を描画する
    
    Args:
        x, y: 描画開始位置
        w, h: 描画領域のサイズ
        depth: 現在の深さ（偶数の場合は縦線、奇数の場合は横線）
    """
    if depth >= MAX_DEPTH:
        return
    
    if depth % 2 == 0:
        # 縦線を描画（中心に配置）
        draw.rectangle([
            (x + w/2 - BORDER_WIDTH/2, y),
            (x + w/2 + BORDER_WIDTH/2, y + h)
        ], fill=STROKE_COLOR)
        draw_divisions(x + w/2, y, w/2, h, depth + 1)
    else:
        # 横線を描画（中心に配置）
        draw.rectangle([
            (x, y + h/2 - BORDER_WIDTH/2),
            (x + w, y + h/2 + BORDER_WIDTH/2)
        ], fill=STROKE_COLOR)
        draw_divisions(x, y, w, h/2, depth + 1)

# キャンバスの作成
image = Image.new('RGBA', (CANVAS_SIZE, CANVAS_SIZE), BACKGROUND_COLOR)
draw = ImageDraw.Draw(image)

# 外枠を描画（中心に配置）
draw.rectangle([
    (MARGIN - BORDER_WIDTH/2, MARGIN - BORDER_WIDTH/2),
    (CANVAS_SIZE - MARGIN + BORDER_WIDTH/2, CANVAS_SIZE - MARGIN + BORDER_WIDTH/2)
], fill=STROKE_COLOR)

# 外枠の内側を透明に
draw.rectangle([
    (MARGIN + BORDER_WIDTH/2, MARGIN + BORDER_WIDTH/2),
    (CANVAS_SIZE - MARGIN - BORDER_WIDTH/2, CANVAS_SIZE - MARGIN - BORDER_WIDTH/2)
], fill=BACKGROUND_COLOR)

# 分割線の描画を開始
draw_divisions(MARGIN, MARGIN, BASE_SIZE, BASE_SIZE)

# 画像の保存
image.save("recursive_division_pattern.png")
