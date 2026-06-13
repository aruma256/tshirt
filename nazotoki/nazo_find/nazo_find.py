"""謎解きTシャツ「FIND」入稿用画像を生成するスクリプト。

謎: 大きな中抜きの「D」の中に、虫眼鏡で「F」を見つける。
    → "F in D" = "FIND"。
    下部の "____ the answer." の 4 つの独立した下線が、
    答えが 4 文字（find）であることを示す。読みは "find the answer."。

フォント: Source Han Serif JP。
    ※ この環境には Adobe 版 "Source Han Serif" は未インストールだが、
      同一デザインソースの Google 版 "Noto Serif CJK JP" が入っている
      （両者は字形が一致する同じ書体）。よってこれを使用する。
"""

import math

from PIL import Image, ImageDraw, ImageFont

# ============== パラメータ ==============
# キャンバス（Tシャツ前面プリント向けにやや縦長）
CANVAS_W = 2000
CANVAS_H = 2600

# 色（黒デザイン）。背景は見やすさ優先で白（入稿時は透過に戻すなら (0,0,0,0)）
COLOR = (0, 0, 0, 255)
BG_COLOR = (255, 255, 255, 255)

# フォント（Source Han Serif JP = Noto Serif CJK JP, index 0）
FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
FONT_INDEX = 0

# --- 大きな D（中抜き） ---
D_FONT_SIZE = 2500     # D のフォントサイズ（実寸は bbox で測る）
D_OUTLINE = 30         # 中抜き輪郭線の太さ
D_CY_FRAC = 0.40       # D の縦中心位置（キャンバス高に対する割合）

# --- D の中の F（虫眼鏡で見つける文字） ---
F_FONT_SIZE = 500      # F のフォントサイズ
F_CX_FRAC = 0.565       # F 中心の x（D の bbox に対する割合）
F_CY_FRAC = 0.5       # F 中心の y（D の bbox に対する割合）

# --- 虫眼鏡（F の右下に追従させる。基準は F のサイズ） ---
MAG_OFFSET_X_FRAC = -0.025  # レンズ中心の右オフセット（F 幅に対する割合）
MAG_OFFSET_Y_FRAC = 0.0  # レンズ中心の下オフセット（F 高に対する割合）
MAG_LENS_R_FRAC = 0.9    # レンズ外半径（F 高に対する割合）
MAG_LENS_W = 30        # レンズ枠の太さ
MAG_HANDLE_LEN = 540   # 持ち手の長さ（レンズ外縁から）
MAG_HANDLE_W = 100      # 持ち手の太さ
MAG_HANDLE_ANGLE = 45  # 持ち手の向き（度・画面座標で右下＝45）

# --- 下部の "____ the answer." ---
BOTTOM_FONT_SIZE = 220  # "the answer." のフォントサイズ
BOTTOM_TEXT = "the answer."
BLANK_COUNT = 4         # 下線の本数（= 答え "find" の文字数）
BLANK_LEN = 95          # 下線 1 本の長さ
BLANK_W = 12            # 下線の太さ
BLANK_GAP = 20          # 下線どうしの間隔
GROUP_GAP = 60          # 下線群と "the answer." の間隔
BOTTOM_MARGIN = 450     # D の下端から下線ベースラインまでの余白


# ============== ヘルパー ==============

def load_font(size):
    return ImageFont.truetype(FONT_PATH, size, index=FONT_INDEX)


def render_glyph(text, font, fill=None, stroke_width=0, stroke_fill=None):
    """文字（列）を透過レイヤに描き、alpha の bbox でタイトに切り抜いて返す。

    中抜きにするときは fill=(0,0,0,0)（透明）+ stroke_width/stroke_fill を指定。
    戻り値の内部は透明なので、下のレイヤ（シャツ色や中の F）が透ける。
    一時キャンバスは文字列の実 bbox から確保するので、長い文字列でも切れない。
    """
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    l, t, r, b = probe.textbbox((0, 0), text, font=font, stroke_width=stroke_width)
    pad = max(font.size // 2, stroke_width * 3, 8)
    tmp = Image.new("RGBA", (r - l + pad * 2, b - t + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    d.text((pad - l, pad - t), text, font=font,
           fill=fill if fill is not None else (0, 0, 0, 0),
           stroke_width=stroke_width, stroke_fill=stroke_fill)
    return tmp.crop(tmp.getbbox())


def round_cap_line(draw, x1, y1, x2, y2, width, fill):
    """両端が丸い太線（持ち手用）。"""
    draw.line([(x1, y1), (x2, y2)], fill=fill, width=width)
    r = width / 2
    for (cx, cy) in [(x1, y1), (x2, y2)]:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)


# ============== セットアップ ==============
img = Image.new("RGBA", (CANVAS_W, CANVAS_H), BG_COLOR)
draw = ImageDraw.Draw(img)

# ============== 大きな D（中抜き） ==============
d_font = load_font(D_FONT_SIZE)
d_layer = render_glyph("D", d_font, fill=(0, 0, 0, 0),
                       stroke_width=D_OUTLINE, stroke_fill=COLOR)
DW, DH = d_layer.size
D_left = (CANVAS_W - DW) // 2
D_top = round(CANVAS_H * D_CY_FRAC - DH / 2)
img.alpha_composite(d_layer, (D_left, D_top))

# D の bbox 内座標 → キャンバス座標 への変換
def in_D(fx, fy):
    return (D_left + fx * DW, D_top + fy * DH)

# ============== D の中の F ==============
f_font = load_font(F_FONT_SIZE)
f_layer = render_glyph("F", f_font, fill=COLOR)
FW, FH = f_layer.size
fcx, fcy = in_D(F_CX_FRAC, F_CY_FRAC)
img.alpha_composite(f_layer, (round(fcx - FW / 2), round(fcy - FH / 2)))

# ============== 虫眼鏡（F の右下） ==============
lens_r = MAG_LENS_R_FRAC * FH
lx = fcx + MAG_OFFSET_X_FRAC * FW
ly = fcy + MAG_OFFSET_Y_FRAC * FH
# レンズ（リング）
draw.ellipse([lx - lens_r, ly - lens_r, lx + lens_r, ly + lens_r],
             outline=COLOR, width=MAG_LENS_W)
# 持ち手（レンズ外縁から右下 45 度へ）
ang = math.radians(MAG_HANDLE_ANGLE)
ux, uy = math.cos(ang), math.sin(ang)
hx1 = lx + ux * (lens_r + MAG_LENS_W / 2)
hy1 = ly + uy * (lens_r + MAG_LENS_W / 2)
hx2 = lx + ux * (lens_r + MAG_HANDLE_LEN)
hy2 = ly + uy * (lens_r + MAG_HANDLE_LEN)
round_cap_line(draw, hx1, hy1, hx2, hy2, MAG_HANDLE_W, COLOR)

# ============== 下部 "____ the answer." ==============
b_font = load_font(BOTTOM_FONT_SIZE)
text_layer = render_glyph(BOTTOM_TEXT, b_font, fill=COLOR)  # 文字列も同様に切り抜き
TW, TH = text_layer.size

blanks_w = BLANK_COUNT * BLANK_LEN + (BLANK_COUNT - 1) * BLANK_GAP
total_w = blanks_w + GROUP_GAP + TW
start_x = (CANVAS_W - total_w) // 2

# ベースライン（D の下端からの余白で決める）。切り抜きの下端 ≒ 文字のベースライン。
baseline_y = D_top + DH + BOTTOM_MARGIN

# "the answer." を配置（下端をベースラインに合わせる）
text_x = start_x + blanks_w + GROUP_GAP
text_y = baseline_y - TH
img.alpha_composite(text_layer, (round(text_x), round(text_y)))

# 4 本の独立した下線（つなげない）。ベースラインの直下に置く。
bx = start_x
for _ in range(BLANK_COUNT):
    draw.rounded_rectangle(
        [bx, baseline_y, bx + BLANK_LEN, baseline_y + BLANK_W],
        radius=BLANK_W / 2, fill=COLOR)
    bx += BLANK_LEN + BLANK_GAP

# ============== 保存 ==============
out = "nazo_find.png"
img.save(out)
print(f"画像を保存しました: {out} ({CANVAS_W} x {CANVAS_H} px)")
