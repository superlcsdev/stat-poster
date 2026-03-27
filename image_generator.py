"""
image_generator.py — stat-poster
Format : 1080x1080 square
Stat posts use a dark card as PRIMARY design (text IS the content).
Photo background used when available for visual variety.
Pipeline:
  1. HuggingFace SDXL-Lightning
  2. HuggingFace SD 1.5
  3. Local stock image (stock/stats/ folder — shared with finance/health photos)
  4. Dark card (30,30,30) ← primary fallback, always looks clean for stat posts
Branding: LAWRENCE SIA / YOUR PERSONAL COACH
Font    : Montserrat (fonts/ folder) → Liberation/DejaVu fallback
"""

import os
import time
import hashlib
import requests
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

IMAGE_WIDTH  = 1080
IMAGE_HEIGHT = 1080

HF_API_TOKEN      = os.getenv("HF_API_TOKEN", "")
HF_SDXL_LIGHTNING = "https://router.huggingface.co/hf-inference/models/ByteDance/SDXL-Lightning"
HF_SD15           = "https://router.huggingface.co/hf-inference/models/stable-diffusion-v1-5/stable-diffusion-v1-5"

_BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
STOCK_DIR  = os.path.join(_BASE_DIR, "stock", "stats")
_FONTS_DIR = os.path.join(_BASE_DIR, "fonts")

FONT_EXTRABOLD = [
    os.path.join(_FONTS_DIR, "Montserrat-ExtraBold.ttf"),
    os.path.join(_FONTS_DIR, "Montserrat-Bold.ttf"),
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_BOLD = [
    os.path.join(_FONTS_DIR, "Montserrat-Bold.ttf"),
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]
FONT_MEDIUM = [
    os.path.join(_FONTS_DIR, "Montserrat-Medium.ttf"),
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
]

# Topic-specific background prompts
TOPIC_PROMPTS = {
    "salary_networth": "professional at desk looking at financial documents, warm office, square, no text",
    "sgd_php":         "Singapore skyline golden hour, Marina Bay, aspirational, square, no text",
    "compounding":     "growing plant with coins, wealth growth concept, clean minimal, square, no text",
    "health_cost":     "stethoscope on clean white background, medical professional, square, no text",
    "income_streams":  "multiple streams flowing into one river, aerial nature, square, no text",
}

SAFE_PROMPT = "abstract dark blue gradient, professional minimal, square, no text, no words"


def _load_font(paths: list, size: int) -> ImageFont.FreeTypeFont:
    for path in paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def _wrap_text(draw, text: str, font, max_width: int) -> list:
    words, lines, current = text.split(), [], ""
    for word in words:
        test = f"{current} {word}".strip()
        if draw.textbbox((0, 0), test, font=font)[2] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def _hf_call(prompt: str, api_url: str) -> Image.Image | None:
    if not HF_API_TOKEN:
        return None
    w = (min(IMAGE_WIDTH,  1024) // 8) * 8
    h = (min(IMAGE_HEIGHT, 1024) // 8) * 8
    try:
        resp = requests.post(
            api_url,
            headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
            json={"inputs": prompt, "parameters": {
                "width": w, "height": h,
                "num_inference_steps": 4,
                "guidance_scale": 0,
            }},
            timeout=120,
        )
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content)).convert("RGB")
            return img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.LANCZOS)
        if resp.status_code == 503:
            print("  ⏳ HF model loading, waiting 20s...")
            time.sleep(20)
            resp2 = requests.post(api_url,
                headers={"Authorization": f"Bearer {HF_API_TOKEN}"},
                json={"inputs": prompt}, timeout=120)
            if resp2.status_code == 200:
                img = Image.open(BytesIO(resp2.content)).convert("RGB")
                return img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.LANCZOS)
        print(f"  ⚠️  HF HTTP {resp.status_code}: {resp.text[:100]}")
    except Exception as e:
        print(f"  ⚠️  HF error: {e}")
    return None


def _stock_image(topic: str) -> Image.Image | None:
    if not os.path.isdir(STOCK_DIR):
        return None
    files = sorted([f for f in os.listdir(STOCK_DIR)
                    if f.lower().endswith((".jpg", ".jpeg", ".png"))])
    if not files:
        return None
    seed      = datetime.now().strftime("%Y-%m-%d") + topic
    hash_seed = int(hashlib.md5(seed.encode()).hexdigest(), 16)
    chosen    = files[hash_seed % len(files)]
    try:
        img = Image.open(os.path.join(STOCK_DIR, chosen)).convert("RGB")
        img = img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.LANCZOS)
        print(f"  🖼️  Stock image: {chosen}")
        return img
    except Exception as e:
        print(f"  ⚠️  Stock image error: {e}")
    return None


def generate_background(topic: str) -> Image.Image | None:
    prompt = TOPIC_PROMPTS.get(topic, SAFE_PROMPT)
    prompt = f"{prompt}, high resolution, photorealistic, vibrant"

    print("  🤗 Trying HuggingFace SDXL-Lightning...")
    img = _hf_call(prompt, HF_SDXL_LIGHTNING)
    if img:
        print(f"  ✅ SDXL-Lightning ({img.size[0]}x{img.size[1]}px)")
        return img

    print("  🤗 Trying HuggingFace SD 1.5...")
    img = _hf_call(SAFE_PROMPT, HF_SD15)
    if img:
        print(f"  ✅ SD 1.5 ({img.size[0]}x{img.size[1]}px)")
        return img

    print("  ⚠️  HF failed — trying stock image...")
    img = _stock_image(topic)
    if img:
        return img

    print("  ❌ All providers failed — using dark card.")
    return None


def _draw_logo_bar(draw, w: int, y_top: int, bar_h: int = 56) -> None:
    draw.rectangle([(0, y_top), (w, y_top + bar_h)], fill=(12, 12, 16, 220))
    fb = _load_font(FONT_BOLD,   20)
    fs = _load_font(FONT_MEDIUM, 11)
    bt, st = "LAWRENCE SIA", "YOUR PERSONAL COACH"
    bb = draw.textbbox((0, 0), bt, font=fb)
    sb = draw.textbbox((0, 0), st, font=fs)
    draw.text(((w-(bb[2]-bb[0]))//2, y_top+7),  bt, font=fb, fill=(255, 255, 255))
    draw.text(((w-(sb[2]-sb[0]))//2, y_top+33), st, font=fs, fill=(155, 155, 155))
    draw.rectangle([(0, y_top), (w, y_top+2)], fill=(180, 120, 40))


def _extract_stat_line(caption: str) -> str:
    """Extract the first line of the caption to use as the image headline."""
    lines = [l.strip() for l in caption.split('\n') if l.strip()]
    if lines:
        stat = lines[0]
        return stat[:90] + "..." if len(stat) > 90 else stat
    return "The numbers don't lie."


def add_text_overlay(image: Image.Image, stat_line: str, tag: str = "STAT OF THE DAY") -> Image.Image:
    w, h       = image.size
    SIDE_PAD   = 50
    BOTTOM_PAD = 36
    LOGO_BAR_H = 56
    CAP_GAP    = 16

    font      = _load_font(FONT_EXTRABOLD, 52)
    temp_draw = ImageDraw.Draw(image)
    max_w     = w - SIDE_PAD * 2

    def pw(text, fnt, mx):
        words, lines, cur = text.split(), [], ""
        for word in words:
            test = f"{cur} {word}".strip()
            if temp_draw.textbbox((0, 0), test, font=fnt)[2] > mx and cur:
                lines.append(cur); cur = word
            else:
                cur = test
        if cur: lines.append(cur)
        return lines

    lines = pw(stat_line, font, max_w)
    if len(lines) > 2: font = _load_font(FONT_EXTRABOLD, 42); lines = pw(stat_line, font, max_w)
    if len(lines) > 3: font = _load_font(FONT_EXTRABOLD, 34); lines = pw(stat_line, font, max_w)

    line_h      = int(font.size * 1.28)
    total_cap_h = len(lines) * line_h
    cap_y_start = h - BOTTOM_PAD - total_cap_h
    logo_y_top  = cap_y_start - CAP_GAP - LOGO_BAR_H
    grad_h      = (h - logo_y_top) + 60

    rgba    = image.convert("RGBA")
    overlay = Image.new("RGBA", rgba.size, (0, 0, 0, 0))
    od      = ImageDraw.Draw(overlay)
    for i in range(grad_h):
        od.rectangle([(0, h-grad_h+i), (w, h-grad_h+i+1)],
                     fill=(0, 0, 0, int(240*i/grad_h)))
    image = Image.alpha_composite(rgba, overlay).convert("RGB")
    draw  = ImageDraw.Draw(image)

    # Teal tag badge for stats
    font_tag = _load_font(FONT_BOLD, 22)
    tag_text = f"  {tag}  "
    tb       = draw.textbbox((0, 0), tag_text, font=font_tag)
    tw, th   = tb[2]-tb[0]+20, tb[3]-tb[1]+14
    draw.rounded_rectangle([(SIDE_PAD, SIDE_PAD), (SIDE_PAD+tw, SIDE_PAD+th)],
                           radius=6, fill=(20, 140, 140, 230))
    draw.text((SIDE_PAD+10, SIDE_PAD+7), tag_text, font=font_tag, fill=(255, 255, 255))

    _draw_logo_bar(draw, w, logo_y_top, LOGO_BAR_H)

    y = cap_y_start
    for line in lines:
        draw.text((SIDE_PAD+2, y+2), line, font=font, fill=(0, 0, 0, 150))
        draw.text((SIDE_PAD,   y),   line, font=font, fill=(255, 255, 255))
        y += line_h
    return image


def _create_dark_card(stat_line: str, tag: str = "STAT OF THE DAY") -> Image.Image:
    """Dark charcoal card — clean and professional for stat posts."""
    img  = Image.new("RGB", (IMAGE_WIDTH, IMAGE_HEIGHT), (30, 30, 30))
    draw = ImageDraw.Draw(img)
    w, h = img.size
    PAD  = 60
    LBH  = 56

    font_tag = _load_font(FONT_BOLD, 22)
    tag_text = f"  {tag}  "
    tb = draw.textbbox((0, 0), tag_text, font=font_tag)
    tw, th = tb[2]-tb[0]+20, tb[3]-tb[1]+14
    draw.rounded_rectangle([(PAD, PAD), (PAD+tw, PAD+th)], radius=6, fill=(20, 140, 140, 230))
    draw.text((PAD+10, PAD+7), tag_text, font=font_tag, fill=(255, 255, 255))

    lyt = h - 30 - LBH
    _draw_logo_bar(draw, w, lyt, LBH)

    usable_top = PAD + th + 40
    usable_h   = (lyt - 20) - usable_top
    max_w      = w - PAD * 2
    font       = _load_font(FONT_EXTRABOLD, 64)
    lines      = _wrap_text(draw, stat_line, font, max_w)
    if len(lines) > 3: font = _load_font(FONT_EXTRABOLD, 52); lines = _wrap_text(draw, stat_line, font, max_w)
    if len(lines) > 4: font = _load_font(FONT_EXTRABOLD, 42); lines = _wrap_text(draw, stat_line, font, max_w)

    lh = int(font.size * 1.38)
    y  = usable_top + (usable_h - len(lines)*lh) // 2
    for line in lines:
        draw.text((PAD, y), line, font=font, fill=(255, 255, 255))
        y += lh
    return img


def create_stat_image(caption: str, output_path: str, topic: str = "salary_networth") -> str | None:
    stat_line = _extract_stat_line(caption)
    print(f'\n📸 Creating stat image: "{stat_line[:55]}..."')
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    bg    = generate_background(topic)
    final = add_text_overlay(bg, stat_line) if bg else _create_dark_card(stat_line)
    if bg is None:
        print("  ⚠️  Using dark card.")
    # Save — detect format from extension, fallback to explicit JPEG
    ext = os.path.splitext(output_path)[1].lower()
    fmt = "JPEG" if ext in (".jpg", ".jpeg") else "PNG"
    final.save(output_path, fmt, quality=92)
    print(f"  💾 Saved → {output_path}")
    return output_path


if __name__ == "__main__":
    os.makedirs("output_images", exist_ok=True)
    create_stat_image(
        caption     = "8 out of 10 high-earning professionals retire with less than 3 months of savings.\n\nA good salary feels like security. But without a plan, it's just a faster way to spend.",
        output_path = "output_images/test_stat.jpg",
        topic       = "salary_networth",
    )
