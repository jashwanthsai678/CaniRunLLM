(function () {
  "use strict";

  const state = {
    scan: null,
    sortKey: "overall_verdict",
    sortDir: 1,
    search: "",
    filterVerdict: "",
    filterQuant: "",
    filterRuntime: "",
  };

  const GB = 1024 ** 3;

  function bytesToGB(bytes) {
    if (bytes === null || bytes === undefined) return "-";
    return (bytes / GB).toFixed(1) + " GB";
  }

  function formatParams(n) {
    if (n >= 1e9) return (n / 1e9).toFixed(1).replace(/\.0$/, "") + "B";
    if (n >= 1e6) return (n / 1e6).toFixed(0) + "M";
    return String(n);
  }

  function badge(verdict) {
    return `<span class="badge badge-${verdict}">${verdict}</span>`;
  }

  async function fetchJSON(url) {
    const res = await fetch(url);
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || `Request failed: ${res.status}`);
    }
    return res.json();
  }

  function setScanStatus(text) {
    document.getElementById("scan-status").textContent = text;
  }

  function renderHardware(hardware) {
    const grid = document.getElementById("hardware-grid");
    const cpu = hardware.cpu;
    const mem = hardware.memory;
    const os = hardware.os;
    const gpus = hardware.gpus || [];

    let cards = "";

    cards += `
      <div class="hw-card">
        <div class="hw-label">CPU</div>
        <div class="hw-value">${cpu.name}</div>
        <div class="hw-sub">${cpu.physical_cores ?? "?"} cores / ${cpu.logical_cores ?? "?"} threads</div>
      </div>`;

    const ramPercent = mem.total_bytes > 0
      ? Math.min(100, (mem.used_bytes / mem.total_bytes) * 100)
      : 0;
    const ramClass = ramPercent > 90 ? "danger" : ramPercent > 75 ? "warn" : "";

    cards += `
      <div class="hw-card">
        <div class="hw-label">RAM</div>
        <div class="hw-value">${bytesToGB(mem.total_bytes)}</div>
        <div class="hw-sub">${bytesToGB(mem.available_bytes)} available</div>
        <div class="memory-bar"><div class="memory-bar-fill ${ramClass}" style="width:${ramPercent.toFixed(0)}%"></div></div>
      </div>`;

    if (gpus.length === 0) {
      cards += `
        <div class="hw-card">
          <div class="hw-label">GPU</div>
          <div class="hw-value">No dedicated GPU detected</div>
          <div class="hw-sub">CPU-only inference may still be possible.</div>
        </div>`;
    } else {
      gpus.forEach((gpu, index) => {
        const vramPercent = gpu.memory_total_bytes > 0
          ? Math.min(100, (gpu.memory_used_bytes / gpu.memory_total_bytes) * 100)
          : 0;
        const vramClass = vramPercent > 90 ? "danger" : vramPercent > 75 ? "warn" : "";

        cards += `
          <div class="hw-card">
            <div class="hw-label">GPU ${gpus.length > 1 ? index : ""}</div>
            <div class="hw-value">${gpu.name}</div>
            <div class="hw-sub">${bytesToGB(gpu.memory_free_bytes)} free / ${bytesToGB(gpu.memory_total_bytes)} total</div>
            <div class="memory-bar"><div class="memory-bar-fill ${vramClass}" style="width:${vramPercent.toFixed(0)}%"></div></div>
          </div>`;
      });

      if (gpus.length > 1) {
        cards += `
          <div class="hw-card">
            <div class="hw-label">Note</div>
            <div class="hw-sub">${gpus.length} GPUs detected. VRAM is evaluated per-GPU and combined only when a model's runtime supports multi-GPU distribution — it is never treated as one unified pool.</div>
          </div>`;
      }
    }

    cards += `
      <div class="hw-card">
        <div class="hw-label">Operating System</div>
        <div class="hw-value">${os.system} ${os.release}</div>
        <div class="hw-sub">${os.machine}</div>
      </div>`;

    grid.innerHTML = cards;
  }

  function renderSummary(summary) {
    const el = document.getElementById("summary-cards");
    el.innerHTML = `
      <div class="summary-card total">
        <div class="num">${summary.total}</div>
        <div class="label">Models Evaluated</div>
      </div>
      <div class="summary-card can-run">
        <div class="num">${summary.can_run}</div>
        <div class="label">Can Run</div>
      </div>
      <div class="summary-card offload">
        <div class="num">${summary.can_run_with_offload}</div>
        <div class="label">Can Run + Offload</div>
      </div>
      <div class="summary-card needs-validation">
        <div class="num">${summary.needs_validation}</div>
        <div class="label">Needs Validation</div>
      </div>
      <div class="summary-card cannot-run">
        <div class="num">${summary.cannot_run}</div>
        <div class="label">Cannot Run</div>
      </div>`;
  }

  function renderRecommended(recommended) {
    const el = document.getElementById("recommended-cards");

    if (!recommended || recommended.length === 0) {
      el.innerHTML = `<div class="empty-note">No models currently rank as a good fit for this hardware.</div>`;
      return;
    }

    el.innerHTML = recommended.map((entry) => {
      const m = entry.model;
      const c = entry.compatibility;
      return `
        <div class="model-card" data-model-id="${encodeURIComponent(m.name)}">
          <div class="model-name">${m.name}</div>
          ${badge(c.overall_verdict)}
          <div class="model-meta">
            Memory: ${bytesToGB(c.required_memory_bytes)}<br>
            Runtime: ${m.runtime || "unknown"}<br>
            Confidence: ${c.confidence}<br>
            Performance: Not benchmarked
          </div>
        </div>`;
    }).join("");

    el.querySelectorAll(".model-card").forEach((card) => {
      card.addEventListener("click", () => openDetail(card.dataset.modelId));
    });
  }

  function populateFilterOptions(results) {
    const quantSelect = document.getElementById("filter-quant");
    const runtimeSelect = document.getElementById("filter-runtime");

    const quants = [...new Set(results.map((r) => r.model.quantization))].sort();
    const runtimes = [...new Set(results.map((r) => r.model.runtime || "unknown"))].sort();

    quantSelect.innerHTML = '<option value="">All quantizations</option>' +
      quants.map((q) => `<option value="${q}">${q}</option>`).join("");

    runtimeSelect.innerHTML = '<option value="">All runtimes</option>' +
      runtimes.map((r) => `<option value="${r}">${r}</option>`).join("");
  }

  function getSortValue(row, key) {
    switch (key) {
      case "name": return row.model.name;
      case "family": return row.model.family;
      case "parameters": return row.model.parameters;
      case "quantization": return row.model.quantization;
      case "runtime": return row.model.runtime || "";
      case "required_memory_bytes": return row.compatibility.required_memory_bytes;
      case "memory_verdict": return row.compatibility.memory_verdict;
      case "runtime_verdict": return row.compatibility.runtime_verdict;
      case "overall_verdict": return row.compatibility.overall_verdict;
      case "confidence": return row.compatibility.confidence;
      default: return "";
    }
  }

  function applyFiltersAndSort(results) {
    const q = state.search.trim().toLowerCase();

    let filtered = results.filter((row) => {
      if (q && !row.model.name.toLowerCase().includes(q) && !row.model.family.toLowerCase().includes(q)) {
        return false;
      }
      if (state.filterVerdict && row.compatibility.overall_verdict !== state.filterVerdict) {
        return false;
      }
      if (state.filterQuant && row.model.quantization !== state.filterQuant) {
        return false;
      }
      if (state.filterRuntime && (row.model.runtime || "unknown") !== state.filterRuntime) {
        return false;
      }
      return true;
    });

    filtered.sort((a, b) => {
      const av = getSortValue(a, state.sortKey);
      const bv = getSortValue(b, state.sortKey);
      if (av < bv) return -1 * state.sortDir;
      if (av > bv) return 1 * state.sortDir;
      return 0;
    });

    return filtered;
  }

  function renderTable() {
    const tbody = document.getElementById("model-table-body");
    const rows = applyFiltersAndSort(state.scan.results);

    if (rows.length === 0) {
      tbody.innerHTML = `<tr><td colspan="10" class="empty-note">No models match the current filters.</td></tr>`;
      return;
    }

    tbody.innerHTML = rows.map((row) => {
      const m = row.model;
      const c = row.compatibility;
      return `
        <tr data-model-id="${encodeURIComponent(m.name)}">
          <td>${m.name}</td>
          <td>${m.family}</td>
          <td>${formatParams(m.parameters)}</td>
          <td>${m.quantization}</td>
          <td>${m.runtime || "unknown"}</td>
          <td>${bytesToGB(c.required_memory_bytes)}</td>
          <td>${c.memory_verdict}</td>
          <td>${c.runtime_verdict}</td>
          <td>${badge(c.overall_verdict)}</td>
          <td>${c.confidence}</td>
        </tr>`;
    }).join("");

    tbody.querySelectorAll("tr[data-model-id]").forEach((tr) => {
      tr.addEventListener("click", () => openDetail(tr.dataset.modelId));
    });
  }

  function renderMemoryBar(label, usedBytes, totalBytes) {
    const percent = totalBytes > 0 ? Math.min(100, (usedBytes / totalBytes) * 100) : 0;
    const cls = percent > 90 ? "danger" : percent > 75 ? "warn" : "";
    return `
      <div class="detail-row">
        <span class="k">${label}</span>
        <span class="v">${bytesToGB(usedBytes)} / ${bytesToGB(totalBytes)}</span>
      </div>
      <div class="memory-bar"><div class="memory-bar-fill ${cls}" style="width:${percent.toFixed(0)}%"></div></div>`;
  }

  async function openDetail(encodedModelId) {
    const modal = document.getElementById("detail-modal");
    const content = document.getElementById("modal-content");

    content.innerHTML = "Loading...";
    modal.hidden = false;

    try {
      const detail = await fetchJSON(`/api/models/${encodedModelId}`);
      const m = detail.model;
      const c = detail.compatibility;
      const mem = detail.memory_breakdown;

      content.innerHTML = `
        <div class="detail-title">${m.name}</div>
        <div class="detail-family">${m.family} &middot; ${m.architecture}</div>

        <div class="detail-section">
          <h3>Model</h3>
          <div class="detail-row"><span class="k">Parameters</span><span class="v">${formatParams(m.parameters)}</span></div>
          <div class="detail-row"><span class="k">Quantization</span><span class="v">${m.quantization}</span></div>
          <div class="detail-row"><span class="k">Context Length</span><span class="v">${m.context_length.toLocaleString()}</span></div>
          <div class="detail-row"><span class="k">Runtime</span><span class="v">${m.runtime || "unknown"}</span></div>
          <div class="detail-row"><span class="k">File Size</span><span class="v">${m.file_size_bytes ? bytesToGB(m.file_size_bytes) : "unknown"}</span></div>
        </div>

        <div class="detail-section">
          <h3>Memory Requirements</h3>
          <div class="detail-row"><span class="k">Weights</span><span class="v">${bytesToGB(mem.weight_memory_bytes)}</span></div>
          <div class="detail-row"><span class="k">KV Cache</span><span class="v">${bytesToGB(mem.kv_cache_bytes)}</span></div>
          <div class="detail-row"><span class="k">Runtime Overhead</span><span class="v">${bytesToGB(mem.runtime_overhead_bytes)}</span></div>
          <div class="detail-row"><span class="k">Safety Margin</span><span class="v">${bytesToGB(mem.safety_margin_bytes)}</span></div>
          <div class="detail-row"><span class="k">Total Required</span><span class="v">${bytesToGB(mem.total_required_bytes)}</span></div>
        </div>

        <div class="detail-section">
          <h3>Hardware</h3>
          ${renderMemoryBar("GPU VRAM", c.required_memory_bytes, c.available_vram_bytes)}
          ${renderMemoryBar("System RAM", c.required_memory_bytes, c.available_ram_bytes)}
        </div>

        <div class="detail-section">
          <h3>Compatibility</h3>
          <div class="detail-row"><span class="k">Memory Verdict</span><span class="v">${c.memory_verdict}</span></div>
          <div class="detail-row"><span class="k">Memory Strategy</span><span class="v">${c.memory_strategy}</span></div>
          <div class="detail-row"><span class="k">Runtime Verdict</span><span class="v">${c.runtime_verdict}</span></div>
          <div class="detail-row"><span class="k">Overall Verdict</span><span class="v">${badge(c.overall_verdict)}</span></div>
          <div class="detail-row"><span class="k">Confidence</span><span class="v">${c.confidence}</span></div>
        </div>

        <div class="detail-section">
          <h3>Reason</h3>
          <div class="detail-reason">${c.reason}</div>
        </div>

        <div class="detail-section">
          <h3>Performance</h3>
          <div class="detail-reason">Not benchmarked. This project does not fabricate performance numbers — a benchmark engine will populate this once it exists.</div>
        </div>`;
    } catch (err) {
      content.innerHTML = `<div class="detail-reason">Could not load model details: ${err.message}</div>`;
    }
  }

  function formatScanTime(iso) {
    try {
      const date = new Date(iso);
      return date.toLocaleString();
    } catch {
      return iso;
    }
  }

  async function loadScan() {
    setScanStatus("Scanning hardware...");

    try {
      const scan = await fetchJSON("/api/scan");
      state.scan = scan;

      renderHardware(scan.hardware);
      renderSummary(scan.summary);
      renderRecommended(scan.recommended);
      populateFilterOptions(scan.results);
      renderTable();

      setScanStatus(`● Scanned ${formatScanTime(scan.scanned_at)} — ${scan.summary.total} models evaluated`);
    } catch (err) {
      setScanStatus(`Scan failed: ${err.message}`);
    }
  }

  function setupControls() {
    document.getElementById("rescan-btn").addEventListener("click", loadScan);

    document.getElementById("search-input").addEventListener("input", (e) => {
      state.search = e.target.value;
      renderTable();
    });

    document.getElementById("filter-verdict").addEventListener("change", (e) => {
      state.filterVerdict = e.target.value;
      renderTable();
    });

    document.getElementById("filter-quant").addEventListener("change", (e) => {
      state.filterQuant = e.target.value;
      renderTable();
    });

    document.getElementById("filter-runtime").addEventListener("change", (e) => {
      state.filterRuntime = e.target.value;
      renderTable();
    });

    document.querySelectorAll("th[data-sort]").forEach((th) => {
      th.addEventListener("click", () => {
        const key = th.dataset.sort;
        if (state.sortKey === key) {
          state.sortDir *= -1;
        } else {
          state.sortKey = key;
          state.sortDir = 1;
        }
        renderTable();
      });
    });

    document.getElementById("modal-close").addEventListener("click", () => {
      document.getElementById("detail-modal").hidden = true;
    });

    document.getElementById("detail-modal").addEventListener("click", (e) => {
      if (e.target.id === "detail-modal") {
        e.currentTarget.hidden = true;
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    setupControls();
    loadScan();
  });
})();
