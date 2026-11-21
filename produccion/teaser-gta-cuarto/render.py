#!/usr/bin/env python3
"""MARK KAIZEN · "Si mi cuarto fuera GTA VI" · teaser interactivo 9:16 (1080x1920, 30 fps).

Recorrido en primera persona por un cuarto ilustrado: 7 escenas distintas (sin repetir),
HUD de juego (objetivo, dinero, estrellas, minimapa, prompts [E]) que reacciona a cada acción
y una foto final con la cara de Mark (ref_selfie.jpg).

Uso:  python3 render.py [salida.mp4]
Requiere: numpy, Pillow, ffmpeg. Fuentes/logos/posters salen del repo.
"""
import math, os, sys, subprocess, random, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "mark_kaizen_gta-vi-cuarto_9x16.mp4")
W, H, FPS, S = 1080, 1920, 30, 2
FD = os.path.join(ROOT, "docs", "fuente", "fuentes")
FONTS = {"sora": os.path.join(FD, "Sora-recorte.ttf"),
         "inter": "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf",
         "jp": os.path.join(FD, "NotoSansJP-recorte.ttf")}
if not os.path.exists(FONTS["inter"]): FONTS["inter"] = FONTS["sora"]

# paleta GTA VI "suave": durazno -> rosa -> crepúsculo, acentos apagados, naranja de marca solo en detalles
PEACH, ROSE, DUSK, NIGHT = (246, 172, 124), (216, 102, 132), (92, 68, 134), (22, 17, 36)
TEAL, PINK, WARM, ORANGE = (82, 200, 196), (240, 112, 168), (255, 206, 150), (255, 107, 0)
GREEN, GOLD = (126, 214, 150), (238, 202, 120)

# ---- línea de tiempo (6 escenas de juego + cierre) ----
DURS = [2.5, 2.4, 2.4, 2.4, 2.4, 2.5, 2.0]
STARTS = [sum(DURS[:i]) for i in range(len(DURS))]
TOTAL = sum(DURS)
TW = 0.11  # media ventana de la transición "whip pan"
OBJ = ["ABRIR LA PUERTA", "PRENDER EL PC", "LEER EL MENSAJE", "ENCENDER EL NEÓN",
       "NO DORMIR. MEJORAR", "TOMAR LA FOTO"]
# prompts [E]: (escena, t_in, t_press, texto)
PROMPTS = [(0, 0.5, 1.0, "ABRIR PUERTA"), (1, 0.4, 1.0, "PRENDER PC"),
           (2, 1.2, 1.75, "RESPONDER"), (3, 0.45, 1.05, "ENCENDER NEÓN"),
           (4, 0.3, 0.95, "DESCANSAR"), (4, 1.15, 1.7, "MEJORAR"), (5, 0.25, 1.35, "TOMAR FOTO")]
PRESS_T = [STARTS[s] + tp for s, ti, tp, _ in PROMPTS]


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def ease(t): t = clamp(t); return 1 - (1 - t) ** 3
def smooth(t): t = clamp(t); return t * t * (3 - 2 * t)
def lerp(a, b, t): return a + (b - a) * t
def lerpc(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


_f = {}
def F(name, size):
    size = max(6, int(size)); k = (name, size)
    if k not in _f: _f[k] = ImageFont.truetype(FONTS[name], size)
    return _f[k]


_g = {}
def vbg(stops):
    """Fondo con degradado vertical a resolución de supersampling."""
    key = tuple((p, c) for p, c in stops)
    if key not in _g:
        ys = np.linspace(0, 1, H * S)
        arr = np.stack([np.interp(ys, [s[0] for s in stops], [s[1][c] for s in stops]) for c in range(3)], axis=1)
        _g[key] = np.repeat(arr[:, None, :], 8, axis=1).astype(np.uint8)
    return Image.fromarray(_g[key]).resize((W * S, H * S), Image.NEAREST)


def hand(t, seed, amp=1.0):
    """Cámara en mano: balanceo suave, no sacudida."""
    return (amp * (9 * math.sin(6.28 * 0.55 * t + seed) + 5 * math.sin(6.28 * 1.3 * t + seed * 2.1)),
            amp * (7 * math.sin(6.28 * 0.7 * t + seed * 1.7) + 4 * math.sin(6.28 * 1.7 * t + seed * 0.6)))


class R:
    """Lienzo 2x con cámara (zoom + desplazamiento) y paralaje por capa (dp)."""
    def __init__(s, cam, bg):
        s.z, s.dx, s.dy = cam
        s.img, s.d, s.gl, s.ov, s.od = bg, ImageDraw.Draw(bg), [], None, None

    def zl(s, dp): return 1 + (s.z - 1) * dp
    def P(s, x, y, dp=1.0):
        z = s.zl(dp)
        return (((x - 540) * z + 540 + s.dx * dp) * S, ((y - 960) * z + 960 + s.dy * dp) * S)
    def sc(s, dp=1.0): return s.zl(dp) * S
    def poly(s, pts, fill, dp=1.0, outline=None):
        s.d.polygon([s.P(x, y, dp) for x, y in pts], fill=fill, outline=outline)
    def apoly(s, pts, col, a, dp=1.0):
        if s.ov is None:
            s.ov = Image.new("RGBA", s.img.size, (0, 0, 0, 0)); s.od = ImageDraw.Draw(s.ov)
        s.od.polygon([s.P(x, y, dp) for x, y in pts], fill=col + (int(255 * a),))
    def rect(s, x0, y0, x1, y1, fill, dp=1.0, r=0):
        a, b = s.P(x0, y0, dp), s.P(x1, y1, dp)
        if r: s.d.rounded_rectangle([a, b], radius=r * s.sc(dp), fill=fill)
        else: s.d.rectangle([a, b], fill=fill)
    def ell(s, cx, cy, rx, ry, fill, dp=1.0):
        a, b = s.P(cx - rx, cy - ry, dp), s.P(cx + rx, cy + ry, dp)
        s.d.ellipse([a, b], fill=fill)
    def line(s, pts, fill, w, dp=1.0):
        s.d.line([s.P(x, y, dp) for x, y in pts], fill=fill, width=max(1, int(w * s.sc(dp))), joint="curve")
    def text(s, x, y, txt, font, size, fill, dp=1.0, anchor="mm", stroke=0, sfill=None):
        s.d.text(s.P(x, y, dp), txt, font=F(font, size * s.sc(dp)), fill=fill, anchor=anchor,
                 stroke_width=int(stroke * s.sc(dp)), stroke_fill=sfill)
    def glow(s, x, y, rx, ry, col, a, dp=1.0):
        if a > 0.01: s.gl.append((s.P(x, y, dp), rx * s.zl(dp), ry * s.zl(dp), col, a))
    def paste(s, im, cx, cy, w, dp=1.0):
        k = w * s.sc(dp) / im.width
        r = im.resize((max(2, int(im.width * k)), max(2, int(im.height * k))), Image.BILINEAR)
        x, y = s.P(cx, cy, dp)
        s.img.paste(r, (int(x - r.width / 2), int(y - r.height / 2)), r if r.mode == "RGBA" else None)

    def finish(s):
        img = s.img
        if s.ov is not None:
            img = Image.alpha_composite(img.convert("RGBA"), s.ov).convert("RGB")
        img = img.reduce(S)
        gw, gh = W // 4, H // 4
        cv = Image.new("RGB", (gw, gh))
        for (px, py), rx, ry, col, a in s.gl:
            t = Image.new("RGB", (gw, gh)); td = ImageDraw.Draw(t)
            cx, cy = px / S / 4, py / S / 4
            td.ellipse([cx - rx / 4, cy - ry / 4, cx + rx / 4, cy + ry / 4], fill=tuple(int(c * a) for c in col))
            cv = ImageChops.add(cv, t)
        if s.gl:
            cv = cv.filter(ImageFilter.GaussianBlur(11)).resize((W, H), Image.BICUBIC)
            img = ImageChops.screen(img, cv)
        return img


# ---------------- activos ----------------
SIM = Image.open(os.path.join(ROOT, "img", "simbolo.webp")).convert("RGBA")
_ps = {}
def poster(name, w, ang):
    k = (name, w, ang)
    if k not in _ps:
        im = Image.open(os.path.join(ROOT, "posters", name + ".jpg")).convert("RGB")
        im = im.resize((int(w * 1.4), int(im.height * w * 1.4 / im.width)), Image.LANCZOS)
        im = Image.blend(im, Image.new("RGB", im.size, (58, 36, 70)), 0.28)  # unifica y baja saturación
        a = Image.new("L", im.size, 255)
        rgba = im.convert("RGBA"); rgba.putalpha(a)
        _ps[k] = rgba.rotate(ang, expand=True, resample=Image.BICUBIC)
    return _ps[k]

SELFIE = Image.open(os.path.join(HERE, "ref_selfie.jpg")).convert("RGB")
_selfie = None
def selfie_img():
    global _selfie
    if _selfie is None:
        c = SELFIE.crop((0, 320, 1080, 1700))                   # sin barras negras del video viejo
        c = c.resize((int(c.width * 1.42), int(c.height * 1.42)), Image.LANCZOS)
        c = c.crop(((c.width - W) // 2 - 10, 0, (c.width - W) // 2 - 10 + W, c.height))
        cv = Image.new("RGB", (W, H), (20, 14, 30)); cv.paste(c, (0, (H - c.height) // 2 + 40))
        m = Image.new("L", (W, H), 0); md = ImageDraw.Draw(m)
        md.rectangle([0, (H - c.height) // 2 + 120, W, (H + c.height) // 2 - 60], fill=255)
        _selfie = cv
    return _selfie

_rng = random.Random(7)
SKY_FAR = [(x, _rng.randint(50, 100), _rng.randint(120, 330)) for x in range(130, 960, 80)]
SKY_NEAR = [(x, _rng.randint(60, 120), _rng.randint(180, 430)) for x in range(110, 980, 105)]


# =================== ESCENAS ===================
def sc_door(ts):
    a = ease((ts - 1.05) / 0.95)
    z = 1.06 + 0.40 * smooth(ts / 2.8) ** 1.5
    r = R((z, *hand(ts, 1.0, 0.8)), vbg([(0, (30, 23, 44)), (1, (18, 14, 28))]))
    r.poly([(-500, -500), (330, 430), (330, 1450), (-500, 2400)], (50, 37, 68))        # pared izq
    r.poly([(1580, -500), (750, 430), (750, 1450), (1580, 2400)], (42, 31, 60))        # pared der
    r.poly([(-500, -500), (1580, -500), (750, 430), (330, 430)], (26, 20, 40))         # techo
    r.poly([(-500, 2400), (1580, 2400), (750, 1450), (330, 1450)], (60, 43, 68))       # piso
    r.poly([(440, 1450), (640, 1450), (800, 2400), (280, 2400)], (92, 56, 88))         # alfombra
    # cuadros (perspectiva)
    for pts, inner in [([(60, 720), (230, 640), (230, 880), (60, 1000)], PEACH),
                       ([(1020, 720), (850, 640), (850, 880), (1020, 1000)], TEAL)]:
        r.poly(pts, (24, 18, 34))
        cx = sum(p[0] for p in pts) / 4; cy = sum(p[1] for p in pts) / 4
        r.poly([(cx + (x - cx) * 0.78, cy + (y - cy) * 0.78) for x, y in pts], lerpc(inner, (60, 40, 70), 0.35))
    for sx in (195, 885):                                                              # apliques
        r.ell(sx, 560, 14, 20, (255, 214, 160)); r.glow(sx, 560, 150, 190, PEACH, 0.30)
    # habitación detrás de la puerta
    warm = lerpc((14, 10, 20), (255, 198, 148), a)
    r.rect(330, 430, 750, 1450, warm)
    if a > 0.02:
        r.rect(330, 1080, 750, 1450, lerpc(warm, (170, 84, 112), 0.55))
        r.rect(470, 640, 610, 900, lerpc(warm, (255, 238, 200), 0.8))
        r.line([(540, 640), (540, 900)], lerpc(warm, (150, 90, 100), 0.7), 6)
        r.ell(700, 1000, 18, 60, lerpc(warm, (60, 40, 60), 0.8))                       # silueta planta
    xr = 330 + 420 * (1 - 0.9 * a); y0 = 430 + 60 * a; y1 = 1450 - 60 * a
    def dp_(u, v):
        top = lerp(430, y0, u); bot = lerp(1450, y1, u)
        return (330 + (xr - 330) * u, top + (bot - top) * v)
    r.poly([(330, 430), (xr, y0), (xr, y1), (330, 1450)], (96, 68, 94))
    for u0, v0, u1, v1 in [(0.14, 0.07, 0.86, 0.44), (0.14, 0.52, 0.86, 0.93)]:
        r.poly([dp_(u0, v0), dp_(u1, v0), dp_(u1, v1), dp_(u0, v1)], (112, 80, 106))
    hx, hy = dp_(0.88, 0.52); r.ell(hx, hy, 11, 11, GOLD)
    r.poly([(320, 420), (760, 420), (760, 440), (320, 440)], (30, 22, 42))             # marco
    r.glow(540, 1450, 520 * (0.3 + a), 640 * (0.3 + a), WARM, 0.55 * a)                # luz en el piso
    r.glow(540, 1460, 420, 70, (255, 190, 130), 0.5 * (1 - a))                          # rayo bajo la puerta
    r.glow(540, 220, 600, 160, (255, 170, 140), 0.18)
    return r.finish()


def sc_desk(ts):
    on = smooth((ts - 1.0) / 0.45)
    fl = on * (0.82 + 0.18 * math.sin(ts * 60)) if ts < 1.7 else on
    z = 1.07 + 0.14 * smooth(ts / 2.6)
    hx, hy = hand(ts, 2.3, 1.0)
    r = R((z, hx, hy - 10 * smooth(ts / 2.4)), vbg([(0, (42, 31, 60)), (0.6, (31, 24, 48)), (1, (20, 15, 32))]))
    # tira LED + estante
    r.rect(40, 468, 1040, 486, lerpc((60, 40, 70), PINK, 0.9), 0.7)
    r.glow(540, 478, 600, 80, PINK, 0.50, 0.7)
    r.rect(60, 250, 360, 262, (60, 44, 74), 0.7); r.rect(700, 330, 1000, 342, (60, 44, 74), 0.7)
    for i, (x, h) in enumerate([(100, 90), (160, 60), (230, 100), (770, 70), (840, 110), (930, 80)]):
        yb = 250 if x < 400 else 330
        r.rect(x, yb - h, x + 46, yb, lerpc((70, 52, 88), (120, 70, 110), (i % 3) / 3), 0.7, r=6)
    # escritorio
    r.poly([(-300, 1240), (1380, 1240), (1560, 1560), (-480, 1560)], (56, 40, 60))
    r.line([(-300, 1240), (1380, 1240)], (130, 92, 124), 5)
    r.rect(-500, 1560, 1580, 2500, (26, 20, 34))
    # soportes
    for x in (520, 560):
        r.poly([(x - 30, 930), (x + 30, 930), (x + 46, 1240), (x - 46, 1240)], (22, 18, 30))
    # pantallas
    def screen(quad, base):
        r.poly(quad, (12, 10, 18))
        tl, tr, br, bl = quad
        def q(u, v):
            t = (lerp(tl[0], tr[0], u), lerp(tl[1], tr[1], u)); b = (lerp(bl[0], br[0], u), lerp(bl[1], br[1], u))
            return (lerp(t[0], b[0], v), lerp(t[1], b[1], v))
        inner = [q(.03, .04), q(.97, .04), q(.97, .96), q(.03, .96)]
        r.poly(inner, lerpc((9, 8, 14), base, fl))
        return q
    qc = screen([(300, 560), (780, 560), (780, 930), (300, 930)], (36, 58, 84))
    ql = screen([(70, 600), (275, 565), (275, 925), (70, 905)], (58, 40, 78))
    qr = screen([(805, 565), (1010, 600), (1010, 905), (805, 925)], (30, 50, 70))
    if fl > 0.05:
        for k in range(8):                                                            # barras que suben
            h = (0.18 + 0.5 * abs(math.sin(k * 1.31 + 0.4))) * ease((ts - 1.25 - 0.05 * k) / 0.7)
            u0 = 0.08 + k * 0.105
            r.poly([qc(u0, 0.86 - h), qc(u0 + 0.075, 0.86 - h), qc(u0 + 0.075, 0.86), qc(u0, 0.86)],
                   lerpc(TEAL, PINK, k / 7))
        pts = [qc(0.08 + i * 0.1, 0.55 - 0.32 * smooth((ts - 1.2) / 1.0) * i / 8 - 0.05 * math.sin(i * 1.7)) for i in range(9)]
        r.line(pts, (240, 240, 250), 5)
        r.text(540, 640, "+312%", "inter", 46, lerpc((0, 0, 0), (170, 240, 230), fl))
        for k in range(3):                                                            # timeline de edición
            for j in range(4):
                u0 = 0.08 + j * 0.22 + (k % 2) * 0.05
                r.poly([ql(u0, 0.22 + k * .22), ql(u0 + .18, .22 + k * .22), ql(u0 + .18, .36 + k * .22), ql(u0, .36 + k * .22)],
                       lerpc(PINK, PEACH, ((j + k) % 4) / 3))
        for k in range(9):                                                            # líneas de código
            w = 0.25 + 0.55 * abs(math.sin(k * 2.3 + 1))
            r.poly([qr(.08, .1 + k * .09), qr(.08 + w, .1 + k * .09), qr(.08 + w, .15 + k * .09), qr(.08, .15 + k * .09)],
                   lerpc(TEAL, (200, 200, 230), (k % 3) / 2))
    r.glow(540, 880, 640, 400, TEAL, 0.34 * fl)
    r.glow(170, 760, 260, 300, PINK, 0.20 * fl)
    # teclado RGB + mouse
    r.poly([(290, 1300), (790, 1300), (830, 1400), (250, 1400)], (22, 18, 30))
    for row in range(3):
        for kx in range(14):
            x0 = 305 + kx * 34 + row * 6; y0_ = 1312 + row * 28
            col = lerpc((50, 40, 70), [PINK, TEAL, PEACH][(kx + row + int(ts * 6)) % 3], 0.55 + 0.45 * on)
            r.rect(x0, y0_, x0 + 26, y0_ + 20, col, r=4)
    r.ell(900, 1350, 36, 24, (24, 18, 34)); r.glow(900, 1350, 90, 50, PINK, 0.3 * on)
    r.rect(120, 1290, 190, 1360, (70, 52, 80), r=10)                                  # taza
    r.glow(540, 1300, 520, 120, PINK, 0.18 * on)
    # silla en primer plano
    r.poly([(150, 2500), (230, 1700), (850, 1700), (930, 2500)], (20, 14, 28), 1.25)
    r.ell(540, 1700, 330, 120, (28, 20, 38), 1.25)
    r.line([(230, 1700), (150, 2500)], (110, 70, 110), 4, 1.25)
    return r.finish()


def sc_window(ts):
    z = 1.08 + 0.10 * smooth(ts / 2.5)
    r = R((z, *hand(ts, 3.7, 0.9)), vbg([(0, DUSK), (0.30, (160, 84, 130)), (0.52, ROSE), (0.62, PEACH), (1, (60, 40, 80))]))
    r.glow(540, 1040, 720, 440, PEACH, 0.60, 0.3)
    r.ell(540, 1040, 170, 170, (255, 224, 164), 0.3)
    for k in range(22):                                                               # mar + reflejo
        pass
    r.rect(-200, 1090, 1300, 1500, lerpc((130, 76, 122), (74, 52, 98), 0.4), 0.35)
    for i in range(14):
        wv = 60 + 160 * (1 - i / 14) * (0.7 + 0.3 * math.sin(ts * 3 + i))
        yv = 1100 + i * 26
        r.rect(540 - wv / 2, yv, 540 + wv / 2, yv + 6, lerpc((255, 220, 170), (150, 90, 130), i / 14), 0.35)
    for x, w_, h in SKY_FAR:                                                          # skyline lejano
        r.rect(x, 1090 - h, x + w_, 1092, (166, 92, 128), 0.45)
    for x, w_, h in SKY_NEAR:                                                         # skyline cercano
        r.rect(x, 1100 - h, x + w_, 1500, (92, 58, 104), 0.7)
        for wy in range(1100 - h + 24, 1090, 46):
            for wx in range(x + 12, x + w_ - 14, 26):
                if (wx * 7 + wy * 3) % 5 < 2: r.rect(wx, wy, wx + 10, wy + 16, (255, 214, 150), 0.7)
    # palmeras
    def palm(bx, tx, ty, dp, sway):
        r.line([(bx, 1560), ((bx + tx) / 2 + 40, (1560 + ty) / 2), (tx, ty)], (28, 18, 40), 22, dp)
        for ang in range(-80, 260, 48):
            a_ = math.radians(ang + sway)
            ex, ey = tx + math.cos(a_) * 250, ty + math.sin(a_) * 140 + 70
            r.poly([(tx, ty), (tx + math.cos(a_ - .22) * 150, ty + math.sin(a_ - .22) * 80 - 30), (ex, ey),
                    (tx + math.cos(a_ + .22) * 150, ty + math.sin(a_ + .22) * 80 + 10)], (30, 20, 44), dp)
    palm(930, 820, 640, 0.95, 4 * math.sin(ts * 2.0))
    palm(210, 330, 760, 0.85, -4 * math.sin(ts * 1.7 + 1))
    # marco de ventana
    for rc in [(-400, -400, 1480, 280), (-400, 280, 130, 1560), (950, 280, 1480, 1560), (-400, 1520, 1480, 2500)]:
        r.rect(*rc, (36, 27, 50))
    r.rect(130, 280, 950, 300, (60, 44, 78)); r.rect(130, 1500, 950, 1520, (70, 52, 86))
    r.rect(526, 300, 554, 1500, (40, 30, 56)); r.rect(130, 880, 950, 904, (40, 30, 56))
    # cortina que se mueve
    for k in range(5):
        wv = 18 * math.sin(ts * 2.4 + k * 0.9)
        x0 = 130 + k * 46 + wv
        r.poly([(x0, 280), (x0 + 50, 280), (x0 + 70 + wv * 1.6, 1500), (x0 + 12 + wv * 1.6, 1500)],
               lerpc((86, 62, 104), (130, 90, 130), (k % 2) * 0.6), 1.05)
    # repisa: maceta
    r.poly([(700, 1520), (840, 1520), (820, 1640), (720, 1640)], (96, 60, 84), 1.1)
    for ang in (-70, -40, -10, 20, 50):
        a_ = math.radians(ang - 90)
        r.line([(770, 1520), (770 + math.cos(a_) * 150, 1520 + math.sin(a_) * 150)], (44, 96, 84), 14, 1.1)
    for i in range(5):                                                                # pájaros
        bx = (200 + ts * 110 + i * 130) % 1100 - 60; by = 520 + 40 * math.sin(ts * 4 + i) + i * 34
        r.line([(bx - 16, by), (bx, by + 8 * math.sin(ts * 12 + i)), (bx + 16, by)], (50, 30, 60), 4, 0.5)
    # notificación del teléfono (capa fija)
    pop = ease((ts - 0.3) / 0.4) * (1 - 0)
    if pop > 0.01:
        yy = 440 + (1 - pop) * -260
        r.rect(70, yy, 1010, yy + 190, (22, 18, 34), 0, r=34)
        r.rect(70, yy, 1010, yy + 190, (26, 21, 40), 0, r=34)
        r.ell(150, yy + 95, 52, 52, (14, 12, 22), 0); r.paste(SIM, 150, yy + 95, 92, 0)
        r.text(236, yy + 58, "KAIZEN STUDIO", "inter", 30, (240, 240, 250), 0, anchor="lm")
        r.text(236, yy + 112, "La marca no crece perfecta.", "sora", 33, (255, 255, 255), 0, anchor="lm")
        r.text(236, yy + 152, "Crece mejorando.", "sora", 33, ORANGE, 0, anchor="lm")
        if ts > 1.8:
            k = ease((ts - 1.8) / 0.3)
            r.rect(560, yy + 210, 1010, yy + 300, (255, 255, 255), 0, r=40) if k > 0.5 else None
            if k > 0.5: r.text(785, yy + 255, "Mejorando.", "sora", 36, (22, 18, 34), 0)
    return r.finish()


def sc_wall(ts):
    on = (ts > 1.05) and (ts > 1.5 or int(ts * 22) % 2 == 0)
    z = 1.10 + 0.04 * smooth(ts / 2.4)
    dxs = lerp(95, -95, smooth(ts / 2.4))
    r = R((z, dxs + hand(ts, 4.1, 0.5)[0], hand(ts, 4.1, 0.6)[1]), vbg([(0, (58, 42, 76)), (1, (40, 29, 56))]))
    for x in range(-200, 1300, 90):
        r.rect(x, -300, x + 38, 2400, (62, 45, 80), 0.9)                              # papel tapiz
    layout = [("death-note", 190, 520, 300, -3), ("bleach", 540, 470, 290, 2), ("attack-on-titan", 880, 530, 270, -2),
              ("black-clover", 240, 1230, 290, 3), ("fullmetal-alchemist", 560, 1260, 290, -2), ("dragon-ball", 880, 1240, 250, 3)]
    for i, (n, cx, cy, w_, ang) in enumerate(layout):
        dp = 0.95 + 0.04 * (i % 2)
        im = poster(n, w_, ang)
        r.rect(cx - im.width / 2.8 + 14, cy - im.height / 2.8 + 18, cx + im.width / 2.8 + 14, cy + im.height / 2.8 + 18,
               (26, 18, 36), dp)                                                      # sombra
        r.paste(im, cx, cy, im.width / 1.4, dp)
        r.rect(cx - 26, cy - im.height / 2.8 - 6, cx + 26, cy - im.height / 2.8 + 14, (240, 220, 190), dp)  # cinta
    # neón 改善
    col = (255, 96, 160) if on else (78, 48, 80)
    r.text(540, 830, "改善", "jp", 330, col, 1.0, stroke=16 if on else 0, sfill=(220, 40, 120))
    if on:
        r.text(540, 830, "改善", "jp", 330, (255, 232, 244), 1.0)
        r.glow(540, 830, 560, 280, (255, 70, 150), 0.70); r.glow(540, 830, 300, 160, (255, 160, 190), 0.4)
    r.line([(260, 1010), (820, 1010)], col, 10); r.line([(260, 1010), (820, 1010)], (255, 232, 244) if on else (95, 62, 96), 4)
    r.glow(540, 1010, 360, 60, (255, 80, 150), 0.5 if on else 0)
    r.rect(-200, 1555, 1300, 1575, (100, 72, 110), 1.0)                               # repisa
    r.glow(540, 1565, 700, 50, TEAL, 0.30)
    for i, (x, h) in enumerate([(120, 160), (300, 120), (700, 180), (900, 140)]):      # figuras
        r.ell(x, 1555 - h * 0.78, 38, 38, lerpc((70, 52, 90), (130, 80, 120), i / 3))
        r.rect(x - 34, 1555 - h * 0.6, x + 34, 1555, lerpc((60, 44, 82), (120, 76, 116), i / 3), r=14)
    return r.finish()


def sc_hoodie(ts):
    z = 1.08 + 0.18 * smooth(ts / 2.4)
    r = R((z, *hand(ts, 5.3, 0.9)), vbg([(0, (46, 33, 54)), (1, (22, 16, 30))]))
    r.rect(-200, -300, 1300, 2500, (58, 40, 56))                                      # puerta de closet
    r.rect(150, 240, 930, 1700, (14, 10, 20))                                         # interior
    r.rect(150, 240, 164, 1700, (96, 66, 90)); r.rect(916, 240, 930, 1700, (96, 66, 90))
    r.line([(150, 380), (930, 380)], (150, 130, 150), 8)                              # riel
    sw = 6 * math.sin(ts * 2.2)
    def X(x, y): return x + sw * (y - 380) / 900
    hp = lambda pts: [(X(x, y), y) for x, y in pts]
    r.line([(X(540, 380), 380), (X(540, 440), 440), (X(500, 470), 470)], (170, 160, 170), 7)       # percha
    r.poly(hp([(300, 470), (540, 450), (780, 470), (900, 540), (960, 1060), (850, 1100), (790, 780), (790, 1500),
               (290, 1500), (290, 780), (230, 1100), (120, 1060), (180, 540)]), (40, 26, 52))
    r.ell(X(540, 520), 520, 150, 100, (30, 20, 42))                                   # capucha
    r.ell(X(540, 560), 560, 110, 72, (16, 11, 24))
    r.line(hp([(180, 540), (120, 1060)]), (122, 86, 124), 5); r.line(hp([(900, 540), (960, 1060)]), (70, 52, 88), 4)
    r.line([(X(480, 620), 620), (X(486, 900), 900)], (150, 140, 150), 6); r.line([(X(600, 620), 620), (X(594, 900), 900)], (150, 140, 150), 6)
    cx = X(540, 960)
    glow_k = ease((ts - 1.5) / 0.5) if ts > 1.5 else 0
    r.glow(cx, 960, 340, 340, ORANGE, 0.55 * glow_k)
    r.paste(SIM, cx, 960, 400)
    r.text(cx, 1210, "M A R K", "sora", 56, (226, 220, 236))
    r.text(cx, 1266, "K A I Z E N", "sora", 26, (255, 150, 70))
    r.rect(150, 1700, 930, 1730, (80, 54, 76))
    r.poly([(260, 1740), (400, 1700), (470, 1760), (330, 1810)], (210, 200, 220))                      # tenis
    r.poly([(620, 1745), (770, 1700), (830, 1770), (690, 1815)], (170, 80, 90))
    r.glow(60, 940, 360, 760, PEACH, 0.52)                                            # lámpara a la izquierda
    r.glow(330, 520, 240, 200, (255, 190, 140), 0.25)
    r.poly([(-200, 2500), (-200, 150), (150, 240), (150, 1700)], (50, 34, 52), 1.2)  # borde de la puerta
    return r.finish()


def sc_selfie(ts):
    base = selfie_img()
    z = 1.0 + 0.07 * smooth(ts / 2.5)
    hx, hy = hand(ts, 6.1, 0.6)
    r = R((z, hx, hy), Image.new("RGB", (W * S, H * S), (16, 11, 26)))
    r.paste(base, 540, 960, W * 1.06, 1.0)
    r.glow(540, 900, 520, 620, PINK, 0.16)
    f = 0.0
    if 1.35 <= ts < 2.0: f = (1 - (ts - 1.35) / 0.65) ** 2
    img = r.finish()
    g = np.asarray(img).astype(np.float32); lu = g.mean(axis=2, keepdims=True)
    g = lu + (g - lu) * 0.68; g[..., 0] += 10; g[..., 2] -= 6                 # menos morado, más durazno
    img = Image.fromarray(g.clip(0, 255).astype(np.uint8))
    if ts >= 1.4:                                                                     # congelada tras el flash
        arr = np.asarray(img).astype(np.float32); arr *= 0.80; img = Image.fromarray(arr.clip(0, 255).astype(np.uint8))
    if f > 0.01:
        img = Image.blend(img, Image.new("RGB", (W, H), (255, 244, 230)), clamp(f))
    return img


def sc_end(ts):
    r = R((1.0 + 0.03 * ts, 0, 0), vbg([(0, (24, 17, 38)), (0.55, (44, 24, 52)), (1, (18, 12, 26))]))
    r.glow(540, 800, 620, 620, ORANGE, 0.20 * ease(ts / 0.6))
    k = ease(ts / 0.55)
    r.paste(SIM, 540, 820, 560 * (0.84 + 0.16 * k), 0)
    return r.finish()


SCENES = [sc_door, sc_desk, sc_window, sc_wall, sc_hoodie, sc_selfie, sc_end]


def scene_at(t):
    for i in range(len(DURS) - 1, -1, -1):
        if t >= STARTS[i]: return i, t - STARTS[i]
    return 0, 0.0


# =================== HUD ===================
_ov = {}
def star_pts(cx, cy, R_, r_):
    return [(cx + (R_ if i % 2 == 0 else r_) * math.sin(i * math.pi / 5),
             cy - (R_ if i % 2 == 0 else r_) * math.cos(i * math.pi / 5)) for i in range(10)]

def stext(d, xy, txt, font, size, fill, anchor="la", sp=0, shadow=True):
    f = F(font, size)
    if sp:
        w = sum(d.textlength(c, font=f) + sp for c in txt) - sp
        x, y = xy
        if anchor[0] == "m": x -= w / 2
        elif anchor[0] == "r": x -= w
        for c in txt:
            if shadow: d.text((x + 2, y + 3), c, font=f, fill=(0, 0, 0, 160), anchor="l" + anchor[1])
            d.text((x, y), c, font=f, fill=fill, anchor="l" + anchor[1]); x += d.textlength(c, font=f) + sp
        return
    if shadow: d.text((xy[0] + 2, xy[1] + 3), txt, font=f, fill=(0, 0, 0, 160), anchor=anchor)
    d.text(xy, txt, font=f, fill=fill, anchor=anchor)

PLAN_PATH = [(0.5, 0.92), (0.22, 0.38), (0.5, 0.12), (0.8, 0.3), (0.82, 0.78), (0.5, 0.55), (0.5, 0.55)]

def hud(img, t, i_sc, ts):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    hud_a = 1.0 if i_sc < 6 else clamp(1 - ts / 0.25)
    for y_ in range(0, 420, 4):
        d.rectangle([0, y_, W, y_ + 4], fill=(10, 6, 18, int(120 * (1 - y_ / 420) ** 1.6 * hud_a)))
    if i_sc == 5: mm_a = clamp(1 - ts / 0.2)
    else: mm_a = hud_a
    done = i_sc + (1 if (i_sc < 6 and ts > [1.15, 1.2, 1.9, 1.3, 1.95, 1.6][min(i_sc, 5)]) else 0) if i_sc < 6 else 6
    done = min(done, 6)
    A = lambda c, a=1.0: c + (int(255 * a * hud_a),)
    # objetivo
    if i_sc < 6 or hud_a > 0:
        k = ease(ts / 0.3) if i_sc < 6 else 1
        x0 = 48 - (1 - k) * 80
        stext(d, (x0, 205), "OBJETIVO", "inter", 24, A(ORANGE, k), sp=5)
        stext(d, (x0, 238), OBJ[min(i_sc, 5)], "inter", 40, A((255, 255, 255), k))
        for n in range(6):
            c = A(GREEN, 1) if n < done else A((255, 255, 255), 0.30)
            d.rounded_rectangle([x0 + n * 44, 300, x0 + n * 44 + 34, 310], radius=5, fill=c)
        if i_sc < 6 and 0 < ts - [1.15, 1.2, 1.9, 1.3, 1.95, 1.6][i_sc] < 0.5:
            pts = [(x0 + 0, 346), (x0 + 12, 360), (x0 + 36, 330)]
            d.line(pts, fill=A(GREEN), width=9, joint="curve")
            stext(d, (x0 + 52, 346), "COMPLETADO", "inter", 28, A(GREEN), anchor="lm", sp=3)
    # dinero y estrellas
    money = 0
    for n in range(6):
        if n < done: money += 100000
    if i_sc < 6 and done == i_sc + 1:
        pass
    stext(d, (1032, 205), "$ {:,}".format(money), "inter", 46, A(GREEN), anchor="ra")
    for n in range(5):
        cx = 1032 - 22 - (4 - n) * 46
        fill = A(GOLD) if n < min(done, 5) else A((255, 255, 255), 0.0)
        pts = star_pts(cx, 282, 22, 9)
        if n < min(done, 5): d.polygon(pts, fill=fill)
        d.polygon(pts, outline=A((255, 255, 255), 0.55) if n >= done else None)
        if n == done and i_sc < 5 and int(t * 4) % 2 == 0: d.polygon(pts, outline=A(GOLD))
    # minimapa
    if mm_a > 0:
        mx, my, ms = 52, 1090, 250
        mA = lambda c, a=1.0: c + (int(255 * a * mm_a),)
        d.rounded_rectangle([mx, my, mx + ms, my + ms], radius=44, fill=mA((18, 14, 28), 0.72), outline=mA((255, 255, 255), 0.55), width=3)
        px = lambda u: mx + 22 + u * (ms - 44); py = lambda v: my + 22 + v * (ms - 44)
        d.rectangle([px(.06), py(.04), px(.94), py(.96)], outline=mA((255, 190, 140), 0.55), width=3)
        d.line([(px(.06), py(.55)), (px(.4), py(.55))], fill=mA((255, 190, 140), 0.45), width=3)
        d.line([(px(.62), py(.55)), (px(.94), py(.55)), ], fill=mA((255, 190, 140), 0.45), width=3)
        d.line([(px(.45), py(.96)), (px(.55), py(.96))], fill=mA((18, 14, 28), 1), width=5)
        # objetivo y jugador
        tgt = PLAN_PATH[min(i_sc + 1, 6)] if i_sc < 6 else PLAN_PATH[5]
        d.ellipse([px(tgt[0]) - 9, py(tgt[1]) - 9, px(tgt[0]) + 9, py(tgt[1]) + 9], fill=mA(GOLD))
        p0 = PLAN_PATH[min(i_sc, 6)]; p1 = PLAN_PATH[min(i_sc + 1, 6)]
        u = smooth((ts - 1.2) / 1.2) if i_sc < 6 else 1
        ppos = (lerp(p0[0], p1[0], u) if i_sc < 5 else p0[0], lerp(p0[1], p1[1], u) if i_sc < 5 else p0[1])
        ang = math.atan2(p1[0] - p0[0], -(p1[1] - p0[1]))
        cx_, cy_ = px(ppos[0]), py(ppos[1])
        tri = [(cx_ + 16 * math.sin(ang + a_), cy_ - 16 * math.cos(ang + a_)) for a_ in (0, 2.5, -2.5)]
        d.polygon(tri, fill=mA((255, 255, 255)))
        stext(d, (mx + ms / 2, my + 4), "N", "inter", 22, mA((255, 255, 255), 0.8), anchor="ma", shadow=False)
        d.rounded_rectangle([mx, my + ms + 14, mx + ms * 0.9, my + ms + 24], radius=5, fill=mA(GREEN, 0.9))
        d.rounded_rectangle([mx, my + ms + 30, mx + ms * 0.62, my + ms + 40], radius=5, fill=mA((110, 170, 235), 0.9))
    # prompts [E]
    for (s, ti, tp, label), pt in zip(PROMPTS, PRESS_T):
        if s != i_sc: continue
        if i_sc == 4 and tp == 0.95 and ts > 1.1: label = "NUNCA."
        tin, tout = ti, tp + 0.6
        if not (tin <= ts < tout): continue
        a = ease((ts - tin) / 0.2) * clamp((tout - ts) / 0.2)
        pressed = ts >= tp
        yc = 1430 + (1 - ease((ts - tin) / 0.25)) * 20
        wtxt = d.textlength(label, font=F("inter", 40))
        w_ = int(wtxt + 170); x0 = W // 2 - w_ // 2
        d.rounded_rectangle([x0, yc - 48, x0 + w_, yc + 48], radius=48, fill=(14, 10, 22, int(190 * a)),
                            outline=(255, 255, 255, int(70 * a)), width=2)
        ks = 0.86 if (pressed and ts < tp + 0.15) else 1.0
        kx, kr = x0 + 56, int(30 * ks)
        d.rounded_rectangle([kx - kr, yc - kr, kx + kr, yc + kr], radius=10,
                            fill=(255, 255, 255, int(255 * a)) if not pressed else ORANGE + (int(255 * a),))
        stext(d, (kx, yc + 1), "E", "inter", 38, (14, 10, 22, int(255 * a)) if not pressed else (255, 255, 255, int(255 * a)), anchor="mm", shadow=False)
        col = (255, 255, 255, int(255 * a)) if not (pressed and label == "NUNCA.") else ORANGE + (int(255 * a),)
        stext(d, (kx + 56, yc + 1), label, "inter", 40, col, anchor="lm")
        if not pressed:                                                               # anillo de carga
            ang_ = 360 * clamp((ts - tin) / (tp - tin))
            d.arc([kx - 40, yc - 40, kx + 40, yc + 40], -90, -90 + ang_, fill=ORANGE + (int(255 * a),), width=5)
    # gancho
    if ts < 2.2 and i_sc == 0 and t < 2.05:
        a = ease(t / 0.2) * clamp((2.05 - t) / 0.25)
        stext(d, (W // 2, 540), "SI MI CUARTO", "sora", 92, (255, 255, 255, int(255 * a)), anchor="mm", sp=2)
        stext(d, (W // 2, 640), "FUERA", "sora", 92, (255, 255, 255, int(255 * a)), anchor="mm", sp=2)
        f = F("sora", 210); tx = "GTA VI"; wd = d.textlength(tx, font=f)
        tmp = Image.new("RGBA", (int(wd) + 20, 260), (0, 0, 0, 0)); td = ImageDraw.Draw(tmp)
        td.text((10, 130), tx, font=f, fill=(255, 255, 255, 255), anchor="lm")
        gr = Image.new("RGBA", tmp.size); gd = ImageDraw.Draw(gr)
        for x in range(tmp.width):
            gd.line([(x, 0), (x, tmp.height)], fill=lerpc((255, 130, 190), (255, 170, 90), x / tmp.width) + (255,))
        tmp = ImageChops.multiply(tmp, gr)
        sh = tmp.copy(); sh = ImageChops.multiply(sh, Image.new("RGBA", sh.size, (0, 0, 0, 120)))
        a_ = int(255 * a); mask = tmp.getchannel("A").point(lambda v: int(v * a_ / 255))
        tmp.putalpha(mask); ov.alpha_composite(tmp, (int(W / 2 - tmp.width / 2), 700))
    # misión cumplida
    if i_sc == 5 and ts > 1.95:
        a = ease((ts - 1.95) / 0.3); sc_ = 1.0 + (1 - a) * 0.15
        stext(d, (W // 2, 960), "MISIÓN", "sora", int(150 * sc_), GOLD + (int(255 * a),), anchor="mm", sp=6)
        stext(d, (W // 2, 1090), "CUMPLIDA", "sora", int(150 * sc_), GOLD + (int(255 * a),), anchor="mm", sp=6)
        stext(d, (W // 2, 1190), "MEJORA CONTINUA", "inter", 36, ORANGE + (int(255 * a),), anchor="mm", sp=10)
    # cuenta atrás y marco de cámara en la selfie
    if i_sc == 5:
        a = clamp(1 - max(0, ts - 1.4) / 0.2)
        L, T_, Rr, B = 70, 400, W - 70, 1500
        for (x, y, dx_, dy_) in [(L, T_, 1, 1), (Rr, T_, -1, 1), (L, B, 1, -1), (Rr, B, -1, -1)]:
            d.line([(x, y + dy_ * 80), (x, y), (x + dx_ * 80, y)], fill=(255, 255, 255, int(220 * a)), width=6)
        n = 3 - int(max(0, ts - 0.25) / 0.35)
        if 0.25 <= ts < 1.35 and n >= 1:
            fr = ((ts - 0.25) % 0.35) / 0.35
            stext(d, (W // 2, 880), str(n), "sora", 340, (255, 255, 255, int(220 * (1 - fr * 0.6))), anchor="mm")
        stext(d, (W // 2, 290), "● CÁMARA", "inter", 28, (255, 255, 255, int(230 * a)), anchor="mm", sp=6)
    # CTA final
    if i_sc == 6:
        a = ease((ts - 0.35) / 0.35)
        stext(d, (W // 2, 1230), "COMENTA", "sora", 76, (255, 255, 255, int(255 * a)), anchor="mm", sp=8)
        w_ = 560; yy = 1330
        d.rounded_rectangle([W // 2 - w_ // 2, yy - 62, W // 2 + w_ // 2, yy + 62], radius=62, fill=ORANGE + (int(255 * a),))
        stext(d, (W // 2, yy + 2), "KAIZEN", "sora", 74, (255, 255, 255, int(255 * a)), anchor="mm", sp=10, shadow=False)
        stext(d, (W // 2, 1450), "MEJORA. PRUEBA. APRENDE. REPITE.", "inter", 26, (255, 255, 255, int(190 * a)), anchor="mm", sp=5)
    return Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")


# =================== post / render ===================
_vig = None; _grain = None
def post(img, i):
    global _vig, _grain
    if _vig is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        d_ = np.sqrt(((xx - W / 2) / (W * 0.72)) ** 2 + ((yy - H / 2) / (H * 0.68)) ** 2)
        _vig = (1 - 0.40 * np.clip(d_ - 0.35, 0, 1) ** 1.5)[..., None]
        rg = np.random.RandomState(3)
        _grain = [rg.normal(0, 0.028, (H, W, 1)).astype(np.float32) for _ in range(5)]
    a = np.asarray(img).astype(np.float32) / 255
    lum = a.mean(axis=2, keepdims=True)
    a = lum + (a - lum) * 0.84                                   # menos saturado
    a = a * 0.95 + 0.02
    a[..., 0:1] += lum * 0.025; a[..., 2:3] += (1 - lum) * 0.03   # luces cálidas, sombras frías
    sm = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).resize((W // 8, H // 8)).filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BICUBIC)
    a += np.clip(np.asarray(sm).astype(np.float32) / 255 - 0.5, 0, 1) * 0.28   # bloom suave
    a = a * _vig + _grain[i % 5]
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))


def whip(A, B, p):
    off = int(smooth(p) * W)
    cv = Image.new("RGB", (W, H)); cv.paste(A, (-off, 0)); cv.paste(B, (W - off, 0))
    arr = np.asarray(cv).astype(np.float32); k = int(70 * math.sin(math.pi * p)) + 1
    acc = sum(np.roll(arr, s, axis=1) for s in np.linspace(-k, k, 7).astype(int)) / 7
    return Image.fromarray(acc.clip(0, 255).astype(np.uint8))


def frame(i):
    t = i / FPS
    s, ts = scene_at(t)
    img = None
    for c in range(1, len(DURS)):
        Tc = STARTS[c]
        if abs(t - Tc) < TW:
            A = SCENES[c - 1](t - STARTS[c - 1]); B = SCENES[c](max(0.0, t - Tc))
            img = whip(A, B, (t - (Tc - TW)) / (2 * TW)); break
    if img is None: img = SCENES[s](ts)
    if s == len(DURS) - 1 and t > TOTAL - 0.3:                    # bucle: destello cálido -> arranca la puerta
        img = Image.blend(img, Image.new("RGB", (W, H), (255, 214, 170)), smooth((t - (TOTAL - 0.3)) / 0.3))
    if s == 0 and t < 0.25:
        img = Image.blend(img, Image.new("RGB", (W, H), (255, 214, 170)), 1 - smooth(t / 0.25))
    img = post(img, i)
    return hud(img, t, s, ts).tobytes()


# =================== audio ===================
def build_audio(path):
    sr = 44100; n = int(TOTAL * sr); t = np.arange(n) / sr; rng = np.random.RandomState(1)
    out = np.zeros(n, np.float32)
    def add(sig, at, g=1.0):
        i0 = int(at * sr)
        if i0 >= n: return
        sig = sig[: n - i0]; out[i0:i0 + len(sig)] += sig * g
    def env(L, a=0.005, r=0.2):
        x = np.arange(int(L * sr)) / sr; return np.minimum(x / a, 1) * np.exp(-x / r)
    # cama: acorde Am sostenido + respiración
    for f_, g_ in [(55, .10), (82.4, .06), (110, .05), (164.8, .025)]:
        out += (g_ * np.sin(6.283 * f_ * t) * (0.8 + 0.2 * np.sin(6.283 * 0.25 * t))).astype(np.float32)
    bpm = 112; beat = 60 / bpm
    notes = [220, 261.6, 329.6, 261.6, 392, 329.6, 261.6, 329.6]
    k = 0; tt = 0.0
    while tt < TOTAL:                                             # pulso: bombo, hat y arpegio suave
        xk = np.arange(int(0.22 * sr)) / sr
        add(np.sin(6.283 * (48 + 90 * np.exp(-xk * 30)) * xk) * np.exp(-xk * 9), tt, 0.34)
        add(rng.normal(0, 1, int(0.04 * sr)) * np.exp(-np.arange(int(0.04 * sr)) / sr * 90), tt + beat / 2, 0.035)
        for j in range(2):
            fz = notes[(k * 2 + j) % 8]; L = 0.18
            x = np.arange(int(L * sr)) / sr
            add((np.sin(6.283 * fz * x) + 0.4 * np.sin(6.283 * 2 * fz * x)) * np.exp(-x * 11), tt + j * beat / 2, 0.045)
        tt += beat; k += 1
    for c in range(1, len(DURS)):                                 # whoosh + golpe grave en cada corte
        L = 0.3; x = np.arange(int(L * sr)) / sr
        nz = rng.normal(0, 1, len(x)) * np.sin(math.pi * x / L) ** 2
        nz = np.convolve(nz, np.ones(30) / 30, mode="same")
        add(nz, STARTS[c] - 0.18, 0.28)
        add(np.sin(6.283 * 60 * x) * np.exp(-x * 14), STARTS[c] - 0.02, 0.5)
    for pt in PRESS_T:                                            # blip de interfaz
        add(np.sin(6.283 * 1318 * np.arange(int(.08 * sr)) / sr) * env(.08, .002, .03), pt, 0.20)
        add(np.sin(6.283 * 1760 * np.arange(int(.1 * sr)) / sr) * env(.1, .002, .04), pt + 0.07, 0.16)
    x = np.arange(int(0.45 * sr)) / sr                            # vibración del teléfono
    add(np.sign(np.sin(6.283 * 170 * x)) * (np.sin(6.283 * 22 * x) > 0) * 0.5, STARTS[2] + 0.3, 0.16)
    x = np.arange(int(0.5 * sr)) / sr                             # zumbido de neón
    add(np.sin(6.283 * 100 * x) * np.exp(-x * 6) * (0.6 + 0.4 * np.sign(np.sin(6.283 * 44 * x))), STARTS[3] + 1.05, 0.2)
    x = np.arange(int(0.12 * sr)) / sr                            # obturador
    add(rng.normal(0, 1, len(x)) * np.exp(-x * 40), STARTS[5] + 1.35, 0.35)
    for f_ in (261.6, 329.6, 392, 523.3):                         # acorde de misión cumplida
        L = 1.6; x = np.arange(int(L * sr)) / sr
        add(np.sin(6.283 * f_ * x) * np.minimum(x / 0.05, 1) * np.exp(-x * 1.7), STARTS[5] + 1.95, 0.10)
    out /= max(1e-6, np.abs(out).max()) / 0.85
    fade = np.minimum(1, np.minimum(t / 0.05, (TOTAL - t) / 0.35)); out *= fade
    with wave.open(path, "wb") as w_:
        w_.setnchannels(1); w_.setsampwidth(2); w_.setframerate(sr)
        w_.writeframes((out * 32767).astype(np.int16).tobytes())


if __name__ == "__main__":
    only = os.environ.get("ONLY")                                 # ONLY=t1,t2 -> PNG de prueba
    if only:
        os.makedirs("/tmp/kz", exist_ok=True)
        for tv in only.split(","):
            fi = int(float(tv) * FPS)
            Image.frombytes("RGB", (W, H), frame(fi)).save(f"/tmp/kz/f_{tv}.png")
        sys.exit()
    wav = os.path.join(HERE, "_audio.wav"); build_audio(wav)
    N = int(round(TOTAL * FPS))
    ff = subprocess.Popen(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                           "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                           "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
    with Pool(4) as p:
        for k, fr in enumerate(p.imap(frame, range(N), chunksize=4)):
            ff.stdin.write(fr)
            if k % 60 == 0: print(f"{k}/{N}", flush=True)
    ff.stdin.close(); ff.wait(); os.remove(wav)
    print("OK", OUT)
