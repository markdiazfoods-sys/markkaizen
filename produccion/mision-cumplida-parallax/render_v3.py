"""Video 9:16 "Misión cumplida" v3 — dinámico, estilo pantalla de carga GTA / Vice City.
Uso: render_v3.py CARPETA SALIDA.mp4 [T_seg] [frames_a_probar...]
Requiere las capas de build_layers.py en CARPETA/layers. Solo numpy + Pillow + ffmpeg.

Movimiento: dolly-in con parallax por profundidad, vaivén + temblor de cámara, nubes a la deriva,
palmeras que se mecen, ventanas de rascacielos que parpadean, luces de freno/faros pulsando,
estelas de tráfico, reflejos de asfalto mojado, bokeh de neón, avatar caminando con luz de contorno
magenta/cian y disco holográfico con destello, textos que entran con golpe (slam) + flash + shake,
estrellas que aparecen una a una y minimapa con radar."""
import numpy as np, sys, subprocess, math
from multiprocessing import Pool
from PIL import Image, ImageFilter

W = sys.argv[1]
OUT = sys.argv[2]
T = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
FPS = 30
OW, OH = 1080, 1920
KX, KY = OW / 899.0, OH / 1599.0
L = f"{W}/layers"
f32 = lambda n: np.load(f"{L}/{n}.npy").astype(np.float32)
full, plate, av_a, ov_a, depth, av_rgb = (f32(n) for n in ("full", "plate", "avatar_a", "overlay_a", "depth", "avatar_rgb"))
yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)


def smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def c01(x):
    return min(max(x, 0.0), 1.0)


def sm_arr(a, lo, hi):
    u = np.clip((a - lo) / (hi - lo), 0, 1)
    return u * u * (3 - 2 * u)


def blur8(a, r):
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r)), dtype=np.float32) / 255.0


def remap(img, sx, sy):
    h, w = img.shape[:2]
    sx = np.clip(sx, 0, w - 1.001); sy = np.clip(sy, 0, h - 1.001)
    x0 = sx.astype(np.int32); y0 = sy.astype(np.int32)
    fx = (sx - x0)[..., None]; fy = (sy - y0)[..., None]
    a = img[y0, x0]; b = img[y0, x0 + 1]; c = img[y0 + 1, x0]; d = img[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


# ------------------------------------------------------------------ pesos estaticos del fondo
luma_p = plate @ np.array([0.299, 0.587, 0.114], np.float32)
sky_w = np.clip((0.085 - depth) / 0.05, 0, 1) * (yy < 1150)                      # nubes
hf = np.clip((1230.0 - yy) / 900.0, 0, 1) ** 1.4                                   # mas movimiento arriba
palm_w = sm_arr(depth, 0.28, 0.38) * np.clip((0.90 - depth) / 0.05, 0, 1) * hf    # palmeras (no el coche)
road_w = sm_arr(yy, 1400, 1520)                                                    # asfalto mojado
lp_img = Image.fromarray((np.clip(luma_p, 0, 1) * 255).astype(np.uint8))
lp6 = np.asarray(lp_img.filter(ImageFilter.GaussianBlur(5)), np.float32) / 255.0
lp14 = np.asarray(lp_img.filter(ImageFilter.GaussianBlur(14)), np.float32) / 255.0
win = ((depth > 0.09) & (depth < 0.22) & (yy < 1400) & (luma_p - lp6 > 0.10) & (lp14 < 0.48)).astype(np.float32)
win = blur8(win, 1.2)
plate4 = np.concatenate([plate, win[..., None]], -1)
rng = np.random.default_rng(11)
fr_lo = rng.uniform(0.35, 1.6, (OH // 3, OW // 3)).astype(np.float32)
ph_lo = rng.uniform(0, 6.283, (OH // 3, OW // 3)).astype(np.float32)
flk_f = np.kron(fr_lo, np.ones((3, 3), np.float32))
flk_p = np.kron(ph_lo, np.ones((3, 3), np.float32))
vig = 1.0 - 0.38 * np.clip(np.sqrt(((xx - 540) / 700.0) ** 2 + ((yy - 980) / 1150.0) ** 2) - 0.35, 0, 1) ** 1.6

# ------------------------------------------------------------------ avatar: ventana + canales extra
AX0, AX1, AY0, AY1 = 100, 980, 100, 1880
ds = np.float32
cx_d, cy_d, rx_d, ry_d, ang = 485 * KX, 650 * KY, 175 * KX, 105 * KY, math.radians(22)
uu = (xx - cx_d) * math.cos(ang) + (yy - cy_d) * math.sin(ang)
vv = -(xx - cx_d) * math.sin(ang) + (yy - cy_d) * math.cos(ang)
rn = np.sqrt((uu / rx_d) ** 2 + (vv / ry_d) ** 2)
disc = np.clip((1.0 - rn) / 0.06, 0, 1) * av_a
ring = sm_arr(rn, 0.58, 0.72) * (1 - sm_arr(rn, 0.70, 0.78)) * disc
glow = np.clip(blur8(av_a, 26) * 1.7, 0, 1)
av7 = np.concatenate([av_rgb * av_a[..., None], av_a[..., None], glow[..., None], ring[..., None], disc[..., None]], -1)
av7 = av7[AY0:AY1, AX0:AX1].astype(np.float32)
ayy, axx = yy[AY0:AY1, AX0:AX1], xx[AY0:AY1, AX0:AX1]

# ------------------------------------------------------------------ grupos de overlay (texto/UI) para animarlos por separado
GROUPS = {}


def mk_group(name, rect, pad=8):
    x0, y0, x1, y1 = rect
    X0, Y0, X1, Y1 = int(x0 * KX), int(y0 * KY), int(x1 * KX), int(y1 * KY)
    a = np.zeros((OH, OW), np.float32)
    a[Y0:Y1, X0:X1] = ov_a[Y0:Y1, X0:X1]
    bx0, by0, bx1, by1 = max(X0 - pad, 0), max(Y0 - pad, 0), min(X1 + pad, OW), min(Y1 + pad, OH)
    aa = a[by0:by1, bx0:bx1]
    crop = np.concatenate([full[by0:by1, bx0:bx1] * aa[..., None], aa[..., None]], -1).astype(np.float32)
    GROUPS[name] = dict(crop=crop, box=(bx0, by0, bx1, by1), c=((X0 + X1) / 2.0, (Y0 + Y1) / 2.0))


mk_group("uno", (30, 44, 120, 96))
mk_group("desliza", (730, 44, 866, 96))
mk_group("mision", (240, 796, 662, 976))
mk_group("cumplida", (150, 976, 750, 1122))
mk_group("objeto", (190, 1122, 715, 1215))
mk_group("repartidor", (475, 1290, 862, 1380))
STAR_X = [508, 577, 646, 714, 782, 852]
for k in range(5):
    mk_group(f"star{k}", (STAR_X[k], 1380, STAR_X[k + 1], 1462))
mk_group("mark", (545, 1466, 862, 1535))
mk_group("mapa", (40, 1264, 330, 1552))
STAR_C = [(543 * KX, 1422 * KY), (611 * KX, 1422 * KY), (680 * KX, 1422 * KY), (748 * KX, 1422 * KY), (816 * KX, 1422 * KY)]
MAP_C, MAP_R = (184.5 * KX, 1408.0 * KY), 141.0 * KX


def place(out, name, sc, dx, dy, al):
    if al <= 0.003:
        return
    g = GROUPS[name]
    crop = g["crop"]; x0, y0, x1, y1 = g["box"]; cx, cy = g["c"]
    hw = (x1 - x0) / 2.0 * sc + abs(dx) + 8
    hh = (y1 - y0) / 2.0 * sc + abs(dy) + 8
    wx0, wx1 = int(max(0, cx + dx - hw)), int(min(OW, cx + dx + hw))
    wy0, wy1 = int(max(0, cy + dy - hh)), int(min(OH, cy + dy + hh))
    if wx1 <= wx0 or wy1 <= wy0:
        return
    gy, gx = np.mgrid[wy0:wy1, wx0:wx1].astype(np.float32)
    sx = cx + (gx - cx - dx) / sc - x0
    sy = cy + (gy - cy - dy) / sc - y0
    r = remap(crop, sx, sy)
    a = (r[..., 3] * al)[..., None]
    out[wy0:wy1, wx0:wx1] = out[wy0:wy1, wx0:wx1] * (1 - a) + r[..., :3] * al


def blob(out, cx, cy, sx, sy, color, amp):
    if amp <= 0.002:
        return
    x0, x1 = int(max(0, cx - 3 * sx)), int(min(OW, cx + 3 * sx))
    y0, y1 = int(max(0, cy - 3 * sy)), int(min(OH, cy + 3 * sy))
    if x1 <= x0 or y1 <= y0:
        return
    gy, gx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    g = np.exp(-(((gx - cx) / sx) ** 2 + ((gy - cy) / sy) ** 2) / 2.0) * amp
    out[y0:y1, x0:x1] += g[..., None] * np.array(color, np.float32)


# ------------------------------------------------------------------ animaciones
def eob(u):  # ease out back
    c1 = 1.70158; c3 = c1 + 1; u = u - 1
    return 1 + c3 * u ** 3 + c1 * u ** 2


def slam(t, t0, dur, big=0.9):
    u = c01((t - t0) / dur)
    sc = 1 + big * (1 - u) ** 3
    dt = t - (t0 + dur)
    if dt > 0:
        sc *= 1 + 0.05 * math.exp(-dt * 9) * math.cos(dt * 28)
    return sc, 0.0, 0.0, c01((t - t0) / dur * 3)


def slide(t, t0, dur, dxs):
    u = c01((t - t0) / dur)
    return 1.0, dxs * (1 - u) ** 3, 0.0, c01(u * 3)


def fade_up(t, t0, dur, dy=26):
    u = c01((t - t0) / dur)
    return 1.0, 0.0, dy * (1 - u) ** 2, u


def star_pop(t, t0):
    u = c01((t - t0) / 0.3)
    sc = 1 + 1.3 * (1 - u) ** 2
    dt = t - (t0 + 0.3)
    if dt > 0:
        sc *= 1 + 0.16 * math.exp(-dt * 8) * math.cos(dt * 24)
        sc *= 1 + 0.045 * math.sin(2 * math.pi * (t - t0) / 1.4)   # titileo
    return sc, 0.0, 0.0, c01((t - t0) / 0.3 * 2.5)


IMPACTS = [(1.15, 11.0), (1.55, 11.0), (2.40, 6.0)] + [(3.3 + k * 0.28, 3.0) for k in range(5)]
STAR_T0 = [3.0 + k * 0.28 for k in range(5)]

# bokeh y estelas
rng = np.random.default_rng(7)
BOKEH = [(rng.uniform(0, OW), rng.uniform(0, OH + 200), rng.uniform(30, 95), rng.uniform(5, 17),
          [(1, .35, .7), (.3, .9, 1), (1, .7, .25)][i % 3], rng.uniform(0, 6.28)) for i in range(26)]
STREAKS = [(1338, 2.3, .10, (1, .45, .2), 4.0, 1), (1398, 3.1, .55, (.3, .85, 1), 3.0, -1),
           (1472, 1.7, .80, (1, .2, .6), 5.0, 1), (1548, 2.7, .30, (1, .9, .6), 3.0, -1),
           (1622, 3.7, .65, (.6, .4, 1), 4.0, 1), (1312, 4.1, .20, (1, 1, .9), 2.5, -1)]

# parametros de camara
CAM_C = (540.0, 1300.0)
Z_BASE, Z_FAR, Z_NEAR = 0.06, 0.02, 0.17
PAN = 26.0
AV_ANCHOR = (540.0, 1560.0)
AV_GROW = 0.17
STEP_T = 1.1
LEG_AMP = 15.0
LEG_X = 460.0


def bgpos(p, d, e, shx_, shy_):
    S = 1.0 + Z_BASE + (Z_FAR + (Z_NEAR - Z_FAR) * d) * e
    return CAM_C[0] + (p[0] - CAM_C[0]) * S + shx_ * (0.12 + 0.88 * d), CAM_C[1] + (p[1] - CAM_C[1]) * S + shy_ * (0.2 + 0.8 * d)


def frame(i):
    t = i / FPS
    u = t / T
    e = smooth(u)
    ph = 2 * math.pi * t / STEP_T
    # --- temblor por impactos
    gx = gy = flash = ca = 0.0
    for ti, amp in IMPACTS:
        dt = t - ti
        if dt >= 0:
            k = math.exp(-dt * 9.0)
            gx += amp * k * math.sin(dt * 55 + ti * 3)
            gy += amp * 0.8 * k * math.cos(dt * 47 + ti)
            flash += (0.20 if amp > 8 else 0.07) * math.exp(-dt * 14)
            ca += amp * 0.6 * k
    # --- fondo
    env = 0.3 + 0.7 * e
    pan = PAN * env * math.sin(2 * math.pi * t / 6.5 + 0.4)
    hand = 2.2 * math.sin(2 * math.pi * t * 1.7) + 1.4 * math.sin(2 * math.pi * t * 2.9 + 1)
    shx = pan + gx + hand
    shy = -30.0 * e - 3.5 * math.sin(2 * ph) + gy + 0.7 * hand
    Z = (Z_FAR + (Z_NEAR - Z_FAR) * depth) * e + Z_BASE
    S = 1.0 + Z
    sx = CAM_C[0] + (xx - CAM_C[0] - shx * (0.12 + 0.88 * depth)) / S
    sy = CAM_C[1] + (yy - CAM_C[1] - shy * (0.2 + 0.8 * depth)) / S
    sway = 20.0 * palm_w * (np.sin(2 * math.pi * t / 2.7 + xx * 0.006 + yy * 0.002)
                            + 0.35 * np.sin(2 * math.pi * t / 1.3 + xx * 0.011))
    shim = 3.6 * road_w * np.sin(yy / 6.5 + t * 7.0)
    sx = sx - sway - shim + sky_w * 20.0 * math.sin(2 * math.pi * t / 10.0)
    bg4 = remap(plate4, sx, sy)
    bg = bg4[..., :3]
    # ventanas parpadeando
    flick = 0.5 + 0.5 * np.sin(2 * math.pi * t * flk_f + flk_p)
    bg = bg + bg * (bg4[..., 3] * flick * 0.55)[..., None]
    # --- luces
    pulse = 0.5 + 0.5 * math.sin(2 * math.pi * t / 1.7)
    blob(bg, 276 + shx * 0.1, 1099, 150, 110, (1.0, 0.5, 0.15), 0.16 + 0.10 * pulse)                    # sol
    px_, py_ = bgpos((1009, 1207), 0.92, e, shx, shy)
    brake = 0.55 + 0.45 * (1.0 if (t * 2.2) % 1.0 < 0.62 else 0.25)
    blob(bg, px_, py_, 70, 40, (1.0, 0.12, 0.16), 0.55 * brake)                                          # luz de freno
    for hx in (72, 175):
        qx, qy = bgpos((hx, 1321), 0.38, e, shx, shy)
        blob(bg, qx, qy, 38, 22, (1.0, 0.85, 0.55), 0.32 + 0.14 * math.sin(2 * math.pi * t / 1.3 + hx))  # faros
    for (y0, per, off, col, sy_, dr) in STREAKS:
        f = (t / per + off) % 1.0
        x = (f if dr > 0 else 1 - f) * (OW + 700) - 350
        fa = math.sin(math.pi * f) ** 0.6
        blob(bg, x, y0, 190, sy_, col, 0.75 * fa)
        blob(bg, x, y0 + 30 + sy_ * 6, 190, sy_ * 3.0, col, 0.14 * fa)                                # reflejo mojado
    # --- avatar
    s = 1.0 + AV_GROW * e + 0.006 * math.sin(ph * 2)
    th = math.radians(1.6) * math.sin(ph)
    tx = 14.0 * math.sin(ph) + 0.3 * pan + gx * 0.6
    ty = -14.0 * abs(math.sin(ph)) + 46.0 * e + gy * 0.6
    qx = axx - AV_ANCHOR[0] - tx
    qy = ayy - AV_ANCHOR[1] - ty
    c, sn = math.cos(-th), math.sin(-th)
    px = AV_ANCHOR[0] + (c * qx - sn * qy) / s - AX0
    py = AV_ANCHOR[1] + (sn * qx + c * qy) / s - AY0
    h = np.clip((py + AY0 - 1180.0) / 480.0, 0, 1); h = h * h * (3 - 2 * h)
    g = np.tanh((px + AX0 - LEG_X) / 22.0)
    py = py + LEG_AMP * math.sin(ph) * g * h
    a7 = remap(av7, px, py)
    A = a7[..., 3:4]
    rgb = a7[..., :3]
    # disco: rotacion de matiz en el aro + destello
    ys0, ys1, xs0, xs1 = 420, 1000, 220, 900
    sub = rgb[ys0 - AY0:ys1 - AY0, xs0 - AX0:xs1 - AX0]
    rw = a7[ys0 - AY0:ys1 - AY0, xs0 - AX0:xs1 - AX0, 5:6]
    dw = a7[ys0 - AY0:ys1 - AY0, xs0 - AX0:xs1 - AX0, 6:7]
    th2 = 2 * math.pi * t / 3.2
    cs, sn2 = math.cos(th2), math.sin(th2)
    Y = sub @ np.array([.299, .587, .114], np.float32)
    I = sub @ np.array([.596, -.274, -.322], np.float32)
    Q = sub @ np.array([.211, -.523, .312], np.float32)
    I2, Q2 = I * cs - Q * sn2, I * sn2 + Q * cs
    rot = np.stack([Y + .956 * I2 + .621 * Q2, Y - .272 * I2 - .647 * Q2, Y - 1.106 * I2 + 1.703 * Q2], -1)
    sub = sub + rw * (rot - sub)
    sy_, sx_ = ayy[ys0 - AY0:ys1 - AY0, xs0 - AX0:xs1 - AX0], axx[ys0 - AY0:ys1 - AY0, xs0 - AX0:xs1 - AX0]
    ss = sx_ * 0.82 + sy_ * 0.57
    cen = 380 + ((t % 2.6) / 2.6) * 900
    gl = np.exp(-((ss - cen) / 38.0) ** 2)[..., None] * dw * 0.75
    sub = sub + gl * np.array([1.0, 0.92, 0.95], np.float32)
    rgb = rgb.copy()
    rgb[ys0 - AY0:ys1 - AY0, xs0 - AX0:xs1 - AX0] = sub
    # luz de contorno magenta/cian
    mix = 0.5 + 0.5 * math.sin(2 * math.pi * t / 1.7)
    rim = (np.array([1.0, 0.18, 0.62], np.float32) * mix + np.array([0.10, 0.85, 1.0], np.float32) * (1 - mix))
    rim_i = 0.55 + 0.30 * math.sin(2 * math.pi * t / 0.85)
    wx0, wx1, wy0, wy1 = AX0, AX1, AY0, AY1
    reg = bg[wy0:wy1, wx0:wx1]
    reg = reg + a7[..., 4:5] * rim * rim_i * 0.8
    reg = reg * (1 - A) + rgb
    out = bg.copy()
    out[wy0:wy1, wx0:wx1] = reg
    # --- bokeh de neon (delante de todo, da profundidad)
    for (bx, by, spd, r, col, bp) in BOKEH:
        yb = (by - t * spd) % (OH + 200) - 100
        xb = bx + 26 * math.sin(t * 0.9 + bp)
        blob(out, xb, yb, r * 0.7, r * 0.7, col, 0.30 + 0.20 * math.sin(t * 2.1 + bp))
    out += flash
    # --- overlay animado
    emerge = c01((t - 0.5) / 0.5)
    place(out, "uno", 1.0, 0, 0, emerge)
    place(out, "desliza", 1.0, 7.0 * math.sin(2 * math.pi * t / 1.1) * emerge, 0, emerge)
    idle = lambda k, a=0.009: 1 + a * math.sin(2 * math.pi * t / 1.7 + k)
    sc, dx, dy, al = slam(t, 0.8, 0.35); place(out, "mision", sc * (idle(0) if t > 1.3 else 1), dx, dy, al)
    sc, dx, dy, al = slam(t, 1.2, 0.35); place(out, "cumplida", sc * (idle(0.6) if t > 1.7 else 1), dx, dy, al)
    sc, dx, dy, al = slide(t, 1.9, 0.5, -420.0); place(out, "objeto", sc * (idle(1.2, 0.006) if t > 2.5 else 1), dx, dy, al)
    sc, dx, dy, al = slide(t, 2.4, 0.5, 420.0); place(out, "repartidor", sc, dx, dy, al)
    for k in range(5):
        sc, dx, dy, al = star_pop(t, STAR_T0[k]); place(out, f"star{k}", sc, dx, dy, al)
        dt = t - (STAR_T0[k] + 0.3)
        if dt >= 0:
            k2 = math.exp(-dt * 6.0)
            blob(out, STAR_C[k][0], STAR_C[k][1], 26, 26, (1.0, 0.95, 0.7), 0.55 * k2)
            blob(out, STAR_C[k][0], STAR_C[k][1], 90, 4, (1.0, 0.95, 0.7), 0.7 * k2)
            blob(out, STAR_C[k][0], STAR_C[k][1], 4, 90, (1.0, 0.95, 0.7), 0.5 * k2)
    place(out, "mark", *fade_up(t, 4.4, 0.6))
    u_m = c01((t - 0.9) / 0.5)
    place(out, "mapa", 0.3 + 0.7 * eob(u_m), 0, 0, c01(u_m * 3))
    # radar del minimapa
    if t > 1.4:
        fr_ = ((t - 1.4) % 1.7) / 1.7
        x0, x1 = int(MAP_C[0] - MAP_R), int(MAP_C[0] + MAP_R)
        y0, y1 = int(MAP_C[1] - MAP_R), int(MAP_C[1] + MAP_R)
        gy_, gx_ = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        d_ = np.sqrt((gx_ - MAP_C[0]) ** 2 + (gy_ - MAP_C[1]) ** 2)
        ringm = np.exp(-((d_ - MAP_R * fr_) / 5.0) ** 2) * (1 - fr_) * 0.75 * (d_ < MAP_R - 3)
        out[y0:y1, x0:x1] += ringm[..., None] * np.array([0.4, 1.0, 0.8], np.float32)
    # --- post: aberracion cromatica en impactos, vineta, grano, fundido de entrada
    if ca > 0.6:
        k = int(ca)
        out[..., 0] = np.roll(out[..., 0], k, axis=1)
        out[..., 2] = np.roll(out[..., 2], -k, axis=1)
    out = out * vig[..., None]
    gr = np.random.default_rng(i).standard_normal((OH // 2, OW // 2)).astype(np.float32) * 0.018
    out = out + np.kron(gr, np.ones((2, 2), np.float32))[..., None]
    out = out * c01(t / 0.4)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)


if __name__ == "__main__":
    probe = [int(a) for a in sys.argv[4:]]
    if probe:
        for i in probe:
            Image.fromarray(frame(i)).save(f"{W}/probe_{i:03d}.png")
        sys.exit(0)
    n = int(T * FPS)
    ff = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS),
         "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
         "-profile:v", "high", "-movflags", "+faststart", OUT],
        stdin=subprocess.PIPE)
    with Pool(4) as p:
        for k, fr in enumerate(p.imap(frame, range(n), chunksize=2)):
            ff.stdin.write(fr.tobytes())
            if k % 30 == 0:
                print("frame", k, "/", n, flush=True)
    ff.stdin.close(); ff.wait()
    print("done", OUT)
