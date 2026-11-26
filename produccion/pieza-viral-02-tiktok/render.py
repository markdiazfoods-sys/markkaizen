#!/usr/bin/env python3
"""MARK KAIZEN · Pieza viral 02 · TikTok 9:16 (1080x1920, 30 fps, 26 s).
"Tu video muere en 2 segundos". Reutiliza helpers de la pieza 01.
Uso: python3 render.py [salida.mp4]   Requiere Pillow + ffmpeg."""
import sys, os, subprocess
MYDIR = os.path.dirname(os.path.abspath(__file__))
HERE = MYDIR
ARG_OUT = sys.argv[1] if len(sys.argv) > 1 else None
sys.argv = sys.argv[:1]
sys.path.insert(0, os.path.join(HERE, "..", "pieza-viral-01-tiktok"))
import render as r
from render import *  # noqa
OUT = ARG_OUT or os.path.join(MYDIR, "mark_kaizen_pieza-viral-02_tiktok_9x16.mp4")
DUR = 26

def frame(t):
    img = Image.new("RGB", (W, H), BG); light(img, 1.0)
    d = ImageDraw.Draw(img)
    if t < 2:  # HOOK
        paste_sym(img, 300, W // 2, 420, ease(t / 0.4))
        a = ease((t - 0.1) / 0.3)
        text_c(d, 740, "TU VIDEO", SORA(150), WHITE, a, dy=(1 - a) * 50)
        a = ease((t - 0.35) / 0.3)
        text_c(d, 930, "MUERE EN 2 s", fit_font(d, "MUERE EN 2 s", SORA, 940, 150), ORANGE, a, dy=(1 - a) * 40)
        caption(d, t, 0.2, 2.0, "Tu video no muere por malo. Muere porque empieza lento.")
        flash(img, t, 0.3)
    elif t < 5:
        lt = t - 2; a = ease(lt / 0.3)
        text_c(d, 700, "“HOLA, SOY…”", fit_font(d, "“HOLA, SOY…”", SORA, 940, 130), WHITE, a, dy=(1 - a) * 40)
        w = d.textlength("“HOLA, SOY…”", font=fit_font(d, "“HOLA, SOY…”", SORA, 940, 130))
        if lt > 0.8:
            p = ease((lt - 0.8) / 0.35)
            d.rectangle((W / 2 - w / 2, 790, W / 2 - w / 2 + w * p, 806), fill=ORANGE)
        a = ease((lt - 1.3) / 0.35)
        text_c(d, 960, "ES SCROLL.", SORA(110), ORANGE, a, dy=(1 - a) * 40)
        caption(d, t, 2.0, 5.0, "Empezar con hola, me presento o un logo girando es un pase directo al scroll.")
    elif t < 7:
        lt = t - 5; a = ease(lt / 0.3)
        text_c(d, 760, "LA FÓRMULA,", SORA(150), WHITE, a, dy=(1 - a) * 40)
        a = ease((lt - 0.25) / 0.3)
        text_c(d, 960, "AL FINAL", SORA(150), ORANGE, a, dy=(1 - a) * 40)
        draw_line(d, 200, 880, 1170, (lt - 0.5) / 0.6)
        caption(d, t, 5.0, 7.0, "Te dejo la fórmula completa al final. Primero, tres cambios.")
    elif t < 11:
        step(img, d, t, 7, 1, "EMPIEZA POR EL CLÍMAX"); d = ImageDraw.Draw(img)
        caption(d, t, 7.0, 11.0, "Uno. Empieza por tu mejor segundo, no por el primero.")
    elif t < 15:
        step(img, d, t, 11, 2, "UNA IDEA POR VIDEO"); d = ImageDraw.Draw(img)
        caption(d, t, 11.0, 15.0, "Dos. Una sola idea. Si necesitas dos, son dos videos.")
    elif t < 19:
        step(img, d, t, 15, 3, "CORTA CADA 3 s"); d = ImageDraw.Draw(img)
        caption(d, t, 15.0, 19.0, "Tres. Cambia de plano o de ritmo cada tres segundos.")
    elif t < 22:
        lt = t - 19; size = int(W * 0.78); cx, cy = W // 2, 620
        ring = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rd = ImageDraw.Draw(ring); rr = size // 2
        rd.arc((cx - rr, cy - rr, cx + rr, cy + rr), -90, -90 + 360 * ease(clamp(lt / 1.2)), fill=ORANGE + (255,), width=16)
        img.paste(ring, (0, 0), ring)
        if lt > 1.0:
            a = ease((lt - 1.0) / 0.5)
            s = sym.resize((int(size * .92), int(size * .92)), Image.LANCZOS)
            s.putalpha(s.getchannel("A").point(lambda v: int(v * a)))
            img.paste(s, (cx - s.width // 2, cy - s.height // 2), s)
        a = ease((lt - 1.3) / 0.4)
        text_c(d, 1090, "改善", JP(120), WHITE, a, dy=(1 - a) * 30)
        caption(d, t, 19.0, 22.0, "Mejora. Prueba. Aprende. Repite. Cada video es un borrador del siguiente.")
        flash(img, t, 20.0, 0.15)
    else:
        lt = t - 22
        paste_sym(img, 340, W // 2, 430, ease(lt / 0.4))
        text_c(d, 700, "¿CÓMO EMPIEZA TU ÚLTIMO VIDEO?", fit_font(d, "¿CÓMO EMPIEZA TU ÚLTIMO VIDEO?", SORA, 940, 80), WHITE, ease((lt - 0.2) / 0.3))
        bw, bh, by = 760, 150, 1000
        k = ease((lt - 0.5) / 0.4); sw, sh = int(bw * k), int(bh * k)
        if sw > 4:
            d.rounded_rectangle((W // 2 - sw // 2, by + (bh - sh) // 2, W // 2 + sw // 2, by + (bh + sh) // 2), radius=36, fill=ORANGE)
            if k > 0.85: text_c(d, by + 34, "COMENTA: HOOK", SORA(64), (11, 11, 15))
        caption(d, t, 22.0, 26.0, "Pega aquí tu primera frase. Comenta HOOK y te digo cómo mejorarla.")
        flash(img, t, 22.55, 0.15)
        paste_sym(img, 130, W - 130, 160, 0.9)
    if 7 <= t < 19: paste_sym(img, 110, W - 130, 160, 0.8)
    return img

def main():
    hits = [0, 7, 11, 15, 19, 22]
    expr = "+".join(f"0.3*sin(2*PI*55*(t-{h}))*exp(-6*(t-{h}))*gte(t,{h})" for h in hits)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-i", f"aevalsrc='{expr}':s=44100:d={DUR}",
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", OUT]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(FPS * DUR): p.stdin.write(frame(i / FPS).tobytes())
    p.stdin.close(); p.wait(); print("OK", OUT)

if __name__ == "__main__": main()
