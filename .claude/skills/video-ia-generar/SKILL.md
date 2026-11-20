---
name: video-ia-generar
description: Genera un video con IA para MARK KAIZEN 改善 (Runway, ElevenLabs, Higgsfield, Canva, HyperFrames) con la marca fija y formato 9:16 u otro. Usar cuando se pida crear, generar o producir un video de IA.
---

# Generar video IA · MARK KAIZEN

## 1. Entradas (pregunta solo lo que falte)
- Tema / mensaje, plataforma (TikTok 9:16 por defecto), duración (5–15 s por clip), con o sin voz.
- Si hay avatar: necesitas imagen de referencia del personaje. Sin ella, no inventes uno.

## 2. Conector según tarea
| Tarea | Conector (`.mcp.json`) |
|---|---|
| Texto/imagen → video | `runway` (genera en chat) o `elevenlabs` (`creative_generate_video`) |
| Voz en off | `elevenlabs` (`creative_generate_speech`; `voice_id` solo de `creative_list_voices`) |
| Motion gráfico con marca | `produccion/*/render.py` (Pillow + ffmpeg, sin IA) o HyperFrames/Canva si están conectados |
| Integración por API en código | `runway-dev` |

Si un conector no responde: dilo, no simules el resultado. Antes de generar, confirma créditos con el usuario (cada generación cuesta); no reintentes una generación para "probar".

## 3. Prompt de marca (siempre incluir)
- Colores: negro #0B0B0F 60 %, blanco #FFFFFF 30 %, naranja #FF6B00 10 % solo acento.
- Estética: estudio creativo japonés contemporáneo, fondo oscuro, luz lateral, detalle naranja. Premium, ligeramente futurista. Nunca gamer ni infantil.
- Cámara y movimiento explícitos (plano, travelling, duración). Sin texto largo dentro del video: los subtítulos se añaden después.
- Base de guion y voz: `docs/PROMPT_VIRAL_MARK_KAIZEN.md`.

## 4. Salida
- Descarga el mp4 a `produccion/<slug-pieza>/` (original) con nombre `mark_kaizen_<slug>_<ratio>.mp4`.
- Verifica con `ffprobe` resolución, duración y audio antes de dar por bueno.
- Muéstralo al usuario. "Hecho" = el usuario lo vio. Luego usa `video-ia-insertar` para publicarlo en el sitio.
