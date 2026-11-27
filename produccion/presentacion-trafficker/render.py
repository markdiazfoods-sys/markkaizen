#!/usr/bin/env python3
"""MARK KAIZEN · Presentación Trafficker Digital · 9:16 (1080x1920, 30 fps, 36 s).
Uso: python3 render.py [salida.mp4] [--frame SEGUNDO frame.png]
Requiere: numpy, Pillow, ffmpeg. Fuentes, fotos y capturas salen del repo.
Capturas de la web: assets/web-*.png (móvil 430x932 @2x). Regenerar si cambia el sitio."""
import math, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
args = [a for a in sys.argv[1:] if not a.startswith("--")]
OUT = args[0] if args and args[0].endswith(".mp4") else os.path.join(HERE, "mark_kaizen_presentacion-trafficker_9x16.mp4")
W, H, FPS, DUR = 1080, 1920, 30, 36
BG, WHITE, ORANGE = (11, 11, 15), (255, 255, 255), (255, 107, 0)
FD = os.path.join(ROOT, "docs", "fuente", "fuentes")
def font(name, size): return ImageFont.truetype(os.path.join(FD, name), size)
SORA = lambda s: font("Sora-recorte.ttf", s)
INTER = lambda s: font("Inter-recorte.ttf", s)

sym = Image.open(os.path.join(ROOT, "img", "simbolo.webp")).convert("RGBA")
photo = Image.open(os.path.join(ROOT, "img", "hero.jpg")).convert("RGB")
web1 = Image.open(os.path.join(HERE, "assets", "web-1.png")).convert("RGB")
web2 = Image.open(os.path.join(HERE, "assets", "web-2.png")).convert("RGB")

def ease(t):
    t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 4
def clamp(x): return max(0.0, min(1.0, x))
def mix(c, a): return tuple(int(BG[i] + (c[i] - BG[i]) * a) for i in range(3))

def fit_font(d, text, fn, maxw, start):
    s = start
    while s > 20 and d.textlength(text, font=fn(s)) > maxw: s -= 2
    return fn(s)

def text_c(d, y, text, fnt, fill, a=1.0, dy=0, cx=W // 2):
    w = d.textlength(text, font=fnt)
    d.text((cx - w / 2, y + dy), text, font=fnt, fill=mix(fill, a))
    return w

def rounded(img, r):
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, img.size[0] - 1, img.size[1] - 1), r, fill=255)
    return m

def paste_sym(img, size, cx, cy, a=1.0):
    s = sym.resize((size, size), Image.LANCZOS)
    if a < 1: s.putalpha(s.getchannel("A").point(lambda v: int(v * a)))
    img.paste(s, (int(cx - size / 2), int(cy - size / 2)), s)

def light(img, k=1.0):
    g = Image.new("L", (W, H), 0)
    ImageDraw.Draw(g).ellipse((-700, 500, 300, 1500), fill=int(60 * k))
    g = g.filter(ImageFilter.GaussianBlur(160))
    img.paste(Image.new("RGB", (W, H), ORANGE), (0, 0), g)

def caption(d, t, t0, t1, text, y=1330):
    if not (t0 <= t < t1): return
    a = ease((t - t0) / 0.25) * clamp((t1 - t) / 0.2)
    f = INTER(44); lines, cur = [], ""
    for w_ in text.split():
        trial = (cur + " " + w_).strip()
        if d.textlength(trial, font=f) > 880 and cur: lines.append(cur); cur = w_
        else: cur = trial
    lines.append(cur)
    for i, ln in enumerate(lines):
        text_c(d, y + i * 60, ln, f, WHITE, 0.92 * a, dy=(1 - a) * 14)

def tag(d, t, t0, text, y):
    a = ease((t - t0) / 0.35)
    if a <= 0: return
    f = SORA(30)
    text_c(d, y, text, f, ORANGE, a, dy=(1 - a) * 20)

def cover(src, w, h, zoom=1.0, fy=0.0):
    """Recorta src para llenar w x h (fy: 0 arriba, 1 abajo) con zoom."""
    sc = max(w / src.width, h / src.height) * zoom
    im = src.resize((int(src.width * sc) + 1, int(src.height * sc) + 1), Image.LANCZOS)
    x = (im.width - w) // 2
    y = int((im.height - h) * fy)
    return im.crop((x, y, x + w, y + h))

def phone(img, shot, cx, y, w, zoom=1.0, fy=0.0, a=1.0):
    h = int(w * 2.0)
    scr = cover(shot, w, h, zoom, fy)
    frame = Image.new("RGB", (w + 28, h + 28), (30, 30, 36))
    frame.paste(scr, (14, 14), rounded(scr, 38))
    m = rounded(frame, 52)
    if a < 1: m = m.point(lambda v: int(v * a))
    bw, bh = frame.width + 6, frame.height + 6
    img.paste(Image.new("RGB", (bw, bh), ORANGE), (int(cx - frame.width / 2) - 3, y - 3),
              rounded(Image.new("RGB", (bw, bh)), 55).point(lambda v: int(v * 0.9 * a)))
    img.paste(frame, (int(cx - frame.width / 2), y), m)

# ───────── escenas ─────────
def hook(img, d, t):
    a = ease(t / 0.4)
    paste_sym(img, 260, W // 2, 520, a)
    f1 = SORA(92)
    text_c(d, 760, "¿Buscas un", f1, WHITE, ease((t - 0.2) / 0.4), dy=(1 - ease((t - 0.2) / 0.4)) * 40)
    text_c(d, 870, "Trafficker Digital", fit_font(d, "Trafficker Digital", SORA, 900, 92), ORANGE,
           ease((t - 0.5) / 0.4), dy=(1 - ease((t - 0.5) / 0.4)) * 40)
    text_c(d, 980, "que venda de verdad?", SORA(72), WHITE, ease((t - 0.8) / 0.4), dy=(1 - ease((t - 0.8) / 0.4)) * 40)
    d.rectangle((270, 1100, 270 + 540 * ease((t - 1.2) / 0.6), 1108), fill=ORANGE)

def presenter(img, d, t):
    pw, ph = 900, 1060
    p = cover(photo, pw, ph, 1.0 + 0.08 * clamp(t / 6.0), 0.15)
    a = ease(t / 0.5)
    ring = Image.new("RGB", (pw + 12, ph + 12), ORANGE)
    img.paste(ring, ((W - pw) // 2 - 6, 140 - 6), rounded(ring, 60).point(lambda v: int(v * a)))
    img.paste(p, ((W - pw) // 2, 140), rounded(p, 54).point(lambda v: int(v * a)))
    # franja inferior
    f = fit_font(d, "MARK DÍAZ", SORA, 900, 110)
    text_c(d, 1500, "MARK DÍAZ", f, WHITE, ease((t - 0.4) / 0.4), dy=(1 - ease((t - 0.4) / 0.4)) * 40)
    text_c(d, 1625, "Trafficker Digital · Lima, Perú", SORA(44), ORANGE, ease((t - 0.8) / 0.4))
    text_c(d, 1690, "Paid Media · Performance · Ecommerce", INTER(34), WHITE, 0.8 * ease((t - 1.1) / 0.4))

def web(img, d, t, dur):
    a = ease(t / 0.45)
    cross = clamp((t - dur / 2 + 0.3) / 0.6)
    shot = Image.blend(web1, web2.resize(web1.size), ease(cross)) if cross > 0 else web1
    phone(img, shot, W // 2, 110 + int((1 - a) * 60), 520, 1.0 + 0.04 * clamp(t / dur), 0.0, a)
    tag(d, t, 0.4, "MI PORTAFOLIO WEB", 1500)
    text_c(d, 1555, "markkaizen", SORA(60), WHITE, ease((t - 0.6) / 0.4))
    text_c(d, 1640, "Casos con números · CV · contacto directo", INTER(32), WHITE, 0.8 * ease((t - 0.9) / 0.4))

def metrics(img, d, t):
    items = [("5.13", "ROAS · Septiembre 2026", "S/3,048.95 invertidos · Meta Ads"),
             ("131", "compras atribuidas", "S/15,648.01 de valor atribuido"),
             ("13.89", "ROAS · Flores Amarillas", "85 compras · CPA S/8.01 · S/680.90")]
    text_c(d, 220, "RESULTADOS · FLORELIMA ATELIER", SORA(34), ORANGE, ease(t / 0.4))
    seg = 3.2
    for i, (num, lab, sub) in enumerate(items):
        lt = t - 0.5 - i * seg
        if not (-0.05 <= lt < seg + 0.1): continue
        a = ease(lt / 0.4) * clamp((seg - lt) / 0.3) if i < 2 else ease(lt / 0.4)
        cnt = ease(lt / 1.1)
        val = float(num) * cnt
        shown = f"{val:.2f}" if "." in num else f"{int(round(val))}"
        f = fit_font(d, num, SORA, 900, 320)
        text_c(d, 620, shown, f, ORANGE, a, dy=(1 - a) * 60)
        text_c(d, 1010, lab, fit_font(d, lab, SORA, 940, 56), WHITE, a, dy=(1 - a) * 30)
        text_c(d, 1100, sub, INTER(38), WHITE, 0.85 * a)
        d.rectangle((270, 1190, 270 + 540 * ease((lt - 0.3) / 0.5), 1198), fill=mix(ORANGE, a))
    # progreso
    for i in range(3):
        on = t - 0.5 >= i * seg
        d.rounded_rectangle((470 + i * 50, 1350, 504 + i * 50, 1358), 4, fill=ORANGE if on else (50, 50, 58))

def skills(img, d, t):
    text_c(d, 260, "HERRAMIENTAS", SORA(34), ORANGE, ease(t / 0.4))
    text_c(d, 330, "Lo que domino", SORA(84), WHITE, ease((t - 0.1) / 0.4), dy=(1 - ease((t - 0.1) / 0.4)) * 40)
    chips = ["Meta Ads", "Google Ads", "TikTok Ads", "GA4", "Google Tag Manager", "ROAS · CPA · CTR",
             "Testing A/B", "Dashboards", "Canva · CapCut"]
    f = INTER(40); y = 520; row, rw = [], 0; rows = []
    for c in chips:
        w = d.textlength(c, font=f) + 64
        if rw + w > 920 and row: rows.append((row, rw)); row, rw = [], 0
        row.append((c, w)); rw += w + 20
    rows.append((row, rw))
    k = 0
    for row, rw in rows:
        x = (W - (rw - 20)) / 2
        for c, w in row:
            a = ease((t - 0.5 - k * 0.18) / 0.35); k += 1
            if a > 0:
                yy = y + (1 - a) * 30
                d.rounded_rectangle((x, yy, x + w, yy + 84), 42, outline=mix(ORANGE, a), width=3)
                d.text((x + 32, yy + 18), c, font=f, fill=mix(WHITE, a))
            x += w + 20
        y += 120

def cta(img, d, t):
    paste_sym(img, 200, W // 2, 420, ease(t / 0.4))
    text_c(d, 600, "¿Hablamos?", SORA(130), WHITE, ease((t - 0.2) / 0.4), dy=(1 - ease((t - 0.2) / 0.4)) * 40)
    text_c(d, 790, "Disponible para proyectos", SORA(46), ORANGE, ease((t - 0.5) / 0.4))
    for i, s in enumerate(["markdiazfoods@gmail.com", "TikTok @markkaizen_", "969 722 522 · Lima, Perú"]):
        a = ease((t - 0.8 - i * 0.2) / 0.4)
        text_c(d, 930 + i * 90, s, fit_font(d, s, INTER, 900, 48), WHITE, a, dy=(1 - a) * 20)
    pulse = 1 + 0.03 * math.sin(t * 6)
    w, h = int(760 * pulse), int(120 * pulse)
    a = ease((t - 1.4) / 0.4)
    d.rounded_rectangle((W / 2 - w / 2, 1280 - h / 2, W / 2 + w / 2, 1280 + h / 2), 60, fill=mix(ORANGE, a))
    f = SORA(48); tw = d.textlength("Descarga mi CV en la web", font=f)
    d.text((W / 2 - tw / 2, 1280 - 30), "Descarga mi CV en la web", font=f, fill=mix(BG, a))

SCENES = [  # (inicio, fin, fn, subtítulo)
    (0, 4, hook, None),
    (4, 11, presenter, "Soy Mark Díaz. Planifico, lanzo y optimizo campañas con datos, y le pongo cabeza creativa a cada pieza."),
    (11, 19, None, None),  # web
    (19, 29, metrics, None),
    (29, 33, skills, None),
    (33, 36, cta, None),
]
CAPTIONS = [(11.3, 15, "Mi página web reúne casos reales, servicios y mi CV en un solo lugar."),
            (15.2, 18.8, "Cada proyecto con inversión, compras, CPA y ROAS.")]

def frame(t):
    img = Image.new("RGB", (W, H), BG); light(img, 0.9 + 0.1 * math.sin(t * 1.5))
    d = ImageDraw.Draw(img)
    for t0, t1, fn, sub in SCENES:
        if t0 <= t < t1:
            lt = t - t0
            fade = clamp(lt / 0.01) * clamp((t1 - t) / 0.25)
            layer = Image.new("RGB", (W, H), BG); light(layer, 1.0); ld = ImageDraw.Draw(layer)
            if fn is None: web(layer, ld, lt, t1 - t0)
            else: fn(layer, ld, lt)
            if sub: caption(ld, lt, 0.8, t1 - t0 - 0.2, sub, y=1225)
            if t0 == 11:
                for c0, c1, s in CAPTIONS: caption(ld, t, c0, c1, s, y=1250)
            off = {hook: 260, metrics: 200, skills: 200, cta: 120}.get(fn, 0)
            if off: layer = ImageChops.offset(layer, 0, off)
            if fade < 1: layer = Image.blend(img, layer, fade)
            img = layer
            break
    # barra de progreso
    ImageDraw.Draw(img).rectangle((0, H - 8, int(W * t / DUR), H), fill=ORANGE)
    return img

def main():
    if "--frame" in sys.argv:
        i = sys.argv.index("--frame"); frame(float(sys.argv[i + 1])).save(sys.argv[i + 2]); return
    cuts = [4, 11, 19, 29, 33]
    expr = "+".join(f"0.30*sin(2*PI*55*(t-{c}))*exp(-6*(t-{c}))*gte(t,{c})*lt(t,{c}+1)" for c in cuts)
    expr += "+0.25*sin(2*PI*55*t)*exp(-6*t)*lt(t,1)+0.03*sin(2*PI*110*t)"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=44100:d={DUR}",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", "-c:a", "aac", "-b:a", "128k",
           "-shortest", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(DUR * FPS):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()
    print("OK", OUT)

if __name__ == "__main__":
    main()
