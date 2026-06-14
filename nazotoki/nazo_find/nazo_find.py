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

import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ============== パラメータ ==============
# キャンバス（Tシャツ前面プリント向けにやや縦長）
CANVAS_W = 4000
CANVAS_H = 5200

# 色（黒デザイン）。背景は見やすさ優先で白（入稿時は透過に戻すなら (0,0,0,0)）
COLOR = (0, 0, 0, 255)
BG_COLOR = (255, 255, 255, 255)

# フォント（Source Han Serif JP = Noto Serif CJK JP, index 0）
FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
FONT_INDEX = 0

# --- 大きな D（中抜き） ---
D_FONT_SIZE = 5000     # D のフォントサイズ（実寸は bbox で測る）
D_OUTLINE = 60         # 中抜き輪郭線の太さ
D_CY_FRAC = 0.40       # D の縦中心位置（キャンバス高に対する割合）

# --- D の中の F（虫眼鏡で見つける文字） ---
F_FONT_SIZE = 600      # F のフォントサイズ
F_CX_FRAC = 0.565       # F 中心の x（D の bbox に対する割合）
F_CY_FRAC = 0.5       # F 中心の y（D の bbox に対する割合）

# --- 虫眼鏡（中心は F に合わせ、レンズの大きさは F サイズと独立） ---
MAG_OFFSET_X_FRAC = -0.025  # レンズ中心の右オフセット（F 幅に対する割合）
MAG_OFFSET_Y_FRAC = 0.0  # レンズ中心の下オフセット（F 高に対する割合）
MAG_LENS_R = 656       # レンズ外半径（px・絶対値）。F を小さくしてもレンズは不変
MAG_LENS_W = 60        # レンズ枠の太さ
MAG_HANDLE_GAP = 120   # リング外縁〜持ち手の付け根の距離（＝細いネックの長さ）
MAG_NECK_W = 80        # ネック（リングと持ち手をつなぐ細線）の太さ
MAG_HANDLE_LEN = 1100  # 持ち手の先端までの距離（レンズ外縁から）
MAG_HANDLE_W = 200      # 持ち手の太さ
MAG_HANDLE_ANGLE = 45  # 持ち手の向き（度・画面座標で右下＝45）
MAG_BULGE = 2.45       # レンズの中心倍率（虫眼鏡で見たときの“膨張感”。1.0で歪みなし）

# --- 下部の "____ the answer." ---
BOTTOM_FONT_SIZE = 440  # "the answer." のフォントサイズ
BOTTOM_TEXT = "the answer."
BLANK_COUNT = 4         # 下線の本数（= 答え "find" の文字数）
BLANK_LEN = 190         # 下線 1 本の長さ
BLANK_W = 24            # 下線の太さ
BLANK_GAP = 40          # 下線どうしの間隔
GROUP_GAP = 120         # 下線群と "the answer." の間隔
BOTTOM_MARGIN = 900     # D の下端から下線ベースラインまでの余白


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


def apply_lens_bulge(img, cx, cy, radius, mag):
    """中心 (cx, cy)・半径 radius の円内に、虫眼鏡の“膨張歪み”をかける。

    レンズの物理を模した逆写像（出力ピクセル → 元ピクセル）＋ バイリニア補間。
      正規化半径 d = r / radius（0..1）に対し、元の半径を
        src_d = s*d + (1 - s)*d^3   （s = 1/mag）
      として元画像をサンプルする。中心付近は一様に mag 倍へ拡大され、
      リムに近づくほど圧縮される（＝実物のレンズらしい樽型の歪み）。
      d=1（円周）では src_d=1 なので円外と滑らかに連続し、継ぎ目が出ない。
    円外は一切変更しない。"""
    arr = np.asarray(img).astype(np.float32)
    H, W = arr.shape[:2]
    # 処理は円のバウンディングボックスに限定（全画素を回さない）
    x0 = max(int(math.floor(cx - radius)), 0)
    x1 = min(int(math.ceil(cx + radius)) + 1, W)
    y0 = max(int(math.floor(cy - radius)), 0)
    y1 = min(int(math.ceil(cy + radius)) + 1, H)
    ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dx, dy = xs - cx, ys - cy
    r = np.sqrt(dx * dx + dy * dy)
    d = np.clip(r / radius, 0.0, 1.0)
    s = 1.0 / mag
    src_d = s * d + (1.0 - s) * d ** 3
    scale = np.where(r > 1e-6, src_d * radius / r, 0.0)  # 同じ角度・半径だけ縮める
    sx, sy = cx + dx * scale, cy + dy * scale
    # バイリニア補間
    x0i = np.clip(np.floor(sx), 0, W - 1).astype(np.int32)
    y0i = np.clip(np.floor(sy), 0, H - 1).astype(np.int32)
    x1i = np.clip(x0i + 1, 0, W - 1)
    y1i = np.clip(y0i + 1, 0, H - 1)
    wx = np.clip(sx - x0i, 0.0, 1.0)[..., None]
    wy = np.clip(sy - y0i, 0.0, 1.0)[..., None]
    top = arr[y0i, x0i] * (1 - wx) + arr[y0i, x1i] * wx
    bot = arr[y1i, x0i] * (1 - wx) + arr[y1i, x1i] * wx
    sampled = top * (1 - wy) + bot * wy
    inside = (r <= radius)[..., None]
    arr[y0:y1, x0:x1] = np.where(inside, sampled, arr[y0:y1, x0:x1])
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


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
lens_r = MAG_LENS_R
lx = fcx + MAG_OFFSET_X_FRAC * FW
ly = fcy + MAG_OFFSET_Y_FRAC * FH
# レンズ内に虫眼鏡の“膨張歪み”をかける（リング枠の内側＝ガラスの口径まで）。
# ここまでに描いた D・F が対象。リング枠／持ち手はこの後に上から描くので歪まない。
# img を作り直すため draw も貼り直す。
img = apply_lens_bulge(img, lx, ly, lens_r - MAG_LENS_W / 2, MAG_BULGE)
draw = ImageDraw.Draw(img)
# レンズ（リング）
draw.ellipse([lx - lens_r, ly - lens_r, lx + lens_r, ly + lens_r],
             outline=COLOR, width=MAG_LENS_W)
# 持ち手まわり（レンズ外縁から右下 45 度へ）。
# 構造: リング ─ 細いネック(長さ GAP) ─ 太い持ち手。実物の虫眼鏡に寄せる。
ang = math.radians(MAG_HANDLE_ANGLE)
ux, uy = math.cos(ang), math.sin(ang)


def _on_axis(r):
    return (lx + ux * r, ly + uy * r)


# ネック: リング外縁から付け根まで（細線）。
# butt cap の直線で描くことで、端が内側へ膨らまずレンズ内に食い込まない。
# 内側端はリング枠の中ほど(lens_r - MAG_LENS_W/2)に潜り込ませて（枠内＝黒で
# 見えない）隙間なく接続し、外側端は持ち手の付け根に重ねて接続する。
neck_end = lens_r + MAG_HANDLE_GAP
draw.line([_on_axis(lens_r - MAG_LENS_W / 2),
           _on_axis(neck_end + MAG_HANDLE_W / 2)],
          fill=COLOR, width=MAG_NECK_W)

# 太い持ち手: 付け根(lens_r+GAP)から先端(lens_r+LEN)まで。
hx1, hy1 = _on_axis(neck_end + MAG_HANDLE_W / 2)
hx2, hy2 = _on_axis(lens_r + MAG_HANDLE_LEN)
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
