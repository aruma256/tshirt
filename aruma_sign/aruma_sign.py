"""aruma のロゴ（サイン）を PNG / SVG で出力するスクリプト。

元は GIMP のパスツールで作ったもの（aruma_vr_sign.xcf のパス "gen4"）。
「パスに沿って楕円ブラシを動かした軌跡」として描かれており、ここではそれを
パスの制御点とブラシのパラメータから再現する。

  PNG: 折れ線化したパスの各線分について「両端に置いた楕円の凸包」を塗る。
       楕円を線分に沿って動かした軌跡は、ちょうどこの凸包になる。
  SVG: 楕円は円をアフィン変換（回転＋一方向の縮小）したものなので、パスを
       逆変換した座標で持ち、丸ペン（round cap/join）の stroke を <g transform>
       で楕円に戻す。近似ではなく数学的に同じ形になる。
"""

import argparse
import math

import numpy as np
from PIL import Image, ImageDraw

# PIL の「圧縮爆弾」防御上限を解除。画像は自前生成（外部入力なし）で安全であり、
# SS 倍の内部キャンバスが既定上限(約1.79億px)を超えて誤検知されるため。
Image.MAX_IMAGE_PIXELS = None

# ============== パラメータ ==============
# 座標系の基準となる正方形キャンバス（元の GIMP 画像と同じ）。
CANVAS = 4096

# スーパーサンプリング倍率（内部を SS 倍で描画 → 最後に 1/SS へ縮小して AA）。
SS = 4

# --- ブラシ（楕円） ---
# GIMP 上の設定は「サイズ 175 / 縦横比 0.50 / 角度 10」。GIMP の数値はそのまま楕円の
# 寸法にはならないので、サイズと比は元 PNG に最もよく重なる値（実測フィット）を使う。
BRUSH_SIZE = 172.75  # 長軸の直径(px)
BRUSH_RATIO = 1.47   # 長軸 / 短軸
BRUSH_ANGLE = 10     # 長軸の傾き(度)。画面上で時計回り（SVG の rotate と同じ向き）

# --- パス ---
# 各ストロークは 3 次ベジェの連結で、[P0, C1, C2, P1, C1, C2, P2, ...] の並び
# （SVG の "M P0 C C1 C2 P1 C1 C2 P2 ..." と同じ）。座標は CANVAS 基準の px。
STROKES = [
    [  # 左の A: 山
        (642, 2740),
        (174.139, 1638.239), (350.996, 727.763), (1397, 2172),
    ],
    [  # 左の A: 横棒
        (551.25, 2109.5),
        (815, 1885), (997, 1797.5), (1210, 1707),
    ],
    [  # r（最後の 1 区間は折り返しの短い直線）
        (1309.5, 1670),
        (1513.5, 1770), (1571.312, 1880.688), (1608.312, 2103.688),
        (1493.309, 1948.682), (1475.648, 1436.916), (1776, 1624),
        (1776, 1624), (1765.5, 1665), (1765.5, 1665),
    ],
    [  # u
        (1758, 1808),
        (1926.406, 2292.33), (2082.052, 1976.423), (2048, 1549.5),
        (2042, 1676.5), (2082.333, 2054), (2157.333, 2048),
    ],
    [  # m
        (2156.667, 2048),
        (2283.417, 1337.836), (2624.245, 1497.032), (2419.333, 2089.333),
        (2553.867, 1610.798), (3005.302, 1397.068), (2670, 2162),
    ],
    [  # 右の A: 山
        (2697.938, 2172),
        (3485.697, 1068.427), (4084, 1140), (3456, 2740),
    ],
    [  # 右の A: 横棒
        (3148, 1831),
        (3368, 1950), (3543.073, 2101.995), (3639.812, 2197.125),
    ],
]

# --- 描画精度（PNG） ---
FLATTEN_STEPS = 256   # ベジェ 1 区間を折れ線にするときの分割数
ELLIPSE_VERTS = 360   # ブラシ楕円を多角形にするときの頂点数

COLORS = {"black": (0, 0, 0), "white": (255, 255, 255)}


# ============== PNG ==============

def flatten(stroke, steps=FLATTEN_STEPS):
    """ストローク（3 次ベジェの連結）を折れ線の点列 (N, 2) にする。"""
    t = np.linspace(0, 1, steps + 1)[:, None]
    pts = []
    for i in range(0, len(stroke) - 1, 3):
        p0, c1, c2, p1 = (np.array(p, dtype=float) for p in stroke[i:i + 4])
        seg = ((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * c1
               + 3 * (1 - t) * t ** 2 * c2 + t ** 3 * p1)
        pts.append(seg if i == 0 else seg[1:])
    return np.concatenate(pts)


def brush_outline(k, n=ELLIPSE_VERTS):
    """ブラシ楕円の輪郭（中心原点・k 倍に拡大）を、頂点列と各頂点の外向き法線で返す。"""
    t = np.linspace(0, 2 * math.pi, n, endpoint=False)
    # PIL の polygon は境界上の画素まで塗るため、輪郭が約 0.5px 太る。その分を引いておく。
    a = BRUSH_SIZE / 2 * k - 0.5
    b = BRUSH_SIZE / 2 / BRUSH_RATIO * k - 0.5
    th = math.radians(BRUSH_ANGLE)
    rot = np.array([[math.cos(th), -math.sin(th)],
                    [math.sin(th), math.cos(th)]])
    verts = np.stack([a * np.cos(t), b * np.sin(t)], axis=1) @ rot.T
    normals = np.stack([b * np.cos(t), a * np.sin(t)], axis=1) @ rot.T
    return verts, normals


def render_mask(size=CANVAS, ss=SS):
    """ロゴの形を size x size の 'L' 画像（0=外, 255=内）で返す。"""
    k = size / CANVAS * ss
    mask = Image.new("L", (size * ss, size * ss), 0)
    draw = ImageDraw.Draw(mask)
    verts, normals = brush_outline(k)
    for stroke in STROKES:
        pts = flatten(stroke) * k
        for p0, p1 in zip(pts[:-1], pts[1:]):
            # 2 つの楕円の凸包: 法線が進行方向を向く頂点は終点側、それ以外は
            # 始点側の楕円から取る。頂点の並び順はそのままで凸多角形になる。
            forward = (normals @ (p1 - p0)) > 0
            poly = verts + np.where(forward[:, None], p1, p0)
            draw.polygon([tuple(v) for v in poly], fill=255)
    # 縮小は BOX（面積平均）。LANCZOS だと輪郭の外側に薄いリンギングが出て、
    # 透明であるべき画素にわずかな alpha が残る。
    return mask.reduce(ss) if ss != 1 else mask


def render_png(color="black", bg=None, size=CANVAS, ss=SS):
    """ロゴを RGBA 画像で返す。bg=None なら背景は透明。"""
    img = Image.new("RGBA", (size, size), COLORS[color] + (0,))
    img.putalpha(render_mask(size, ss))
    if bg is not None:
        base = Image.new("RGBA", (size, size), COLORS[bg] + (255,))
        base.alpha_composite(img)
        img = base
    return img


# ============== SVG ==============

def _num(x):
    return f"{x:.3f}".rstrip("0").rstrip(".")


def build_svg(color="black", bg=None, size=CANVAS):
    """ロゴの SVG 文字列を返す。size は width/height 属性（viewBox は CANVAS 固定）。"""
    th = math.radians(BRUSH_ANGLE)
    c, s = math.cos(th), math.sin(th)

    def to_pen_space(p):
        # <g> の transform = rotate(角度) scale(1, 1/比) の逆変換。
        # この座標系では、ブラシは直径 BRUSH_SIZE の真円になる。
        x, y = p
        return (c * x + s * y, (-s * x + c * y) * BRUSH_RATIO)

    paths = []
    for stroke in STROKES:
        q = [" ".join(_num(v) for v in to_pen_space(p)) for p in stroke]
        paths.append(f'    <path d="M {q[0]} C {" ".join(q[1:])}"/>')

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}"'
        f' viewBox="0 0 {CANVAS} {CANVAS}">',
    ]
    if bg is not None:
        lines.append(f'  <rect width="{CANVAS}" height="{CANVAS}" fill="{bg}"/>')
    lines += [
        f'  <g transform="rotate({_num(BRUSH_ANGLE)}) scale(1 {1 / BRUSH_RATIO:.6f})"'
        f' fill="none" stroke="{color}" stroke-width="{_num(BRUSH_SIZE)}"'
        f' stroke-linecap="round" stroke-linejoin="round">',
        *paths,
        "  </g>",
        "</svg>",
    ]
    return "\n".join(lines) + "\n"


# ============== 保存 ==============

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--color", choices=list(COLORS), default="black")
    parser.add_argument("--bg", choices=list(COLORS), default=None,
                        help="背景色（省略時は透明）")
    parser.add_argument("--size", type=int, default=CANVAS,
                        help="出力の一辺(px)")
    args = parser.parse_args()

    stem = f"aruma_sign_{args.color}"
    if args.bg is not None:
        stem += f"_on_{args.bg}"

    img = render_png(args.color, args.bg, args.size)
    img.save(f"{stem}.png")
    print(f"画像を保存しました: {stem}.png ({img.width} x {img.height} px)")

    with open(f"{stem}.svg", "w") as f:
        f.write(build_svg(args.color, args.bg, args.size))
    print(f"画像を保存しました: {stem}.svg")


if __name__ == "__main__":
    main()
