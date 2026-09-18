# Roadmap: download & run models, not just check compatibility

Today, CanIRunLLM tells you what fits your hardware and shows you the
command to run it yourself (llama.cpp, Ollama) — it never downloads or
runs anything itself. This roadmap tracks turning that into: click a
model, it downloads it, and you can use it right there.

This is a real step up in scope (see the "why this is bigger than it
looks" note below), so it's broken into phases that each ship
something usable, rather than one big build.

## Why this is bigger than it looks

- Downloads are multi-GB. Needs real progress UI, cancel/resume, and a
  disk-space preflight check — this app checks RAM/VRAM today but has
  never checked free disk space.
- Gated Hugging Face repos (Llama, Gemma) need the user's own HF token
  with an accepted license — never fully automatable.
- Two different runtime backends (Ollama vs. direct llama.cpp) have
  almost nothing in common under the hood: one wraps an existing tool,
  the other means downloading raw files and managing our own server
  process.
- It changes the app's promise. Today's pitch is "runs entirely on
  your machine, we just tell you what fits" — a read-only advisor.
  Spawning local server processes and managing multi-GB downloads is a
  bigger responsibility (still local/private, but now on the hook for
  disk space, port conflicts, orphaned processes on a crash).

## Shared design

Both backends implement one interface, so the dashboard doesn't care
which one actually serves a model:

```
Runtime:
  is_available()               -> is this backend usable right now?
  download(model, on_progress) -> fetches what's needed
  serve(model)                 -> starts it, returns a local endpoint URL
  stop()                       -> shuts it down cleanly
```

## Phase 0 — Shared foundation

No user-visible behavior change yet, but both backends depend on this.

- [ ] Define the `Runtime` interface and a manager that picks which
      backend(s) apply to a given model.
- [ ] Add disk-space detection to the hardware module.
- [ ] Build a minimal chat UI in the dashboard (send a prompt, stream
      a response) against a fake/mock endpoint first, decoupled from
      either backend being done yet.
- [ ] Add "currently running model" state to the web app (which
      model, which backend, which port) so the dashboard can show
      status and offer to stop it.

## Phase 1 — Ollama backend

Ships first: far less work than Phase 2, and covers most of the
immediate value since many target users already have Ollama installed.

- [ ] Detect whether Ollama is installed/running (`is_available()`).
- [ ] Wire `download()` to `ollama pull <tag>`, streaming its progress
      into the dashboard.
- [ ] Wire `serve()` to Ollama's existing REST API — no process
      spawning needed, it's already serving once pulled.
- [ ] Point the Phase 0 chat UI at Ollama's `/api/chat` endpoint.
- [ ] Expand `_OLLAMA_TAGS` coverage in `presentation.py` beyond
      today's hand-curated subset — same manual-verification
      discipline as `registry/SOURCES.md`. Models with no verified tag
      say "not available via Ollama," never guess one.
- [ ] Release. Test on a machine with Ollama and one without (should
      fall back to install instructions, not break).

## Phase 2 — Direct llama.cpp backend

Ships second, larger scope than Phase 1.

- [ ] Decide the binary strategy: require the user to already have
      `llama-server` on PATH/configured (start here — much less work)
      vs. bundling prebuilt binaries ourselves (real packaging
      expansion, per-OS/per-CPU-vs-CUDA).
- [ ] Build a resumable GGUF downloader using the exact repo + quant
      filename the registry-watch pipeline already resolves, verified
      against the registry's `file_size_bytes`.
- [ ] Wire in the Phase 0 disk-space check as a preflight before any
      download starts.
- [ ] Handle gated repos (Llama, Gemma): prompt for and locally store
      an HF token, clear error message on 401.
- [ ] Build process supervision: spawn `llama-server`, health-check
      it, capture logs, clean up on crash/app exit, avoid port
      collisions.
- [ ] Point the same chat UI at llama.cpp's OpenAI-compatible
      endpoint.
- [ ] Release.

## Phase 3 — Unify

- [ ] When a model has both an Ollama tag and a resolvable GGUF, let
      the user choose, defaulting to whichever backend is already
      installed.
- [ ] Polish the "running model" indicator / stop button.
- [ ] Revisit bundling llama.cpp binaries if the "install it yourself"
      friction from Phase 2 turns out to matter in practice.
