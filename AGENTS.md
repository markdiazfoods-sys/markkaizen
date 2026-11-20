# AGENTS.md

<!-- handoff:learnings:begin -->
## Session Learnings (auto-updated by handoff)

### Implicit Rules
- Site schema: window.DATA.G[brand]=[[kind,title,id]], M[id]={k:'v'}, files media/v/<id>.mp4 and media/t/<id>.jpg
- Brand: black #0B0B0F 60%, white 30%, orange #FF6B00 10%; fonts Sora/Inter/Noto Sans JP
- Develop on branch ccr-2896299f-1aebsw; no PR unless user asks
- User writes Spanish; genshijin terse mode active

### Key Decisions
- Decision: .mcp.json with runway (https://mcp.runwayml.com/mcp), runway-dev (https://dev.runwayml.com/mcp/claude), elevenlabs (https://api.elevenlabs.io/v1/mcp) — Reason: URLs verified in Runway docs / ElevenLabs connector instructions; full ElevenLabs connector needed for video generation
- Decision: video-ia-generar skill locks brand prompt (black #0B0B0F, white, orange #FF6B00 accent, Japanese studio look), routes task to connector, requires credit confirmation, no retry-generation — Reason: generations cost credits, brand consistency
- Decision: insertar_video.py edits window.DATA G/M in index.html via JSON raw_decode and aborts if re-serialization differs — Reason: avoid corrupting 178KB single-file catalog
- Decision: Higgsfield and Kling/HyperFrames left out — Reason: Higgsfield only imports; others failed to connect

<!-- handoff:learnings:end -->
