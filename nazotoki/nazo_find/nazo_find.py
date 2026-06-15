"""謎解きTシャツ「FIND」入稿用画像を生成するスクリプト。

方針: 答えである "Find" を隠さず、"Find the answer." をそのまま 1 行で出力する。
    謎としての加工（"Find" を中抜きの「D」＋虫眼鏡で見つける「F」に仕立てる、
    下線化する等）は、この画像を元にペイントツールで手動で行う。
    ※ 以前はスクリプト側で虫眼鏡演出や下線（"____ the answer."）まで自動生成
      していたが、手動加工に方針変更したため取りやめた。

フォント: Source Han Serif JP。
    ※ この環境には Adobe 版 "Source Han Serif" は未インストールだが、
      同一デザインソースの Google 版 "Noto Serif CJK JP" が入っている
      （両者は字形が一致する同じ書体）。よってこれを使用する。
"""

from PIL import Image, ImageDraw, ImageFont

# PIL の「圧縮爆弾」防御上限を解除。画像は自前生成（外部入力なし）で安全であり、
# SS を上げると一時画像が既定上限(約1.79億px)を超えて誤検知されるため。
Image.MAX_IMAGE_PIXELS = None

# ============== パラメータ ==============
# キャンバス（Tシャツ前面プリント向けにやや縦長）
CANVAS_W = 4000
CANVAS_H = 5200

# スーパーサンプリング倍率（内部を SS 倍で描画 → 最後に 1/SS へ高品質縮小）。
# 文字描画にまとめてアンチエイリアスをかける。2 で十分滑らか、3〜4 でより高品質
# （メモリ・処理時間は SS^2 で増える）。
SS = 4

# 色（黒デザイン）。背景は見やすさ優先で白（入稿時は透過に戻すなら (0,0,0,0)）
COLOR = (0, 0, 0, 255)
BG_COLOR = (255, 255, 255, 255)

# フォント（Source Han Serif JP = Noto Serif CJK JP, index 0）
FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"
FONT_INDEX = 0

# --- テキスト ---
TEXT = "Find the answer."
TEXT_FONT_SIZE = 440    # フォントサイズ
TEXT_CY_FRAC = 0.5      # テキスト縦中心位置（キャンバス高に対する割合）


# ============== ヘルパー ==============

def load_font(size):
    return ImageFont.truetype(FONT_PATH, size, index=FONT_INDEX)


def render_glyph(text, font, fill=None, stroke_width=0, stroke_fill=None):
    """文字（列）を透過レイヤに描き、alpha の bbox でタイトに切り抜いて返す。

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


# ===== スーパーサンプリング: px 系パラメータをまとめて SS 倍 =====
# 割合(_FRAC)・色はスケール不変なのでそのまま。
CANVAS_W *= SS
CANVAS_H *= SS
TEXT_FONT_SIZE *= SS

# ============== セットアップ ==============
img = Image.new("RGBA", (CANVAS_W, CANVAS_H), BG_COLOR)

# ============== "Find the answer." を中央に配置 ==============
font = load_font(TEXT_FONT_SIZE)
text_layer = render_glyph(TEXT, font, fill=COLOR)
TW, TH = text_layer.size
text_x = (CANVAS_W - TW) // 2
text_y = round(CANVAS_H * TEXT_CY_FRAC - TH / 2)
img.alpha_composite(text_layer, (text_x, text_y))

# ============== スーパーサンプリング解除（縮小でアンチエイリアス） ==============
if SS != 1:
    img = img.resize((CANVAS_W // SS, CANVAS_H // SS), Image.LANCZOS)

# ============== 保存 ==============
out = "nazo_find.png"
img.save(out)
print(f"画像を保存しました: {out} ({img.width} x {img.height} px)")
