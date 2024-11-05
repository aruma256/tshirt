from PIL import Image, ImageDraw

# 基本設定
RIVER_WIDTH = 512
BRIDGE_WIDTH = 256
ISLAND_WIDTH = 1024
WIDTH = ISLAND_WIDTH * 4 + BRIDGE_WIDTH * 3
HEIGHT = RIVER_WIDTH * 2 + BRIDGE_WIDTH + (ISLAND_WIDTH - RIVER_WIDTH)
# HEIGHT = 2048
print(f"WIDTH: {WIDTH}, HEIGHT: {HEIGHT}")

# 色設定
WHITE = (255, 255, 255, 255)        # 白（完全不透明）
BLACK = (0, 0, 0, 255)        # 黒（完全不透明）
BLUE = (0, 0, 255, 255)        # 青（完全不透明）
INK_BLUE = (0, 63, 142, 255)    # インクブルー（完全不透明）
TRANSPARENT = (0, 0, 0, 0)    # 透明

# 描画設定
BACKGROUND_COLOR = TRANSPARENT  # 背景色
RIVER_COLOR = INK_BLUE            # 川の色（WHITE/BLACKを切り替え）

# キャンバスの作成
image = Image.new('RGBA', (WIDTH, HEIGHT), BACKGROUND_COLOR)
draw = ImageDraw.Draw(image)

def draw_rect(x, y, w, h, fill=RIVER_COLOR):
    draw.rectangle([(x, y), (x + w, y + h)], fill=fill)

x = 0

# 左から1つめの区画の描画
draw_rect(x + 0, HEIGHT // 2 - RIVER_WIDTH // 2, ISLAND_WIDTH // 2, RIVER_WIDTH)
draw_rect(x + ISLAND_WIDTH // 2, 0, ISLAND_WIDTH // 2, RIVER_WIDTH)
draw_rect(x + ISLAND_WIDTH // 2, HEIGHT - RIVER_WIDTH, ISLAND_WIDTH // 2, RIVER_WIDTH)
draw_rect(x + ISLAND_WIDTH // 2 - RIVER_WIDTH // 2, 0, RIVER_WIDTH, HEIGHT)
x += ISLAND_WIDTH

# 間の橋
x += BRIDGE_WIDTH

# 左から2つめの区画の描画
draw_rect(x, 0, ISLAND_WIDTH, RIVER_WIDTH)
draw_rect(x, HEIGHT - RIVER_WIDTH, ISLAND_WIDTH, RIVER_WIDTH)
x += ISLAND_WIDTH

# 間の橋
x += BRIDGE_WIDTH

# 左から3つめの区画の描画
draw_rect(x, 0, ISLAND_WIDTH, RIVER_WIDTH)
draw_rect(x, HEIGHT - RIVER_WIDTH, ISLAND_WIDTH, RIVER_WIDTH)
draw_rect(x + ISLAND_WIDTH // 2 - RIVER_WIDTH // 2, 0, RIVER_WIDTH, HEIGHT)
draw_rect(x, HEIGHT // 2 - BRIDGE_WIDTH // 2, ISLAND_WIDTH, BRIDGE_WIDTH, TRANSPARENT)
x += ISLAND_WIDTH

# 間の橋
x += BRIDGE_WIDTH

# 左から4つめの区画の描画
draw_rect(x, 0, ISLAND_WIDTH, RIVER_WIDTH)
draw_rect(x, HEIGHT - RIVER_WIDTH, ISLAND_WIDTH, RIVER_WIDTH)
x += ISLAND_WIDTH

image.save("konigsberg.png")
