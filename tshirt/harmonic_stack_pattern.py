from PIL import Image, ImageDraw

# 新しい画像を作成（透明背景）
width = 3000
height = 2000
image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
draw = ImageDraw.Draw(image)

# 積み木のサイズ
block_width = 1000
block_height = 250
block_gap = 20

# 積み木を描画（下から順番に）
blocks = 8
start_x = width // 2 - block_width
start_y = height - block_height

previous_x = start_x  # 前の段のx座標を記録

for i in range(blocks):
    if i == 0:
        x = start_x
    else:
        # 直前の段からの相対位置で計算
        shift = block_width / ((blocks-i) * 2)
        print(i, (blocks-i) * 2)
        x = previous_x + shift
    
    y = start_y - (i * block_height)
    
    # アルファ値を計算（上のブロックほど不透明に）
    alpha = int(255 * (i + 1) / blocks)
    
    # 積み木を描画（長方形）- 上下のみに隙間を作る
    draw.rectangle(
        [(x, y + block_gap), (x + block_width, y + block_height - block_gap)],
        fill=(255, 255, 255, alpha)
    )
    
    previous_x = x  # 次の段のために現在のx座標を保存

# 画像を保存
image.save('harmonic_stack_pattern.png')
