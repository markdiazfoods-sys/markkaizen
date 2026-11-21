# CLAUDE.md

<!-- handoff:learnings:begin -->
## Session Learnings (auto-updated by handoff)

### Implicit Rules
- User writes Spanish; reply in Spanish
- Brand: black #0B0B0F, white, orange #FF6B00 accent; fonts Sora/Inter/Noto Sans JP from docs/fuente/fuentes
- Render: python3 render.py; ONLY=t1,t2 for preview PNGs in /tmp/kz; needs numpy, Pillow, ffmpeg
- Develop on branch ccr-948b53da-wiqbwz; no PR unless asked

### Key Decisions
- Decision: illustrated room via code — Reason: user chose 'no photos' option; Runway/ElevenLabs MCP blocked by proxy 403
- Decision: 7 distinct scenes, 2.0-2.5 s each — Reason: user demanded no repeated scenes; fast cuts aid retention
- Decision: desaturated peach/rose/dusk palette + grain, brand orange only as accent — Reason: user said less oversaturated but GTA VI style
- Decision: re-encode crf 27 — Reason: crf 18 with grain gave 186 MB; now ~6 MB
- Decision: HUD kept below y~200 and prompts at y~1430 — Reason: TikTok UI safe zones

<!-- handoff:learnings:end -->
