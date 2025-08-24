import itertools
from PIL import Image, ImageDraw
import numpy as np

"""
1 2 3
4 5 6
7 8 9
"""

POSITIONS = {i + 1: np.array((x, y)) for i, (y, x) in enumerate(itertools.product([-1, 0, 1], repeat=2))}

ALPHABET_SHAPES = { # 角張ったデザインのアルファベット
    "A": [(1, 7), (1, 3), (3, 9), (4, 6)],
    "I": [(2, 8)],
    "K": [(1, 7), (3, 4), (4, 9)],
    "N": [(1, 7), (1, 9), (3, 9)],
    "O": [(1, 7), (7, 9), (9, 3), (3, 1)],
    "T": [(1, 3), (2, 8)],
    "Z": [(1, 3), (3, 7), (7, 9)],
}


def get_node_vertex_positions(position_num, offset_x, char_size, node_size):
    center = np.array((offset_x + char_size//2, char_size//2), dtype=np.int32)
    base = center + POSITIONS[position_num] * char_size//2
    base -= POSITIONS[position_num] * node_size//2 # char_sizeに収まるように調整
    offset = node_size//2
    return (
        (base[0] + offset -1, base[1] + offset -1),
        (base[0] - offset, base[1] + offset -1),
        (base[0] - offset, base[1] - offset),
        (base[0] + offset -1, base[1] - offset),
    )


def draw_line(draw, pos1, pos2, offset_x, char_size, node_size, line_width, text_color):
    """
    線を描画する
    """
    vertices_1 = get_node_vertex_positions(pos1, offset_x, char_size, node_size)
    vertices_2 = get_node_vertex_positions(pos2, offset_x, char_size, node_size)
    for v1, v2 in itertools.product(vertices_1, vertices_2):
        for o in itertools.chain(vertices_1, vertices_2):
            if o == v1 or o == v2:
                    continue
            draw.polygon([v1, v2, o], fill=text_color)


def draw_character(draw, char, offset_x, char_size, node_size, line_width, text_color):
    """
    文字を描画する
    """
    for pos1, pos2 in ALPHABET_SHAPES[char]:
        draw_line(draw, pos1, pos2, offset_x, char_size, node_size, line_width, text_color)



def draw_text(text, output_path="nazotoki_output.png", width=1024, height=128, 
              char_size=128, node_size=16, line_width=16, 
              bg_color="black", text_color="white"):
    """
    テキストを描画して画像を保存する
    
    Args:
        text (str): 描画するテキスト
        output_path (str): 出力ファイルのパス
        width (int): 画像の幅
        height (int): 画像の高さ
        char_size (int): 1文字のサイズ
        node_size (int): 頂点のサイズ
        line_width (int): 線の太さ
        bg_color (str): 背景色
        text_color (str): テキスト色
    """
    # 画像を作成
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # 各文字を描画
    for i, char in enumerate(text):
        offset_x = i * char_size
        draw_character(draw, char, offset_x, char_size, node_size, line_width, text_color)
    
    # 画像を保存
    img.save(output_path)
    print(f"Image saved to {output_path}")

def main():
    """メイン関数"""
    text = "NAZOTOKI"
    draw_text(text)

if __name__ == "__main__":
    main()
