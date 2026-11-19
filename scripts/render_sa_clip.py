"""Clip 9:16 estilo pantalla de carga GTA San Andreas (balanceo de caminata, paneo,
grano, vineta, estrellas que se encienden). Uso: render_sa_clip.py slide.jpg out.mp4"""
import sys, math, subprocess
import numpy as np
from PIL import Image

src, out = sys.argv[1], sys.argv[2]
W, H, FPS, DUR = 1080, 1920, 30, 9.0
N = int(FPS * DUR)
im = Image.open(src).convert("RGB")
sw, sh = im.size
S = W / sw                             # escala base: el slide completo entra en el encuadre
PAD = 90                               # borde reflejado para cubrir el movimiento de camara
big0 = np.asarray(im.resize((round(sw * S), round(sh * S)), Image.LANCZOS))
big = Image.fromarray(np.pad(big0, ((PAD, PAD), (PAD, PAD), (0, 0)), mode='reflect'))
bw, bh = big.size

# --- estrellas: apagadas (gris) en la base, encendidas por mascara ---
a = np.asarray(big).astype(np.float32)
y0, y1 = round(1385 * S) + PAD, round(1460 * S) + PAD
stars_x = [(519, 566), (588, 633), (656, 703), (724, 772), (792, 839)]
base = a.copy()
masks = []
for (xa, xb) in stars_x:
    xa, xb = round((xa - 4) * S) + PAD, round((xb + 5) * S) + PAD
    reg = a[y0:y1, xa:xb]
    m = ((reg[..., 0] > 170) & (reg[..., 1] > 120) & (reg[..., 2] < 140)).astype(np.float32)
    # suavizar mascara
    mm = np.zeros(a.shape[:2], np.float32); mm[y0:y1, xa:xb] = m
    masks.append(mm)
    lum = reg.mean(axis=2, keepdims=True)
    gray = np.concatenate([lum * 0.75] * 3, axis=2)
    base[y0:y1, xa:xb] = reg * (1 - m[..., None]) + gray * m[..., None]
light_t = [2.2 + i * 0.85 for i in range(5)]   # segundos en que se enciende cada una

# --- vineta y grano ---
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
d = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
vig = np.clip(1 - 0.55 * np.clip(d - 0.45, 0, None) ** 1.6, 0.25, 1)[..., None]
rng = np.random.default_rng(7)

ff = subprocess.Popen(
    ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
     "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "medium",
     "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out],
    stdin=subprocess.PIPE)

for f in range(N):
    t = f / FPS
    # estrellas
    frame = base.copy()
    for i, mm in enumerate(masks):
        k = (t - light_t[i]) / 0.18
        if k >= 0:
            k = min(k, 1.0)
            flash = 1 + 0.7 * max(0.0, 1 - (t - light_t[i]) / 0.35)
            reg = a[y0:y1] * flash
            frame[y0:y1] = frame[y0:y1] * (1 - mm[y0:y1, :, None] * k) + reg * (mm[y0:y1, :, None] * k)
    img = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8))
    # camara: paso ~1.8 Hz (subida/bajada), paneo lento + zoom progresivo, ligera inclinacion
    p = t / DUR
    step = 2 * math.pi * 1.8 * t
    bob = 12 * abs(math.sin(step / 2)) * 2 - 12
    sway = 6 * math.sin(step / 2)
    ang = math.radians(0.45 * math.sin(step / 2 + 0.6))
    pan = -24 + 48 * p
    zoom = 1.0 + 0.035 * p
    cx, cy = bw / 2 + pan + sway, bh / 2 + bob
    # matriz inversa destino->origen (rotacion + escala alrededor del centro)
    c, s = math.cos(ang) / zoom, math.sin(ang) / zoom
    A = (c, -s, cx - c * W / 2 + s * H / 2, s, c, cy - s * W / 2 - c * H / 2)
    out_img = img.transform((W, H), Image.AFFINE, A, resample=Image.BICUBIC)
    arr = np.asarray(out_img).astype(np.float32)
    # leve desaturacion/contraste filmico, vineta, grano
    arr = arr * vig
    arr += rng.normal(0, 9, (H, W, 1)).astype(np.float32)
    ff.stdin.write(np.clip(arr, 0, 255).astype(np.uint8).tobytes())
ff.stdin.close(); ff.wait()
