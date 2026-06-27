"""謎解きTシャツ「question / 正答」入稿用画像を生成するスクリプト（ラフ v0）。

謎の核:
    英単語 "question" の **部分アナグラム** が "seitou"（= 正答）と読める。
    （question の文字 q,u,e,s,t,i,o,n から s,e,i,t,o,u を取り出して並べ替えると seitou）

このスクリプトの担当:
    その作品の鍵となる「？」マーク上部の **フック（カール）状の部分** を、
    **美しく（＝バランスよく）7 等分** して描く。

7 等分の考え方（重要）:
    ・フックは「centerline（ペン先が通る軌跡）に沿って太さ W を掃いたリボン」とみなす。
    ・「縦・横」で切るのではなく、**書く線に沿って切る** ＝ 各切れ目は centerline の
      接線に **直交** させる（リボンの“真横”を切る断面になる）。
    ・「バランスの取れた 7 等分」＝ centerline の **弧長を 7 等分**。各ピースはペンが
      進む長さが等しい。太さが一定なら 7 ピースは面積もほぼ等しく、最もバランスが良い。

    → centerline を弧長でパラメータ化し、k/7 (k=1..6) の位置で接線直交の切れ目を入れる。

フォントは使わず、フックを **パラメトリック曲線** で作る（弧長を厳密に扱え、等分が正確）。
"""

import math

import numpy as np
from PIL import Image, ImageDraw

# ============== パラメータ ==============
# キャンバス
CANVAS_W = 2600
CANVAS_H = 3000

# スーパーサンプリング（内部を SS 倍で描き、最後に 1/SS へ LANCZOS 縮小して AA）。
SS = 3

# 色
COLOR = (0, 0, 0, 255)
BG_COLOR = (255, 255, 255, 255)

# --- フック centerline（「？」の上のカール） ---
# centerline は「？」の上のフックを通る制御点を Catmull-Rom 補間して作る。
# ペン順（書き順）: 左上 → 頂点 → 右上 → 右 → 右下 → 底（中央へ寄る）→ 末端（中央で下向き）。
# 左下が開いた“フック（釣り針）”形で、末端は中央で下を向く（？のステム／ドットへ続く向き）。
HOOK_CX = 1300          # フックの基準 x（中央）
CONTROL_POINTS = [
    (HOOK_CX - 430,  560),   # 始点（左・やや上、ペン入り）
    (HOOK_CX - 320,  300),   # 左上
    (HOOK_CX +   0,  235),   # 頂点（中央上）
    (HOOK_CX + 340,  320),   # 右上
    (HOOK_CX + 470,  610),   # 右
    (HOOK_CX + 370,  900),   # 右下
    (HOOK_CX + 110, 1010),   # 底（中央へ寄る）
    (HOOK_CX +  10, 1180),   # 末端（中央で下向き）
]

# --- ストローク（リボン）の太さ ---
STROKE_W = 150          # 基本の太さ（px）
WIDTH_MOD = 0.0         # 太さの変調(0=一定が最もバランス良い／>0で中央を太く)

# --- 7 等分の切れ目 ---
N_DIV = 7               # 分割数
SLIT_W = 26             # 切れ目（隙間）の幅（px）
SLIT_MARGIN = 40        # 切れ目をリボン幅より長く伸ばす余白（確実に切るため）

# 検証用カラーパレット（7 ピースを色分けして等分を目視確認する debug 出力用）
PALETTE = [
    (228, 26, 28), (255, 127, 0), (255, 200, 0), (77, 175, 74),
    (52, 152, 219), (60, 60, 160), (152, 78, 163),
]


# ============== centerline（Catmull-Rom 補間） ==============
def catmull_rom(points, samples_per_seg=900):
    """制御点列を通るなめらかな曲線。端は端点を複製して自然に処理。"""
    P = [points[0]] + list(points) + [points[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = (np.array(P[j], float) for j in (i - 1, i, i + 1, i + 2))
        for k in range(samples_per_seg):
            t = k / samples_per_seg
            t2, t3 = t * t, t * t * t
            pt = 0.5 * ((2 * p1)
                        + (-p0 + p2) * t
                        + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                        + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
            out.append(pt)
    out.append(np.array(P[-2], float))
    return np.array(out)


def stroke_width(t):
    """t in [0,1] → 太さ。WIDTH_MOD=0 なら一定。"""
    return STROKE_W * (1.0 + WIDTH_MOD * np.sin(math.pi * np.asarray(t)))


# ============== 弧長サンプリング ==============
_pts = catmull_rom(CONTROL_POINTS)
xs = _pts[:, 0].copy()
ys = _pts[:, 1].copy()
M = len(xs)
ts = np.linspace(0.0, 1.0, M)
ws = stroke_width(ts)
# 累積弧長
seg = np.hypot(np.diff(xs), np.diff(ys))
s = np.concatenate([[0.0], np.cumsum(seg)])
L = s[-1]

# 7 等分の境界（弧長）と、各サンプルが属するピース番号
boundaries_s = [L * k / N_DIV for k in range(N_DIV + 1)]
piece_idx = np.clip((s / (L / N_DIV)).astype(int), 0, N_DIV - 1)


def point_and_tangent_at_s(target_s):
    """弧長 target_s の位置の (点, 単位接線)。"""
    i = int(np.searchsorted(s, target_s))
    i = max(1, min(i, M - 1))
    # 接線（中央差分）
    a = max(i - 1, 0)
    b = min(i + 1, M - 1)
    tx, ty = xs[b] - xs[a], ys[b] - ys[a]
    n = math.hypot(tx, ty) or 1.0
    return (float(xs[i]), float(ys[i])), (tx / n, ty / n)


# ============== 描画ヘルパー ==============
def stamp_stroke(draw, color_fn):
    """centerline に沿って円盤を連続スタンプし、可変幅リボンを描く。
    color_fn(i) で i 番目サンプルの色を返す（None ならスキップ）。"""
    for i in range(M):
        c = color_fn(i)
        if c is None:
            continue
        r = ws[i] / 2.0
        draw.ellipse([xs[i] - r, ys[i] - r, xs[i] + r, ys[i] + r], fill=c)


def draw_slits(draw, color):
    """6 本の切れ目を、各境界で接線に直交する向きに入れる。"""
    for k in range(1, N_DIV):
        (px, py), (tx, ty) = point_and_tangent_at_s(boundaries_s[k])
        nx, ny = -ty, tx  # 法線（接線に直交）
        # その地点のリボン幅
        ti = int(np.searchsorted(s, boundaries_s[k]))
        w_local = ws[min(ti, M - 1)]
        half = w_local / 2.0 + SLIT_MARGIN
        hw = SLIT_W / 2.0
        # 切れ目＝法線方向に長く、接線方向に SLIT_W 幅の長方形
        corners = [
            (px + nx * half - tx * hw, py + ny * half - ty * hw),
            (px + nx * half + tx * hw, py + ny * half + ty * hw),
            (px - nx * half + tx * hw, py - ny * half + ty * hw),
            (px - nx * half - tx * hw, py - ny * half - ty * hw),
        ]
        draw.polygon(corners, fill=color)


# ============== スーパーサンプリング: px 系を SS 倍 ==============
def scale_all(factor):
    global CANVAS_W, CANVAS_H, STROKE_W, SLIT_W, SLIT_MARGIN
    global xs, ys, ws, s, L, boundaries_s
    CANVAS_W *= factor
    CANVAS_H *= factor
    STROKE_W *= factor
    SLIT_W *= factor
    SLIT_MARGIN *= factor
    xs = xs * factor
    ys = ys * factor
    ws = ws * factor
    s = s * factor
    L = L * factor
    boundaries_s = [b * factor for b in boundaries_s]


scale_all(SS)


# ============== 出力 1: 本番（黒・切れ目で 7 分割） ==============
def render_main():
    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    stamp_stroke(draw, lambda i: COLOR)        # まず黒でリボンを塗る
    draw_slits(draw, BG_COLOR)                  # 背景色で 6 本の切れ目を入れる
    if SS != 1:
        img = img.resize((CANVAS_W // SS, CANVAS_H // SS), Image.LANCZOS)
    img.save("nazo_question.png")
    print(f"保存: nazo_question.png ({img.width}x{img.height}), 全弧長 L={L/SS:.1f}px, "
          f"1ピース={L/SS/N_DIV:.1f}px")


# ============== 出力 2: 検証（7 ピースを色分け） ==============
def render_debug():
    img = Image.new("RGBA", (CANVAS_W, CANVAS_H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    stamp_stroke(draw, lambda i: PALETTE[piece_idx[i]] + (255,))
    draw_slits(draw, BG_COLOR)
    if SS != 1:
        img = img.resize((CANVAS_W // SS, CANVAS_H // SS), Image.LANCZOS)
    img.save("nazo_question_debug.png")
    print(f"保存: nazo_question_debug.png ({img.width}x{img.height})")


if __name__ == "__main__":
    render_main()
    render_debug()
