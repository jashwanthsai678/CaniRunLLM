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

Ships second, larger scope than Phase 1. Uses the same "Download & Run"
UI as Phase 1 - a model with both a verified Ollama tag and a verified
GGUF repo shows two buttons, one per backend.

- [x] Binary strategy: requires `llama-server` already installed - on
      PATH, or pointed to via the `LLAMA_SERVER_PATH` environment
      variable. Bundling a binary ourselves is left for later (see
      "Revisit" note in Phase 3).
- [x] GGUF downloader (`backends/llama_cpp.py`): the exact HF repo per
      family is curated in `backends/llama_cpp_sources.py`, extracted
      directly from `registry/SOURCES.md`'s own citations (all 29
      families covered, verified with a test that cross-checks every
      `models.json` family has an entry). The exact filename for a
      given quantization is resolved dynamically against the repo's
      real file listing - never guessed. Supports HTTP Range resume
      if a partial file already exists.
- [x] Disk-space preflight: checks `hardware/disk.py` before any
      download starts, raises `InsufficientDiskSpaceError` with the
      actual shortfall if there isn't room (10% margin beyond the
      file's own size).
- [x] Gated repos (Llama, Gemma, etc.): reads an `HF_TOKEN` environment
      variable if set; a 401 raises `GatedRepositoryError` with a
      clear message instead of a stack trace. No token-entry UI -
      standard `HF_TOKEN` env var only, consistent with
      huggingface_hub's own convention.
- [x] Process supervision: spawns `llama-server` on a free port,
      health-checks its `/health` endpoint (with a clear error if the
      process exits early instead of just timing out silently), logs
      to `~/.canirunllm/models/llama-server.log`, and registers
      `atexit` cleanup.
- [x] Chat wired to llama.cpp's OpenAI-compatible
      `/v1/chat/completions` endpoint.
- [x] Verified end-to-end against a real, downloaded llama.cpp release
      binary (`llama-server` b11035, Windows CPU build) - not mocked:
      downloaded TinyLlama-1.1B-Chat-v1.0-Q4_K_M's real GGUF straight
      from Hugging Face (668MB, exact byte match), spawned a real
      `llama-server` process, passed its health check, and got a real
      response back through `/v1/chat/completions` (log confirms real
      prompt/eval token counts, not a code-level echo). **Known,
      honest limitation found during this test:** `atexit` cleanup
      only fires on a graceful process exit - a forceful kill
      (`taskkill /F`, a crash, SIGKILL) orphans the `llama-server`
      child process, since no application-level code can intercept a
      forceful OS kill. Confirmed the graceful path works correctly by
      checking the port was released after a normal Python exit, and
      confirmed the forceful-kill gap by reproducing it directly. A
      more complete fix (e.g. a Windows Job Object tying the child's
      lifetime to the parent's) is future work, not done here.
- [x] Release (bundled with Phase 1 in the same version, if/when cut -
      no separate PyPI release needed for this phase alone).

## Phase 3 — Unify

- [ ] When a model has both an Ollama tag and a resolvable GGUF, let
      the user choose, defaulting to whichever backend is already
      installed.
- [ ] Polish the "running model" indicator / stop button.
- [ ] Revisit bundling llama.cpp binaries if the "install it yourself"
      friction from Phase 2 turns out to matter in practice.
