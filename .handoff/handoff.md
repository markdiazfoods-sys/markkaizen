---
date: 2026-11-20T23:15:07.553Z
project: markkaizen
session: 7bd02c07
schema_version: 1
next_steps_count: 6
has_blockers: false
keywords: ai video, mcp connectors, insertar_video, runway, elevenlabs, markkaizen
headline: Goal: add connectors + skills so AI videos can be generated and inserted into markkaizen static portfolio site. Intent: 
---

# Session Handoff Snapshot
> **Generated:** 11/20/2026, 11:15:07 PM

## 🎯 High-Level Objective
* **Goal:** Goal: add connectors + skills so AI videos can be generated and inserted into markkaizen static portfolio site. Intent: repeatable on-brand video pipeline, generate → publish.

## 📌 Current State & Next Steps
* **Status:** Done: connectors, skills, script, test, commit+push. Remaining: real login to MCPs, real AI video generation, browser playback check. Connectors untested because session proxy blocks external MCP hosts.
* **Next Action:** User logs in to each MCP (claude mcp login runway / runway-dev / elevenlabs)

### Remaining Queue
- [ ] Provide avatar reference image if talking-avatar video wanted
- [ ] Generate a real AI video, save to produccion/<slug>/, run insertar_video.py
- [ ] Verify playback in index.html on desktop and mobile
- [ ] Open PR only if user asks
- [ ] Optionally set up Dailybot CLI via /dailybot:report

## 🛠️ Modified Files Delta
* .mcp.json: new, 3 HTTP MCP servers
* .claude/skills/video-ia-generar/SKILL.md: new, generation workflow
* .claude/skills/video-ia-insertar/SKILL.md: new, insertion docs
* .claude/skills/video-ia-insertar/insertar_video.py: new, copies mp4 to media/v, thumb to media/t, registers in index.html DATA
* .claude-designlog-hooks.log: hook log appended

## 🚫 Failed Approaches (DO NOT RETRY)
* Approach: add Higgsfield connector → Result: connector cannot generate media, import only → Lesson: not useful for generation
* Approach: use Kling/HyperFrames/video plugin MCPs → Result: ERR_PROXY_TUNNEL 403 → Lesson: proxy blocks hosts; cannot verify or add

## 🔑 Crucial Context & Implicit Rules
* Site schema: window.DATA.G[brand]=[[kind,title,id]], M[id]={k:'v'}, files media/v/<id>.mp4 and media/t/<id>.jpg
* Brand: black #0B0B0F 60%, white 30%, orange #FF6B00 10%; fonts Sora/Inter/Noto Sans JP
* Develop on branch ccr-2896299f-1aebsw; no PR unless user asks
* User writes Spanish; genshijin terse mode active

## Key Decisions
- Decision: .mcp.json with runway (https://mcp.runwayml.com/mcp), runway-dev (https://dev.runwayml.com/mcp/claude), elevenlabs (https://api.elevenlabs.io/v1/mcp) — Reason: URLs verified in Runway docs / ElevenLabs connector instructions; full ElevenLabs connector needed for video generation
- Decision: video-ia-generar skill locks brand prompt (black #0B0B0F, white, orange #FF6B00 accent, Japanese studio look), routes task to connector, requires credit confirmation, no retry-generation — Reason: generations cost credits, brand consistency
- Decision: insertar_video.py edits window.DATA G/M in index.html via JSON raw_decode and aborts if re-serialization differs — Reason: avoid corrupting 178KB single-file catalog
- Decision: Higgsfield and Kling/HyperFrames left out — Reason: Higgsfield only imports; others failed to connect

## Summary
Created .mcp.json (3 MCP connectors), two skills, one insert script. Dry-run and real end-to-end insert tested then reverted. Committed + pushed to branch ccr-2896299f-1aebsw. No PR.

---
*A short hint surfaces on session start; full context loads only if your next prompt matches a keyword above, or via manual `/handoff-resume`. The same record is available as a sibling `.json` file for external tools.*