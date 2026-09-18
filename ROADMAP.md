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

No real backend wired in yet, but the scaffolding both backends
depend on is done and verified working (headless-browser run,
screenshot, zero console errors).

- [x] Define the `Backend` interface (`src/canirunllm/backends/interface.py`)
      and a `BackendManager` that picks which backend(s) apply to a
      given model (`src/canirunllm/backends/manager.py`).
- [x] Add disk-space detection to the hardware module
      (`hardware/disk.py`, wired into `scan_hardware()` and
      `/api/hardware`).
- [x] Build a minimal chat UI in the dashboard (send a prompt, get a
      response) against a mock `/api/chat` endpoint - a "Try It
      (Preview)" section in the model detail modal. Always returns an
      honest placeholder reply, never a fabricated model response.
- [x] Add "currently running model" state
      (`src/canirunllm/backends/state.py`, `GET /api/runtime/status`)
      and a "No model running" indicator in the dashboard topbar.

## Phase 1 — Ollama backend

Ships first: far less work than Phase 2, and covers most of the
immediate value since many target users already have Ollama installed.

- [x] Detect whether Ollama is installed/running
      (`OllamaBackend.is_available()`, `backends/ollama.py`).
- [x] Wire `download()` to `ollama pull <tag>` (Ollama's `/api/pull`,
      streamed), surfaced through `POST /api/models/{id}/download` as
      newline-delimited JSON progress events, and a "Download & Run"
      button + live progress in the dashboard.
- [x] Wire `serve()` to Ollama's existing REST API — no process
      spawning needed, it's already serving once pulled. Tracked via
      `backends/state.py` + `GET /api/runtime/status`, shown as
      "● Running: `<model>` (ollama)" in the topbar.
- [x] Point the Phase 0 chat UI at Ollama's `/api/chat` endpoint - only
      when the requested model matches what's actually running;
      otherwise an honest "isn't running yet" message, never a
      fabricated reply.
- [ ] Expand `OLLAMA_TAGS` coverage (`backends/ollama_tags.py`) beyond
      today's hand-curated subset — same manual-verification
      discipline as `registry/SOURCES.md`. Deliberately **not** done
      as part of this pass: verifying each tag against
      https://ollama.com/library requires checking one model at a
      time, same as the registry itself, and guessing a plausible-
      looking tag would be worse than not offering one. Left for a
      dedicated follow-up.
- [x] Tested against a real, running Ollama instance end-to-end (not
      mocked): downloaded `TinyLlama-1.1B-Chat-v1.0-Q4_K_M` for real
      (668MB, live progress observed going 0 -> 100%), got a real
      chat reply back through `/api/chat`, and verified the full flow
      in a real browser (screenshot, zero console errors). Behavior
      when Ollama isn't running/installed is covered by tests
      (`test_api.py`, `test_ollama_backend.py`) using a mocked
      `is_available()`, since CI can't assume Ollama is present.
- [ ] Release (cut a new pip/exe version including this).

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
