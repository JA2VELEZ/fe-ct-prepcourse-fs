"""Transportes Don Ramón - video publicitario (1080x1920, 30fps)."""
import math, subprocess, sys, wave, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
UP = "/root/.claude/uploads/8119d2c8-4316-5490-ba27-260211af296a/"
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "Transportes_Don_Ramon.mp4")
W, H, FPS = 1080, 1920, 30
NAVY, NAVY2, YEL, WHITE, LIGHT = (12, 35, 64), (6, 20, 40), (255, 193, 7), (255, 255, 255), (205, 215, 230)
GREEN = (37, 211, 102)
ANTON = os.path.join(HERE, "fonts/Anton-Regular.ttf")
OSWALD = os.path.join(HERE, "fonts/Oswald.ttf")
DEJAVU = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

def anton(s): return ImageFont.truetype(ANTON, s)
def oswald(s, w="Bold"):
    f = ImageFont.truetype(OSWALD, s)
    try: f.set_variation_by_name(w)
    except Exception: pass
    return f

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease_out(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_back(x):
    x = clamp(x); c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def prog(t, a, d): return clamp((t - a) / d)

def text_img(txt, font, fill=WHITE, shadow=True, spacing=0):
    d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    widths = [d.textlength(c, font=font) for c in txt]
    tw = int(sum(widths) + spacing * (len(txt) - 1)) if spacing else int(d.textlength(txt, font=font))
    asc, desc = font.getmetrics(); pad = 40
    im = Image.new("RGBA", (tw + pad * 2, asc + desc + pad * 2), (0, 0, 0, 0))
    def draw(drw, col):
        if spacing:
            x = pad
            for c, w in zip(txt, widths): drw.text((x, pad), c, font=font, fill=col); x += w + spacing
        else: drw.text((pad, pad), txt, font=font, fill=col)
    if shadow:
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); draw(ImageDraw.Draw(sh), (0, 0, 0, 210))
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(10)))
    draw(ImageDraw.Draw(im), fill + (255,))
    return im

def tight(im): return im.crop(im.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox())

def with_alpha(im, a):
    if a >= 0.999: return im
    im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a))); return im

def paste(base, im, cx, cy, alpha=1.0, scale=1.0, anchor="c", rot=0):
    if alpha <= 0.01 or scale <= 0.01: return
    if abs(scale - 1) > 0.001: im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if rot: im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    im = with_alpha(im, alpha)
    x = int(cx - im.width / 2) if anchor == "c" else int(cx); y = int(cy - im.height / 2)
    if 0 <= x and 0 <= y and x + im.width <= W and y + im.height <= H: base.alpha_composite(im, (x, y))
    else:
        layer = Image.new("RGBA", base.size, (0, 0, 0, 0)); layer.paste(im, (x, y), im); base.alpha_composite(layer)

def pill(w, h, color, r=None):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle((0, 0, w - 1, h - 1), r if r is not None else h // 2, fill=color + (255,)); return im

# ---------- brand ----------
def pickup(w, col=NAVY, cut=YEL, ss=4):
    S = w * ss; im = Image.new("RGBA", (S, int(S * 0.5)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    P = lambda pts: [(x * S, y * S) for x, y in pts]
    d.polygon(P([(0.0, 0.20), (0.47, 0.20), (0.50, 0.05), (0.72, 0.05), (0.84, 0.19), (0.97, 0.23), (1.0, 0.36), (0.0, 0.36)]), fill=col + (255,))
    d.polygon(P([(0.535, 0.085), (0.69, 0.085), (0.79, 0.19), (0.535, 0.19)]), fill=cut + (255,))
    d.line(P([(0.66, 0.085), (0.66, 0.19)]), fill=col + (255,), width=int(S * 0.015))
    for cx in (0.22, 0.80):
        r = 0.095; d.ellipse((S * (cx - r - 0.02), S * (0.37 - r - 0.02), S * (cx + r + 0.02), S * (0.37 + r + 0.02)), fill=cut + (255,))
        d.ellipse((S * (cx - r), S * (0.37 - r), S * (cx + r), S * (0.37 + r)), fill=col + (255,))
        r2 = 0.04; d.ellipse((S * (cx - r2), S * (0.37 - r2), S * (cx + r2), S * (0.37 + r2)), fill=cut + (255,))
    return im.resize((w, w // 2), Image.LANCZOS)

def badge(s):
    im = pill(s, s, YEL, s // 5); t = pickup(int(s * 0.78)); im.alpha_composite(t, ((s - t.width) // 2, int(s * 0.27))); return im

def logo_h(h):
    a = tight(text_img("TRANSPORTES", oswald(int(h * 0.42), "SemiBold"), WHITE, shadow=False, spacing=int(h * 0.09)))
    b = tight(text_img("DON RAMÓN", anton(int(h * 1.05)), YEL, shadow=False))
    th = a.height + int(h * 0.12) + b.height; bd = badge(int(th * 1.05))
    w = max(a.width, b.width)
    im = Image.new("RGBA", (bd.width + int(h * 0.25) + w, max(bd.height, th)), (0, 0, 0, 0))
    im.alpha_composite(bd, (0, (im.height - bd.height) // 2)); x = bd.width + int(h * 0.25); y = (im.height - th) // 2
    im.alpha_composite(a, (x + 2, y)); im.alpha_composite(b, (x, y + a.height + int(h * 0.12))); return im

def phone_icon(d, col=NAVY):
    g = tight(text_img("✆", ImageFont.truetype(DEJAVU, int(d * 1.2)), col, shadow=False))
    return g.resize((int(g.width * d / g.height), d), Image.LANCZOS)

def wa_icon(d, col=WHITE, bg=GREEN):
    S = d * 4; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    dr.ellipse((0, 0, S - 1, S - 1), fill=bg + (255,)); m = S * 0.2; w = int(S * 0.07)
    dr.ellipse((m, m, S - m, S - m), outline=col + (255,), width=w)
    dr.polygon([(m + S * 0.04, S - m - S * 0.12), (m - S * 0.05, S - m + S * 0.05), (m + S * 0.16, S - m - S * 0.03)], fill=col + (255,))
    hs = Image.new("RGBA", (S, S), (0, 0, 0, 0)); hd = ImageDraw.Draw(hs)
    hd.rounded_rectangle((S * 0.42, S * 0.33, S * 0.58, S * 0.67), S * 0.06, fill=col + (255,))
    hd.rectangle((S * 0.47, S * 0.41, S * 0.59, S * 0.59), fill=(0, 0, 0, 0))
    im.alpha_composite(hs.rotate(-35, center=(S / 2, S / 2))); return im.resize((d, d), Image.LANCZOS)

def ig_icon(d, col=YEL):
    S = d * 4; im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); dr = ImageDraw.Draw(im); w = int(S * 0.09)
    dr.rounded_rectangle((w, w, S - w, S - w), S // 4, outline=col + (255,), width=w)
    dr.ellipse((S * .3, S * .3, S * .7, S * .7), outline=col + (255,), width=w); dr.ellipse((S * .7, S * .2, S * .8, S * .3), fill=col + (255,))
    return im.resize((d, d), Image.LANCZOS)

# ---------- backgrounds ----------
def navy_bg():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt((xx - W / 2) ** 2 + ((yy - H * 0.42) * 0.8) ** 2) / (H * 0.7)
    k = np.clip(1 - r, 0, 1)[..., None]
    base = np.array(NAVY2, np.float32) + (np.array(NAVY, np.float32) * 1.5 - np.array(NAVY2, np.float32)) * k
    topo = np.zeros((H, W), np.float32)
    for i in range(14):  # topographic contour lines (mountains of Antioquia)
        y0 = 120 + i * 140; yl = y0 + 50 * np.sin(xx[0] / 160 + i) + 30 * np.sin(xx[0] / 60 + i * 2)
        topo[np.clip(yl.astype(int), 0, H - 1), np.arange(W)] = 1
    topo = np.array(Image.fromarray((topo * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) / 255.0
    base = base + topo[..., None] * 14
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
BG = navy_bg()

def vgrad(top_a, bot_a, y0, y1, col=NAVY2):
    ys = np.arange(H); k = np.clip((ys - y0) / max(1, y1 - y0), 0, 1)
    a = np.where((ys >= y0) & (ys <= y1), top_a + (bot_a - top_a) * k, np.where(ys > y1, bot_a, 0)).astype(np.uint8)
    im = Image.new("RGBA", (W, H), col + (0,)); im.putalpha(Image.fromarray(np.repeat(a[:, None], W, 1))); return im
GRAD_TOP = vgrad(220, 0, 0, 320)
GRAD_BOT = vgrad(0, 235, 1150, 1450)

# ---------- photos as cards ----------
def card_scene(name, zin=True):
    src = Image.open(UP + name).convert("RGB")
    s = max(W / src.width, H / src.height) * 1.05
    bgi = src.resize((int(src.width * s), int(src.height * s)), Image.BILINEAR)
    bgi = bgi.crop(((bgi.width - W) // 2, (bgi.height - H) // 2, (bgi.width - W) // 2 + W, (bgi.height - H) // 2 + H)).filter(ImageFilter.GaussianBlur(36)).convert("RGBA")
    bgi.alpha_composite(Image.new("RGBA", (W, H), NAVY2 + (150,)))
    cw = 990; ch = int(src.height * cw / src.width)
    ph = src.resize((cw, ch), Image.LANCZOS).convert("RGBA"); b, pad = 8, 40
    card = Image.new("RGBA", (cw + 2 * (b + pad), ch + 2 * (b + pad)), (0, 0, 0, 0))
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 14, pad + cw + 2 * b, pad + ch + 2 * b + 14), 30, fill=(0, 0, 0, 220))
    card.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    ImageDraw.Draw(card).rounded_rectangle((pad, pad, pad + cw + 2 * b, pad + ch + 2 * b), 30, fill=YEL + (255,))
    m = Image.new("L", (cw, ch), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, cw - 1, ch - 1), 24, fill=255)
    card.paste(ph, (pad + b, pad + b), m)
    def fn(t, dur):
        f = bgi.copy(); p = t / dur; z = 0.95 + 0.07 * (p if zin else 1 - p)
        paste(f, card, W / 2, 760, scale=z); return f
    return fn

# ---------- chrome ----------
LOGO_SMALL = logo_h(64)
PH_TXT = tight(text_img("324 677 9520", anton(70), NAVY, shadow=False))
PH_LBL = tight(text_img("LLAMA O ESCRIBE", oswald(30, "SemiBold"), NAVY, shadow=False, spacing=3))
def chrome(f, T):
    f.alpha_composite(GRAD_TOP); f.alpha_composite(LOGO_SMALL, (50, 40))
    band = Image.new("RGBA", (W, 140), YEL + (255,)); bd = ImageDraw.Draw(band); off = int(T * 70) % 70
    for x in range(-200, W + 200, 70): bd.polygon([(x + off, 0), (x + off + 24, 0), (x + off - 26, 140), (x + off - 50, 140)], fill=(240, 176, 0, 255))
    f.alpha_composite(band, (0, H - 140))
    paste(f, wa_icon(78), 100, H - 70, scale=1 + 0.05 * math.sin(T * 4 * math.pi))
    f.alpha_composite(PH_LBL, (165, H - 112)); f.alpha_composite(PH_TXT, (163, H - 72 - 4))

class Caption:
    def __init__(self, tag, title, sub, size=128):
        self.tag = tight(text_img(tag, oswald(40, "Bold"), NAVY, shadow=False))
        self.title = text_img(title, anton(size), WHITE)
        if self.title.width > 1030: self.title = self.title.resize((1030, int(self.title.height * 1030 / self.title.width)), Image.LANCZOS)
        self.sub = text_img(sub, oswald(54, "Medium"), LIGHT)
    def draw(self, f, t, dur):
        out = 1 - prog(t, dur - 0.25, 0.25); x0 = 70
        p = ease_back(prog(t, 0.05, 0.4))
        b = pill(self.tag.width + 50, 66, YEL, 8); b.alpha_composite(self.tag, (25, (66 - self.tag.height) // 2))
        paste(f, b, x0 - 10, 1255, alpha=clamp(p) * out, scale=max(0.01, p), anchor="l", rot=2)
        pb = ease_out(prog(t, 0.1, 0.4))
        ImageDraw.Draw(f).rectangle((x0, 1320, x0 + 14, 1320 + int(230 * pb * out)), fill=YEL + (255,))
        pt = ease_out(prog(t, 0.15, 0.45)); paste(f, self.title, x0 + int((1 - pt) * -500), 1410, alpha=pt * out, anchor="l")
        ps = ease_out(prog(t, 0.35, 0.45)); paste(f, self.sub, x0, 1560 + int((1 - ps) * 40), alpha=ps * out, anchor="l")

# ---------- intro ----------
BADGE_BIG = badge(330)
I_T = text_img("TRANSPORTES", oswald(96, "SemiBold"), WHITE, spacing=16)
I_D = text_img("DON RAMÓN", anton(230), YEL)
I_S = tight(text_img("TRANSPORTE Y LOGÍSTICA", anton(64), NAVY, shadow=False))
I_L = text_img("Medellín  ·  Valle de Aburrá", oswald(58, "Medium"), WHITE)
TRUCK_W = pickup(260, YEL, NAVY2)
def intro(t):
    f = BG.copy(); d = ImageDraw.Draw(f)
    # road with moving dashes
    d.rectangle((0, 1640, W, 1760), fill=(20, 28, 40, 255))
    off = int(t * 600) % 160
    for x in range(-160, W + 160, 160): d.rectangle((x - off, 1695, x - off + 80, 1705), fill=YEL + (255,))
    tx = -300 + ease_out(prog(t, 0.0, 1.4)) * (W / 2 + 300) + max(0, t - 2.9) * 900
    paste(f, TRUCK_W, tx, 1610 + math.sin(t * 25) * 2)
    p = ease_back(prog(t, 0.2, 0.6)); paste(f, BADGE_BIG, W / 2, 470, alpha=clamp(p), scale=max(0.01, p))
    pt = ease_out(prog(t, 0.5, 0.5)); paste(f, I_T, W / 2 - (1 - pt) * 700, 735, alpha=pt)
    pd = ease_back(prog(t, 0.75, 0.5)); paste(f, I_D, W / 2, 935, alpha=clamp(pd), scale=max(0.01, 0.6 + 0.4 * pd))
    ps = ease_out(prog(t, 1.2, 0.4)); b = pill(I_S.width + 70, 104, YEL, 12); b.alpha_composite(I_S, (35, (104 - I_S.height) // 2))
    paste(f, b, W / 2, 1110 + (1 - ps) * 40, alpha=ps)
    paste(f, I_L, W / 2, 1250, alpha=ease_out(prog(t, 1.5, 0.4)))
    return f

# ---------- map ----------
MED = (540, 760)
DEST = [("ORIENTE", "ANTIOQUEÑO", (850, 560)), ("SUROESTE", "ANTIOQUEÑO", (260, 1060)), ("EJE", "CAFETERO", (640, 1340))]
M_T1 = text_img("VIAJES", anton(110), WHITE); M_T2 = text_img("INTERMUNICIPALES", anton(110), YEL)
M_MED = tight(text_img("MEDELLÍN", anton(58), NAVY, shadow=False))
M_SUB = text_img("Desde Medellín y todo el Valle de Aburrá", oswald(48, "Medium"), WHITE)
TRUCK_S = pickup(110, YEL, NAVY2)
DEST_IMG = [(tight(text_img(a, anton(64), WHITE, shadow=False)), tight(text_img(b, oswald(36, "SemiBold"), YEL, shadow=False, spacing=3))) for a, b, _ in DEST]
def pin(s, col=YEL):
    S = s * 4; im = Image.new("RGBA", (S, int(S * 1.4)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((0, 0, S, S), fill=col + (255,)); d.polygon([(S * 0.15, S * 0.75), (S * 0.85, S * 0.75), (S / 2, S * 1.4)], fill=col + (255,))
    d.ellipse((S * .3, S * .3, S * .7, S * .7), fill=NAVY + (255,)); return im.resize((s, int(s * 1.4)), Image.LANCZOS)
PIN = pin(64)
def mapscene(t):
    f = BG.copy(); d = ImageDraw.Draw(f)
    p = ease_out(prog(t, 0, 0.5)); paste(f, M_T1, W / 2, 190 - (1 - p) * 60, alpha=p)
    p = ease_back(prog(t, 0.2, 0.5)); paste(f, M_T2, W / 2, 320, alpha=clamp(p), scale=max(0.01, p))
    for i, (a, b, (x, y)) in enumerate(DEST):
        st = 0.7 + i * 0.9; q = ease_out(prog(t, st, 0.9))
        if q <= 0: continue
        n = 40
        for k in range(int(n * q)):
            if k % 2: continue
            x1 = MED[0] + (x - MED[0]) * k / n; y1 = MED[1] + (y - MED[1]) * k / n
            x2 = MED[0] + (x - MED[0]) * (k + 1) / n; y2 = MED[1] + (y - MED[1]) * (k + 1) / n
            d.line((x1, y1, x2, y2), fill=YEL + (255,), width=8)
        if q < 1:
            paste(f, TRUCK_S if x >= MED[0] else TRUCK_S.transpose(Image.FLIP_LEFT_RIGHT), MED[0] + (x - MED[0]) * q, MED[1] + (y - MED[1]) * q - 30)
        pp = ease_back(prog(t, st + 0.8, 0.4))
        paste(f, PIN, x, y - 40, alpha=clamp(pp), scale=max(0.01, pp))
        ti, si = DEST_IMG[i]; lx = x + (-ti.width / 2 if i == 2 else 0)
        al = ease_out(prog(t, st + 0.9, 0.4)); ty = y + 30
        lab_x = min(max(x, 70 + max(ti.width, si.width) / 2), W - 70 - max(ti.width, si.width) / 2)
        paste(f, ti, lab_x, ty + 40, alpha=al); paste(f, si, lab_x, ty + 95, alpha=al)
    # Medellín hub
    r = 30 + 6 * math.sin(t * 6)
    d.ellipse((MED[0] - r - 20, MED[1] - r - 20, MED[0] + r + 20, MED[1] + r + 20), fill=YEL + (60,))
    d.ellipse((MED[0] - 26, MED[1] - 26, MED[0] + 26, MED[1] + 26), fill=YEL + (255,), outline=WHITE + (255,), width=6)
    b = pill(M_MED.width + 40, 80, WHITE, 10); b.alpha_composite(M_MED, (20, (80 - M_MED.height) // 2))
    paste(f, b, MED[0] - 230, MED[1], alpha=ease_out(prog(t, 0.3, 0.4)))
    paste(f, M_SUB, W / 2, 1560, alpha=ease_out(prog(t, 3.6, 0.5)))
    return f

# ---------- outro ----------
O1 = text_img("¡COTIZA", anton(170), WHITE); O2 = text_img("TU VIAJE!", anton(170), YEL)
O3 = text_img("Trasteos  ·  Carga  ·  Viajes intermunicipales", oswald(46, "Medium"), LIGHT)
O_NUM = tight(text_img("324 677 9520", anton(120), NAVY, shadow=False))
O_LBL = tight(text_img("LLAMA O ESCRIBE POR WHATSAPP", oswald(34, "SemiBold"), NAVY, shadow=False, spacing=2))
O_LOGO = logo_h(110)
_s = tight(text_img("@Transportes_donRamon", oswald(56, "Medium"), WHITE, shadow=False))
O_IG = Image.new("RGBA", (80 + _s.width, 70), (0, 0, 0, 0)); O_IG.alpha_composite(ig_icon(62), (0, 4)); O_IG.alpha_composite(_s, (80, (70 - _s.height) // 2))
O_ZONE = tight(text_img("MEDELLÍN · VALLE DE ABURRÁ · ORIENTE · SUROESTE · EJE CAFETERO", oswald(28, "Medium"), LIGHT, shadow=False, spacing=2))
def outro(t):
    f = BG.copy()
    p = ease_back(prog(t, 0.1, 0.5)); paste(f, O1, W / 2, 300, alpha=clamp(p), scale=max(0.01, p))
    p = ease_back(prog(t, 0.3, 0.5)); paste(f, O2, W / 2, 480, alpha=clamp(p), scale=max(0.01, p))
    paste(f, O3, W / 2, 630, alpha=ease_out(prog(t, 0.6, 0.4)))
    p = ease_back(prog(t, 0.9, 0.5)); pulse = 1 + 0.03 * math.sin(t * 4 * math.pi) * prog(t, 1.4, 0.2)
    card = pill(940, 270, YEL, 36); card.alpha_composite(wa_icon(150), (45, 60))
    card.alpha_composite(O_LBL, (225, 52)); card.alpha_composite(O_NUM, (222, 108))
    paste(f, card, W / 2, 860, alpha=clamp(p), scale=max(0.01, p * pulse))
    p = ease_out(prog(t, 1.5, 0.5)); paste(f, O_LOGO, W / 2, 1180, alpha=p, scale=0.9 + 0.1 * p)
    pi = ease_back(prog(t, 2.0, 0.5)); paste(f, O_IG, W / 2, 1390, alpha=clamp(pi), scale=max(0.01, pi))
    paste(f, O_ZONE, W / 2, 1500, alpha=ease_out(prog(t, 2.4, 0.5)))
    d = ImageDraw.Draw(f); d.rectangle((0, 1640, W, 1760), fill=(20, 28, 40, 255))
    off = int(t * 600) % 160
    for x in range(-160, W + 160, 160): d.rectangle((x - off, 1695, x - off + 80, 1705), fill=YEL + (255,))
    paste(f, TRUCK_W, -300 + ((t * 420) % (W + 600)), 1610 + math.sin(t * 25) * 2)
    return f

# ---------- timeline ----------
BASE = [
    (4.0, lambda t, d: intro(t)),
    (2.5, card_scene("995d160a-image.jpg", True)),   # 1 trasteos
    (2.5, card_scene("1cd5fad7-image.jpg", False)),  # 2
    (2.5, card_scene("603feb3a-image.jpg", True)),   # 3 todo tamaño
    (2.5, card_scene("29039d52-image.jpg", False)),  # 4 protegida
    (2.5, card_scene("92b658d9-image.jpg", True)),   # 5
    (6.0, lambda t, d: mapscene(t)),                 # 6 map
    (6.5, lambda t, d: outro(t)),                    # 7 outro
]
starts = np.cumsum([0] + [d for d, _ in BASE]).tolist(); TOTAL = starts[-1]; XF = 0.3
at = lambda i: starts[i]
CAPS = [
    (at(1), at(3), Caption("SERVICIO PUERTA A PUERTA", "TRASTEOS Y MUDANZAS", "Muebles, electrodomésticos y equipaje", 118)),
    (at(3), at(4), Caption("CAMIONETA 4x4", "CARGA DE TODO TAMAÑO", "Colchones, neveras, maletas y más", 112)),
    (at(4), at(6), Caption("TU CARGA SEGURA", "CARGA PROTEGIDA", "Cubierta contra el sol y la lluvia", 124)),
]

def frame(T):
    i = min(max(k for k in range(len(BASE)) if starts[k] <= T), len(BASE) - 1); lt = T - starts[i]
    f = BASE[i][1](lt, BASE[i][0])
    if i > 0 and lt < XF: f = Image.blend(BASE[i - 1][1](BASE[i - 1][0] + lt, BASE[i - 1][0]), f, ease_out(lt / XF))
    if at(1) <= T < at(6):
        f.alpha_composite(GRAD_BOT)
        a = ease_out(prog(T, at(1), 0.4)) * (1 - prog(T, at(6) - 0.3, 0.3))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0)); chrome(layer, T); f.alpha_composite(with_alpha(layer, a))
    for s, e, cap in CAPS:
        if s <= T < e: cap.draw(f, T - s, e - s)
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
    if "--preview" in sys.argv:
        for T in [0.8, 2.5, 5.5, 9.5, 13.5, 18.5, 20.5, 23.0, 26.0, 28.5]:
            frame(T).save(os.path.join(sys.argv[-1], f"tp_{T:05.1f}.jpg"), quality=80)
        sys.exit()
    wav = OUT + ".wav"; music(wav, TOTAL)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(int(TOTAL * FPS)): p.stdin.write(frame(k / FPS).tobytes())
    p.stdin.close(); p.wait(); os.remove(wav); print("done", OUT, TOTAL)
