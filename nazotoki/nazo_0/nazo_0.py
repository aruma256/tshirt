from PIL import Image, ImageDraw

# パラメータ設定
square_size = 256  # 正方形の1辺のサイズ
gap = 16  # 正方形間の間隔
cols = 8  # 横方向の正方形の数
rows = 6  # 縦方向の正方形の数
corner_radius = 20  # 角の丸みの半径

# 色の定義 (RGBA形式)
color_blue = (0, 0, 255, 255)    # 青
color_yellow = (255, 255, 0, 255)  # 黄
color_green = (0, 255, 0, 255)   # 緑
color_pink = (255, 192, 203, 255)  # ピンク
color_light_yellow = (255, 255, 200, 255)  # 薄い黄色
color_light_pink = (255, 230, 240, 255)    # 薄いピンク
color_light_green = (200, 255, 200, 255)   # 薄い緑

# 描画する正方形の定義 [(col範囲, row範囲, 色)]
# 注意: 範囲は[開始, 終了]（終了を含む）
square_definitions = [
    ([2], range(0, 4), color_blue),             # (2,0～3): 青
    (range(0, 6), [1], color_yellow),           # (0～5, 1): 黄
    (range(2, 7), [5], color_green),            # (2～6,5): 緑
    (range(4, 8), [3], color_pink),             # (4～7,3): ピンク
    ([2], [1], color_green),                    # (2,1): 緑
    ([5], [1], color_light_yellow),             # (5,1): 薄い黄色
    ([5], [3], color_light_pink),               # (5,3): 薄いピンク
    ([5], [5], color_light_green),              # (5,5): 薄い緑
]

# キャンバスサイズを計算
canvas_width = cols * square_size + (cols - 1) * gap
canvas_height = rows * square_size + (rows - 1) * gap

# RGBA画像を作成（背景は透明）
img = Image.new('RGBA', (canvas_width, canvas_height), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# 定義に従って正方形を描画
for col_range, row_range, color in square_definitions:
    for row in row_range:
        for col in col_range:
            # 各正方形の左上座標を計算
            x = col * (square_size + gap)
            y = row * (square_size + gap)
            
            # 角丸の正方形を指定色で描画
            draw.rounded_rectangle(
                [x, y, x + square_size, y + square_size],
                radius=corner_radius,
                fill=color
            )

# 画像を保存
img.save('grid_squares.png')
print(f'画像を保存しました: grid_squares.png')
print(f'キャンバスサイズ: {canvas_width} x {canvas_height} px')
