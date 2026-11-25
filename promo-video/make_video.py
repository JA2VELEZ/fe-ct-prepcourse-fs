"""Directo USA Store - promo video "Llegaron sus encargos" (1080x1920, 30fps)."""
import math, subprocess, sys, wave, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
UP = "/root/.claude/uploads/8119d2c8-4316-5490-ba27-260211af296a/"
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out.mp4")
W, H, FPS = 1080, 1920, 30
RED, ORANGE, WHITE, GREEN = (227, 38, 46), (255, 106, 26), (255, 255, 255), (37, 211, 102)

ANTON = os.path.join(HERE, "fonts/Anton-Regular.ttf")
OSWALD = os.path.join(HERE, "fonts/Oswald.ttf")

def anton(s): return ImageFont.truetype(ANTON, s)
def oswald(s, w="Bold"):
    f = ImageFont.truetype(OSWALD, s)
    try: f.set_variation_by_name(w)
    except Exception: pass
    return f

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
    if spacing:
        widths = [d.textlength(c, font=font) for c in txt]
        tw = int(sum(widths) + spacing * (len(txt) - 1))
    else:
        tw = int(d.textlength(txt, font=font))
    asc, desc = font.getmetrics()
    pad = 40
    im = Image.new("RGBA", (tw + pad * 2, asc + desc + pad * 2), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    def draw(drw, col, sw):
        if spacing:
            x = pad
            for c, w in zip(txt, widths):
                drw.text((x, pad), c, font=font, fill=col, stroke_width=sw, stroke_fill=col if col[3:] == (0,) else stroke_fill)
                x += w + spacing
        else:
            drw.text((pad, pad), txt, font=font, fill=col, stroke_width=sw, stroke_fill=stroke_fill)
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        draw(ImageDraw.Draw(sh), (0, 0, 0, 200), stroke)
        sh = sh.filter(ImageFilter.GaussianBlur(10))
        im = Image.alpha_composite(im, sh)
        dr = ImageDraw.Draw(im)
    draw(dr, fill + (255,) if len(fill) == 3 else fill, stroke)
    return im.crop(im.getbbox()) if not shadow else im

def with_alpha(im, a):
    if a >= 0.999: return im
    im = im.copy()
    im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    return im

def paste(base, im, cx, cy, alpha=1.0, scale=1.0, anchor="c"):
    if alpha <= 0.01 or scale <= 0.01: return
    if abs(scale - 1) > 0.001:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    im = with_alpha(im, alpha)
    x = int(cx - im.width / 2) if anchor == "c" else int(cx)
    y = int(cy - im.height / 2)
    base.alpha_composite(im, (x, y)) if 0 <= x and 0 <= y and x + im.width <= W and y + im.height <= H else _safe(base, im, x, y)

def _safe(base, im, x, y):
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    layer.paste(im, (x, y), im)
    base.alpha_composite(layer)

def pill(w, h, color, r=None):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), r if r is not None else h // 2, fill=color + (255,))
    return im

# ---------- photos ----------
def load_cover(name, extra=1.18):
    im = Image.open(UP + name).convert("RGB")
    s = max(W * extra / im.width, H * extra / im.height)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)

def kenburns(img, t, dur, z0, z1, px=0.0, py=0.0):
    p = t / dur
    z = z0 + (z1 - z0) * p
    cw, ch = img.width / z, img.height / z
    # base crop is the W:H window that fits the scaled image
    cw = min(cw, img.width); ch = cw * H / W
    if ch > img.height: ch = img.height; cw = ch * W / H
    cx = img.width / 2 + px * (p - 0.5) * (img.width - cw)
    cy = img.height / 2 + py * (p - 0.5) * (img.height - ch)
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return img.resize((W, H), Image.BILINEAR, box=box).convert("RGBA")

def vgrad(top_a, bot_a, y0, y1):
    a = np.zeros((H, 1), np.float32)
    ys = np.arange(H)
    k = np.clip((ys - y0) / max(1, (y1 - y0)), 0, 1)
    a[:, 0] = np.where((ys >= y0) & (ys <= y1), top_a + (bot_a - top_a) * k, 0)
    a = np.repeat(a, W, axis=1).astype(np.uint8)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); im.putalpha(Image.fromarray(a))
    return im

GRAD_BOT = vgrad(0, 235, 1300, 1920)
GRAD_TOP = vgrad(190, 0, 0, 380)

# ---------- brand pieces ----------
F_LOGO = anton(64)
LOGO_SMALL = None
def build_logo(size_main, sub_size):
    a = text_img("DIRECTO ", anton(size_main), WHITE)
    b = text_img("USA", anton(size_main), RED)
    s = text_img("STORE  ·  PERSONAL SHOPPER", oswald(sub_size, "Medium"), (230, 230, 230), spacing=4)
    w = a.width + b.width - 80
    im = Image.new("RGBA", (max(w, s.width), a.height + s.height - 110), (0, 0, 0, 0))
    im.alpha_composite(a, (0, 0)); im.alpha_composite(b, (a.width - 80, 0))
    im.alpha_composite(s, ((im.width - s.width) // 2 if s.width < w else 0, a.height - 95))
    return im
LOGO_SMALL = build_logo(66, 26)

def flag(w):
    h = int(w * 0.55)
    im = Image.new("RGBA", (w, h)); d = ImageDraw.Draw(im)
    for i in range(13):
        d.rectangle((0, i * h / 13, w, (i + 1) * h / 13), fill=RED + (255,) if i % 2 == 0 else WHITE + (255,))
    d.rectangle((0, 0, w * 0.42, h * 7 / 13), fill=(30, 50, 120, 255))
    for r in range(4):
        for c in range(5):
            x = w * 0.42 * (c + 0.5 + (0.25 if r % 2 else 0)) / 5.4; y = h * 7 / 13 * (r + 0.5) / 4
            d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=WHITE + (255,))
    return im
FLAG = flag(84)

WA_TXT = text_img("WHATSAPP  316 439 5101", anton(58), WHITE, shadow=False)

def wa_icon(d):
    im = Image.new("RGBA", (d, d), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    dr.ellipse((0, 0, d - 1, d - 1), fill=GREEN + (255,))
    m = d * 0.2; dr.ellipse((m, m, d - m, d - m), outline=WHITE + (255,), width=max(3, d // 14))
    dr.polygon([(m + d * 0.02, d - m - d * 0.02), (m - d * 0.06, d - m + d * 0.1), (m + d * 0.16, d - m - d * 0.04)], fill=WHITE + (255,))
    # handset
    hs = Image.new("RGBA", (d, d), (0, 0, 0, 0)); hd = ImageDraw.Draw(hs)
    hd.rounded_rectangle((d * 0.42, d * 0.33, d * 0.58, d * 0.67), d * 0.06, fill=WHITE + (255,))
    hd.rectangle((d * 0.47, d * 0.40, d * 0.58, d * 0.60), fill=GREEN + (255,))
    im.alpha_composite(hs.rotate(-35, center=(d / 2, d / 2)))
    return im
WA_ICON = wa_icon(70)

def brand_chrome(f, t, total_t):
    """Top logo + bottom WhatsApp band used on photo scenes."""
    f.alpha_composite(GRAD_TOP)
    f.alpha_composite(FLAG, (60, 92))
    f.alpha_composite(LOGO_SMALL, (150, 40))
    # bottom band
    band = Image.new("RGBA", (W, 130), RED + (255,))
    bd = ImageDraw.Draw(band)
    # moving diagonal stripes
    off = int(total_t * 60) % 60
    for x in range(-200, W + 200, 60):
        bd.polygon([(x + off, 0), (x + off + 24, 0), (x + off - 26, 130), (x + off - 50, 130)], fill=(200, 25, 33, 255))
    f.alpha_composite(band, (0, H - 130))
    pulse = 1 + 0.04 * math.sin(total_t * 2 * math.pi * 2)
    paste(f, WA_ICON, 110, H - 65, scale=pulse)
    f.alpha_composite(WA_TXT, (165, H - 65 - WA_TXT.height // 2))

# ---------- captions ----------
class Caption:
    def __init__(self, tag, title, sub, title_size=170):
        self.tag = tag and text_img(tag, anton(46), WHITE, shadow=False)
        self.title = text_img(title, anton(title_size), WHITE)
        self.sub = text_img(sub, oswald(58, "SemiBold"), (255, 214, 190))

    def draw(self, f, t, dur):
        out = 1 - prog(t, dur - 0.25, 0.25)
        x0 = 70
        # tag badge
        if self.tag:
            p = ease_back(prog(t, 0.05, 0.4))
            b = pill(self.tag.width + 50, 74, ORANGE, 10)
            b.alpha_composite(self.tag, (25, (74 - self.tag.height) // 2))
            b = b.rotate(4, expand=True, resample=Image.BICUBIC)
            paste(f, b, x0 - 10, 1395, alpha=clamp(p) * out, scale=max(0.01, p), anchor="l")
        # accent bar
        pb = ease_out(prog(t, 0.1, 0.4))
        ImageDraw.Draw(f).rectangle((x0, 1480, x0 + 16, 1480 + int(200 * pb * out)), fill=RED + (255,))
        pt = ease_out(prog(t, 0.15, 0.45))
        paste(f, self.title, x0 - 10 + int((1 - pt) * -500) + 10, 1560, alpha=pt * out, anchor="l")
        ps = ease_out(prog(t, 0.35, 0.45))
        paste(f, self.sub, x0 - 10 + 10, 1700 + int((1 - ps) * 40), alpha=ps * out, anchor="l")

# ---------- intro ----------
def dark_bg(seed_t=0.0):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt((xx - W / 2) ** 2 + ((yy - H * 0.42) * 0.8) ** 2) / (H * 0.7)
    v = np.clip(34 - 30 * r, 6, 40)
    stripes = ((xx + yy) // 28 % 2) * 4
    arr = np.stack([v + stripes, v * 0.95 + stripes, v * 0.95 + stripes], -1).astype(np.uint8)
    return Image.fromarray(arr).convert("RGBA")
DARK = dark_bg()

def crosshair(r, rot, col=RED, width=10):
    s = int(r * 2.6); im = Image.new("RGBA", (s, s), (0, 0, 0, 0)); d = ImageDraw.Draw(im); c = s / 2
    d.ellipse((c - r, c - r, c + r, c + r), outline=col + (255,), width=width)
    d.ellipse((c - r * 0.62, c - r * 0.62, c + r * 0.62, c + r * 0.62), outline=col + (150,), width=width // 2)
    for a in range(4):
        ang = math.radians(rot + a * 90)
        d.line((c + math.cos(ang) * r * 0.75, c + math.sin(ang) * r * 0.75, c + math.cos(ang) * r * 1.25, c + math.sin(ang) * r * 1.25), fill=col + (255,), width=width)
    for a in range(36):
        ang = math.radians(rot * -0.5 + a * 10)
        d.line((c + math.cos(ang) * r * 1.06, c + math.sin(ang) * r * 1.06, c + math.cos(ang) * r * 1.12, c + math.sin(ang) * r * 1.12), fill=WHITE + (120,), width=3)
    return im

I_DIRECTO = text_img("DIRECTO", anton(240), WHITE)
I_USA = text_img("USA", anton(330), RED, stroke=0)
I_STORE = text_img("STORE", oswald(84, "Bold"), WHITE, spacing=38)
I_PS_TXT = text_img("PERSONAL SHOPPER", anton(64), WHITE, shadow=False)
I_PS = pill(I_PS_TXT.width + 80, 110, ORANGE, 14); I_PS.alpha_composite(I_PS_TXT, (40, (110 - I_PS_TXT.height) // 2))
I_IMP = text_img("COMPRAS EN USA  ·  IMPORTACIONES A COLOMBIA", oswald(40, "Medium"), (220, 220, 220), spacing=2)
FLAG_BIG = flag(200)

def intro(t):
    f = DARK.copy()
    ch = crosshair(330, t * 40)
    p = ease_back(prog(t, 0.0, 0.6))
    paste(f, ch, W / 2, 820, alpha=0.55 * clamp(p), scale=max(0.01, p))
    paste(f, FLAG_BIG, W / 2, 470 - (1 - ease_out(prog(t, 0.1, 0.5))) * 80, alpha=ease_out(prog(t, 0.1, 0.5)))
    pd = ease_out(prog(t, 0.25, 0.5))
    paste(f, I_DIRECTO, W / 2 - (1 - pd) * 900, 700, alpha=pd)
    pu = ease_back(prog(t, 0.5, 0.5))
    paste(f, I_USA, W / 2, 960, alpha=clamp(pu), scale=max(0.01, 0.6 + 0.4 * pu))
    paste(f, I_STORE, W / 2 + 19, 1180, alpha=ease_out(prog(t, 0.9, 0.4)))
    pp = ease_back(prog(t, 1.2, 0.45))
    paste(f, I_PS, W / 2, 1330, alpha=clamp(pp), scale=max(0.01, pp))
    paste(f, I_IMP, W / 2, 1470, alpha=ease_out(prog(t, 1.5, 0.4)))
    # stripe sweep
    d = ImageDraw.Draw(f)
    sw = ease_out(prog(t, 0.2, 0.8))
    for i, col in enumerate([RED, WHITE, RED]):
        d.rectangle((0, 1560 + i * 14, int(W * sw), 1560 + i * 14 + 8), fill=col + (255,))
        d.rectangle((W - int(W * sw), 380 - i * 14, W, 380 - i * 14 + 8), fill=col + (255,))
    return f

# ---------- scenes ----------
photos = {k: load_cover(v) for k, v in {
    "box": "7ff0e587-image.webp", "hugo1": "4203620d-image.webp", "hugo2": "ed6c980c-image.webp",
    "hugo3": "51b38966-image.webp", "karl": "cceb0f43-image.webp", "adi1": "9b6dc497-image.webp",
    "adi2": "e0d4271a-image.webp", "lattafa": "06bf798c-image.webp", "nike1": "52937938-image.webp",
    "nike2": "8f770ddd-image.webp", "nike3": "eb698309-image.webp", "nike4": "852adee0-image.webp",
    "dkny1": "adacd9b2-image.webp", "dkny2": "00af0dcf-image.webp", "dkny3": "94d0617b-image.webp",
    "mk": "cc44f2ac-image.webp", "karl2": "f5ea090a-image.webp", "orig1": "cc25459f-image.webp",
    "orig2": "d2a62970-image.webp", "guess1": "ea5d39e3-image.webp", "guess2": "281344d6-image.webp",
    "guess3": "d5e22b78-image.webp", "guess4": "f8265b40-image.webp",
}.items()}

CARD_BOX, CARD_CY = (960, 1250), 860
_cards = {}
def card_assets(key):
    """Full (uncropped) photo as a framed card + blurred backdrop."""
    if key in _cards: return _cards[key]
    src = photos[key]
    bg = kenburns(src, 0, 1, 1.0, 1.0).filter(ImageFilter.GaussianBlur(40))
    bg.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 120)))
    sc = min(CARD_BOX[0] / src.width, CARD_BOX[1] / src.height)
    cw, ch = int(src.width * sc), int(src.height * sc)
    ph = src.resize((cw, ch), Image.LANCZOS).convert("RGBA")
    b, pad = 8, 40
    card = Image.new("RGBA", (cw + 2 * (b + pad), ch + 2 * (b + pad)), (0, 0, 0, 0))
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 12, pad + cw + 2 * b, pad + ch + 2 * b + 12), 30, fill=(0, 0, 0, 200))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    ImageDraw.Draw(card).rounded_rectangle((pad, pad, pad + cw + 2 * b, pad + ch + 2 * b), 30, fill=WHITE + (255,))
    m = Image.new("L", (cw, ch), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, cw - 1, ch - 1), 24, fill=255)
    card.paste(ph, (pad + b, pad + b), m)
    _cards[key] = (bg, card)
    return _cards[key]

def photo_scene(key, z0, z1, px=0, py=0, darken=0):
    def fn(t, dur):
        bg, card = card_assets(key)
        f = bg.copy()
        p = t / dur
        z = 0.96 + 0.06 * (p if z1 > z0 else 1 - p)  # gentle zoom of the whole card, nothing cropped
        paste(f, card, W / 2, CARD_CY, scale=z)
        if darken: f.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * darken))))
        return f
    return fn

# base layer: (duration, render(t, dur))
BASE = [
    (3.0, lambda t, d: intro(t)),
    (3.0, photo_scene("box", 1.0, 1.15, 0, 0.3, darken=0.45)),
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
    (6.0, None),  # 23 outro
]
starts = np.cumsum([0] + [d for d, _ in BASE]).tolist()
TOTAL = starts[-1]
XF = 0.3

# caption groups: (start, end, Caption)
def at(i): return starts[i]
CAPS = [
    (at(2), at(5), Caption("YA LLEGÓ", "HUGO BOSS", "Camisetas de marca")),
    (at(5), at(7), Caption("YA LLEGÓ", "KARL LAGERFELD", "Camisetas Paris", 140)),
    (at(7), at(8), Caption("YA LLEGÓ", "MICHAEL KORS", "Camisetas de marca", 150)),
    (at(8), at(10), Caption("YA LLEGÓ", "ADIDAS ORIGINALS", "Camisetas y tops", 130)),
    (at(10), at(12), Caption("YA LLEGÓ", "ADIDAS GALAXY 7", "Running  ·  Cloudfoam", 150)),
    (at(12), at(16), Caption("YA LLEGÓ", "NIKE AIR MAX 90", "Clásico de siempre", 150)),
    (at(16), at(20), Caption("YA LLEGÓ", "GUESS", "Sneakers con logo dorado")),
    (at(20), at(22), Caption("YA LLEGÓ", "DKNY", "Sneakers slip-on")),
    (at(22), at(23), Caption("YA LLEGÓ", "LATTAFA", "Qaed Al Fursan  ·  90 ml")),
]

# intro-2 headline over box photo
H1 = text_img("¡LLEGARON", anton(200), WHITE, stroke=4, stroke_fill=(0, 0, 0))
H2 = text_img("SUS ENCARGOS!", anton(170), ORANGE, stroke=4, stroke_fill=(0, 0, 0))
H3 = text_img("Mercancía nueva directo desde USA", oswald(58, "SemiBold"), WHITE)
def headline(f, t):
    p1 = ease_back(prog(t, 0.1, 0.45)); p2 = ease_back(prog(t, 0.35, 0.45))
    shake = math.sin(t * 60) * 6 * (1 - prog(t, 0.3, 0.4)) if t > 0.1 else 0
    paste(f, H1, W / 2 + shake, 820, alpha=clamp(p1), scale=max(0.01, 1.6 - 0.6 * p1))
    paste(f, H2, W / 2 - shake, 1010, alpha=clamp(p2), scale=max(0.01, 1.6 - 0.6 * p2))
    p3 = ease_out(prog(t, 0.8, 0.5))
    bar = pill(H3.width + 40, 100, RED, 12)
    paste(f, bar, W / 2, 1180 + (1 - p3) * 40, alpha=p3)
    paste(f, H3, W / 2, 1180 + (1 - p3) * 40, alpha=p3)

# ---------- outro ----------
OUT_BG = photos["nike1"].filter(ImageFilter.GaussianBlur(28)).convert("RGBA")
OUT_BG = OUT_BG.crop(((OUT_BG.width - W) // 2, (OUT_BG.height - H) // 2, (OUT_BG.width - W) // 2 + W, (OUT_BG.height - H) // 2 + H))
OUT_BG.alpha_composite(Image.new("RGBA", (W, H), (8, 8, 8, 205)))
O1 = text_img("¿YA RECLAMASTE", anton(140), WHITE)
O2 = text_img("TU PEDIDO?", anton(190), ORANGE)
O3 = text_img("Escríbenos y coordinamos tu entrega", oswald(52, "Medium"), (235, 235, 235))
O_NUM = text_img("316 439 5101", anton(120), WHITE, shadow=False)
O_WA = text_img("ESCRÍBENOS POR WHATSAPP", oswald(38, "SemiBold"), WHITE, shadow=False, spacing=3)
O_LOGO = build_logo(110, 40)
def ig_icon(d):
    g = Image.new("RGBA", (d, d)); gd = ImageDraw.Draw(g)
    stops = [(254, 218, 117), (250, 126, 30), (214, 41, 118), (150, 47, 191), (79, 91, 213)]
    for y in range(d):
        k = (d - 1 - y) / (d - 1) * (len(stops) - 1); i = min(int(k), len(stops) - 2); u = k - i
        gd.line((0, y, d, y), fill=tuple(int(stops[i][c] + (stops[i + 1][c] - stops[i][c]) * u) for c in range(3)) + (255,))
    m = Image.new("L", (d, d), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, d - 1, d - 1), d // 4, fill=255)
    im = Image.new("RGBA", (d, d), (0, 0, 0, 0)); im.paste(g, (0, 0), m); dr = ImageDraw.Draw(im); w = max(3, d // 14)
    dr.rounded_rectangle((d * .2, d * .2, d * .8, d * .8), d // 6, outline=WHITE + (255,), width=w)
    dr.ellipse((d * .35, d * .35, d * .65, d * .65), outline=WHITE + (255,), width=w)
    dr.ellipse((d * .66, d * .27, d * .73, d * .34), fill=WHITE + (255,))
    return im
O_IG_TXT = text_img("@directo_usastore", anton(60), WHITE, shadow=False)
O_IG = Image.new("RGBA", (O_IG_TXT.width + 110, 90), (0, 0, 0, 0))
O_IG.alpha_composite(ig_icon(80), (0, 5)); O_IG.alpha_composite(O_IG_TXT, (100, (90 - O_IG_TXT.height) // 2))
O_CATS = text_img("MODA  ·  CALZADO  ·  TECNOLOGÍA  ·  TACTICAL  ·  OUTDOOR", oswald(34, "Medium"), (200, 200, 200), spacing=2)
O_CTA = text_img("¡PIDE LO TUYO DESDE USA!", anton(78), WHITE)

def outro(t):
    f = OUT_BG.copy()
    paste(f, crosshair(380, t * 30, RED, 8), W / 2, 960, alpha=0.18)
    p = ease_out(prog(t, 0.1, 0.5))
    paste(f, O1, W / 2, 360 - (1 - p) * 60, alpha=p)
    p = ease_back(prog(t, 0.3, 0.5))
    paste(f, O2, W / 2, 540, alpha=clamp(p), scale=max(0.01, p))
    paste(f, O3, W / 2, 690, alpha=ease_out(prog(t, 0.6, 0.4)))
    # WhatsApp card
    p = ease_back(prog(t, 0.9, 0.5))
    pulse = 1 + 0.03 * math.sin(t * 2 * math.pi * 2) * prog(t, 1.4, 0.2)
    card = pill(900, 300, GREEN, 40)
    big_icon = wa_icon(130)
    card.alpha_composite(big_icon, (50, 85))
    card.alpha_composite(O_WA, (200, 40))
    card.alpha_composite(O_NUM, (205, 100))
    paste(f, card, W / 2, 960, alpha=clamp(p), scale=max(0.01, p * pulse))
    p = ease_out(prog(t, 1.4, 0.5))
    paste(f, O_CTA, W / 2, 1200 + (1 - p) * 40, alpha=p)
    p = ease_out(prog(t, 1.8, 0.6))
    paste(f, FLAG_BIG, W / 2, 1350, alpha=p, scale=0.6)
    paste(f, O_LOGO, W / 2, 1500, alpha=p)
    paste(f, O_CATS, W / 2, 1650, alpha=ease_out(prog(t, 2.2, 0.5)))
    pi = ease_back(prog(t, 2.5, 0.5))
    paste(f, O_IG, W / 2, 1790, alpha=clamp(pi), scale=max(0.01, pi))
    return f

BASE[-1] = (6.0, lambda t, d: outro(t))

# ---------- frame composition ----------
def base_at(i, t):
    d, fn = BASE[i]
    return fn(t, d)

def frame(T):
    i = max(k for k in range(len(BASE)) if starts[k] <= T)
    i = min(i, len(BASE) - 1)
    lt = T - starts[i]
    f = base_at(i, lt)
    if i > 0 and lt < XF:
        prev = base_at(i - 1, BASE[i - 1][0] + lt)
        f = Image.blend(prev, f, ease_out(lt / XF))
    # chrome on photo scenes (not intro / outro)
    if starts[2] <= T < starts[-2]:
        f.alpha_composite(GRAD_BOT)
    if starts[1] <= T < starts[-2]:
        a = ease_out(prog(T, starts[1], 0.4))
        if a < 1:
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); brand_chrome(layer, T - starts[1], T); f.alpha_composite(with_alpha(layer, a))
        else:
            brand_chrome(f, T - starts[1], T)
    if starts[1] <= T < starts[2]:
        headline(f, T - starts[1])
    for s, e, cap in CAPS:
        if s <= T < e:
            cap.draw(f, T - s, e - s)
    # white flash at intro->box cut
    fl = 1 - prog(T, starts[1], 0.25) if T >= starts[1] else 0
    if 0 < fl < 1:
        f.alpha_composite(Image.new("RGBA", (W, H), (255, 255, 255, int(200 * fl))))
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
    intro_beats = 6
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
        for T in [1.5, 2.9, 4.5, 6.6, 10.6, 13.0, 17.0, 23.5, 27.5, 31.5, 34.0, 37.5]:
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
