"""Separa el slide v2 (899x1599) en capas: avatar, fondo limpio, mapa de profundidad y overlay estatico.
Solo numpy + Pillow. Salida a 1080x1920."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import sys, os

W = sys.argv[1]
SRC = Image.open(f"{W}/slide_v2.jpg").convert("RGB")
SW, SH = SRC.size  # 899 x 1599
OW, OH = 1080, 1920
sx, sy = OW / SW, OH / SH


def blur(a, r):
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r)), dtype=np.float32) / 255.0


def dilate(m, r):
    im = Image.fromarray((m * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.MaxFilter(2 * r + 1)), dtype=np.float32) / 255.0


def erode(m, r):
    im = Image.fromarray((m * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.MinFilter(2 * r + 1)), dtype=np.float32) / 255.0


src = np.asarray(SRC, dtype=np.float32) / 255.0
luma = 0.299 * src[..., 0] + 0.587 * src[..., 1] + 0.114 * src[..., 2]

# ---------------------------------------------------------------- avatar polygon (coords del slide)
POLY = [
    (470, 190), (490, 194), (520, 208), (551, 232), (562, 258), (556, 282), (542, 294), (527, 305), (512, 320), (508, 336),
    (523, 346), (530, 358), (545, 372), (568, 392), (590, 430), (606, 470), (622, 510), (640, 545), (652, 580),
    (672, 625), (690, 672), (699, 705), (690, 722), (672, 732), (672, 775), (650, 800), (610, 802),
    (598, 792), (575, 812), (560, 850), (535, 900), (520, 950), (515, 1000), (515, 1050), (520, 1110),
    (520, 1140), (515, 1190), (512, 1235), (512, 1290), (510, 1330), (497, 1397), (440, 1403),
    (388, 1397), (380, 1362), (372, 1343), (352, 1337), (345, 1305), (350, 1285), (338, 1262),
    (340, 1240), (335, 1200), (330, 1160), (332, 1110), (333, 1050), (335, 1000), (330, 950),
    (330, 900), (325, 850), (315, 820), (298, 786), (293, 765), (285, 745), (270, 726), (225, 650),
    (202, 596), (200, 565), (215, 505), (235, 450), (250, 405), (267, 375), (300, 355), (322, 347),
    (350, 340), (370, 315), (410, 311), (420, 325), (422, 305), (410, 256), (413, 238), (425, 222), (438, 208), (452, 195),
]


def poly_mask(poly, scale_x=1.0, scale_y=1.0, size=(SW, SH), ss=4):
    w, h = size
    im = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(im).polygon([(x * scale_x * ss, y * scale_y * ss) for x, y in poly], fill=255)
    im = im.resize((w, h), Image.LANCZOS)
    return np.asarray(im, dtype=np.float32) / 255.0


m = poly_mask(POLY)

# refinamiento: contra el cielo brillante, el borde del hoodie/pelo es oscuro -> recorta pixeles claros en banda de borde
band = dilate(m, 7) - erode(m, 7)
band = np.clip(band, 0, 1)
yy, xx = np.mgrid[0:SH, 0:SW]
skyzone = (yy < 800)
# zonas donde SI hay piel/disco claro cerca del borde (no recortar): cara y manos
face = (xx > 420) & (xx < 505) & (yy > 255) & (yy < 340)
lhand = (xx > 300) & (xx < 430) & (yy > 640) & (yy < 770)
rhand = (xx > 590) & (xx < 690) & (yy > 700) & (yy < 810)
disc = (xx > 305) & (xx < 665) & (yy > 520) & (yy < 800)
protect = (face | lhand | rhand | disc)
bright = np.clip((luma - 0.30) / 0.15, 0, 1)  # 0 oscuro (hoodie) -> 1 cielo
cut = band * bright * (skyzone & ~protect)
m = np.clip(m - cut, 0, 1)
# suaviza y erosiona 1px para evitar halo
m = erode(m, 1)
m = blur(m, 0.8)

# ---------------------------------------------------------------- overlay estatico (texto, logo, estrellas, minimapa)
R, G, B = src[..., 0], src[..., 1], src[..., 2]
mn = src.min(-1)
white = (mn > 0.78)
yellow = (R > 0.88) & (G > 0.72) & (B < 0.28)

# (caja, tipo) tipo: w=blanco, y=amarillo, wy=ambos
BOXES = [
    ((35, 48, 115, 90), "w"), ((735, 48, 860, 90), "w"),
    ((250, 804, 652, 978), "w"), ((165, 976, 738, 1116), "w"),      # MISION / CUMPLIDA
    ((200, 1133, 705, 1207), "y"),                                  # objeto desbloqueado
    ((480, 1296, 858, 1340), "w"), ((620, 1337, 858, 1373), "y"),   # repartidor / mejora
    ((508, 1386, 852, 1456), "y"),                                  # estrellas
    ((550, 1470, 772, 1527), "w"),                                  # mark kaizen
]
ink = np.zeros((SH, SW), np.float32)
boxmask = np.zeros((SH, SW), np.float32)
for (x0, y0, x1, y1), t in BOXES:
    sel = np.zeros((SH, SW), bool)
    if "w" in t: sel |= white
    if "y" in t: sel |= yellow
    ink[y0:y1, x0:x1] = np.maximum(ink[y0:y1, x0:x1], sel[y0:y1, x0:x1].astype(np.float32))
    boxmask[y0:y1, x0:x1] = 1
# 改善: dorado mas apagado -> umbral relajado solo en su caja
x0, y0, x1, y1 = 772, 1470, 858, 1527
kz = ((R > 0.62) & (G > 0.50) & (B < 0.50) & (R - B > 0.28)).astype(np.float32)
ink[y0:y1, x0:x1] = np.maximum(ink[y0:y1, x0:x1], kz[y0:y1, x0:x1])
boxmask[y0:y1, x0:x1] = 1
near_ink2 = dilate(ink, 1)
near_ink6 = dilate(ink, 6)
outline = ((luma < 0.26).astype(np.float32)) * near_ink6 * boxmask
text_a = np.clip(np.maximum(near_ink2 * boxmask, outline), 0, 1)
text_a = dilate(erode(text_a, 1), 1)
text_a = np.maximum(text_a, ink)

# minimapa circular
cx, cy, rad = 184.5, 1408.0, 141.0
circ = ((xx - cx) ** 2 + (yy - cy) ** 2 <= rad ** 2).astype(np.float32)
circ = blur(circ, 0.7)

overlay_a = np.clip(np.maximum(text_a, circ), 0, 1)
overlay_a = blur(overlay_a, 0.6)


# ---------------------------------------------------------------- fondo limpio (push-pull inpaint bajo el avatar)
hole = np.maximum(dilate(m, 10), dilate((overlay_a > 0.03).astype(np.float32), 2))
hole = (hole > 0.02).astype(np.float32)


def _rs(a, size, resample):
    return np.stack([np.asarray(Image.fromarray(a[..., i], mode="F").resize(size, resample)) for i in range(a.shape[2])], -1)


def pushpull(img, valid):
    a = img * valid[..., None]
    w = valid.astype(np.float32)[..., None]
    pyr = []
    cur = np.concatenate([a, w], -1)
    while min(cur.shape[:2]) > 3:
        pyr.append(cur)
        h, wd = cur.shape[:2]
        cur = _rs(cur, ((wd + 1) // 2, (h + 1) // 2), Image.BOX)
    res = cur[..., :3] / np.maximum(cur[..., 3:4], 1e-6)
    for lv in reversed(pyr):
        h, wd = lv.shape[:2]
        up = _rs(res, (wd, h), Image.BILINEAR)
        wl = lv[..., 3:4]
        col = lv[..., :3] / np.maximum(wl, 1e-6)
        k = np.clip(wl * 4.0, 0, 1)
        res = col * k + up * (1 - k)
    return res


# versiones: relleno suave + difusion extra para textura plana
valid = 1.0 - hole
plate = pushpull(src, valid)
plate = np.where(hole[..., None] > 0, plate, src)
# suaviza la zona rellena para que no queden escalones
soft = np.stack([blur(plate[..., i], 5) for i in range(3)], -1)
hole_soft = blur(hole, 3)
plate = plate * (1 - hole_soft[..., None]) + soft * hole_soft[..., None]
plate = np.clip(plate, 0, 1)

# ---------------------------------------------------------------- textura del avatar sin texto
text_hole = dilate((overlay_a > 0.04).astype(np.float32), 3)
valid_av = (1.0 - text_hole) * (dilate(m, 2) > 0.02).astype(np.float32)
av_fill = pushpull(src, valid_av)
av_tex = np.where(text_hole[..., None] > 0.5, av_fill, src)
# mezcla suave en el borde del hueco
th_s = blur(text_hole, 1.0)
av_tex = src * (1 - th_s[..., None]) + av_fill * th_s[..., None]
av_tex = np.clip(av_tex, 0, 1)

# ---------------------------------------------------------------- mapa de profundidad (0 lejos .. 1 cerca)
D = np.zeros((SH, SW), np.float32)
D[:] = 0.04                                       # cielo
# skyline lejano
D = np.where((yy > 420) & (yy < 1150), 0.12, D)
# carretera: mas cerca cuanto mas abajo
road = np.clip((yy - 1130) / (SH - 1130), 0, 1)
D = np.where(yy >= 1130, 0.25 + 0.55 * road, D)
dark = (luma < 0.20).astype(np.float32)
dark_s = blur(dark, 1.5)


def region_dark(box, d):
    global D
    x0, y0, x1, y1 = box
    r = np.zeros((SH, SW), np.float32)
    r[y0:y1, x0:x1] = 1
    k = blur(r, 6) * dark_s
    D = np.maximum(D, k * d)


region_dark((0, 290, 205, 1010), 0.70)       # palmeras grandes izquierda
region_dark((700, 100, 899, 430), 0.85)      # palma grande arriba derecha
region_dark((615, 470, 800, 900), 0.45)      # palmeras medias derecha
region_dark((0, 820, 175, 1060), 0.35)       # palmeras pequenas izquierda

# coches
def box_depth(box, d, sig=4):
    global D
    x0, y0, x1, y1 = box
    r = np.zeros((SH, SW), np.float32)
    r[y0:y1, x0:x1] = 1
    r = blur(r, sig)
    D = D * (1 - r) + d * r


box_depth((12, 1062, 208, 1148), 0.38)       # coche izquierda (lejos)
box_depth((540, 925, 899, 1195), 0.92)       # coche derecha (cerca)
D = blur(D, 7)
# bajo el avatar usa el valor del entorno (queda tapado por el avatar)

# ---------------------------------------------------------------- guardar a 1080x1920
def up_rgb(a):
    return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((OW, OH), Image.LANCZOS), dtype=np.float32) / 255.0


def up_a(a):
    return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)).resize((OW, OH), Image.BICUBIC), dtype=np.float32) / 255.0


os.makedirs(f"{W}/layers", exist_ok=True)
np.save(f"{W}/layers/full.npy", up_rgb(src).astype(np.float16))
np.save(f"{W}/layers/avatar_rgb.npy", up_rgb(av_tex).astype(np.float16))
np.save(f"{W}/layers/plate.npy", up_rgb(plate).astype(np.float16))
np.save(f"{W}/layers/avatar_a.npy", up_a(m).astype(np.float16))
np.save(f"{W}/layers/overlay_a.npy", up_a(overlay_a).astype(np.float16))
np.save(f"{W}/layers/depth.npy", up_a(D).astype(np.float16))

# debug
def sv(name, a):
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(f"{W}/layers/{name}")

sv("dbg_plate.png", plate)
sv("dbg_avtex.png", av_tex * m[..., None] + 0.0)
sv("dbg_depth.png", D)
sv("dbg_overlay_a.png", overlay_a)
# avatar sobre verde para revisar borde
g = np.zeros_like(src); g[...] = (0.0, 0.8, 0.2)
sv("dbg_avatar.png", src * m[..., None] + g * (1 - m[..., None]))
# overlay sobre gris
g2 = np.zeros_like(src); g2[...] = (0.35, 0.35, 0.35)
sv("dbg_overlay.png", src * overlay_a[..., None] + g2 * (1 - overlay_a[..., None]))
print("ok")
