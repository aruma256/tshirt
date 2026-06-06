import math
from PIL import Image, ImageDraw

# ============== パラメータ ==============
CANVAS_W = 4000
CANVAS_H = 1500

# 直径（地球=1）。惑星・月は忠実比。
EARTH_DIA = 200
MERCURY_DIA = round(EARTH_DIA * 0.3825)
VENUS_DIA = round(EARTH_DIA * 0.9489)
MOON_DIA = round(EARTH_DIA * 0.2724)

# 太陽だけは別扱い。実比は 109.1251 倍だが、それだと
#   (1) 巨大な「壁」になり、
#   (2) 公転軌道（太陽中心の弧）の半径が大きすぎてほぼ直線になる。
# 距離と同じく「視覚優先」で縮小する。SUN_VISUAL_RATIO を変えて調整。
SUN_TRUE_RATIO = 109.1251  # 参考: 実際の直径比
SUN_VISUAL_RATIO = 12      # ← 見た目調整用（大きいほど壁＆軌道が直線寄り）
SUN_DIA = round(EARTH_DIA * SUN_VISUAL_RATIO)

# 太陽は大きすぎるので左に大きく見切れる
SUN_VISIBLE_RIGHT = 280  # キャンバス上で太陽の右端が見える位置
SUN_RADIUS = SUN_DIA // 2
SUN_CX = SUN_VISIBLE_RIGHT - SUN_RADIUS  # 中心はキャンバス左外
SUN_CY = CANVAS_H // 2  # 縦中央

# 惑星の位置: 太陽からの距離を「実際の間隔」で配置する。
PLANET_Y = 1000  # 惑星の高さ（下寄り）

# 太陽からの平均距離（AU, 実値）。間隔比は忠実に。
MERCURY_AU = 0.387
VENUS_AU = 0.723
EARTH_AU = 1.000

# 地球をこの x に置きたい（構図優先）。ここから AU→px スケールを逆算する。
EARTH_X = 2550

# 太陽を実比より大きく描いているため、距離は太陽の“描画上の表面”を
# 起点に測る（中心から実比で測ると水星が巨大な太陽にめり込むため）。
_orbit_dy = PLANET_Y - SUN_CY
AU_PX = (math.hypot(EARTH_X - SUN_CX, _orbit_dy) - SUN_RADIUS) / EARTH_AU


def _planet_x_from_au(au):
    """太陽表面から au[AU] の距離にある惑星の x 座標。"""
    r = SUN_RADIUS + au * AU_PX
    return SUN_CX + math.sqrt(r * r - _orbit_dy * _orbit_dy)


MERCURY_X = _planet_x_from_au(MERCURY_AU)
VENUS_X = _planet_x_from_au(VENUS_AU)

# 月は地球を周回。公転半径は実データから決める。
# 本来 月-地球 = 384,400 km。これをどのスケールで描いても破綻する:
#   ・距離スケール(AU_PX): 0.00257 AU ≈ 6px（地球に埋まる）
#   ・直径スケール       : 約30.1地球直径 ≈ 6000px（画面外）
# そこで両スケールの幾何平均（対数スケールの中点）を採用する＝約188px。
MOON_DIST_KM = 384_400
EARTH_SUN_KM = 149_597_870  # = 1 AU
EARTH_DIA_KM = 12_756
_moon_r_dist = (MOON_DIST_KM / EARTH_SUN_KM) * AU_PX      # 距離スケール
_moon_r_size = (MOON_DIST_KM / EARTH_DIA_KM) * EARTH_DIA  # 直径スケール
MOON_ORBIT_R = round(math.sqrt(_moon_r_dist * _moon_r_size))

# 地球から見た月の方向（右下。ラベルが地球ラベルと重ならない側に置く）
MOON_ORBIT_ANGLE = 35
MOON_X = EARTH_X + MOON_ORBIT_R * math.cos(math.radians(MOON_ORBIT_ANGLE))
MOON_Y = PLANET_Y + MOON_ORBIT_R * math.sin(math.radians(MOON_ORBIT_ANGLE))

# ラベル（斜め線の先）の見た目
# 惑星の縁から右上45度に線を引き、その延長線上に文字を45度回転して並べる。
LABEL_LEAD_LEN = 170     # ラベルまでの斜めリード線の長さ
LABEL_CHAR_PITCH = 130   # ラベル文字の間隔（斜め方向、中心〜中心）
LABEL_SQUARE_SIZE = 84   # ■（空欄＝置換前のかな）の一辺
LABEL_ANGLE = 45         # ラベル全体の傾き（度）

# 線の太さ
LINE_W = 8     # 軌道、引き出し線

# 7セグ風の数字
DIGIT_W = 64
DIGIT_H = 90
SEG_T = 14

# 色
COLOR = (0, 0, 0, 255)
BG_COLOR = (255, 255, 255, 255)  # 検討用に一旦不透明の白

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


def _draw_digit_on(td, cx, cy, digit):
    """7セグ風の数字を td(ImageDraw) の (cx, cy) を中心に描く。"""
    w, h, t = DIGIT_W, DIGIT_H, SEG_T
    x = cx - w // 2
    y = cy - h // 2
    mid = y + h // 2
    half_t = t // 2

    if digit == 1:
        td.rectangle([cx - half_t, y, cx + half_t, y + h], fill=COLOR)
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
        td.rectangle(segs[seg], fill=COLOR)


def render_label_char(kana):
    """ラベル1文字を透明タイルに upright で描いて返す（回転前）。"""
    size = 160
    tile = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    c = size // 2
    d = KANA_TO_DIGIT.get(kana)
    if d is not None:
        _draw_digit_on(td, c, c, d)
    else:
        s = LABEL_SQUARE_SIZE // 2
        td.rectangle([c - s, c - s, c + s, c + s], fill=COLOR)
    return tile


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


def draw_moon_orbit():
    """月の地球周回軌道（円）。"""
    draw.ellipse(
        [
            EARTH_X - MOON_ORBIT_R, PLANET_Y - MOON_ORBIT_R,
            EARTH_X + MOON_ORBIT_R, PLANET_Y + MOON_ORBIT_R,
        ],
        outline=COLOR,
        width=LINE_W,
    )


def draw_planet(planet_x, planet_y, dia):
    """惑星（塗りつぶし円）。"""
    r = dia / 2
    draw.ellipse(
        [planet_x - r, planet_y - r, planet_x + r, planet_y + r],
        fill=COLOR,
    )


def draw_planet_label(planet_x, planet_y, planet_dia, kana_str, lead_len=None):
    """惑星の縁から右上45度に線を引き、その延長線上に
    45度回転させた文字を並べる。"""
    if lead_len is None:
        lead_len = LABEL_LEAD_LEN

    pr = planet_dia / 2
    dirx = math.cos(math.radians(-LABEL_ANGLE))
    diry = math.sin(math.radians(-LABEL_ANGLE))

    # 惑星の縁から開始（右上45度方向）
    edge_x = planet_x + pr * dirx
    edge_y = planet_y + pr * diry

    # 斜めのリード線
    line_end_x = edge_x + dirx * lead_len
    line_end_y = edge_y + diry * lead_len
    draw.line(
        [(edge_x, edge_y), (line_end_x, line_end_y)],
        fill=COLOR,
        width=LINE_W,
        joint="curve",
    )

    # 延長線上に、45度回転した文字を並べる
    cx = line_end_x + dirx * (LABEL_CHAR_PITCH * 0.5)
    cy = line_end_y + diry * (LABEL_CHAR_PITCH * 0.5)
    for ch in kana_str:
        tile = render_label_char(ch)
        rot = tile.rotate(LABEL_ANGLE, expand=True, resample=Image.BICUBIC)
        img.alpha_composite(
            rot,
            (round(cx - rot.width / 2), round(cy - rot.height / 2)),
        )
        cx += dirx * LABEL_CHAR_PITCH
        cy += diry * LABEL_CHAR_PITCH


# ============== 描画 ==============

# 太陽
draw_sun_filled()

# 軌道
draw_orbit(MERCURY_X, PLANET_Y)
draw_orbit(VENUS_X, PLANET_Y)
draw_orbit(EARTH_X, PLANET_Y)
draw_moon_orbit()

# 惑星
draw_planet(MERCURY_X, PLANET_Y, MERCURY_DIA)
draw_planet(VENUS_X, PLANET_Y, VENUS_DIA)
draw_planet(EARTH_X, PLANET_Y, EARTH_DIA)
draw_planet(MOON_X, MOON_Y, MOON_DIA)

# ラベル（引き出し線つき）
draw_planet_label(MERCURY_X, PLANET_Y, MERCURY_DIA, "すいせい")
draw_planet_label(VENUS_X, PLANET_Y, VENUS_DIA, "きんせい")
draw_planet_label(EARTH_X, PLANET_Y, EARTH_DIA, "ちきゅう")
draw_planet_label(MOON_X, MOON_Y, MOON_DIA, "つき")

img.save("nazo_3.png")
print(f"画像を保存しました: nazo_3.png ({CANVAS_W} x {CANVAS_H} px)")
