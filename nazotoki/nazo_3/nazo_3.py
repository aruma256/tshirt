import math
from PIL import Image, ImageDraw

# ============== パラメータ ==============
CANVAS_W = 4000
CANVAS_H = 1500

# 直径（地球=1）。比は忠実に。
EARTH_DIA = 200
SUN_DIA = round(EARTH_DIA * 109.1251)
MERCURY_DIA = round(EARTH_DIA * 0.3825)
VENUS_DIA = round(EARTH_DIA * 0.9489)
MOON_DIA = round(EARTH_DIA * 0.2724)

# 太陽は大きすぎるので左に大きく見切れる
SUN_VISIBLE_RIGHT = 280  # キャンバス上で太陽の右端が見える位置
SUN_RADIUS = SUN_DIA // 2
SUN_CX = SUN_VISIBLE_RIGHT - SUN_RADIUS  # 中心はキャンバス左外
SUN_CY = CANVAS_H // 2  # 縦中央

# 惑星の位置（距離は視覚優先で適当に）
PLANET_Y = 1000  # 惑星の高さ（下寄り）
MERCURY_X = 800
VENUS_X = 1650
EARTH_X = 2550
# 月は地球の右上に少しずらして配置（地球を周回するイメージ）
MOON_X = 2850
MOON_Y = 820

# ラベル（折れ線の先）の位置と見た目
LABEL_Y = 350  # 惑星より上にラベル列
LABEL_CIRCLE_DIA = 150
LABEL_CIRCLE_GAP = 10
LABEL_LINE_W = 7   # ラベル円の枠線太さ

# 月のラベルは小さく、月の右側に短い引き出しで
MOON_LABEL_Y = 600

# 線の太さ
LINE_W = 8     # 軌道、引き出し線

# 7セグ風の数字
DIGIT_W = 64
DIGIT_H = 90
SEG_T = 14

# 色
COLOR = (0, 0, 0, 255)
BG_COLOR = (255, 255, 255, 0)

# かな→数字 の対応
KANA_TO_DIGIT = {"い": 1, "ん": 2, "せ": 3, "き": 4}

# ============== セットアップ ==============
img = Image.new("RGBA", (CANVAS_W, CANVAS_H), BG_COLOR)
draw = ImageDraw.Draw(img)

# ============== ヘルパ ==============

# 7セグの構成（a:上, b:右上, c:右下, d:下, e:左下, f:左上, g:中央）
DIGIT_SEGMENTS = {
    2: ["a", "b", "g", "e", "d"],
    3: ["a", "b", "g", "c", "d"],
    4: ["f", "b", "g", "c"],
}


def draw_digit(cx, cy, digit):
    """7セグ風の数字を (cx, cy) を中心に描く。"""
    w, h, t = DIGIT_W, DIGIT_H, SEG_T
    x = cx - w // 2
    y = cy - h // 2
    mid = y + h // 2
    half_t = t // 2

    if digit == 1:
        draw.rectangle([cx - half_t, y, cx + half_t, y + h], fill=COLOR)
        return

    segs = {
        "a": [x, y, x + w, y + t],
        "b": [x + w - t, y, x + w, mid + half_t],
        "c": [x + w - t, mid - half_t, x + w, y + h],
        "d": [x, y + h - t, x + w, y + h],
        "e": [x, mid - half_t, x + t, y + h],
        "f": [x, y, x + t, mid + half_t],
        "g": [x, mid - half_t, x + w, mid + half_t],
    }
    for seg in DIGIT_SEGMENTS[digit]:
        draw.rectangle(segs[seg], fill=COLOR)


def draw_label_char(cx, cy, kana):
    """ラベル1文字分: 円の輪郭 + 必要なら数字を中に描く。"""
    r = LABEL_CIRCLE_DIA // 2
    draw.ellipse(
        [cx - r, cy - r, cx + r, cy + r],
        outline=COLOR,
        width=LABEL_LINE_W,
    )
    d = KANA_TO_DIGIT.get(kana)
    if d is not None:
        draw_digit(cx, cy, d)


def arc_points_around_sun(through_x, through_y):
    """太陽を中心とし (through_x, through_y) を通る円の、キャンバス可視域の点列を返す。"""
    cx, cy = SUN_CX, SUN_CY
    r = math.hypot(through_x - cx, through_y - cy)
    points = []
    margin = 200
    for y in range(-margin, CANVAS_H + margin + 1, 2):
        dy = y - cy
        if r > abs(dy):
            dx = math.sqrt(r * r - dy * dy)
            x = cx + dx  # 円の右側
            if -margin <= x <= CANVAS_W + margin:
                points.append((x, y))
    return points


def draw_sun_filled():
    """太陽（塗りつぶし）。可視部分のみのポリゴンとして描画してメモリ節約。"""
    boundary = arc_points_around_sun(SUN_CX + SUN_RADIUS, SUN_CY)
    if len(boundary) < 2:
        return
    # 左側をぐるりと閉じる
    boundary.append((-200, CANVAS_H + 200))
    boundary.append((-200, -200))
    draw.polygon(boundary, fill=COLOR)


def draw_orbit(planet_x, planet_y):
    """惑星の公転軌道（弧）を描く。"""
    pts = arc_points_around_sun(planet_x, planet_y)
    if len(pts) >= 2:
        draw.line(pts, fill=COLOR, width=LINE_W, joint="curve")


def draw_planet(planet_x, planet_y, dia):
    """惑星（塗りつぶし円）。"""
    r = dia / 2
    draw.ellipse(
        [planet_x - r, planet_y - r, planet_x + r, planet_y + r],
        fill=COLOR,
    )


def draw_planet_label(planet_x, planet_y, planet_dia, kana_str, label_y=None):
    """惑星から右上方向に折れ線を伸ばし、ラベル（かな置換）を描く。
    折れ線の経路: 惑星の縁 → 右上45度の斜め → 水平 → ラベル先頭"""
    if label_y is None:
        label_y = LABEL_Y

    pr = planet_dia / 2

    # 惑星の縁から開始（右上45度方向）
    edge_x = planet_x + pr * math.cos(math.radians(-45))
    edge_y = planet_y + pr * math.sin(math.radians(-45))

    # 斜め線の終点（45度で label_y まで上がる）
    diag_end_x = edge_x + (edge_y - label_y)
    diag_end_y = label_y

    # 水平延長
    horiz_ext = 40
    horiz_end_x = diag_end_x + horiz_ext

    # ラベル先頭文字の中心
    label_first_cx = horiz_end_x + LABEL_CIRCLE_DIA // 2

    # 折れ線
    draw.line(
        [
            (edge_x, edge_y),
            (diag_end_x, diag_end_y),
            (horiz_end_x, diag_end_y),
        ],
        fill=COLOR,
        width=LINE_W,
        joint="curve",
    )

    # ラベル各文字
    cx = label_first_cx
    for ch in kana_str:
        draw_label_char(cx, label_y, ch)
        cx += LABEL_CIRCLE_DIA + LABEL_CIRCLE_GAP


# ============== 描画 ==============

# 太陽
draw_sun_filled()

# 軌道
draw_orbit(MERCURY_X, PLANET_Y)
draw_orbit(VENUS_X, PLANET_Y)
draw_orbit(EARTH_X, PLANET_Y)

# 惑星
draw_planet(MERCURY_X, PLANET_Y, MERCURY_DIA)
draw_planet(VENUS_X, PLANET_Y, VENUS_DIA)
draw_planet(EARTH_X, PLANET_Y, EARTH_DIA)
draw_planet(MOON_X, MOON_Y, MOON_DIA)

# ラベル（引き出し線つき）
draw_planet_label(MERCURY_X, PLANET_Y, MERCURY_DIA, "すいせい")
draw_planet_label(VENUS_X, PLANET_Y, VENUS_DIA, "きんせい")
draw_planet_label(EARTH_X, PLANET_Y, EARTH_DIA, "ちきゅう")
# 月のラベルは別の高さ（重なり回避）
draw_planet_label(MOON_X, MOON_Y, MOON_DIA, "つき", label_y=MOON_LABEL_Y)

img.save("nazo_3.png")
print(f"画像を保存しました: nazo_3.png ({CANVAS_W} x {CANVAS_H} px)")
