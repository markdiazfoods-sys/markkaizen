#!/usr/bin/env python3
"""MARK KAIZEN · Pieza viral 02 · TikTok 9:16 (1080x1920, 30 fps, 30 s).
Uso: python3 render.py [salida.mp4]
Requiere: numpy, Pillow, ffmpeg. Fuentes y logos salen del repo (docs/fuente, img/)."""
import math, subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "mark_kaizen_pieza-viral-02-hercules_tiktok_9x16.mp4")
W, H, FPS, DUR = 1080, 1920, 30, 30
BG, WHITE, ORANGE = (11, 11, 15), (255, 255, 255), (255, 107, 0)
FD = os.path.join(ROOT, "docs", "fuente", "fuentes")
def font(name, size): return ImageFont.truetype(os.path.join(FD, name), size)
SORA = lambda s: font("Sora-recorte.ttf", s)
INTER = lambda s: font("Inter-recorte.ttf", s)
JP = lambda s: font("NotoSansJP-recorte.ttf", s)

logo = Image.open(os.path.join(ROOT, "img", "logo-mark-kaizen.webp")).convert("RGB")
sym = Image.open(os.path.join(ROOT, "img", "simbolo.webp")).convert("RGBA")

def ease(t):  # cubic-bezier(.2,.8,.2,1) aproximada
    t = max(0.0, min(1.0, t)); return 1 - (1 - t) ** 4
def clamp(x): return max(0.0, min(1.0, x))

def fit_font(draw, text, fnt_fn, maxw, start):
    s = start
    while s > 20 and draw.textlength(text, font=fnt_fn(s)) > maxw: s -= 4
    return fnt_fn(s)

def text_c(d, y, text, fnt, fill, alpha=1.0, dy=0, cx=W // 2):
    w = d.textlength(text, font=fnt)
    col = tuple(int(BG[i] + (fill[i] - BG[i]) * alpha) for i in range(3))
    d.text((cx - w / 2, y + dy), text, font=fnt, fill=col)
    return w

def paste_sym(img, size, cx, cy, alpha=1.0):
    s = sym.resize((size, size), Image.LANCZOS)
    if alpha < 1: s.putalpha(s.getchannel("A").point(lambda v: int(v * alpha)))
    img.paste(s, (int(cx - size / 2), int(cy - size / 2)), s)

def caption(d, t, t0, t1, text):
    """Subtítulo de la voz (Inter), zona segura de TikTok (y 1290-1450)."""
    if not (t0 <= t < t1): return
    a = ease((t - t0) / 0.25) * clamp((t1 - t) / 0.2)
    f = INTER(44)
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if d.textlength(trial, font=f) > 860 and cur: lines.append(cur); cur = w_
        else: cur = trial
    lines.append(cur)
    for i, ln in enumerate(lines):
        text_c(d, 1290 + i * 60, ln, f, WHITE, alpha=0.9 * a, dy=(1 - a) * 14)

def flash(img, t, at, dur=0.18):
    k = clamp(1 - abs(t - at) / dur)
    if k > 0:
        ov = Image.new("RGB", (W, H), ORANGE)
        img.paste(Image.blend(img, ov, 0.35 * k))

def light(img, strength=1.0):
    """Luz lateral naranja suave (borde izquierdo)."""
    g = Image.new("L", (W, H), 0); gd = ImageDraw.Draw(g)
    gd.ellipse((-700, 500, 300, 1500), fill=int(60 * strength))
    g = g.filter(ImageFilter.GaussianBlur(160))
    img.paste(Image.new("RGB", (W, H), ORANGE), (0, 0), g)

def draw_line(d, x0, x1, y, p, width=8):
    d.rectangle((x0, y, x0 + (x1 - x0) * ease(p), y + width), fill=ORANGE)

def step(img, d, t, t0, num, label):
    lt = t - t0
    a = ease(lt / 0.35)
    text_c(d, 560, str(num), JP(420) if False else SORA(420), ORANGE, a, dy=(1 - a) * 60)
    a2 = ease((lt - 0.1) / 0.35)
    f = fit_font(d, label, SORA, 900, 84)
    text_c(d, 1050, label, f, WHITE, a2, dy=(1 - a2) * 40)
    draw_line(d, 270, 810, 1170, (lt - 0.3) / 0.5)

def frame(t):
    img = Image.new("RGB", (W, H), BG)
    light(img, 1.0)
    d = ImageDraw.Draw(img)
    zoom = 1.0
    # HOOK 0-2
    if t < 2:
        k = ease(t / 0.4)
        paste_sym(img, 300, W // 2, 420, k)
        a = ease((t - 0.1) / 0.3)
        text_c(d, 760, "12 TRABAJOS.", fit_font(d, "12 TRABAJOS.", SORA, 940, 190), ORANGE, a, dy=(1 - a) * 50)
        a = ease((t - 0.35) / 0.3)
        text_c(d, 1000, "CERO MAGIA", fit_font(d, "CERO MAGIA", SORA, 940, 100), WHITE, a, dy=(1 - a) * 40)
        caption(d, t, 0.2, 2.0, "Hércules no se volvió leyenda por fuerza. Se volvió leyenda por repetir.")
        flash(img, t, 0.3)
    # 2-6
    elif t < 6:
        lt = t - 2; z = 1 + 0.08 * (lt / 4)
        a = ease(lt / 0.3)
        text_c(d, 700, "INVENCIBLE", SORA(130), WHITE, a, dy=(1 - a) * 40)
        w = d.textlength("INVENCIBLE", font=SORA(130))
        if lt > 0.8:  # tachado naranja
            p = ease((lt - 0.8) / 0.35)
            d.rectangle((W / 2 - w / 2, 790, W / 2 - w / 2 + w * p, 806), fill=ORANGE)
        a = ease((lt - 1.4) / 0.35)
        text_c(d, 960, "LO LOGRÓ REPITIENDO.", fit_font(d, "LO LOGRÓ REPITIENDO.", SORA, 940, 96), ORANGE, a, dy=(1 - a) * 40)
        caption(d, t, 2.0, 6.0, "Hércules no nació invencible. Hizo doce trabajos, uno por uno, y falló antes de dominarlos.")
        if z > 1: img = img.crop((0, 0, W, H)).resize((int(W * z), int(H * z)), Image.LANCZOS).crop(((int(W * z) - W) // 2, (int(H * z) - H) // 2, (int(W * z) - W) // 2 + W, (int(H * z) - H) // 2 + H)); d = ImageDraw.Draw(img)
    # 6-9 bucle abierto
    elif t < 9:
        lt = t - 6
        a = ease(lt / 0.3)
        text_c(d, 760, "LA LECCIÓN,", fit_font(d, "LA LECCIÓN,", SORA, 940, 170), WHITE, a, dy=(1 - a) * 40)
        a = ease((lt - 0.25) / 0.3)
        text_c(d, 960, "AL FINAL", SORA(170), ORANGE, a, dy=(1 - a) * 40)
        draw_line(d, 200, 880, 1180, (lt - 0.6) / 0.8)
        caption(d, t, 6.0, 9.0, "Te la explico en tres pasos. Al final te dejo la que uso en mi marca.")
    elif t < 15:
        step(img, d, t, 9, 1, "ELIGE UN LEÓN"); d = ImageDraw.Draw(img)
        caption(d, t, 9.0, 15.0, "Uno. Elige un solo trabajo y empieza hoy.")
    elif t < 20:
        step(img, d, t, 15, 2, "REPITE"); d = ImageDraw.Draw(img)
        caption(d, t, 15.0, 20.0, "Dos. Repite hasta que deje de costar. Así cae la hidra.")
    elif t < 24:
        step(img, d, t, 20, 3, "MEJORA 1%"); d = ImageDraw.Draw(img)
        caption(d, t, 20.0, 24.0, "Tres. En cada vuelta, mejora una sola cosa.")
    # 24-27 símbolo + 改善
    elif t < 27:
        lt = t - 24
        size = int(W * 0.78)
        cx, cy = W // 2, 620
        p = clamp(lt / 1.2)
        ring = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rd = ImageDraw.Draw(ring)
        r = size // 2
        rd.arc((cx - r, cy - r, cx + r, cy + r), -90, -90 + 360 * ease(p), fill=ORANGE + (255,), width=16)
        img.paste(ring, (0, 0), ring)
        if lt > 1.0:
            a = ease((lt - 1.0) / 0.5)
            s = sym.resize((int(size * 0.92), int(size * 0.92)), Image.LANCZOS)
            s.putalpha(s.getchannel("A").point(lambda v: int(v * a)))
            img.paste(s, (cx - s.width // 2, cy - s.height // 2), s)
        a = ease((lt - 1.3) / 0.4)
        text_c(d, 1090, "改善", JP(120), WHITE, a, dy=(1 - a) * 30)
        caption(d, t, 24.0, 27.0, "Mejora. Prueba. Aprende. Repite. Eso es kaizen.")
        flash(img, t, 25.0, 0.15)
    # 27-30 cierre / CTA
    else:
        lt = t - 27
        a = ease(lt / 0.4)
        paste_sym(img, 340, W // 2, 430, a)
        text_c(d, 700, "¿CUÁL ES TU HIDRA?", fit_font(d, "¿CUÁL ES TU HIDRA?", SORA, 940, 92), WHITE, ease((lt - 0.2) / 0.3))
        bw, bh, by = 760, 150, 1000
        k = ease((lt - 0.5) / 0.4)
        sw, sh = int(bw * k), int(bh * k)
        if sw > 4:
            d.rounded_rectangle((W // 2 - sw // 2, by + (bh - sh) // 2, W // 2 + sw // 2, by + (bh + sh) // 2), radius=36, fill=ORANGE)
            if k > 0.85: text_c(d, by + 34, "COMENTA: KAIZEN", SORA(64), (11, 11, 15))
        caption(d, t, 27.0, 30.0, "¿Qué trabajo llevas meses evitando? Comenta KAIZEN y te digo por dónde empezar.")
        flash(img, t, 27.55, 0.15)
        paste_sym(img, 130, W - 130, 160, 0.9)
    # marca de agua en pasos 1-3
    if 9 <= t < 24: paste_sym(img, 110, W - 130, 160, 0.8)
    return img

def main():
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", f"aevalsrc='0.35*sin(2*PI*55*t)*exp(-6*mod(t,30))*(lt(t,1)) + 0.30*sin(2*PI*50*(t-24))*exp(-5*(t-24))*(gte(t,24))*(lt(t,27))':s=44100:d={DUR}",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(FPS * DUR):
        p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait()
    print("OK", OUT)

if __name__ == "__main__": main()
