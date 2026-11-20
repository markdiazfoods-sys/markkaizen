"""Misión cumplida v3 - pantalla de carga GTA / Vice City con movimiento real.
Uso: render_v3.py CARPETA_CON_layers OUT.mp4 [T_seg] [frames_a_probar...]
Requiere las capas de build_layers.py (CARPETA/layers/*.npy). Solo numpy + Pillow + ffmpeg."""
import numpy as np, sys, subprocess, math
from multiprocessing import Pool
from PIL import Image, ImageFilter

W = sys.argv[1]
OUT = sys.argv[2]
T = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
FPS = 30
OW, OH = 1080, 1920
SW, SH = 899, 1599
FX, FY = OW / SW, OH / SH
L = f"{W}/layers"
F32 = np.float32

full = np.load(f"{L}/full.npy").astype(F32)
plate = np.load(f"{L}/plate.npy").astype(F32)
av_a = np.load(f"{L}/avatar_a.npy").astype(F32)
ov_a = np.load(f"{L}/overlay_a.npy").astype(F32)
depth = np.load(f"{L}/depth.npy").astype(F32)
av_rgb = np.load(f"{L}/avatar_rgb.npy").astype(F32)
yy, xx = np.mgrid[0:OH, 0:OW].astype(F32)
luma = (0.299 * full[..., 0] + 0.587 * full[..., 1] + 0.114 * full[..., 2]).astype(F32)
PI2 = 2 * math.pi


# ------------------------------------------------------------------ utilidades
def blur(a, r):
    im = Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r)), dtype=F32) / 255.0


def remap(img, sx, sy):
    h, w = img.shape[:2]
    sx = np.clip(sx, 0, w - 1.001); sy = np.clip(sy, 0, h - 1.001)
    x0 = sx.astype(np.int32); y0 = sy.astype(np.int32)
    fx = (sx - x0)[..., None]; fy = (sy - y0)[..., None]
    a = img[y0, x0]; b = img[y0, x0 + 1]; c = img[y0 + 1, x0]; d = img[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def clip01(u):
    return min(max(u, 0.0), 1.0)


def smooth(u):
    u = clip01(u)
    return u * u * (3 - 2 * u)


def eo(u):
    u = clip01(u)
    return 1 - (1 - u) ** 3


def back(u):
    u = clip01(u)
    c1 = 1.70158; c3 = c1 + 1
    return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2


def rect_o(box, pad=0):
    x0, y0, x1, y1 = box
    return (max(0, int(x0 * FX) - pad), max(0, int(y0 * FY) - pad), min(OW, int(x1 * FX) + 1 + pad), min(OH, int(y1 * FY) + 1 + pad))


def region_mask(box, sig):
    x0, y0, x1, y1 = rect_o(box)
    r = np.zeros((OH, OW), F32); r[y0:y1, x0:x1] = 1
    return blur(r, sig)


# ------------------------------------------------------------------ plate limpio (relleno por espejo, sin manchas difusas)
def dil(m, r):
    o = m.astype(np.uint8)
    for _ in range(r):
        n = o.copy()
        n[1:] |= o[:-1]; n[:-1] |= o[1:]; n[:, 1:] |= o[:, :-1]; n[:, :-1] |= o[:, 1:]
        n[1:, 1:] |= o[:-1, :-1]; n[:-1, :-1] |= o[1:, 1:]; n[1:, :-1] |= o[:-1, 1:]; n[:-1, 1:] |= o[1:, :-1]
        o = n
    return o.astype(bool)


def fill_rows(img, valid):
    H, Wd = valid.shape
    xs = np.arange(Wd, dtype=np.int32)[None, :]
    X = np.broadcast_to(xs, (H, Wd))
    li = np.maximum.accumulate(np.where(valid, xs, -1), axis=1)
    ri = np.minimum.accumulate(np.where(valid, xs, Wd * 4)[:, ::-1], axis=1)[:, ::-1]
    hole = ~valid
    rows = np.arange(H)[:, None]
    xl = 2 * li - X; xr = 2 * ri - X
    okl = hole & (li >= 0) & (xl >= 0) & (xl < Wd)
    okr = hole & (ri < Wd) & (xr >= 0) & (xr < Wd)
    okl &= valid[rows, np.clip(xl, 0, Wd - 1)]
    okr &= valid[rows, np.clip(xr, 0, Wd - 1)]
    dl = (X - li).astype(F32); dr = (ri - X).astype(F32)
    den = np.maximum(dl + dr, 1)
    wl = np.where(okl & okr, dr / den, np.where(okl, 1.0, 0.0)).astype(F32)
    wr = np.where(okl & okr, dl / den, np.where(okr, 1.0, 0.0)).astype(F32)
    cl = img[rows, np.clip(xl, 0, Wd - 1)]; cr = img[rows, np.clip(xr, 0, Wd - 1)]
    filled = okl | okr
    res = np.where(filled[..., None], cl * wl[..., None] + cr * wr[..., None], img)
    rest = hole & ~filled
    if rest.any():
        a = img[rows, np.clip(li, 0, Wd - 1)]; b = img[rows, np.clip(ri, 0, Wd - 1)]
        both = (li >= 0) & (ri < Wd)
        t_ = (dl / den)[..., None]
        interp = np.where(both[..., None], a * (1 - t_) + b * t_, np.where((li >= 0)[..., None], a, b))
        res = np.where(rest[..., None], interp, res)
    return res


def mirror_fill(img, hole, split_y):
    valid = ~hole
    ph = fill_rows(img, valid)
    pv = fill_rows(img.transpose(1, 0, 2), valid.T).transpose(1, 0, 2)
    k = np.clip((yy - split_y) / 40.0 + 0.5, 0, 1)[..., None].astype(F32)   # arriba: horizontal, asfalto: vertical
    res = ph * (1 - k) + pv * k
    return res.astype(F32)


AV_HOLE = dil(av_a > 0.02, 14)
HOLE = AV_HOLE | dil(ov_a > 0.03, 5)
plate = mirror_fill(full, HOLE, 1135 * FY)
_hs = blur(HOLE.astype(F32), 2.0)[..., None]
plate = np.clip(plate * _hs + full * (1 - _hs), 0, 1)
D_AV = 0.35
_wm = blur(dil(av_a > 0.02, 10).astype(F32), 14.0)
depth = depth * (1 - _wm) + D_AV * _wm

# ------------------------------------------------------------------ mapas estaticos del fondo
dark_s = blur((luma < 0.20).astype(F32), 1.5)

# nubes del cielo (profundidad minima)
sky_w = np.clip((0.085 - depth) / 0.05, 0, 1).astype(F32)
sky_w *= (yy < 1000 * FY / 1.0).astype(F32)

# palmeras: (region, pivote, distancia maxima) en coords del slide
PALMS = [((0, 290, 205, 1010), (20, 1000), 750.0),
         ((700, 100, 899, 424), (899, 430), 250.0),
         ((615, 470, 744, 900), (700, 900), 420.0),
         ((780, 690, 899, 935), (860, 935), 260.0),
         ((0, 820, 175, 1060), (90, 1060), 260.0)]
palm_amp = np.zeros((OH, OW), F32)
for box, (pxs, pys), dmax in PALMS:
    rm = region_mask(box, 6) * dark_s
    dist = np.hypot((xx - pxs * FX), (yy - pys * FY)) / (dmax * FX)
    palm_amp = np.maximum(palm_amp, rm * np.clip(dist, 0, 1) ** 1.3)
# edificios (coords slide) que NO deben balancearse aunque tengan pixeles oscuros dentro de una region de palmeras
BUILDINGS = [(738, 400, 872, 700), (738, 690, 850, 835), (708, 660, 770, 835), (870, 590, 899, 700)]
bld_keep = np.ones((OH, OW), F32)
for b in BUILDINGS:
    bld_keep *= 1.0 - region_mask(b, 4)
palm_amp *= bld_keep
palm_phase = (yy / 170.0 + xx / 240.0).astype(F32)

# asfalto mojado
road_w = np.clip((yy - 1130 * FY) / (90 * FY), 0, 1).astype(F32)

# coches (vibracion de motor)
car_r = region_mask((540, 925, 899, 1195), 6)
car_l = region_mask((12, 1062, 208, 1148), 5)

# ventanas de rascacielos
WIN_RECTS = [(60, 690, 135, 1000), (125, 795, 180, 1000), (0, 770, 52, 900), (745, 425, 865, 830),
             (860, 595, 899, 860), (710, 665, 765, 830), (610, 800, 672, 880), (180, 905, 212, 990)]
WY0, WY1 = int(420 * FY), int(1010 * FY)
win_rect = np.zeros((OH, OW), F32)
for b in WIN_RECTS:
    x0, y0, x1, y1 = rect_o(b); win_rect[y0:y1, x0:x1] = 1
hp = luma - blur(luma, 3)
win_mask = (np.clip((hp - 0.035) / 0.10, 0, 1) * win_rect).astype(F32)
cellid = ((yy // 7).astype(np.int64) * 7919 + (xx // 7).astype(np.int64) * 104729) % 1000
win_phase = (cellid / 1000.0 * PI2).astype(F32)
win_freq = (0.6 + (cellid % 7) / 7.0 * 1.6).astype(F32)
win_mask_c = win_mask[WY0:WY1].copy(); win_phase_c = win_phase[WY0:WY1].copy(); win_freq_c = win_freq[WY0:WY1].copy()

# luz de freno (coche derecho) y faros (coche izquierdo)
TX0, TY0, TX1, TY1 = rect_o((780, 960, 899, 1050))
rr_, gg_, bb_ = full[..., 0], full[..., 1], full[..., 2]
tail_m = np.zeros((OH, OW), F32)
tail_m[TY0:TY1, TX0:TX1] = np.clip((rr_ - np.maximum(gg_, bb_) - 0.30) / 0.25, 0, 1)[TY0:TY1, TX0:TX1]
tail_glow = np.clip(blur(tail_m, 14) * 1.6 + blur(tail_m, 40) * 1.2, 0, 1)[TY0 - 60:TY1 + 60]
tail_glow_y = (TY0 - 60, TY1 + 60)
HX0, HY0, HX1, HY1 = rect_o((15, 1085, 200, 1135))
head_m = np.zeros((OH, OW), F32)
head_m[HY0:HY1, HX0:HX1] = np.clip((luma - 0.62) / 0.25, 0, 1)[HY0:HY1, HX0:HX1]
head_glow = np.clip(blur(head_m, 10) * 1.5 + blur(head_m, 30) * 1.1, 0, 1)[HY0 - 60:HY1 + 60]
head_glow_y = (HY0 - 60, HY1 + 60)

# resplandor del sol (solo sobre zonas claras)
SUNX, SUNY = 238 * FX, 925 * FY
sun_zone = (yy > 700) & (yy < 1300)
sun_g = np.exp(-(((xx - SUNX) ** 2 + (yy - SUNY) ** 2) / (2 * 110.0 ** 2))).astype(F32)
sun_g *= np.clip((luma - 0.30) / 0.25, 0, 1) * sun_zone

# viñeta
rr2 = ((xx - OW / 2) / (OW / 2)) ** 2 + ((yy - OH * 0.52) / (OH / 2)) ** 2
VIG = (1.0 - 0.32 * np.clip(rr2 - 0.25, 0, 1.3) ** 1.2).astype(F32)[..., None]

# ------------------------------------------------------------------ avatar
av_pm = np.concatenate([av_rgb * av_a[..., None], av_a[..., None]], -1)
halo = np.clip(blur(av_a, 7) * 1.5 - av_a * 1.35, 0, 1).astype(F32)
halo += np.clip(blur(av_a, 20) * 0.8 - av_a, 0, 1).astype(F32) * 0.22
av_stack = np.concatenate([av_pm, halo[..., None]], -1)
ys_, xs_ = np.where(av_a > 0.02)
AVB = (max(0, xs_.min() - 110), max(0, ys_.min() - 110), min(OW, xs_.max() + 110), min(OH, ys_.max() + 110))
AV_ANCHOR = (540.0, 1560.0)

# disco arcoiris: mascara (elipse inclinada) sin dona ni manos
cxd, cyd = 485 * FX, 655 * FY
ang = math.radians(14)
ca_, sa_ = math.cos(ang), math.sin(ang)
ex = (xx - cxd) * ca_ + (yy - cyd) * sa_
ey = -(xx - cxd) * sa_ + (yy - cyd) * ca_
disc_ell = (ex / (182 * FX)) ** 2 + (ey / (122 * FY)) ** 2
disc_m = np.clip((1.0 - disc_ell) * 6, 0, 1)
dn_x, dn_y = 482 * FX, 628 * FY
dn = ((xx - dn_x) / (92 * FX)) ** 2 + ((yy - dn_y) / (74 * FY)) ** 2
disc_m *= np.clip((dn - 1.0) * 5, 0, 1)
for hb in [(330, 650, 438, 748), (584, 698, 664, 795)]:
    hm = 1 - region_mask(hb, 5)
    disc_m *= hm
mx, mn_ = av_rgb.max(-1), av_rgb.min(-1)
sat = (mx - mn_) / np.maximum(mx, 1e-3)
disc_m *= np.clip((sat - 0.12) / 0.2, 0, 1) * (av_a > 0.5)
disc_m = blur(disc_m, 1.0).astype(F32)
DX0, DY0, DX1, DY1 = rect_o((300, 510, 670, 810))
disc_m_c = disc_m[DY0:DY1, DX0:DX1]
disc_av_c = av_rgb[DY0:DY1, DX0:DX1].copy()
disc_a_c = av_a[DY0:DY1, DX0:DX1]
disc_ex_c = ex[DY0:DY1, DX0:DX1] / (182 * FX)

# ------------------------------------------------------------------ overlay en grupos
def make_group(box, pad=8, anchor=None):
    x0, y0, x1, y1 = rect_o(box)
    h, w = y1 - y0, x1 - x0
    img = np.zeros((h + 2 * pad, w + 2 * pad, 4), F32)
    a = ov_a[y0:y1, x0:x1]
    img[pad:pad + h, pad:pad + w, :3] = full[y0:y1, x0:x1] * a[..., None]
    img[pad:pad + h, pad:pad + w, 3] = a
    ox, oy = x0 - pad, y0 - pad
    if anchor is None:
        ys, xs = np.where(img[..., 3] > 0.3)
        anchor = (ox + (xs.min() + xs.max()) / 2.0, oy + (ys.min() + ys.max()) / 2.0)
    gh, gw = img.shape[:2]
    gy, gx = np.mgrid[0:gh, 0:gw].astype(F32)
    return dict(img=img, ox=ox, oy=oy, ax=anchor[0], ay=anchor[1], w=gw, h=gh,
                su=(gx + 0.35 * gy) / (gw + 0.35 * gh))


G = {}
G["hud_l"] = make_group((35, 48, 115, 90))
G["hud_r"] = make_group((735, 48, 860, 90))
G["mision"] = make_group((250, 804, 652, 977))
G["cumplida"] = make_group((165, 977, 738, 1116))
G["objeto"] = make_group((200, 1133, 705, 1207))
G["repart"] = make_group((480, 1296, 858, 1337))
G["mejora"] = make_group((620, 1337, 858, 1373))
G["logo"] = make_group((550, 1470, 862, 1530))
STAR_X = [508, 575, 645, 715, 785, 852]
for k in range(5):
    G[f"star{k}"] = make_group((STAR_X[k], 1386, STAR_X[k + 1], 1456))
G["map"] = make_group((40, 1262, 332, 1556), pad=10)
MAPC = (184.5 * FX, 1408.0 * FY)
MAPR = 141.0 * FX
_g = G["map"]
_gy, _gx = np.mgrid[0:_g["h"], 0:_g["w"]].astype(F32)
_rx, _ry = _gx - (MAPC[0] - _g["ox"]), _gy - (MAPC[1] - _g["oy"])
MAP_RAD = np.hypot(_rx, _ry).astype(F32)
MAP_ANG = np.arctan2(_ry, _rx).astype(F32)
_g["ax"], _g["ay"] = MAPC

# ------------------------------------------------------------------ particulas y trafico
_rng = np.random.default_rng(11)
NP = 72
P_X = _rng.uniform(0, OW, NP); P_Y = _rng.uniform(0, OH, NP)
P_Z = _rng.uniform(0.25, 1.0, NP); P_R = 2.2 + 6.0 * P_Z ** 1.5 * _rng.uniform(0.6, 1.1, NP)
P_VY = 14 + 44 * P_Z * _rng.uniform(0.7, 1.2, NP); P_PH = _rng.uniform(0, PI2, NP)
P_COL = np.array([(1.0, 0.25, 0.68), (0.25, 0.85, 1.0), (1.0, 0.72, 0.25), (0.8, 0.4, 1.0)])[_rng.integers(0, 4, NP)]

STREAKS = [  # y_slide, direccion, velocidad px/s, fase, largo, color, alto
    (1236, 1, 520, 0.00, 330, (1.0, 0.28, 0.30), 5.0),
    (1236, -1, 640, 0.45, 300, (1.0, 0.95, 0.80), 5.0),
    (1268, 1, 780, 0.20, 420, (0.35, 0.85, 1.0), 6.5),
    (1268, -1, 700, 0.70, 380, (1.0, 0.35, 0.80), 6.5),
    (1292, 1, 900, 0.55, 480, (1.0, 0.70, 0.30), 8.0),
    (1130, -1, 160, 0.10, 90, (1.0, 0.93, 0.78), 2.2),
    (1130, 1, 130, 0.60, 80, (1.0, 0.25, 0.28), 2.2),
]

IMP = [(2.55, 16), (2.90, 24), (6.00, 7), (6.35, 7), (6.70, 7), (7.05, 7), (7.40, 9), (7.90, 5)]


def shake(t):
    sx = sy = pun = ca = 0.0
    for ti, A in IMP:
        d = t - ti
        if d >= 0:
            k = math.exp(-d * 9)
            sx += A * k * math.sin(PI2 * 19 * d + ti)
            sy += A * 0.8 * k * math.cos(PI2 * 23 * d + ti * 2)
            pun += A * 0.0007 * math.exp(-d * 10)
            ca += A * math.exp(-d * 14)
    return sx, sy, pun, ca


def add_glow(out, cx, cy, rad, col, amp):
    x0 = int(max(0, cx - rad * 3)); x1 = int(min(OW, cx + rad * 3 + 1))
    y0 = int(max(0, cy - rad * 3)); y1 = int(min(OH, cy + rad * 3 + 1))
    if x1 <= x0 or y1 <= y0:
        return
    gx = (np.arange(x0, x1, dtype=F32) - cx)[None, :]; gy = (np.arange(y0, y1, dtype=F32) - cy)[:, None]
    g = np.exp(-(gx * gx + gy * gy) / (2 * rad * rad)) * amp
    out[y0:y1, x0:x1] += g[..., None] * np.asarray(col, F32)


def draw_streak(out, x, y, dr, length, col, sy_, amp):
    x0 = int(max(0, x - length * 2.2 - 40)); x1 = int(min(OW, x + length * 2.2 + 40))
    y0 = int(max(0, y - sy_ * 9)); y1 = int(min(OH, y + sy_ * 9))
    if x1 <= x0 or y1 <= y0:
        return
    gx = np.arange(x0, x1, dtype=F32)[None, :]
    gy = np.arange(y0, y1, dtype=F32)[:, None]
    d = (x - gx) * dr
    tail = np.where(d >= 0, np.exp(-np.maximum(d, 0) / (length * 0.45)), np.exp(-(np.minimum(d, 0) / 7.0) ** 2))
    prof = tail * (np.exp(-((gy - y) / sy_) ** 2 / 2) + 0.35 * np.exp(-((gy - y - sy_ * 3.8) / (sy_ * 1.8)) ** 2 / 2))
    c = np.asarray(col, F32)
    out[y0:y1, x0:x1] += (prof * amp)[..., None] * c * 1.1 + (prof ** 3 * amp)[..., None] * 0.5


def blit(out, g, sc=1.0, dx=0.0, dy=0.0, alpha=1.0, rot=0.0, white=0.0, tint=None, shine=None, extra=None):
    if alpha <= 0.002 or sc <= 0.01:
        return
    img = g["img"]
    if shine is not None or extra is not None:
        img = img.copy()
        if shine is not None:
            band = np.exp(-((g["su"] - (shine * 1.5 - 0.25)) / 0.075) ** 2)
            img[..., :3] += (band * img[..., 3] * 0.95)[..., None]
        if extra is not None:
            extra(img)
    ax, ay = g["ax"], g["ay"]
    c, s = math.cos(rot), math.sin(rot)
    pts = []
    for cxp, cyp in [(g["ox"], g["oy"]), (g["ox"] + g["w"], g["oy"]), (g["ox"], g["oy"] + g["h"]), (g["ox"] + g["w"], g["oy"] + g["h"])]:
        rx, ry = cxp - ax, cyp - ay
        pts.append((ax + dx + sc * (c * rx - s * ry), ay + dy + sc * (s * rx + c * ry)))
    x0 = int(max(0, min(p[0] for p in pts) - 2)); x1 = int(min(OW, max(p[0] for p in pts) + 3))
    y0 = int(max(0, min(p[1] for p in pts) - 2)); y1 = int(min(OH, max(p[1] for p in pts) + 3))
    if x1 <= x0 or y1 <= y0:
        return
    gx = np.arange(x0, x1, dtype=F32)[None, :] - (ax + dx)
    gy = np.arange(y0, y1, dtype=F32)[:, None] - (ay + dy)
    ci, si = math.cos(-rot), math.sin(-rot)
    qx = (ci * gx - si * gy) / sc + ax - g["ox"]
    qy = (si * gx + ci * gy) / sc + ay - g["oy"]
    r = remap(img, qx + 0 * gy, qy + 0 * gx)
    a = r[..., 3:4] * alpha
    rgb = r[..., :3] * alpha
    if tint is not None:
        rgb = rgb * np.asarray(tint, F32)
    if white > 0:
        rgb = rgb + white * a
    out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - a) + rgb


def hue_rot(rgb, th):
    c, s = math.cos(th), math.sin(th)
    m = np.array([[.299 + .701 * c + .168 * s, .587 - .587 * c + .330 * s, .114 - .114 * c - .497 * s],
                  [.299 - .299 * c - .328 * s, .587 + .413 * c + .035 * s, .114 - .114 * c + .292 * s],
                  [.299 - .300 * c + 1.25 * s, .587 - .588 * c - 1.05 * s, .114 + .886 * c - .203 * s]], F32)
    return rgb @ m.T


# ------------------------------------------------------------------ frame
CAM_C = (540.0, 1300.0)
Z_FAR, Z_NEAR, BASE = 0.03, 0.20, 1.07
STEP_T = 1.1
LEG_AMP = 14.0
LEG_X = 460.0


def frame(i):
    t = i / FPS
    u = t / T
    e = u * (1.4 - 0.4 * u)
    ph = PI2 * t / STEP_T
    shx_i, shy_i, pun, ca = shake(t)

    # ---- plate con efectos locales (ventanas, luces de coche, sol)
    pl = plate.copy()
    w = win_mask_c * (0.9 * np.sin(PI2 * t * win_freq_c + win_phase_c) - 0.05)
    pl[WY0:WY1] *= (1 + w)[..., None] * np.asarray((1.0, 0.98, 1.0), F32)
    pl[WY0:WY1] += (win_mask_c * np.clip(np.sin(PI2 * t * win_freq_c + win_phase_c), 0, 1) * 0.10)[..., None] * np.asarray((0.5, 0.9, 1.0), F32)
    pulse_t = 0.5 + 0.5 * math.sin(PI2 * t / 0.85)
    pl[tail_glow_y[0]:tail_glow_y[1]] += (tail_glow * (0.15 + 0.85 * pulse_t) * 0.9)[..., None] * np.asarray((1.0, 0.18, 0.28), F32)
    pulse_h = 0.5 + 0.5 * math.sin(PI2 * t / 1.3 + 1.0)
    pl[head_glow_y[0]:head_glow_y[1]] += (head_glow * (0.25 + 0.75 * pulse_h) * 0.8)[..., None] * np.asarray((1.0, 0.86, 0.55), F32)
    pl += (sun_g * (0.12 + 0.10 * math.sin(PI2 * t / 2.8)))[..., None] * np.asarray((1.0, 0.55, 0.25), F32)

    # ---- camara
    S = BASE + (Z_FAR + (Z_NEAR - Z_FAR) * depth) * e + pun
    pan = 24.0 * math.sin(PI2 * u * 0.7 + 0.4) + 5.0 * math.sin(PI2 * t * 1.3)
    crane = 12.0 * math.sin(PI2 * u * 0.5 + 1.0) - 6.0 * math.sin(ph * 2)
    dw = 0.15 + 0.85 * depth
    pan_s = pan + shx_i * 0.8
    shx = pan_s * dw
    shy = (crane + shy_i * 0.8) * dw
    roll = math.radians(0.45 * math.sin(PI2 * u * 0.6) + 0.12 * math.sin(PI2 * t * 1.9) + 0.012 * shx_i)
    cr, sr = math.cos(roll), math.sin(roll)
    gx0, gy0 = xx - 540.0, yy - 960.0
    xr = cr * gx0 - sr * gy0 + 540.0
    yr = sr * gx0 + cr * gy0 + 960.0
    sx = CAM_C[0] + (xr - CAM_C[0] - shx) / S
    sy = CAM_C[1] + (yr - CAM_C[1] - shy) / S
    # animacion del propio fondo: nubes, palmeras, asfalto, motor
    sx = sx + sky_w * (3.0 * t + 6.0 * np.sin(yy / 90.0 + t * 1.1) + 4.0 * np.sin(yy / 37.0 - t * 1.7))
    swing = np.sin(PI2 * t / 2.6 + palm_phase) * 11.0 + np.sin(PI2 * t / 1.1 + palm_phase * 2.3) * 3.0
    sx = sx + palm_amp * swing
    sy = sy + palm_amp * (3.0 * np.sin(PI2 * t / 2.6 + palm_phase + 1.0))
    sx = sx + road_w * 2.4 * np.sin(yy / 7.0 - t * 6.0)
    sy = sy + (car_r * 1.8 + car_l * 1.2) * math.sin(PI2 * 13 * t) + car_l * 0 + car_r * 1.4 * math.sin(PI2 * 7.3 * t + 1)
    out = remap(pl, sx, sy)

    # brillo del asfalto (reflejos que respiran)
    out *= 1 + road_w[..., None] * (0.07 * math.sin(PI2 * t / 1.6) * np.sin(xx / 60.0 + t * 2.0)[..., None])

    # ---- trafico: estelas de luz sobre el asfalto
    for ys, dr, spd, ph0, ln, col, hh in STREAKS:
        per = OW + 2 * ln
        x = ((ph0 * per + t * spd * dr) % per) - ln
        if dr < 0:
            x = per - ln - (((ph0 * per + t * spd) % per))
        edge = 1.0 - abs((x / OW) - 0.5) * 1.4
        draw_streak(out, x, ys * FY, dr, ln, col, hh, 0.85 * clip01(edge + 0.3))

    # ---- particulas lejanas
    for k in range(NP):
        if P_Z[k] >= 0.55:
            continue
        px = (P_X[k] + 26 * math.sin(t * 0.9 + P_PH[k]) + pan_s * P_Z[k]) % OW
        py = (P_Y[k] - P_VY[k] * t) % (OH + 120) - 60
        tw = 0.55 + 0.45 * math.sin(PI2 * t * (0.6 + P_Z[k]) + P_PH[k])
        add_glow(out, px, py, P_R[k], P_COL[k], 0.55 * tw)

    # ---- avatar (anda hacia camara, balanceo, rim light cambiante)
    th = math.radians(1.3) * math.sin(ph)
    tx = 9.0 * math.sin(ph) + shx_i * 0.6
    ty = -10.0 * abs(math.sin(ph)) + shy_i * 0.5
    S_av = BASE + (Z_FAR + (Z_NEAR - Z_FAR) * D_AV) * e + pun
    dwa = 0.15 + 0.85 * D_AV
    x0, y0, x1, y1 = AVB
    x0 = max(0, x0 - 90); x1 = min(OW, x1 + 90); y0 = max(0, y0 - 60); y1 = min(OH, y1 + 100)
    # disco: arcoiris que gira + destello
    hue = hue_rot(disc_av_c, PI2 * t / 3.2)
    base = disc_av_c
    glint = np.exp(-(((ex[DY0:DY1, DX0:DX1] / (182 * FX)) * 0.9 + ((-(xx[DY0:DY1, DX0:DX1] - cxd) * sa_ + (yy[DY0:DY1, DX0:DX1] - cyd) * ca_) / (122 * FY)) * 0.45 - (((t % 2.6) / 1.1) * 2.4 - 1.5)) / 0.16) ** 2)
    newc = base * (1 - disc_m_c[..., None]) + hue * disc_m_c[..., None]
    newc = newc + (glint * disc_m_c * 0.45)[..., None]
    newc = np.clip(newc, 0, 1)
    av_pm[DY0:DY1, DX0:DX1, :3] = newc * disc_a_c[..., None]
    ux = np.arange(x0, x1, dtype=F32)[None, :] + 0 * np.arange(y0, y1, dtype=F32)[:, None]
    uy = np.arange(y0, y1, dtype=F32)[:, None] + 0 * np.arange(x0, x1, dtype=F32)[None, :]
    # deshace camara (mismo pivote/zoom/paneo que el fondo a profundidad D_AV)
    cxp = CAM_C[0] + (ux - CAM_C[0] - pan_s * dwa) / S_av
    cyp = CAM_C[1] + (uy - CAM_C[1] - crane * dwa) / S_av
    # deshace caminata (balanceo, rebote, inclinacion) sobre los pies
    qx = cxp - AV_ANCHOR[0] - tx
    qy = cyp - AV_ANCHOR[1] - ty
    c, sn = math.cos(-th), math.sin(-th)
    px = AV_ANCHOR[0] + (c * qx - sn * qy)
    py = AV_ANCHOR[1] + (sn * qx + c * qy)
    h = np.clip((py - 1180.0) / 480.0, 0, 1); h = h * h * (3 - 2 * h)
    g = np.tanh((px - LEG_X) / 22.0)
    py = py + LEG_AMP * math.sin(ph) * g * h
    r = remap(av_stack, px, py)
    a = r[..., 3:4]
    mixk = 0.5 + 0.5 * math.sin(PI2 * t / 2.4)
    lft = np.asarray((0.15, 0.85, 1.0), F32) * (1 - mixk) + np.asarray((1.0, 0.2, 0.7), F32) * mixk
    rgt = np.asarray((1.0, 0.2, 0.7), F32) * (1 - mixk) + np.asarray((0.15, 0.85, 1.0), F32) * mixk
    xk = np.clip((np.arange(x0, x1, dtype=F32)[None, :, None] - 450.0) / 260.0, 0, 1)
    tint = lft * (1 - xk) + rgt * xk
    inten = 0.8 + 0.25 * math.sin(PI2 * t * 1.3)
    reg = out[y0:y1, x0:x1]
    reg = reg + r[..., 4:5] * tint * inten * (1 - a)
    out[y0:y1, x0:x1] = reg * (1 - a) + r[..., :3]

    # ---- particulas cercanas
    for k in range(NP):
        if P_Z[k] < 0.55:
            continue
        px_ = (P_X[k] + 34 * math.sin(t * 0.8 + P_PH[k]) + pan_s * P_Z[k] * 1.6) % OW
        py_ = (P_Y[k] - P_VY[k] * t) % (OH + 120) - 60
        tw = 0.5 + 0.5 * math.sin(PI2 * t * (0.5 + P_Z[k]) + P_PH[k])
        add_glow(out, px_, py_, P_R[k], P_COL[k], 0.7 * tw)

    # ---- overlay (HUD) con animacion
    jx, jy = shx_i * 0.45, shy_i * 0.45
    fade = clip01((t - 0.5) / 0.4)
    blit(out, G["hud_l"], alpha=fade, dx=jx, dy=jy)
    blit(out, G["hud_r"], alpha=fade, dx=jx + 7 * math.sin(PI2 * t / 0.9) * fade, dy=jy)
    # mapa con radar
    d = t - 0.7
    if d > 0:
        sweep_a = (PI2 * t / 2.0) % PI2

        def radar(img, sweep_a=sweep_a, t=t):
            inside = (MAP_RAD < MAPR - 4).astype(F32)
            dd = (sweep_a - MAP_ANG) % PI2
            sw = np.exp(-dd / 0.55) * inside
            ring = np.exp(-((MAP_RAD - ((t % 1.4) / 1.4) * MAPR) / 7.0) ** 2) * inside * (1 - (t % 1.4) / 1.4) * 0.8
            img[..., :3] += ((sw * 0.55 + ring * 0.5)[..., None]) * np.asarray((0.35, 1.0, 0.7), F32)
            img[..., 3] = np.maximum(img[..., 3], np.clip(sw + ring, 0, 1) * inside * 0.5)
        blit(out, G["map"], sc=back(d / 0.4), alpha=clip01(d / 0.15), dx=jx, dy=jy, extra=radar)
    # MISION / CUMPLIDA (impacto)
    for name, t0 in (("mision", 2.55), ("cumplida", 2.90)):
        d = t - t0
        if d >= 0:
            sc = 1 + 1.6 * math.exp(-d * 24) + 0.06 * math.sin(PI2 * 4 * d) * math.exp(-d * 8)
            sc *= 1 + 0.012 * math.sin(PI2 * t / 1.2 + (0.6 if name == "cumplida" else 0)) * clip01(d - 0.5)
            sp = (((t - 3.6 - (0.25 if name == "cumplida" else 0)) % 3.2) / 0.9)
            blit(out, G[name], sc=sc, alpha=clip01(d / 0.06), dx=jx, dy=jy - 2 * math.sin(PI2 * t / 1.2), white=0.5 * math.exp(-d * 14),
                 shine=sp if (t > 3.6 and sp < 1) else None)
    # objeto desbloqueado / repartidor / mejora
    for name, t0, dirx, dist in (("objeto", 4.1, -1, 560), ("repart", 5.2, 1, 560), ("mejora", 5.45, 1, 560)):
        d = t - t0
        if d >= 0:
            off = dirx * dist * (1 - eo(d / 0.55))
            sp = (((t - t0 - 0.8) % 3.0) / 0.9)
            blit(out, G[name], alpha=clip01(d / 0.2), dx=jx + off, dy=jy + (3 * math.sin(PI2 * t / 1.5) if name == "objeto" else 0),
                 shine=sp if (d > 0.8 and sp < 1) else None)
    # estrellas de busqueda
    for k in range(5):
        t0 = 6.0 + 0.35 * k
        d = t - t0
        if d >= 0:
            sc = back(d / 0.4) * (1 + 0.04 * math.sin(PI2 * t * 1.6 + k * 0.7) * clip01(d - 0.5))
            wh = 0.9 * math.exp(-d * 10) + (0.35 * max(0.0, math.sin(PI2 * 1.6 * t - k * 0.9)) if t > 7.9 else 0)
            blit(out, G[f"star{k}"], sc=sc, alpha=clip01(d / 0.1), rot=(1 - eo(d / 0.5)) * -1.4, white=wh, dx=jx, dy=jy)
            if d < 0.6:
                add_glow(out, G[f"star{k}"]["ax"] + jx, G[f"star{k}"]["ay"] + jy, 60 + 90 * d, (1.0, 0.8, 0.25), 0.85 * math.exp(-d * 6))
    d = t - 7.9
    if d >= 0:
        sp = (((t - 8.6) % 3.0) / 0.9)
        blit(out, G["logo"], sc=0.7 + 0.3 * back(d / 0.5), alpha=clip01(d / 0.2), dx=jx, dy=jy, shine=sp if (t > 8.6 and sp < 1) else None)

    # ---- onda de choque en los impactos
    for ti, cx, cy in ((2.55, 540 * 1.0, 1000.0), (2.90, 540.0, 1150.0)):
        d = t - ti
        if 0 <= d < 0.55:
            rad = np.hypot(xx - cx, yy - cy)
            ring = np.exp(-((rad - 1100 * d) / 34.0) ** 2) * 0.35 * math.exp(-d * 5)
            out += ring[..., None] * np.asarray((1.0, 0.85, 0.9), F32)

    # ---- postproceso: pulso de neon, flash, aberracion cromatica, viñeta, grano, fundido
    nb = 0.03 * math.sin(PI2 * t / 2.4)
    out *= np.asarray((1 + nb, 1.0, 1 - nb), F32)
    fl = 0.0
    for ti, A in IMP[:2]:
        if t >= ti:
            fl += 0.30 * math.exp(-(t - ti) * 16)
    for ti, A in IMP[2:]:
        if t >= ti:
            fl += 0.07 * math.exp(-(t - ti) * 14)
    out += fl * np.asarray((1.0, 0.93, 0.88), F32)
    k = int(round(min(9.0, ca * 0.35)))
    if k >= 1:
        out[..., 0] = np.roll(out[..., 0], k, axis=1)
        out[..., 2] = np.roll(out[..., 2], -k, axis=1)
    out *= VIG
    rng = np.random.default_rng(1000 + i)
    out += rng.standard_normal((OH, OW, 1)).astype(F32) * 0.012
    out *= clip01(t / 0.45) ** 0.8
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


if __name__ == "__main__":
    probe = [int(a) for a in sys.argv[4:]]
    if probe:
        import time
        for i in probe:
            t0 = time.time()
            Image.fromarray(frame(i)).save(f"{W}/probe_{i:03d}.png")
            print("frame", i, round(time.time() - t0, 2), "s", flush=True)
        sys.exit(0)
    n = int(T * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS),
         "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
         "-profile:v", "high", "-movflags", "+faststart", OUT],
        stdin=subprocess.PIPE)
    with Pool(4) as p:
        for k, fr in enumerate(p.imap(frame, range(n), chunksize=2)):
            ff.stdin.write(fr.tobytes())
            if k % 30 == 0:
                print("frame", k, "/", n, flush=True)
    ff.stdin.close(); ff.wait()
    print("done", OUT)
