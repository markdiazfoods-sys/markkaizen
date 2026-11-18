"""Marca de agua MARK KAIZEN (símbolo) abajo-derecha. Uso: python3 marca_de_agua.py entrada salida [ancho_rel] [opacidad]"""
import sys
from PIL import Image, ImageFilter

def aplicar(src, dst, rel=0.13, op=0.78):
    base = Image.open(src).convert("RGB")
    w, h = base.size
    s = Image.open("img/simbolo-256.png").convert("RGBA")
    d = max(36, int(w * rel))
    s = s.resize((d, d), Image.LANCZOS)
    a = s.getchannel("A").point(lambda v: int(v * op))
    s.putalpha(a)
    sombra = Image.new("RGBA", s.size, (0, 0, 0, 0))
    sombra.putalpha(a.point(lambda v: int(v * .5)))
    sombra = sombra.filter(ImageFilter.GaussianBlur(d * .03))
    m = int(w * .035)
    x, y = w - d - m, h - d - m
    out = base.convert("RGBA")
    out.alpha_composite(sombra, (x, y + 2))
    out.alpha_composite(s, (x, y))
    out.convert("RGB").save(dst, "JPEG", quality=90, optimize=True)

if __name__ == "__main__":
    aplicar(sys.argv[1], sys.argv[2], *(float(v) for v in sys.argv[3:5]))
