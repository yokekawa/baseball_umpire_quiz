"""Play Store 用の画像を生成・加工する。

入力:
- logo-1024.png : ロゴ素材
- phone.png, phone1.png ... phone4.png : スマホ縦スクショ (1080×2400)
- Tablet7-1.png ... Tablet7-5.png : 7インチ縦スクショ (1200×1920)
- Tablet10-1.png ... Tablet10-4.png : 10インチ縦スクショ (1600×2560)

出力 (screenshots/ サブフォルダ):
- アイコン 512×512、フィーチャーグラフィック 1024×500
- 各スクショ: ブラウザフレーム除去 + AdMob テスト広告除去 +
  Play Store の縦横比要件 (9:16〜16:9) に収まる横パディング
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

ROOT = Path(__file__).parent
SRC_LOGO = ROOT / "logo-1024.png"
OUT = ROOT / "screenshots"
OUT.mkdir(exist_ok=True)
FONT_PATH = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"

APP_BG = (26, 25, 24)  # アプリのダーク背景色

# -------------------------------------------------------------------------
# 1. アプリアイコン
# -------------------------------------------------------------------------
logo = Image.open(SRC_LOGO).convert("RGBA")
icon = logo.resize((512, 512), Image.LANCZOS)
icon.save(ROOT / "icon-512.png", "PNG")
print("Saved icon-512.png")

# -------------------------------------------------------------------------
# 2. フィーチャーグラフィック 1024×500
# -------------------------------------------------------------------------
W, H = 1024, 500
fg = Image.new("RGB", (W, H), (255, 255, 255))
draw = ImageDraw.Draw(fg)
top = (28, 76, 156)
bottom = (15, 50, 110)
for y in range(H):
    t = y / (H - 1)
    r = int(top[0] * (1 - t) + bottom[0] * t)
    g = int(top[1] * (1 - t) + bottom[1] * t)
    b = int(top[2] * (1 - t) + bottom[2] * t)
    draw.line([(0, y), (W, y)], fill=(r, g, b))

LOGO_SIZE = 380
logo_resized = logo.resize((LOGO_SIZE, LOGO_SIZE), Image.LANCZOS)
logo_x = 40
logo_y = (H - LOGO_SIZE) // 2
fg.paste(logo_resized, (logo_x, logo_y), logo_resized)

fg_rgba = fg.convert("RGBA")
txt_layer = Image.new("RGBA", fg_rgba.size, (0, 0, 0, 0))
tdraw = ImageDraw.Draw(txt_layer)
title_font = ImageFont.truetype(FONT_PATH, 70)
subtitle_font = ImageFont.truetype(FONT_PATH, 30)
text_x = logo_x + LOGO_SIZE + 30
tdraw.text((text_x, 110), "審判メカニクス", font=title_font, fill=(255, 255, 255, 255))
tdraw.text((text_x, 200), "クイズ", font=title_font, fill=(255, 220, 100, 255))
tdraw.line([(text_x, 305), (text_x + 360, 305)], fill=(255, 255, 255, 120), width=2)
tdraw.text((text_x, 325), "少年野球お父さん審判のための", font=subtitle_font, fill=(220, 235, 250, 255))
tdraw.text((text_x, 370), "メカニクス学習アプリ", font=subtitle_font, fill=(220, 235, 250, 255))
result = Image.alpha_composite(fg_rgba, txt_layer).convert("RGB")
result.save(ROOT / "feature-graphic-1024x500.png", "PNG")
print("Saved feature-graphic-1024x500.png")

# -------------------------------------------------------------------------
# 3. スクリーンショット加工
# -------------------------------------------------------------------------
# 各カテゴリの crop 範囲・広告位置（事前に色解析で確定した座標）
CONFIGS = {
    "phone": {
        # source 1080x2400, top white frame y=0..63, bottom white y=2337..
        "files": [("phone.png", False), ("phone1.png", True), ("phone2.png", True),
                  ("phone3.png", True), ("phone4.png", True)],
        "crop_top": 64,
        "crop_bot": 2337,   # exclusive
        "ad_top":  2106,    # 元画像座標
        "ad_bot":  2274,
        "min_w_for_aspect_h": 9 / 16,  # w/h >= 9/16
    },
    "tablet7": {
        # source 1200x1920, top y=0..71, bottom y=1856..
        "files": [("Tablet7-1.png", False), ("Tablet7-2.png", False), ("Tablet7-3.png", False),
                  ("Tablet7-4.png", False), ("Tablet7-5.png", False)],
        "crop_top": 72,
        "crop_bot": 1856,
        "ad_top": None,
        "ad_bot": None,
        "min_w_for_aspect_h": 9 / 16,
    },
    "tablet10": {
        # source 1600x2560, top y=0..71, bottom y=2496..
        "files": [("Tablet10-1.png", True), ("Tablet10-2.png", True),
                  ("Tablet10-3.png", True), ("Tablet10-4.png", True)],
        "crop_top": 72,
        "crop_bot": 2496,
        "ad_top": 2252,
        "ad_bot": 2432,
        "min_w_for_aspect_h": 9 / 16,
    },
}


def process(src_path: Path, dst_path: Path, cfg: dict, has_ad: bool):
    img = Image.open(src_path).convert("RGB")
    w, h = img.size
    # 1) 縦方向にブラウザフレームを切り落とし
    cropped = img.crop((0, cfg["crop_top"], w, cfg["crop_bot"]))
    cw, ch = cropped.size
    # 2) AdMob テスト広告を背景色で塗りつぶす
    if has_ad and cfg["ad_top"] is not None:
        ad_top_local = cfg["ad_top"] - cfg["crop_top"]
        ad_bot_local = cfg["ad_bot"] - cfg["crop_top"]
        d = ImageDraw.Draw(cropped)
        d.rectangle([0, ad_top_local, cw, ad_bot_local], fill=APP_BG)
    # 3) Play Store の縦横比 (w/h >= 9/16) を満たすように左右にダーク背景でパディング
    target_min_w = int(round(ch * cfg["min_w_for_aspect_h"]))
    if cw < target_min_w:
        new_w = target_min_w
        canvas = Image.new("RGB", (new_w, ch), APP_BG)
        canvas.paste(cropped, ((new_w - cw) // 2, 0))
        out = canvas
    else:
        out = cropped
    out.save(dst_path, "PNG", optimize=True)
    return out.size


print()
print("=== Screenshots ===")
for category, cfg in CONFIGS.items():
    for fname, has_ad in cfg["files"]:
        src = ROOT / fname
        if not src.exists():
            print(f"  skip: {fname} not found")
            continue
        dst = OUT / fname
        size = process(src, dst, cfg, has_ad)
        size_kb = dst.stat().st_size // 1024
        print(f"  {category:9s} {fname:20s} -> {size[0]}x{size[1]}  {size_kb:5d} KB")

print()
print("Done.")
