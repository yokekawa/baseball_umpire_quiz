"""Play Store 用の画像を logo-1024.png から生成する。"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "logo-1024.png"
FONT_PATH = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"

logo = Image.open(SRC).convert("RGBA")

# --- 1. アプリアイコン 512×512 ---
icon = logo.resize((512, 512), Image.LANCZOS)
icon.save(ROOT / "icon-512.png", "PNG")
print("Saved icon-512.png")

# --- 2. フィーチャーグラフィック 1024×500 ---
W, H = 1024, 500

# サンプリングして実際のロゴ色を抽出
sample = logo.resize((1, 1)).getpixel((0, 0))
print("Logo avg color:", sample)

# 背景：濃紺グラデーション（ロゴの青系に合わせる）
fg = Image.new("RGB", (W, H), (255, 255, 255))
draw = ImageDraw.Draw(fg)

# 縦方向のグラデーション
top = (28, 76, 156)     # 濃い青
bottom = (15, 50, 110)  # より暗い青
for y in range(H):
    t = y / (H - 1)
    r = int(top[0] * (1 - t) + bottom[0] * t)
    g = int(top[1] * (1 - t) + bottom[1] * t)
    b = int(top[2] * (1 - t) + bottom[2] * t)
    draw.line([(0, y), (W, y)], fill=(r, g, b))

# ロゴを左側に配置（380×380）
LOGO_SIZE = 380
logo_resized = logo.resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
logo_x = 40
logo_y = (H - LOGO_SIZE) // 2
fg.paste(logo_resized, (logo_x, logo_y), logo_resized)

# テキスト追加
fg_rgba = fg.convert("RGBA")
txt_layer = Image.new("RGBA", fg_rgba.size, (0, 0, 0, 0))
tdraw = ImageDraw.Draw(txt_layer)

title_font = ImageFont.truetype(FONT_PATH, 70)
subtitle_font = ImageFont.truetype(FONT_PATH, 30)

text_x = logo_x + LOGO_SIZE + 30
title1 = "審判メカニクス"
title2 = "クイズ"
subtitle1 = "少年野球お父さん審判のための"
subtitle2 = "メカニクス学習アプリ"

# 配置可能幅を確認しタイトルが収まるかチェック
avail_w = W - text_x - 20

# タイトル（2行）
tdraw.text((text_x, 110), title1, font=title_font, fill=(255, 255, 255, 255))
tdraw.text((text_x, 200), title2, font=title_font, fill=(255, 220, 100, 255))

# 区切り線
tdraw.line([(text_x, 305), (text_x + 360, 305)], fill=(255, 255, 255, 120), width=2)

# サブタイトル（2行）
tdraw.text((text_x, 325), subtitle1, font=subtitle_font, fill=(220, 235, 250, 255))
tdraw.text((text_x, 370), subtitle2, font=subtitle_font, fill=(220, 235, 250, 255))

result = Image.alpha_composite(fg_rgba, txt_layer).convert("RGB")
result.save(ROOT / "feature-graphic-1024x500.png", "PNG")
print("Saved feature-graphic-1024x500.png")

# --- 3. 念のため確認用：サイズを表示 ---
for f in ["icon-512.png", "feature-graphic-1024x500.png"]:
    p = ROOT / f
    im = Image.open(p)
    print(f"{f}: {im.size}, {p.stat().st_size:,} bytes")
