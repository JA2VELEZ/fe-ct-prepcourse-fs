"""Directo USA Store - promo video "Llegaron sus encargos" (1080x1920, 30fps). Brand v2: octagon crosshair, #F26B1D, Oswald."""
import math, subprocess, sys, wave, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
UP = "/root/.claude/uploads/8119d2c8-4316-5490-ba27-260211af296a/"
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out.mp4")
W, H, FPS = 1080, 1920, 30
OR, BLACK, WHITE, GRAY = (242, 107, 29), (11, 11, 11), (255, 255, 255), (163, 163, 163)
OR_DARK = (214, 88, 16)

OSWALD = os.path.join(HERE, "fonts/Oswald.ttf")
DEJAVU = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def oswald(s, w="Bold"):
    f = ImageFont.truetype(OSWALD, s)
    try: f.set_variation_by_name(w)
    except Exception: pass
    return f
bold = lambda s: oswald(s, "Bold")

# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_back(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def prog(t, a, d): return clamp((t - a) / d)

# ---------- text helpers ----------
def text_img(txt, font, fill=WHITE, stroke=0, stroke_fill=(0, 0, 0), shadow=True, spacing=0):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    widths = [d.textlength(c, font=font) for c in txt]
    tw = int(sum(widths) + spacing * (len(txt) - 1)) if spacing else int(d.textlength(txt, font=font))
    asc, desc = font.getmetrics()
    pad = 40
    im = Image.new("RGBA", (tw + pad * 2 + stroke * 2, asc + desc + pad * 2), (0, 0, 0, 0))
    def draw(drw, col, sw, sf):
        if spacing:
            x = pad
            for c, w in zip(txt, widths):
                drw.text((x, pad), c, font=font, fill=col, stroke_width=sw, stroke_fill=sf); x += w + spacing
        else:
            drw.text((pad, pad), txt, font=font, fill=col, stroke_width=sw, stroke_fill=sf)
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        draw(ImageDraw.Draw(sh), (0, 0, 0, 210), stroke, (0, 0, 0, 210))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(10)))
    draw(ImageDraw.Draw(im), fill + (255,), stroke, stroke_fill)
    return im

def tight(im):
    return im.crop(im.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox())

def shear(im, k=0.22):
    w = im.width + int(im.height * k)
    return im.transform((w, im.height), Image.AFFINE, (1, k, -im.height * k, 0, 1, 0), Image.BICUBIC)

def with_alpha(im, a):
    if a >= 0.999: return im
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a))); return im

def paste(base, im, cx, cy, alpha=1.0, scale=1.0, anchor="c", rot=0):
    if alpha <= 0.01 or scale <= 0.01: return
    if abs(scale - 1) > 0.001:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if rot: im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    im = with_alpha(im, alpha)
    x = int(cx - im.width / 2) if anchor == "c" else int(cx)
    y = int(cy - im.height / 2)
    if 0 <= x and 0 <= y and x + im.width <= W and y + im.height <= H:
        base.alpha_composite(im, (x, y))
    else:
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0)); layer.paste(im, (x, y), im); base.alpha_composite(layer)

def pill(w, h, color, r=None):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), r if r is not None else h // 2, fill=color + (255,))
    return im

# ---------- brand icon: octagon crosshair ----------
def brand_icon(size, col=OR, ss=4):
    S = size * ss; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = S / 2
    R, sw = S * 0.34, S * 0.075
    pts = [(c + R * math.cos(math.radians(22.5 + 45 * i)), c + R * math.sin(math.radians(22.5 + 45 * i))) for i in range(8)]
    d.polygon(pts, outline=col + (255,), width=int(sw))
    for p in pts:  # round off joints
        d.ellipse((p[0] - sw / 2.6, p[1] - sw / 2.6, p[0] + sw / 2.6, p[1] + sw / 2.6), fill=col + (255,))
    r = S * 0.155; d.ellipse((c - r, c - r, c + r, c + r), outline=col + (255,), width=int(S * 0.055))
    a, pw = S * 0.065, int(S * 0.035)
    d.line((c - a, c, c + a, c), fill=col + (255,), width=pw); d.line((c, c - a, c, c + a), fill=col + (255,), width=pw)
    t0, t1, tw = S * 0.22, S * 0.5, S * 0.06
    for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
        if dx: d.rectangle((c + dx * t0 if dx > 0 else c - t1, c - tw / 2, c + t1 if dx > 0 else c - t0, c + tw / 2), fill=col + (255,))
        else: d.rectangle((c - tw / 2, c + t0 if dy > 0 else c - t1, c + tw / 2, c + t1 if dy > 0 else c - t0), fill=col + (255,))
    return im.resize((size, size), Image.LANCZOS)

def logo_h(h, word_col=WHITE, usa_col=OR, store_col=GRAY, icon_col=OR, tagline=False):
    """Horizontal logo: icon + DIRECTO USA / S T O R E. h = cap height of main text."""
    fs = int(h * 1.32)
    a = tight(text_img("DIRECTO", bold(fs), word_col, shadow=False))
    b = tight(text_img("USA", bold(fs), usa_col, shadow=False))
    gap = int(h * 0.45)
    st = tight(text_img("STORE", oswald(int(h * 0.42), "Regular"), store_col, shadow=False, spacing=int(h * 0.30)))
    tg = tight(text_img("TACTICAL PERSONAL SHOPPER", oswald(int(h * 0.17), "Medium"), GRAY, shadow=False, spacing=int(h * 0.09))) if tagline else None
    th = a.height + int(h * 0.22) + st.height + (int(h * 0.14) + tg.height if tg else 0)
    ic = brand_icon(int(th * 1.12), icon_col)
    tw = a.width + gap + b.width
    im = Image.new("RGBA", (ic.width + int(h * 0.3) + tw, max(ic.height, th)), (0, 0, 0, 0))
    im.alpha_composite(ic, (0, (im.height - ic.height) // 2))
    x0, y0 = ic.width + int(h * 0.3), (im.height - th) // 2
    im.alpha_composite(a, (x0, y0)); im.alpha_composite(b, (x0 + a.width + gap, y0))
    y = y0 + a.height + int(h * 0.22); im.alpha_composite(st, (x0 + 4, y))
    if tg: im.alpha_composite(tg, (x0 + 4, y + st.height + int(h * 0.14)))
    return im

def logo_v_parts(h):
    fs = int(h * 1.32)
    a = tight(text_img("DIRECTO", bold(fs), WHITE, shadow=False)); b = tight(text_img("USA", bold(fs), OR, shadow=False))
    gap = int(h * 0.45)
    word = Image.new("RGBA", (a.width + gap + b.width, a.height)); word.alpha_composite(a); word.alpha_composite(b, (a.width + gap, 0))
    st = tight(text_img("STORE", oswald(int(h * 0.36), "Regular"), WHITE, shadow=False, spacing=int(h * 0.34)))
    tg = tight(text_img("TACTICAL PERSONAL SHOPPER", oswald(int(h * 0.15), "Medium"), GRAY, shadow=False, spacing=int(h * 0.11)))
    return word, st, tg

def logo_v(h, icon=True):
    word, st, tg = logo_v_parts(h)
    ic = brand_icon(int(h * 2.0)) if icon else None
    w = max(word.width, tg.width)
    lh = int(h * 0.05) + 2
    hh = (ic.height + int(h * 0.15) if ic else 0) + word.height + int(h * 0.3) + st.height + int(h * 0.25) + tg.height
    im = Image.new("RGBA", (w, hh), (0, 0, 0, 0)); d = ImageDraw.Draw(im); y = 0
    if ic: im.alpha_composite(ic, ((w - ic.width) // 2, 0)); y = ic.height + int(h * 0.15)
    im.alpha_composite(word, ((w - word.width) // 2, y)); y += word.height + int(h * 0.3)
    sx = (w - st.width) // 2; im.alpha_composite(st, (sx, y))
    my = y + st.height // 2
    d.rectangle(((w - word.width) // 2, my - lh // 2, sx - int(h * 0.25), my + lh // 2), fill=OR + (255,))
    d.rectangle((sx + st.width + int(h * 0.25), my - lh // 2, (w + word.width) // 2, my + lh // 2), fill=OR + (255,))
    y += st.height + int(h * 0.25); im.alpha_composite(tg, ((w - tg.width) // 2, y))
    return im

# ---------- small icons ----------
def wa_icon(d, col=BLACK, bg=None):
    S = d * 4; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    if bg: dr.ellipse((0, 0, S - 1, S - 1), fill=bg + (255,))
    m = S * (0.2 if bg else 0.08); w = int(S * 0.08)
    dr.ellipse((m, m, S - m, S - m), outline=col + (255,), width=w)
    dr.polygon([(m + S * 0.06, S - m - S * 0.16), (m - S * 0.04, S - m + S * 0.02), (m + S * 0.2, S - m - S * 0.06)], fill=col + (255,))
    hs = Image.new("RGBA", (S, S), (0, 0, 0, 0)); hd = ImageDraw.Draw(hs)
    hd.rounded_rectangle((S * 0.41, S * 0.31, S * 0.59, S * 0.69), S * 0.07, fill=col + (255,))
    hd.rectangle((S * 0.47, S * 0.40, S * 0.60, S * 0.60), fill=(0, 0, 0, 0))
    im.alpha_composite(hs.rotate(-35, center=(S / 2, S / 2)))
    return im.resize((d, d), Image.LANCZOS)

def ig_icon(d, col=OR):
    S = d * 4; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); dr = ImageDraw.Draw(im); w = int(S * 0.09)
    dr.rounded_rectangle((w, w, S - w, S - w), S // 4, outline=col + (255,), width=w)
    dr.ellipse((S * .3, S * .3, S * .7, S * .7), outline=col + (255,), width=w)
    dr.ellipse((S * .7, S * .2, S * .8, S * .3), fill=col + (255,))
    return im.resize((d, d), Image.LANCZOS)

def fb_icon(d, col=OR):
    im = Image.new("RGBA", (d, d), (0, 0, 0, 0)); ImageDraw.Draw(im).ellipse((2, 2, d - 3, d - 3), fill=col + (255,))
    f = tight(text_img("f", bold(int(d * 0.9)), BLACK, shadow=False))
    im.alpha_composite(f, ((d - f.width) // 2 + 2, d - f.height)); return im

def tt_icon(d, col=OR):
    n = tight(text_img("♪", ImageFont.truetype(DEJAVU, int(d * 1.1)), col, shadow=False))
    n = n.resize((int(n.width * d / n.height), d), Image.LANCZOS)
    im = Image.new("RGBA", (d, d), (0, 0, 0, 0)); im.alpha_composite(n, ((d - n.width) // 2, 0)); return im

# ---------- photos ----------
def load_cover(name, extra=1.18):
    im = Image.open(UP + name).convert("RGB")
    s = max(W * extra / im.width, H * extra / im.height)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)

def cover_frame(img):
    cw = img.width; ch = cw * H / W
    if ch > img.height: ch = img.height; cw = ch * W / H
    box = ((img.width - cw) / 2, (img.height - ch) / 2, (img.width + cw) / 2, (img.height + ch) / 2)
    return img.resize((W, H), Image.BILINEAR, box=box).convert("RGBA")

def vgrad(top_a, bot_a, y0, y1):
    ys = np.arange(H); k = np.clip((ys - y0) / max(1, (y1 - y0)), 0, 1)
    a = np.where((ys >= y0) & (ys <= y1), top_a + (bot_a - top_a) * k, 0).astype(np.uint8)
    im = Image.new("RGBA", (W, H), BLACK + (0,)); im.putalpha(Image.fromarray(np.repeat(a[:, None], W, 1))); return im

GRAD_BOT = vgrad(0, 240, 1300, 1920)
GRAD_TOP = vgrad(210, 0, 0, 330)

# ---------- chrome (photo scenes) ----------
LOGO_SMALL = logo_h(58)
WA_TXT = tight(text_img("WHATSAPP  316-439-5101", bold(62), BLACK, shadow=False))
WA_BAND_ICON = wa_icon(72, BLACK)

def brand_chrome(f, total_t):
    f.alpha_composite(GRAD_TOP)
    f.alpha_composite(LOGO_SMALL, (44, 34))
    band = Image.new("RGBA", (W, 130), OR + (255,)); bd = ImageDraw.Draw(band)
    off = int(total_t * 60) % 60
    for x in range(-200, W + 200, 60):
        bd.polygon([(x + off, 0), (x + off + 22, 0), (x + off - 28, 130), (x + off - 50, 130)], fill=OR_DARK + (255,))
    f.alpha_composite(band, (0, H - 130))
    pulse = 1 + 0.05 * math.sin(total_t * 2 * math.pi * 2)
    paste(f, WA_BAND_ICON, 105, H - 65, scale=pulse)
    f.alpha_composite(WA_TXT, (165, H - 65 - WA_TXT.height // 2))

# ---------- captions ----------
class Caption:
    def __init__(self, tag, title, sub, title_size=150):
        self.tag = tag and tight(text_img(tag, bold(42), BLACK, shadow=False))
        self.title = text_img(title, bold(title_size), WHITE)
        self.sub = text_img(sub, oswald(56, "Medium"), (225, 225, 225))

    def draw(self, f, t, dur):
        out = 1 - prog(t, dur - 0.25, 0.25); x0 = 70
        if self.tag:
            p = ease_back(prog(t, 0.05, 0.4))
            b = pill(self.tag.width + 50, 70, OR, 8); b.alpha_composite(self.tag, (25, (70 - self.tag.height) // 2))
            paste(f, b, x0 - 10, 1405, alpha=clamp(p) * out, scale=max(0.01, p), anchor="l", rot=3)
        pb = ease_out(prog(t, 0.1, 0.4))
        ImageDraw.Draw(f).rectangle((x0, 1480, x0 + 14, 1480 + int(200 * pb * out)), fill=OR + (255,))
        pt = ease_out(prog(t, 0.15, 0.45))
        paste(f, self.title, x0 + int((1 - pt) * -500), 1565, alpha=pt * out, anchor="l")
        ps = ease_out(prog(t, 0.35, 0.45))
        paste(f, self.sub, x0, 1700 + int((1 - ps) * 40), alpha=ps * out, anchor="l")

# ---------- intro ----------
def dark_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt((xx - W / 2) ** 2 + ((yy - H * 0.42) * 0.8) ** 2) / (H * 0.7)
    v = np.clip(30 - 26 * r, 8, 34)
    grid = (((xx % 90) < 2) | ((yy % 90) < 2)) * 5
    arr = np.stack([v + grid, v + grid, v + grid], -1).astype(np.uint8)
    return Image.fromarray(arr).convert("RGBA")
DARK = dark_bg()

ICON_BIG = brand_icon(380)
ICON_GHOST = brand_icon(1100, (40, 22, 12))
V_WORD, V_STORE, V_TAG = logo_v_parts(120)
TAG1 = shear(text_img("Lo que necesitas...", oswald(76, "Medium"), WHITE))
TAG2 = shear(text_img("desde USA", bold(110), OR))
def brush(w, h):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.polygon([(0, h * 0.7), (w, 0), (w * 0.97, h * 0.45), (w * 0.05, h)], fill=OR + (255,)); return im
BRUSH = brush(520, 26)

def intro(t):
    f = DARK.copy()
    paste(f, ICON_GHOST, W / 2, 900, alpha=0.9 * ease_out(prog(t, 0, 1.0)), rot=t * 8)
    p = ease_back(prog(t, 0.0, 0.7))
    paste(f, ICON_BIG, W / 2, 560, alpha=clamp(p), scale=max(0.01, p), rot=(1 - ease_out(prog(t, 0, 0.8))) * 90)
    pw = ease_out(prog(t, 0.45, 0.5))
    paste(f, V_WORD, W / 2, 900 + (1 - pw) * 80, alpha=pw)
    ps = ease_out(prog(t, 0.8, 0.5))
    paste(f, V_STORE, W / 2, 1055, alpha=ps)
    d = ImageDraw.Draw(f); half = V_WORD.width / 2; gap = V_STORE.width / 2 + 30
    ln = (half - gap) * ps
    d.rectangle((W / 2 - gap - ln, 1052, W / 2 - gap, 1058), fill=OR + (255,))
    d.rectangle((W / 2 + gap, 1052, W / 2 + gap + ln, 1058), fill=OR + (255,))
    paste(f, V_TAG, W / 2, 1150, alpha=ease_out(prog(t, 1.1, 0.5)))
    p1 = ease_out(prog(t, 1.6, 0.5)); p2 = ease_back(prog(t, 1.9, 0.5))
    paste(f, TAG1, W / 2 - 60 - (1 - p1) * 300, 1380, alpha=p1)
    paste(f, TAG2, W / 2 + 60, 1490, alpha=clamp(p2), scale=max(0.01, p2))
    pb = ease_out(prog(t, 2.2, 0.4))
    if pb > 0: paste(f, BRUSH.crop((0, 0, max(1, int(BRUSH.width * pb)), BRUSH.height)), W / 2 + 60 - BRUSH.width / 2, 1580, anchor="l")
    return f

# ---------- scenes ----------
photos = {k: load_cover(v) for k, v in {
    "box": "7ff0e587-image.webp", "hugo1": "4203620d-image.webp", "hugo2": "ed6c980c-image.webp",
    "hugo3": "51b38966-image.webp", "karl": "cceb0f43-image.webp", "adi1": "9b6dc497-image.webp",
    "adi2": "e0d4271a-image.webp", "lattafa": "06bf798c-image.webp", "nike1": "52937938-image.webp",
    "nike2": "8f770ddd-image.webp", "nike3": "eb698309-image.webp", "nike4": "852adee0-image.webp",
    "dkny1": "adacd9b2-image.webp", "dkny3": "94d0617b-image.webp",
    "mk": "cc44f2ac-image.webp", "karl2": "f5ea090a-image.webp", "orig1": "cc25459f-image.webp",
    "orig2": "d2a62970-image.webp", "guess1": "ea5d39e3-image.webp", "guess2": "281344d6-image.webp",
    "guess3": "d5e22b78-image.webp", "guess4": "f8265b40-image.webp", "poster": "be91cd22-image.jpg",
}.items()}

_cards = {}
def card_assets(key, box, border):
    if key in _cards: return _cards[key]
    src = photos[key]
    bg = cover_frame(src).filter(ImageFilter.GaussianBlur(40))
    bg.alpha_composite(Image.new("RGBA", (W, H), BLACK + (140,)))
    sc = min(box[0] / src.width, box[1] / src.height)
    cw, ch = int(src.width * sc), int(src.height * sc)
    ph = src.resize((cw, ch), Image.LANCZOS).convert("RGBA")
    b, pad = border, 40
    card = Image.new("RGBA", (cw + 2 * (b + pad), ch + 2 * (b + pad)), (0, 0, 0, 0))
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 12, pad + cw + 2 * b, pad + ch + 2 * b + 12), 30, fill=(0, 0, 0, 210))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    ImageDraw.Draw(card).rounded_rectangle((pad, pad, pad + cw + 2 * b, pad + ch + 2 * b), 30, fill=OR + (255,))
    m = Image.new("L", (cw, ch), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, cw - 1, ch - 1), 24, fill=255)
    card.paste(ph, (pad + b, pad + b), m)
    _cards[key] = (bg, card)
    return _cards[key]

def photo_scene(key, z0, z1, darken=0, box=(960, 1250), cy=860, border=6):
    def fn(t, dur):
        bg, card = card_assets(key, box, border)
        f = bg.copy(); p = t / dur
        z = 0.96 + 0.06 * (p if z1 > z0 else 1 - p)
        paste(f, card, W / 2, cy, scale=z)
        if darken: f.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * darken))))
        return f
    return fn

BASE = [
    (4.0, lambda t, d: intro(t)),
    (3.0, photo_scene("box", 1.0, 1.15, darken=0.5)),
    (2.0, photo_scene("hugo1", 1.0, 1.12)),          # 2 HUGO
    (2.0, photo_scene("hugo2", 1.12, 1.0)),
    (2.0, photo_scene("hugo3", 1.0, 1.1)),
    (2.0, photo_scene("karl", 1.0, 1.1)),            # 5 KARL
    (2.0, photo_scene("karl2", 1.1, 1.0)),
    (2.0, photo_scene("mk", 1.0, 1.1)),              # 7 MICHAEL KORS
    (2.0, photo_scene("orig1", 1.1, 1.0)),           # 8 ADIDAS ORIGINALS
    (2.0, photo_scene("orig2", 1.0, 1.1)),
    (2.0, photo_scene("adi1", 1.0, 1.12)),           # 10 GALAXY
    (2.0, photo_scene("adi2", 1.12, 1.0)),
    (2.0, photo_scene("nike1", 1.0, 1.1)),           # 12 NIKE
    (2.0, photo_scene("nike2", 1.1, 1.0)),
    (2.0, photo_scene("nike3", 1.0, 1.12)),
    (2.0, photo_scene("nike4", 1.12, 1.0)),
    (2.0, photo_scene("guess1", 1.0, 1.1)),          # 16 GUESS
    (2.0, photo_scene("guess2", 1.1, 1.0)),
    (2.0, photo_scene("guess3", 1.0, 1.1)),
    (2.0, photo_scene("guess4", 1.1, 1.0)),
    (2.0, photo_scene("dkny1", 1.0, 1.12)),          # 20 DKNY
    (2.0, photo_scene("dkny3", 1.0, 1.1)),
    (3.0, photo_scene("lattafa", 1.0, 1.12)),        # 22 LATTAFA
    (3.5, photo_scene("poster", 1.0, 1.1, box=(1000, 1700), cy=960, border=0)),  # 23 POSTER
    (6.0, None),                                     # 24 OUTRO
]
starts = np.cumsum([0] + [d for d, _ in BASE]).tolist()
TOTAL = starts[-1]
XF = 0.3
def at(i): return starts[i]
CHROME_END = at(23)

CAPS = [
    (at(2), at(5), Caption("YA LLEGÓ", "HUGO BOSS", "Camisetas de marca")),
    (at(5), at(7), Caption("YA LLEGÓ", "KARL LAGERFELD", "Camisetas Paris", 128)),
    (at(7), at(8), Caption("YA LLEGÓ", "MICHAEL KORS", "Camisetas de marca", 140)),
    (at(8), at(10), Caption("YA LLEGÓ", "ADIDAS ORIGINALS", "Camisetas y tops", 120)),
    (at(10), at(12), Caption("YA LLEGÓ", "ADIDAS GALAXY 7", "Running  ·  Cloudfoam", 134)),
    (at(12), at(16), Caption("YA LLEGÓ", "NIKE AIR MAX 90", "Clásico de siempre", 134)),
    (at(16), at(20), Caption("YA LLEGÓ", "GUESS", "Sneakers con logo dorado")),
    (at(20), at(22), Caption("YA LLEGÓ", "DKNY", "Sneakers slip-on")),
    (at(22), at(23), Caption("YA LLEGÓ", "LATTAFA", "Qaed Al Fursan  ·  90 ml")),
]

H1 = text_img("¡LLEGARON", bold(190), WHITE)
H2 = text_img("SUS ENCARGOS!", bold(160), OR)
H3 = tight(text_img("Mercancía nueva directo desde USA", oswald(54, "Medium"), BLACK, shadow=False))
H_ICON = brand_icon(200)
def headline(f, t):
    paste(f, H_ICON, W / 2, 560, alpha=0.95 * ease_out(prog(t, 0, 0.4)), scale=max(0.01, ease_back(prog(t, 0, 0.5))), rot=t * 20)
    p1 = ease_back(prog(t, 0.1, 0.45)); p2 = ease_back(prog(t, 0.35, 0.45))
    shake = math.sin(t * 60) * 6 * (1 - prog(t, 0.3, 0.4)) if t > 0.1 else 0
    paste(f, H1, W / 2 + shake, 820, alpha=clamp(p1), scale=max(0.01, 1.6 - 0.6 * p1))
    paste(f, H2, W / 2 - shake, 1000, alpha=clamp(p2), scale=max(0.01, 1.6 - 0.6 * p2))
    p3 = ease_out(prog(t, 0.8, 0.5))
    bar = pill(H3.width + 60, 96, OR, 10); bar.alpha_composite(H3, (30, (96 - H3.height) // 2))
    paste(f, bar, W / 2, 1170 + (1 - p3) * 40, alpha=p3)

# ---------- outro ----------
OUT_BG = cover_frame(photos["guess2"]).filter(ImageFilter.GaussianBlur(30))
OUT_BG.alpha_composite(Image.new("RGBA", (W, H), BLACK + (220,)))
O1 = text_img("¿YA RECLAMASTE", bold(130), WHITE)
O2 = text_img("TU PEDIDO?", bold(180), OR)
O3 = text_img("Escríbenos y coordinamos tu entrega", oswald(50, "Regular"), (235, 235, 235))
O_NUM = tight(text_img("316-439-5101", bold(124), BLACK, shadow=False))
O_WA = tight(text_img("ESCRÍBENOS POR WHATSAPP", oswald(36, "SemiBold"), BLACK, shadow=False, spacing=3))
O_CTA = shear(text_img("¡Cotiza con nosotros!", bold(84), WHITE))
O_LOGO = logo_v(84)
O_CATS = tight(text_img("ROPA · CALZADO · TÁCTICO · OUTDOOR · DEPORTIVO · TECNOLOGÍA", oswald(30, "Medium"), GRAY, shadow=False, spacing=2))
_s = tight(text_img("@directo_usastore", oswald(52, "Medium"), WHITE, shadow=False))
O_SOC = Image.new("RGBA", (3 * 70 + 40 + _s.width, 64), (0, 0, 0, 0))
for i, ic in enumerate([ig_icon(56), fb_icon(56), tt_icon(56)]): O_SOC.alpha_composite(ic, (i * 70, 4))
O_SOC.alpha_composite(_s, (3 * 70 + 30, (64 - _s.height) // 2))
O_FAV = tight(text_img("TU PRODUCTO FAVORITO DESDE ESTADOS UNIDOS", oswald(30, "Medium"), WHITE, shadow=False, spacing=4))

def outro(t):
    f = OUT_BG.copy()
    paste(f, ICON_GHOST, W / 2, 1000, alpha=0.8, rot=t * 10)
    p = ease_out(prog(t, 0.1, 0.5)); paste(f, O1, W / 2, 230 - (1 - p) * 60, alpha=p)
    p = ease_back(prog(t, 0.3, 0.5)); paste(f, O2, W / 2, 390, alpha=clamp(p), scale=max(0.01, p))
    paste(f, O3, W / 2, 530, alpha=ease_out(prog(t, 0.6, 0.4)))
    p = ease_back(prog(t, 0.9, 0.5))
    pulse = 1 + 0.03 * math.sin(t * 2 * math.pi * 2) * prog(t, 1.4, 0.2)
    card = pill(920, 280, OR, 36)
    card.alpha_composite(wa_icon(150, BLACK), (45, 65))
    card.alpha_composite(O_WA, (225, 50)); card.alpha_composite(O_NUM, (222, 108))
    paste(f, card, W / 2, 740, alpha=clamp(p), scale=max(0.01, p * pulse))
    p = ease_out(prog(t, 1.4, 0.5)); paste(f, O_CTA, W / 2, 950 + (1 - p) * 40, alpha=p)
    if p > 0: paste(f, BRUSH, W / 2 + 20, 1020, alpha=p)
    p = ease_out(prog(t, 1.8, 0.6)); paste(f, O_LOGO, W / 2, 1300, alpha=p, scale=0.9 + 0.1 * p)
    paste(f, O_CATS, W / 2, 1560, alpha=ease_out(prog(t, 2.2, 0.5)))
    pi = ease_back(prog(t, 2.5, 0.5)); paste(f, O_SOC, W / 2, 1680, alpha=clamp(pi), scale=max(0.01, pi))
    pf = ease_out(prog(t, 2.8, 0.5)); paste(f, O_FAV, W / 2, 1790, alpha=pf)
    ImageDraw.Draw(f).rectangle((W / 2 - O_FAV.width / 2 * pf, 1825, W / 2 + O_FAV.width / 2 * pf, 1829), fill=OR + (255,))
    return f

BASE[-1] = (6.0, lambda t, d: outro(t))

def base_at(i, t):
    d, fn = BASE[i]; return fn(t, d)

def frame(T):
    i = min(max(k for k in range(len(BASE)) if starts[k] <= T), len(BASE) - 1)
    lt = T - starts[i]
    f = base_at(i, lt)
    if i > 0 and lt < XF:
        f = Image.blend(base_at(i - 1, BASE[i - 1][0] + lt), f, ease_out(lt / XF))
    if starts[2] <= T < CHROME_END: f.alpha_composite(GRAD_BOT)
    if starts[1] <= T < CHROME_END:
        a = ease_out(prog(T, starts[1], 0.4)) * (1 - prog(T, CHROME_END - 0.3, 0.3))
        if a < 1:
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); brand_chrome(layer, T); f.alpha_composite(with_alpha(layer, a))
        else:
            brand_chrome(f, T)
    if starts[1] <= T < starts[2]: headline(f, T - starts[1])
    for s, e, cap in CAPS:
        if s <= T < e: cap.draw(f, T - s, e - s)
    if T >= starts[1]:
        fl = 1 - prog(T, starts[1], 0.25)
        if 0 < fl < 1: f.alpha_composite(Image.new("RGBA", (W, H), OR + (int(170 * fl),)))
    return f.convert("RGB")

# ---------- music ----------
def music(path, dur, bpm=120, sr=44100):
    n = int(dur * sr); out = np.zeros(n, np.float32); beat = 60 / bpm
    tt = np.arange(int(sr * 0.5)) / sr
    kick = np.sin(2 * np.pi * (45 * tt + 90 * (1 - np.exp(-tt * 30)) / 30)) * np.exp(-tt * 9)
    rng = np.random.default_rng(1)
    snare = (rng.standard_normal(len(tt)) * np.exp(-tt * 22) * 0.6 + np.sin(2 * np.pi * 190 * tt) * np.exp(-tt * 25) * 0.4)
    hat = rng.standard_normal(int(sr * 0.06)); hat = np.diff(hat, prepend=0) * np.exp(-np.arange(len(hat)) / sr * 70)
    def add(sig, at, g):
        i = int(at * sr)
        if i >= n: return
        j = min(n, i + len(sig)); out[i:j] += sig[: j - i] * g
    roots = [57, 53, 48, 55]  # A F C G (midi)
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    nb = int(dur / beat) + 1
    intro_beats = 8
    for b in range(nb):
        t0 = b * beat
        bar = (b // 4) % 4
        full = b >= intro_beats
        add(kick, t0, 0.9 if full or b % 2 == 0 else 0.0)
        if full and b % 2 == 1: add(snare, t0, 0.45)
        for h in range(2): add(hat, t0 + h * beat / 2, 0.12 if h else 0.07)
        if full:
            for e in range(2):
                ts = np.arange(int(sr * beat / 2)) / sr
                f0 = hz(roots[bar] - 24 + (12 if e else 0))
                saw = 2 * ((ts * f0) % 1) - 1
                add(saw * np.exp(-ts * 6) * 0.22, t0 + e * beat / 2, 1)
        if b % 4 == 0:
            ts = np.arange(int(sr * beat * 4)) / sr
            env = np.minimum(1, ts / 0.3) * np.exp(-ts * 0.5)
            pad = sum(np.sin(2 * np.pi * hz(m) * ts) + 0.3 * np.sin(2 * np.pi * hz(m) * 2.003 * ts) for m in chords[bar])
            add(pad * env * 0.06, t0, 1)
            # pluck arpeggio
            for k in range(8):
                ts2 = np.arange(int(sr * beat / 2)) / sr
                m = chords[bar][k % 3] + 12 * (k // 3 % 2)
                add(np.sin(2 * np.pi * hz(m + 12) * ts2) * np.exp(-ts2 * 10) * (0.08 if full else 0.05), t0 + k * beat / 2, 1)
    # riser before the drop
    rs, re_ = intro_beats * beat - 1.5, intro_beats * beat
    ts = np.arange(int((re_ - rs) * sr)) / sr
    add(rng.standard_normal(len(ts)) * (ts / ts[-1]) ** 2 * 0.25, rs, 1)
    fade = int(sr * 1.8); out[-fade:] *= np.linspace(1, 0, fade)
    out[: int(sr * 0.05)] *= np.linspace(0, 1, int(sr * 0.05))
    out = np.tanh(out * 1.2); out /= np.abs(out).max() / 0.89
    st = np.stack([out, out], 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes((st * 32767).astype(np.int16).tobytes())

if __name__ == "__main__":
    wav = os.path.join(HERE, "music.wav")
    music(wav, TOTAL)
    if "--preview" in sys.argv:
        for T in [0.6, 1.5, 3.9, 5.5, 8.0, 18.0, 33.0, 45.0, 51.5, 53.5, 55.5, 59.5]:
            frame(T).save(os.path.join(HERE, f"prev_{T:05.1f}.jpg"), quality=80)
        sys.exit()
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    nfr = int(TOTAL * FPS)
    for k in range(nfr):
        p.stdin.write(frame(k / FPS).tobytes())
        if k % 150 == 0: print(f"{k}/{nfr}", flush=True)
    p.stdin.close(); p.wait()
    print("done", OUT, TOTAL)
