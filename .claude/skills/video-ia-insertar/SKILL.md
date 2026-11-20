---
name: video-ia-insertar
description: Inserta un mp4 (por ejemplo uno generado con IA) en el portafolio de MARK KAIZEN: copia a media/v, crea portada y lo registra en index.html. Usar cuando se pida meter, subir o publicar un video en el sitio.
---

# Insertar video en el sitio

El sitio es estático. Catálogo en `index.html` → `window.DATA`:
- `G[marca] = [["v", "Título", "id"], ...]` (galería por marca)
- `M[id] = {"k": "v"}` (tipo)
- Archivos: `media/v/<id>.mp4` y portada `media/t/<id>.jpg`

## Uso
```
python3 .claude/skills/video-ia-insertar/insertar_video.py RUTA.mp4 --marca "Otros diseños" --titulo "Título corto" [--id slug] [--dry-run]
```
Marcas existentes: Cajas Aldana, Liu Liú, Florelima, Parada 111, Podología Integral, Otros diseños. Una marca nueva se crea sola (opcional: añadir su texto en `BDESC` de `index.html`).

El script: valida el mp4 con ffprobe, saca la portada con ffmpeg, copia el video, edita `G`/`M` y **aborta sin tocar nada** si la serialización de `DATA` no es idéntica a la original.

## Después
1. Abre `index.html` (navegador/Playwright) → sección de trabajos → comprueba que reproduce en PC y móvil.
2. Mantén el mp4 ligero (H.264, ≤ 20 MB); recomprime con ffmpeg si pesa más.
3. Commit solo si el usuario lo pide.
