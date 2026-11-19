"""Renderiza el video 9:16 con parallax desde las capas. Uso: render.py W OUT.mp4 [T_seg] [frames_a_probar...]"""
import numpy as np, sys, subprocess, math
from multiprocessing import Pool
from PIL import Image

W = sys.argv[1]
OUT = sys.argv[2]
T = float(sys.argv[3]) if len(sys.argv) > 3 else 8.0
FPS = 30
OW, OH = 1080, 1920
L = f"{W}/layers"
full = np.load(f"{L}/full.npy").astype(np.float32)
plate = np.load(f"{L}/plate.npy").astype(np.float32)
av_a = np.load(f"{L}/avatar_a.npy").astype(np.float32)
ov_a = np.load(f"{L}/overlay_a.npy").astype(np.float32)
depth = np.load(f"{L}/depth.npy").astype(np.float32)
av_rgb = np.load(f"{L}/avatar_rgb.npy").astype(np.float32)
av_pm = np.concatenate([av_rgb * av_a[..., None], av_a[..., None]], -1)  # premultiplicado + alfa
yy, xx = np.mgrid[0:OH, 0:OW].astype(np.float32)


def remap(img, sx, sy):
    h, w = img.shape[:2]
    sx = np.clip(sx, 0, w - 1.001); sy = np.clip(sy, 0, h - 1.001)
    x0 = sx.astype(np.int32); y0 = sy.astype(np.int32)
    fx = (sx - x0)[..., None]; fy = (sy - y0)[..., None]
    a = img[y0, x0]; b = img[y0, x0 + 1]; c = img[y0 + 1, x0]; d = img[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


# parametros de movimiento
CAM_C = (540.0, 1300.0)            # punto de fuga (horizonte)
Z_FAR, Z_NEAR = 0.012, 0.075      # zoom total fondo lejos / cerca
PAN = 14.0                         # px de vaiven lateral de camara (capa cercana)
AV_ANCHOR = (540.0, 1560.0)
AV_GROW = 0.10                     # el avatar crece 10% al "acercarse"
STEP_T = 1.25                      # s por ciclo completo de paso (izq+der)
LEG_AMP = 9.0
LEG_X = 460.0


def frame(i):
    t = i / FPS
    u = t / T
    e = smooth(u)
    ph = 2 * math.pi * t / STEP_T
    # ---- fondo con parallax por profundidad
    Z = (Z_FAR + (Z_NEAR - Z_FAR) * depth) * e
    S = 1.0 + Z
    pan = PAN * math.sin(2 * math.pi * u * 0.8 + 0.4)
    shx = pan * (0.12 + 0.88 * depth)
    shy = -3.0 * math.sin(ph * 2) * (0.2 + 0.8 * depth)  # micro bob de camara con los pasos
    sx = CAM_C[0] + (xx - CAM_C[0] - shx) / S
    sy = CAM_C[1] + (yy - CAM_C[1] - shy) / S
    bg = remap(plate, sx, sy)
    # ---- avatar: crece, se balancea y "pisa"
    s = 1.0 + AV_GROW * e + 0.004 * math.sin(ph * 2)
    th = math.radians(0.9) * math.sin(ph)
    tx = 7.0 * math.sin(ph) + 10.0 * math.sin(2 * math.pi * u * 0.8 + 0.4) * 0.3
    ty = -7.0 * abs(math.sin(ph)) + 30.0 * e   # baja un poco al acercarse
    qx = xx - AV_ANCHOR[0] - tx
    qy = yy - AV_ANCHOR[1] - ty
    c, sn = math.cos(-th), math.sin(-th)
    px = AV_ANCHOR[0] + (c * qx - sn * qy) / s
    py = AV_ANCHOR[1] + (sn * qx + c * qy) / s
    # animacion de piernas: pies alternan subiendo/bajando (desplazamiento vertical que crece hacia los pies)
    h = np.clip((py - 1180.0) / 480.0, 0, 1); h = h * h * (3 - 2 * h)
    g = np.tanh((px - LEG_X) / 22.0)
    py = py + LEG_AMP * math.sin(ph) * g * h
    a = remap(av_pm, px, py)
    out = bg * (1 - a[..., 3:4]) + a[..., :3]
    # ---- overlay estatico (texto, logo, estrellas, minimapa) intacto
    out = out * (1 - ov_a[..., None]) + full * ov_a[..., None]
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
