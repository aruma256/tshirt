from PIL import Image, ImageDraw

# パラメータ設定
square_size = 256  # 正方形の1辺のサイズ
gap = 16  # 正方形間の間隔
cols = 8  # 横方向の正方形の数
rows = 6  # 縦方向の正方形の数
corner_radius = 20  # 角の丸みの半径
arrow_width = 40  # 矢印の太さ
arrow_corner_radius = 20  # 矢印の曲がり角の丸みの半径
arrow_visual_offset = 8  # 矢印の視覚調整用右シフト量

# 色の定義 (RGBA形式)
color_blue = (25, 118, 210, 255)    # 青
color_yellow = (249, 209, 78, 255)  # 黄
color_green = (76, 174, 79, 255)    # 緑
color_pink = (255, 102, 196, 255)   # ピンク
color_light_blue = (140, 186, 232, 255)    # 薄い青 (元の色と白の中間)
color_light_yellow = (252, 232, 166, 255)  # 薄い黄色 (元の色と白の中間)
color_light_pink = (255, 178, 225, 255)    # 薄いピンク (元の色と白の中間)
color_light_green = (165, 214, 167, 255)   # 薄い緑 (元の色と白の中間)

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

# RGBA画像を作成（背景は白）
img = Image.new('RGBA', (canvas_width, canvas_height), (255, 255, 255, 255))
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

# グリッド座標からピクセル座標（中心）への変換
def grid_to_pixel(col, row):
    x = col * (square_size + gap) + square_size // 2
    y = row * (square_size + gap) + square_size // 2
    return x, y

# 折れ曲がった矢印を描画
# 経路: (5,4) → (3,4) → (3,2) → (5,2) → (5,3) → (7,3)
arrow_color = (0, 0, 0, 255)  # 黒

# 各セグメントの座標を計算
p1 = grid_to_pixel(5, 4)
p2 = grid_to_pixel(3, 4)
p3 = grid_to_pixel(3, 2)
p4 = grid_to_pixel(5, 2)
p5 = grid_to_pixel(5, 3)
p6 = grid_to_pixel(7, 3)

# 矢印の半幅
half_width = arrow_width // 2

# セグメント1: (5,4) → (3,4) 水平線（左へ）
draw.rectangle([p2[0], p1[1] - half_width, p1[0], p1[1] + half_width], fill=arrow_color)

# セグメント2: (3,4) → (3,2) 垂直線（上へ）
draw.rectangle([p3[0] - half_width, p3[1], p2[0] + half_width, p2[1]], fill=arrow_color)

# セグメント3: (3,2) → (5,2) 水平線（右へ）
draw.rectangle([p3[0], p4[1] - half_width, p4[0], p3[1] + half_width], fill=arrow_color)

# セグメント4: (5,2) → (5,3) 垂直線（下へ）
draw.rectangle([p4[0] - half_width, p4[1], p5[0] + half_width, p5[1]], fill=arrow_color)

# セグメント5: (5,3) → (7,3) 水平線（右へ）- 矢印の根元まで
arrow_head_size = arrow_width * 1.5
arrow_head_offset = arrow_head_size / 2  # 三角形の中心を正方形の中心に合わせるためのオフセット
draw.rectangle([p5[0], p6[1] - half_width, p6[0] - arrow_head_offset + arrow_visual_offset, p5[1] + half_width], fill=arrow_color)

# 曲がり角を丸くする（円で接続部分を描画）
for center in [p2, p3, p4, p5]:
    draw.ellipse([center[0] - half_width, center[1] - half_width, 
                  center[0] + half_width, center[1] + half_width], fill=arrow_color)

# 矢印の先端を描画（三角形）- 三角形の中心が正方形の中心になるように（視覚調整込み）
draw.polygon([
    (p6[0] + arrow_head_offset + arrow_visual_offset, p6[1]),  # 先端
    (p6[0] - arrow_head_offset + arrow_visual_offset, p6[1] - arrow_head_size // 2),
    (p6[0] - arrow_head_offset + arrow_visual_offset, p6[1] + arrow_head_size // 2)
], fill=arrow_color)

# 画像を保存
img.save('grid_squares.png')
print(f'画像を保存しました: grid_squares.png')
print(f'キャンバスサイズ: {canvas_width} x {canvas_height} px')
