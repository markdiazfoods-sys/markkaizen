"""Teaser vertical 9:16 (1080x1920): 32 cortes al beat (128 BPM), color natural, plano completo."""
import subprocess, sys, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

W, H, FPS, BPM, BEATS = 1080, 1920, 30, 128, 32
BEAT = 60 / BPM
NF = round(BEAT * BEATS * FPS)
sheet = Image.open("fuentes/hoja-personaje.png").convert("RGB")

# (caja de recorte en la hoja, centro de foco x,y en fracción)
SRC = {
 "A": ((0, 0, 775, 810),     (.74, .50)),
 "B": ((785, 5, 1020, 360),  (.50, .50)),
 "C": ((1027, 5, 1254, 360), (.50, .50)),
 "D": ((785, 390, 1020, 810),(.50, .50)),
 "E": ((1027, 390, 1254, 810),(.50, .50)),
 "F": ((0, 825, 420, 1254),  (.52, .50)),
 "G": ((430, 825, 850, 1254),(.52, .50)),
 "H": ((855, 825, 1254, 1254),(.52, .50)),
}
imgs = {k: sheet.crop(b) for k, (b, _) in SRC.items()}
order = "A F B G A C H D E A G F B H C D A E F G B H A C D E F G H A".split()
order = (order * 2)[:BEATS]
order[-4:] = ["A"] * 4  # cierre en plano principal

FONT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
def font(s): return ImageFont.truetype(FONT, s)

# texto: (beat inicio, beat fin, líneas, tamaño, posición y)
TEXTS = [
 (0, 4,  ["ASÍ SERÍA", "MARK KAIZEN", "EN GTA VI"], 128, .70),
 (8, 12, ["MEJORA", "CONTINUA"], 150, .70),
 (16, 20, ["VICE CITY"], 170, .70),
 (24, 28, ["NO ES UN", "JUEGO"], 150, .70),
 (28, 32, ["SÍGUEME", "PARA MÁS"], 150, .70),
]

def cover(img, fx, fy, z):
    """Recorte 9:16 que llena todo el cuadro (sin bandas), zoom z, centrado en el foco."""
    iw, ih = img.size
    ch = ih / z; cw = ch * W / H
    if cw > iw: cw = iw; ch = cw * H / W
    cx = min(max(fx * iw, cw / 2), iw - cw / 2)
    cy = min(max(fy * ih, ch / 2), ih - ch / 2)
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return img.resize((W, H), Image.LANCZOS, box=box)

def grade(im, seed):
    # look juego Vice City (PS2): apagado, negros levantados, tinte cálido suave, grano
    im = ImageEnhance.Color(im).enhance(0.58)
    im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=50, threshold=3))
    a = np.asarray(im, dtype=np.float32)
    a = a * 0.90 + 16                                   # negros levantados
    a[..., 0] *= 1.02; a[..., 2] *= 0.96                # cálido leve
    rng = np.random.default_rng(seed)
    a += rng.normal(0, 3.5, a.shape[:2])[..., None]     # grano
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def draw_text(im, lines, size, ypos, t):
    d = ImageDraw.Draw(im)
    f = font(size)
    k = min(1.0, t / 0.12)               # pop de entrada
    f = font(int(size * (0.86 + 0.14 * k)))
    lh = int(size * 1.02)
    y = int(H * ypos - lh * len(lines) / 2)
    for ln in lines:
        w = d.textlength(ln, font=f)
        x = (W - w) / 2
        d.text((x, y), ln, font=f, fill=(255, 255, 255), stroke_width=10, stroke_fill=(0, 0, 0))
        y += lh

def star(d, cx, cy, r, fill):
    import math
    pts=[]
    for i in range(10):
        ang = -math.pi/2 + i*math.pi/5
        rr = r if i % 2 == 0 else r*0.42
        pts.append((cx+rr*math.cos(ang), cy+rr*math.sin(ang)))
    d.polygon(pts, fill=fill, outline=(0,0,0))

def hud(im, b, t):
    d = ImageDraw.Draw(im, "RGBA")
    f = font(40)
    d.text((64, 64), "@MARKKAIZEN", font=f, fill=(255,255,255), stroke_width=4, stroke_fill=(0,0,0))
    # dinero estilo juego, sube con cada beat
    money = "$%08d" % (12500 + b * 1750)
    f2 = font(62); w = d.textlength(money, font=f2)
    d.text((W-64-w, 150), money, font=f2, fill=(214, 226, 168), stroke_width=6, stroke_fill=(0,0,0))
    # nivel de búsqueda: 0 → 5 estrellas a lo largo del vídeo
    lvl = min(5, 1 + b // 6)
    for i in range(5):
        star(d, W-64-34-i*84, 262, 34, (240,240,240,255) if i < lvl else (30,30,30,150))
    # radar abajo-izquierda
    cx, cy, r = 170, H-210, 110
    d.ellipse((cx-r, cy-r, cx+r, cy+r), fill=(20,24,34,170), outline=(0,0,0,255), width=6)
    for k in (r*0.33, r*0.66):
        d.ellipse((cx-k, cy-k, cx+k, cy+k), outline=(120,130,150,90), width=2)
    d.polygon([(cx, cy-18), (cx-12, cy+10), (cx+12, cy+10)], fill=(255,255,255))
    px = cx + int(60*np.sin(t*2.1)); py = cy - 40 + int(30*np.cos(t*1.7))
    d.ellipse((px-8, py-8, px+8, py+8), fill=(210, 80, 90))
    # barra de vida/armadura abajo
    d.rectangle((W-64-300, H-150, W-64, H-130), fill=(0,0,0,170))
    d.rectangle((W-64-300, H-150, W-64-30, H-130), fill=(200,70,80))
    d.rectangle((W-64-300, H-122, W-64, H-102), fill=(0,0,0,170))
    d.rectangle((W-64-300, H-122, W-64-90, H-102), fill=(230,230,230))

ff = subprocess.Popen(
    ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
     "-r", str(FPS), "-i", "-", "-i", sys.argv[1], "-c:v", "libx264", "-preset", "medium", "-crf", "24", "-maxrate", "12M", "-bufsize", "24M",
     "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", sys.argv[2]],
    stdin=subprocess.PIPE)

for fr in range(NF):
    t = fr / FPS
    b = min(int(t / BEAT), BEATS - 1)
    tb = (t - b * BEAT) / BEAT                    # 0..1 dentro del beat
    src = order[b]
    fx, fy = SRC[src][1]
    z = 1.0 + 0.14 * tb + (0.06 if b % 2 else 0)  # empuje de cámara por corte
    if src == "A": z += 0.16                      # recorta el logo GTA del borde izquierdo
    drift = (0.015 if b % 2 else -0.015) * tb
    im = cover(imgs[src], fx + drift, fy, z)
    im = grade(im, fr)
    if tb < 0.08:                                 # flash blanco corto al corte (impacto)
        im = Image.blend(im, Image.new("RGB", (W, H), (255, 255, 255)), 0.18 * (1 - tb / 0.08))
    for (b0, b1, lines, size, yp) in TEXTS:
        if b0 <= b < b1:
            draw_text(im, lines, size, yp, t - b0 * BEAT)
    hud(im, b, t)
    ff.stdin.write(im.tobytes())
ff.stdin.close(); ff.wait()
