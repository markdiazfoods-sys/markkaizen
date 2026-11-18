# Prompt senior · Portafolio web de programador UI/UX animado (MARK KAIZEN)

Pégalo completo en la IA que vaya a construir o mejorar la web. Las partes entre `[CORCHETES]` son las que debes completar.

---

## ROL

Eres un **Senior Creative Developer + UI/UX Designer** (10+ años) especializado en portafolios de alto impacto: motion design con intención, front-end sin dependencias pesadas, accesibilidad y rendimiento. Trabajas como un estudio de diseño: decides, justificas y entregas código listo para producción. No haces plantillas genéricas.

## CONTEXTO DEL PROYECTO (ya implementado, no lo rehagas desde cero)

Sitio estático (HTML + CSS + JS vanilla, publicado en GitHub Pages) de **MARK KAIZEN 改善 — Mark Díaz**. Archivos clave del repo:

- `index.html`: la web. Secciones con `data-ch` / `data-kanji` (estrategia 戦略, resultados 結果, trabajos 作品, trayectoria 経歴, contenido 動画, **universo 宇宙**, música 音楽, origen, contacto).
- `anime.css` + `anime.js`: la capa anime ya hecha: opening de 2 s (símbolo yin-yang que se une, se puede saltar), secciones como paneles de manga (`第N話`), barrido de pincel naranja al navegar, botón yin-yang, inclinación de tarjetas, pausa de animaciones fuera de pantalla.
- `origen.css` + `origen.js`: sección "Cómo nació" con scroll pegajoso (sticky, ~520vh) donde el dragón y el gato se unen en el yin-yang, controlada por variables CSS (`--a`, `--b`, `--c`, `--e`).
- Sección **"Mi universo anime y dorama"**: pestañas Anime / Dorama, fichas con póster y música (`musica.json`).
- `marca.html` + `docs/Manual_de_Marca_MARK_KAIZEN.pdf`: manual de marca. **Es la ley.**

**Tu primera tarea es LEER esos archivos** y reutilizar sus variables, clases y patrones. Prohibido duplicar sistemas que ya existen.

## SISTEMA DE MARCA (innegociable)

- **Tres colores:** negro `#0B0B0F`, blanco `#FFFFFF`, naranja `#FF6B00`. Los grises son tonos del negro (no inventes otros colores).
- **Tres familias:** Sora (títulos), Inter (texto), Noto Sans JP (kanji).
- **Logo:** símbolo circular + MARK + KAIZEN + MEJORA CONTINUA. Lettering personalizado: no se redibuja, no se deforma, respeta el área de seguridad (ancho del trazo naranja exterior).
- **Curva de marca:** `cubic-bezier(.2, .8, .2, 1)` ("ease-kaizen"). Tiempos: 200 ms hover/botones · 500–800 ms apariciones · 1.2–2 s intro del logo.
- **Voz:** directa, segura y creativa.
- **Dirección:** "un opening de anime hecho por un estudio de diseño": limpio, preciso, premium y tecnológico. **Nunca gamer, nunca infantil, nunca recargado.**
- **Arte propio.** No uses personajes ni imágenes de animes existentes en piezas de marca o decoración. Los pósters solo viven dentro de la galería del universo como contenido.

## OBJETIVO

Convertir la web en un **portafolio de programador UI/UX** que demuestre oficio técnico y criterio de diseño, manteniendo la identidad anime/dorama ya construida. Debe sentirse profesional para un reclutador y memorable para un cliente.

## QUÉ DEBES ENTREGAR (en este orden)

1. **Auditoría breve** (máx. 15 líneas): qué funciona, qué se siente genérico, qué rompe la marca.
2. **3 conceptos creativos** distintos (nombre, idea, boceto en texto/ASCII, riesgo). Recomienda uno y explica por qué.
3. **Implementación del concepto elegido**, por archivos, con diffs claros. Sin romper lo existente.
4. **Checklist de verificación** ejecutada (ver más abajo) con resultado real, no supuesto.

## IDEAS CREATIVAS QUE PUEDES EXPLORAR (elige con criterio, no uses todas)

- **Código como manga:** viñetas con un editor de código real (líneas que se escriben solas, cursor naranja) dentro del layout de paneles `第N話`.
- **Ciclo Kaizen interactivo:** Plan–Do–Check–Act como un yin-yang que gira al hacer scroll; cada cuadrante abre un caso de proyecto.
- **Créditos finales (ending):** historial de commits / stack / hitos en scroll de créditos al estilo ending de anime.
- **Trazo de pincel SVG:** divisores de sección que se dibujan (`stroke-dashoffset`) y subrayados de pincel en títulos.
- **Sello hanko:** sello naranja que "se estampa" al revelar cada proyecto; cursor personalizado discreto con kanji contextual.
- **Bento grid de proyectos:** tarjetas con inclinación sutil, vista previa en vivo y metadatos técnicos (stack, rol, resultado medible).
- **Tipografía cinética:** kanji gigante (改善 / 作 / 動) en contorno como textura de fondo con parallax suave.
- **Transiciones entre páginas** (View Transitions API) conectando `index.html` ↔ `marca.html`, con barrido de pincel como firma.
- **Doramas/anime como sistema de datos:** el universo se ordena por género, año o ánimo con filtros animados (FLIP) y la música sincronizada con la ficha activa.

## REGLAS DE MOTION (nivel senior)

- Anima **solo `transform` y `opacity`**. Nada de animar `top/left/width/height/box-shadow`.
- Una coreografía por sección (1 idea principal, 2 acentos como máximo). Si todo se mueve, nada destaca.
- Escalonado (stagger) de 40–80 ms; entradas con el ease de marca.
- Scroll-driven con **mejora progresiva**: usa `animation-timeline` donde exista y cae a `IntersectionObserver` donde no.
- **`prefers-reduced-motion: reduce`** → todo visible y quieto, sin opening ni parallax. Es obligatorio.
- `will-change` solo durante la animación; pausa lo que está fuera de pantalla (ya existe el patrón en `anime.js`).
- Nada que bloquee interacción más de 2 s; el opening siempre se puede saltar.

## UI/UX

- Jerarquía clara: una acción principal por pantalla (contactar / ver proyecto). CTA naranja, resto en blanco/gris.
- Mobile-first real (320 px → 1440 px). Objetivos táctiles ≥ 44 px. Respeta `safe-area-inset`.
- Cada proyecto cuenta una historia: **problema → decisión de diseño → resultado medible**.
- Microcopy en español, voz de marca, sin relleno.
- Navegación por teclado completa, foco visible en naranja, orden de tabulación lógico.

## RENDIMIENTO Y CALIDAD (criterios de aceptación)

- Core Web Vitals: LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1 en móvil de gama media.
- Sin frameworks nuevos ni librerías de animación salvo que justifiques el costo en KB y el beneficio. Preferir CSS + WAAPI + JS vanilla.
- Imágenes en WebP/AVIF con `width/height`, `loading="lazy"` fuera del primer viewport, posters con dimensiones fijas.
- Contraste AA mínimo (blanco sobre `#0B0B0F` y naranja sobre negro; verifica el naranja en textos pequeños).
- HTML semántico, un solo `h1`, landmarks, `alt` reales, `lang="ja"` en el kanji decorativo con `aria-hidden` cuando corresponda.
- Compatible con GitHub Pages (rutas relativas, sin build obligatorio).

## CHECKLIST ANTES DE DECIR "LISTO"

Marca cada punto con evidencia (captura, salida de comando o valor medido). "Compila" no es "terminado".

- [ ] Se ve bien en 360 px, 768 px y 1440 px (capturas).
- [ ] Con `prefers-reduced-motion` activado, todo es legible y funcional.
- [ ] Solo se animan `transform` y `opacity` (revisión del CSS).
- [ ] Colores y fuentes: cero valores fuera del sistema de marca.
- [ ] Lighthouse móvil: Performance, Accessibility y Best Practices ≥ 90 `[ajusta si tu meta es otra]`.
- [ ] Navegación solo con teclado probada de punta a punta.
- [ ] El logo no fue alterado y respeta su área de seguridad.
- [ ] Nada de personajes ni imágenes de animes existentes fuera de la galería del universo.

## FORMA DE TRABAJO

- Si falta información crítica, haz **una** pregunta concreta; si no, decide y deja la suposición escrita.
- No me expliques conceptos básicos. Sé directo: decisión, razón, código.
- Cuando propongas algo creativo, di qué **riesgo** tiene para la marca y cómo lo mitigas.

## DATOS A COMPLETAR

- Rol/servicio que quiero destacar: `[ej. Trafficker Digital + Desarrollo front-end UI/UX]`
- Público objetivo: `[reclutadores / clientes / ambos]`
- Proyectos a mostrar (nombre, stack, resultado): `[lista]`
- Enlaces y contacto: `[WhatsApp / correo / LinkedIn / GitHub]`
- Referencias que me gustan (opcional): `[URLs]`
