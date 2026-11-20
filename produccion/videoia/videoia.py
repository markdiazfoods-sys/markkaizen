#!/usr/bin/env python3
"""MARK KAIZEN · videoia — generar videos con IA y editarlos.

Solo librería estándar + ffmpeg/ffprobe. Sin dependencias pip.

GENERAR (Runway API; requiere RUNWAYML_API_SECRET en el entorno):
  videoia.py gen-texto  "prompt" -o salida.mp4 [--ratio 720:1280] [--dur 5]
  videoia.py gen-imagen foto.jpg "prompt" -o salida.mp4 [--ratio 720:1280] [--dur 5]

EDITAR (ffmpeg local):
  videoia.py info       in.mp4
  videoia.py cortar     in.mp4 -o out.mp4 --inicio 2 --fin 8
  videoia.py unir       a.mp4 b.mp4 [...] -o out.mp4
  videoia.py formato    in.mp4 -o out.mp4 --a 9:16|16:9|1:1 [--relleno recorte|barras]
  videoia.py velocidad  in.mp4 -o out.mp4 --x 1.5
  videoia.py subtitulos in.mp4 subs.srt -o out.mp4
  videoia.py audio      in.mp4 musica.mp3 -o out.mp4 [--vol 0.3] [--reemplazar]
  videoia.py miniatura  in.mp4 -o thumb.jpg [--t 1.0]
  videoia.py pipeline   in.mp4 receta.json -o out.mp4   (encadena pasos)
"""
import argparse, json, os, shutil, subprocess, sys, tempfile, time
import urllib.error, urllib.request

API = "https://api.dev.runwayml.com"
API_VERSION = "2024-11-06"  # cabecera X-Runway-Version obligatoria
# Verificado en docs.dev.runwayml.com (api.md). No mezclar valores entre modelos.
MODELOS = {
    "texto": {"model": "gen4.5", "ratios": ["1280:720", "720:1280"], "dur": (2, 10), "max_prompt": 1000},
    "imagen": {"model": "gen4.5", "ratios": ["1280:720", "720:1280", "1104:832", "960:960", "832:1104", "1584:672"],
               "dur": (2, 10), "max_prompt": 1000},
}
ASPECTOS = {"9:16": (1080, 1920), "16:9": (1920, 1080), "1:1": (1080, 1080), "4:5": (1080, 1350)}


class Error(Exception):
    pass


# ───────────────────────── utilidades ffmpeg ─────────────────────────
def _need(binname):
    if not shutil.which(binname):
        raise Error(f"No se encontró '{binname}'. Instala ffmpeg.")


def run_ffmpeg(args):
    _need("ffmpeg")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + args
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise Error("ffmpeg falló:\n" + r.stderr.strip())


def probe(path):
    _need("ffprobe")
    if not os.path.isfile(path):
        raise Error(f"No existe el archivo: {path}")
    r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise Error(f"ffprobe no pudo leer {path}: {r.stderr.strip()}")
    d = json.loads(r.stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    if not v:
        raise Error(f"{path} no tiene pista de video.")
    return {"w": int(v["width"]), "h": int(v["height"]), "dur": float(d["format"].get("duration", 0)),
            "audio": a is not None, "fps": v.get("r_frame_rate")}


ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
       "-movflags", "+faststart"]


# ───────────────────────── edición ─────────────────────────
def cortar(src, out, inicio=0.0, fin=None):
    info = probe(src)
    fin = info["dur"] if fin is None else fin
    if not (0 <= inicio < fin <= info["dur"] + 0.05):
        raise Error(f"Rango inválido: {inicio}–{fin} s (el video dura {info['dur']:.2f} s).")
    # -ss/-to después de -i = corte exacto de fotograma (re-codifica).
    run_ffmpeg(["-i", src, "-ss", str(inicio), "-to", str(fin)] + ENC + [out])


def unir(srcs, out):
    if len(srcs) < 2:
        raise Error("Necesito al menos 2 videos para unir.")
    infos = [probe(s) for s in srcs]
    w, h = infos[0]["w"], infos[0]["h"]  # el primero fija la resolución
    ins, filt = [], []
    for i, (s, inf) in enumerate(zip(srcs, infos)):
        ins += ["-i", s]
        filt.append(f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2,"
                    f"setsar=1,fps=30,format=yuv420p[v{i}]")
        if inf["audio"]:
            filt.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo[a{i}]")
        else:  # silencio con la duración del clip para mantener sincronía
            filt.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{inf['dur']:.3f}[a{i}]")
    pares = "".join(f"[v{i}][a{i}]" for i in range(len(srcs)))
    filt.append(f"{pares}concat=n={len(srcs)}:v=1:a=1[v][a]")
    run_ffmpeg(ins + ["-filter_complex", ";".join(filt), "-map", "[v]", "-map", "[a]"] + ENC + [out])


def formato(src, out, aspecto, relleno="recorte"):
    if aspecto not in ASPECTOS:
        raise Error(f"Aspecto '{aspecto}' no soportado. Usa: {', '.join(ASPECTOS)}")
    if relleno not in ("recorte", "barras"):
        raise Error("--relleno debe ser 'recorte' o 'barras'.")
    w, h = ASPECTOS[aspecto]
    if relleno == "recorte":
        vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1"
    else:  # barras: fondo desenfocado del mismo video
        vf = (f"split[a][b];[a]scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},boxblur=30:5[bg];"
              f"[b]scale={w}:{h}:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1")
    run_ffmpeg(["-i", src, "-filter_complex" if relleno == "barras" else "-vf", vf] + ENC + [out])


def _atempo(x):
    # atempo admite 0.5–2.0 por filtro: se encadena para valores fuera de rango.
    f = []
    while x > 2.0:
        f.append("atempo=2.0"); x /= 2.0
    while x < 0.5:
        f.append("atempo=0.5"); x /= 0.5
    f.append(f"atempo={x:.4f}")
    return ",".join(f)


def velocidad(src, out, x):
    if not (0.1 <= x <= 16):
        raise Error("--x debe estar entre 0.1 y 16.")
    info = probe(src)
    if info["audio"]:
        run_ffmpeg(["-i", src, "-filter_complex", f"[0:v]setpts=PTS/{x}[v];[0:a]{_atempo(x)}[a]",
                    "-map", "[v]", "-map", "[a]"] + ENC + [out])
    else:
        run_ffmpeg(["-i", src, "-vf", f"setpts=PTS/{x}"] + ENC + [out])


def subtitulos(src, srt, out):
    info = probe(src)
    if not os.path.isfile(srt):
        raise Error(f"No existe el archivo de subtítulos: {srt}")
    # El filtro subtitles pide escapar ruta; se copia a un temporal sin caracteres raros.
    with tempfile.TemporaryDirectory() as td:
        tmp = os.path.join(td, "s.srt")
        shutil.copy(srt, tmp)
        # libass interpreta el estilo de un .srt en una escala de 288 px de alto (PlayResY),
        # sea cual sea la resolución real: así el tamaño/margen es proporcional en 9:16, 16:9, etc.
        estilo = ("FontName=Inter,FontSize=9,PrimaryColour=&H00FFFFFF,OutlineColour=&H000B0B0F,"
                  "BorderStyle=1,Outline=1.2,Alignment=2,MarginV=63")
        r = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", os.path.abspath(src),
                            "-vf", f"subtitles=s.srt:force_style='{estilo}'"] + ENC + [os.path.abspath(out)],
                           cwd=td, capture_output=True, text=True)
        if r.returncode != 0:
            raise Error("ffmpeg falló (¿sin libass?):\n" + r.stderr.strip())


def audio(src, pista, out, vol=0.3, reemplazar=False):
    info = probe(src)
    if not os.path.isfile(pista):
        raise Error(f"No existe el audio: {pista}")
    if reemplazar or not info["audio"]:
        f = f"[1:a]volume={1.0 if reemplazar else vol},atrim=0:{info['dur']:.3f}[a]"
    else:  # mezcla: música baja bajo la voz/audio original
        f = f"[1:a]volume={vol},atrim=0:{info['dur']:.3f}[m];[0:a][m]amix=inputs=2:duration=first:normalize=0[a]"
    run_ffmpeg(["-i", src, "-stream_loop", "-1", "-i", pista, "-filter_complex", f, "-map", "0:v", "-map", "[a]",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])


def miniatura(src, out, t=1.0):
    info = probe(src)
    t = min(max(t, 0), max(info["dur"] - 0.05, 0))
    run_ffmpeg(["-ss", str(t), "-i", src, "-frames:v", "1", "-q:v", "2", out])


def pipeline(src, receta, out):
    """receta.json: [{"op":"cortar","inicio":1,"fin":6},{"op":"formato","a":"9:16"},{"op":"velocidad","x":1.2}, ...]"""
    with open(receta, encoding="utf-8") as f:
        pasos = json.load(f)
    if not isinstance(pasos, list) or not pasos:
        raise Error("La receta debe ser una lista JSON no vacía de pasos.")
    ops = {
        "cortar": lambda i, o, p: cortar(i, o, p.get("inicio", 0), p.get("fin")),
        "formato": lambda i, o, p: formato(i, o, p["a"], p.get("relleno", "recorte")),
        "velocidad": lambda i, o, p: velocidad(i, o, p["x"]),
        "subtitulos": lambda i, o, p: subtitulos(i, p["srt"], o),
        "audio": lambda i, o, p: audio(i, p["pista"], o, p.get("vol", 0.3), p.get("reemplazar", False)),
    }
    for p in pasos:
        if p.get("op") not in ops:
            raise Error(f"Paso desconocido: {p.get('op')!r}. Válidos: {', '.join(ops)}")
    with tempfile.TemporaryDirectory() as td:
        actual = src
        for n, p in enumerate(pasos, 1):
            dest = out if n == len(pasos) else os.path.join(td, f"p{n}.mp4")
            print(f"[{n}/{len(pasos)}] {p['op']}")
            try:
                ops[p["op"]](actual, dest, p)
            except KeyError as e:
                raise Error(f"Paso {n} ({p['op']}): falta el campo {e}")
            actual = dest


# ───────────────────────── generación (Runway) ─────────────────────────
def _http(method, path, key, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method, headers={
        "Authorization": f"Bearer {key}", "X-Runway-Version": API_VERSION, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        detalle = e.read().decode(errors="replace")[:500]
        raise Error(f"Runway HTTP {e.code} en {method} {path}: {detalle}")
    except urllib.error.URLError as e:
        raise Error(f"No se pudo conectar con Runway: {e.reason}")


def _key():
    k = os.environ.get("RUNWAYML_API_SECRET", "").strip()
    if not k:
        raise Error("Falta RUNWAYML_API_SECRET. Crea la clave en https://dev.runwayml.com y expórtala "
                    "(no la pegues en chats ni la subas al repo).")
    return k


def _validar(kind, prompt, ratio, dur):
    m = MODELOS[kind]
    if not prompt.strip():
        raise Error("El prompt está vacío.")
    if len(prompt) > m["max_prompt"]:
        raise Error(f"Prompt de {len(prompt)} caracteres; el máximo de {m['model']} es {m['max_prompt']}.")
    if ratio not in m["ratios"]:
        raise Error(f"Ratio {ratio} no válido para {m['model']} ({kind}). Opciones: {', '.join(m['ratios'])}")
    if not (m["dur"][0] <= dur <= m["dur"][1]):
        raise Error(f"Duración {dur}s fuera de rango {m['dur'][0]}–{m['dur'][1]} para {m['model']}.")


def _imagen_a_uri(path):
    import base64, mimetypes
    if path.startswith(("http://", "https://")):
        return path
    if not os.path.isfile(path):
        raise Error(f"No existe la imagen: {path}")
    mime = mimetypes.guess_type(path)[0] or "image/jpeg"
    if os.path.getsize(path) > 8 * 1024 * 1024:
        raise Error("Imagen >8 MB: reduce su tamaño o pasa una URL https pública.")
    with open(path, "rb") as f:
        return f"data:{mime};base64," + base64.b64encode(f.read()).decode()


def generar(kind, prompt, out, ratio, dur, imagen=None, poll=5, timeout=900):
    _validar(kind, prompt, ratio, dur)
    key = _key()
    body = {"model": MODELOS[kind]["model"], "promptText": prompt, "ratio": ratio, "duration": dur}
    ruta = "/v1/text_to_video"
    if kind == "imagen":
        ruta = "/v1/image_to_video"
        body["promptImage"] = _imagen_a_uri(imagen)
    tid = _http("POST", ruta, key, body)["id"]
    print(f"Tarea {tid} creada. Esperando…")
    t0, espera = time.time(), poll
    while True:
        t = _http("GET", f"/v1/tasks/{tid}", key)
        st = t.get("status")
        if st == "SUCCEEDED":
            break
        if st in ("FAILED", "CANCELLED"):
            raise Error(f"Generación {st}: {t.get('failure')} ({t.get('failureCode')})")
        if time.time() - t0 > timeout:
            raise Error(f"Timeout tras {timeout}s (tarea {tid} sigue en {st}). Reintenta con GET /v1/tasks/{tid}.")
        print(f"  {st} {int((t.get('progress') or 0) * 100)}%")
        time.sleep(espera)
        espera = min(espera * 1.3, 20)
    url = t["output"][0]  # las URLs son temporales: se descarga ya
    with urllib.request.urlopen(url, timeout=120) as r, open(out, "wb") as f:
        shutil.copyfileobj(r, f)
    print(f"Guardado: {out}")


# ───────────────────────── CLI ─────────────────────────
def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest="cmd", required=True)

    def add(name, *pos, out=True):
        s = sp.add_parser(name)
        for a in pos:
            s.add_argument(a, nargs="+" if a == "videos" else None)
        if out:
            s.add_argument("-o", "--out", required=True)
        return s

    s = add("gen-texto", "prompt"); s.add_argument("--ratio", default="720:1280"); s.add_argument("--dur", type=int, default=5)
    s = add("gen-imagen", "imagen", "prompt"); s.add_argument("--ratio", default="720:1280"); s.add_argument("--dur", type=int, default=5)
    add("info", "video", out=False)
    s = add("cortar", "video"); s.add_argument("--inicio", type=float, default=0.0); s.add_argument("--fin", type=float)
    add("unir", "videos")
    s = add("formato", "video"); s.add_argument("--a", required=True); s.add_argument("--relleno", default="recorte")
    s = add("velocidad", "video"); s.add_argument("--x", type=float, required=True)
    add("subtitulos", "video", "srt")
    s = add("audio", "video", "pista"); s.add_argument("--vol", type=float, default=0.3); s.add_argument("--reemplazar", action="store_true")
    s = add("miniatura", "video"); s.add_argument("--t", type=float, default=1.0)
    add("pipeline", "video", "receta")

    a = p.parse_args(argv)
    try:
        c = a.cmd
        if c == "gen-texto": generar("texto", a.prompt, a.out, a.ratio, a.dur)
        elif c == "gen-imagen": generar("imagen", a.prompt, a.out, a.ratio, a.dur, imagen=a.imagen)
        elif c == "info": print(json.dumps(probe(a.video), indent=2))
        elif c == "cortar": cortar(a.video, a.out, a.inicio, a.fin)
        elif c == "unir": unir(a.videos, a.out)
        elif c == "formato": formato(a.video, a.out, a.a, a.relleno)
        elif c == "velocidad": velocidad(a.video, a.out, a.x)
        elif c == "subtitulos": subtitulos(a.video, a.srt, a.out)
        elif c == "audio": audio(a.video, a.pista, a.out, a.vol, a.reemplazar)
        elif c == "miniatura": miniatura(a.video, a.out, a.t)
        elif c == "pipeline": pipeline(a.video, a.receta, a.out)
        if c not in ("info",) and not c.startswith("gen-"):
            print(f"Listo: {a.out}")
    except Error as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
