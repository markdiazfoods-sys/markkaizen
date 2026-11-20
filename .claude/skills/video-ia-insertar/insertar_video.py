#!/usr/bin/env python3
"""Inserta un mp4 en el portafolio: media/v, media/t e index.html (window.DATA)."""
import argparse, json, os, re, shutil, subprocess, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
INDEX = os.path.join(ROOT, "index.html")
KEY = "window.DATA="

def slug(s):
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "video-ia"

def main():
    a = argparse.ArgumentParser()
    a.add_argument("mp4")
    a.add_argument("--marca", default="Otros diseños")
    a.add_argument("--titulo", required=True)
    a.add_argument("--id")
    a.add_argument("--dry-run", action="store_true")
    a = a.parse_args()

    if not os.path.isfile(a.mp4): sys.exit("No existe: " + a.mp4)
    pr = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                         "stream=codec_name,width,height:format=duration", "-of", "json", a.mp4],
                        capture_output=True, text=True)
    if pr.returncode: sys.exit("ffprobe falló: " + pr.stderr)
    info = json.loads(pr.stdout)
    if not info.get("streams"): sys.exit("El archivo no tiene video")
    dur = float(info["format"]["duration"])
    vid = a.id or "ia-" + slug(a.titulo)

    src = open(INDEX, encoding="utf8").read()
    i = src.index(KEY) + len(KEY)
    data, n = json.JSONDecoder().raw_decode(src[i:])
    dump = lambda d: json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    if dump(data) != src[i:i + n]:
        sys.exit("Abortado: la serialización de DATA no es idéntica; edita index.html a mano.")
    if vid in data["M"]: sys.exit("Ya existe el id " + vid)

    data["G"].setdefault(a.marca, []).append(["v", a.titulo, vid])
    data["M"][vid] = {"k": "v"}
    print(f"{vid}: {info['streams'][0]['width']}x{info['streams'][0]['height']}, {dur:.1f}s → marca «{a.marca}»")
    if a.dry_run: return

    dv, dt = os.path.join(ROOT, "media", "v"), os.path.join(ROOT, "media", "t")
    os.makedirs(dv, exist_ok=True); os.makedirs(dt, exist_ok=True)
    shutil.copyfile(a.mp4, os.path.join(dv, vid + ".mp4"))
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(min(1.0, dur / 2)), "-i", a.mp4,
                        "-frames:v", "1", "-vf", "scale=480:-2", "-q:v", "4",
                        os.path.join(dt, vid + ".jpg")])
    if r.returncode: sys.exit("No se pudo crear la portada")
    open(INDEX, "w", encoding="utf8").write(src[:i] + dump(data) + src[i + n:])
    print("Listo: media/v, media/t e index.html actualizados")

main()
