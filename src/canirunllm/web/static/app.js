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
    advancedView: false,
  };

  const GB = 1024 ** 3;

  const BUCKETS = [
    { key: "CAN_RUN", title: "Can Run", subtitle: "Comfortable" },
    { key: "CAN_RUN_WITH_OFFLOAD", title: "Can Run With Offload", subtitle: "Possible, but slower" },
    { key: "NEEDS_VALIDATION", title: "Needs Validation", subtitle: "More information needed" },
    { key: "CANNOT_RUN", title: "Cannot Run", subtitle: "Not enough resources" },
  ];

  const ICON_GLYPH = {
    check: "✓",
    warn: "⚠",
    unknown: "?",
    cross: "✕",
  };

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

  function verdictIcon(compat) {
    return `<span class="verdict-icon icon-${compat.friendly_icon}">
      <span class="glyph">${ICON_GLYPH[compat.friendly_icon] || ""}</span>
      ${compat.friendly_verdict}
    </span>`;
  }

  function reasonList(reasons) {
    return `<ul class="reason-list">` +
      reasons.map((r) => `<li class="${r.ok ? "r-ok" : "r-bad"}">${r.ok ? "✓" : "•"} ${r.text}</li>`).join("") +
      `</ul>`;
  }

  function formatSpeedRange(performance) {
    if (!performance || !performance.generation_speed) return "n/a";
    const s = performance.generation_speed;
    return `~${Math.round(s.low)}-${Math.round(s.high)} ${s.unit}`;
  }

  function midpointSpeed(performance) {
    if (!performance || !performance.generation_speed) return -1;
    const s = performance.generation_speed;
    return (s.low + s.high) / 2;
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

  function renderHero(scan) {
    const summary = scan.summary;
    const el = document.getElementById("hero-summary");

    const comfortable = summary.can_run;
    const offload = summary.can_run_with_offload;
    const cannot = summary.cannot_run;

    let sentence;

    if (comfortable > 0) {
      sentence = `Your computer can run <strong>${comfortable} model${comfortable === 1 ? "" : "s"}</strong> comfortably`;
      if (offload > 0) sentence += `, and <strong>${offload} more</strong> with slower CPU/RAM offload`;
      sentence += ".";
    } else if (offload > 0) {
      sentence = `Your computer can run <strong>${offload} model${offload === 1 ? "" : "s"}</strong> using CPU/RAM offload (expect slower performance). No models fit comfortably in GPU memory alone right now.`;
    } else {
      sentence = `None of the ${summary.total} models in this catalog currently fit your available memory. See "Cannot Run" below for why, and what might help.`;
    }

    if (cannot > 0 && (comfortable > 0 || offload > 0)) {
      sentence += ` ${cannot} model${cannot === 1 ? "" : "s"} would need more memory than you currently have free.`;
    }

    el.innerHTML = sentence;
    el.classList.remove("skeleton");
  }

  function renderBestForYou(bestForYou) {
    const panel = document.getElementById("best-for-you-panel");
    const container = document.getElementById("best-for-you-card");

    if (!bestForYou) {
      panel.hidden = true;
      return;
    }

    panel.hidden = false;

    const m = bestForYou.model;
    const c = bestForYou.compatibility;

    const p = bestForYou.performance;

    container.innerHTML = `
      <div class="best-card model-card" data-model-id="${encodeURIComponent(m.name)}">
        <div class="best-label">Recommended for your hardware</div>
        <div class="best-name">${m.name}</div>
        ${verdictIcon(c)}
        <div class="model-meta">Estimated speed: ${formatSpeedRange(p)}</div>
        ${reasonList(c.reasons)}
        <div class="best-caveat">Compatibility-based recommendation — not yet benchmarked for real-world speed or quality.</div>
      </div>`;

    container.querySelector(".best-card").addEventListener("click", () => openDetail(encodeURIComponent(m.name)));
  }

  function renderVerdictChart(summary) {
    const panel = document.getElementById("overview-chart-panel");
    const container = document.getElementById("verdict-chart");

    const segments = [
      { key: "CAN_RUN", label: "Can Run", count: summary.can_run },
      { key: "CAN_RUN_WITH_OFFLOAD", label: "Can Run With Offload", count: summary.can_run_with_offload },
      { key: "NEEDS_VALIDATION", label: "Needs Validation", count: summary.needs_validation },
      { key: "CANNOT_RUN", label: "Cannot Run", count: summary.cannot_run },
    ];

    if (summary.total === 0) {
      panel.hidden = true;
      return;
    }

    panel.hidden = false;

    const bar = segments
      .filter((s) => s.count > 0)
      .map((s) => {
        const percent = (s.count / summary.total) * 100;
        return `<div class="verdict-segment seg-${s.key}" style="width:${percent}%" title="${s.label}: ${s.count}">${percent >= 12 ? s.count : ""}</div>`;
      })
      .join("");

    const legend = segments
      .filter((s) => s.count > 0)
      .map((s) => `
        <div class="verdict-legend-item">
          <span class="swatch seg-${s.key}"></span>
          <strong>${s.count}</strong> ${s.label}
        </div>
      `)
      .join("");

    container.innerHTML = `
      <div class="verdict-bar">${bar}</div>
      <div class="verdict-legend">${legend}</div>`;
  }

  const MAX_THROUGHPUT_BARS = 15;

  function renderThroughputChart(results) {
    const panel = document.getElementById("throughput-chart-panel");
    const container = document.getElementById("throughput-chart");

    const runnable = results
      .filter((r) => r.performance && r.performance.generation_speed)
      .sort((a, b) => midpointSpeed(b.performance) - midpointSpeed(a.performance));

    if (runnable.length === 0) {
      panel.hidden = true;
      return;
    }

    panel.hidden = false;

    const shown = runnable.slice(0, MAX_THROUGHPUT_BARS);
    const maxHigh = Math.max(...shown.map((r) => r.performance.generation_speed.high));

    const rows = shown.map((r) => {
      const speed = r.performance.generation_speed;
      const lowPercent = (speed.low / maxHigh) * 100;
      const widthPercent = ((speed.high - speed.low) / maxHigh) * 100;

      return `
        <div class="throughput-row" data-model-id="${encodeURIComponent(r.model.name)}" title="${r.model.name}: ${formatSpeedRange(r.performance)}">
          <div class="tp-name">${r.model.name}</div>
          <div class="throughput-track">
            <div class="throughput-fill" style="left:${lowPercent}%; width:${Math.max(widthPercent, 1.5)}%"></div>
          </div>
          <div class="tp-value">${formatSpeedRange(r.performance)}</div>
        </div>`;
    }).join("");

    container.innerHTML = `<div class="throughput-rows">${rows}</div>`;

    if (runnable.length > MAX_THROUGHPUT_BARS) {
      container.innerHTML += `<p class="chart-caption">Showing the top ${MAX_THROUGHPUT_BARS} of ${runnable.length} runnable models by estimated speed.</p>`;
    }

    container.querySelectorAll(".throughput-row").forEach((row) => {
      row.addEventListener("click", () => openDetail(row.dataset.modelId));
    });
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
          <div class="hw-sub">You can still run smaller local models using your CPU.</div>
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
            <div class="hw-sub">${gpus.length} GPUs detected. VRAM is evaluated per-GPU and only combined when a model's runtime supports splitting across GPUs — never treated as one unified pool.</div>
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

  function renderBuckets(results) {
    const container = document.getElementById("model-buckets");

    let html = "";

    BUCKETS.forEach((bucket) => {
      const items = results.filter((r) => r.compatibility.overall_verdict === bucket.key);

      if (items.length === 0) return;

      html += `
        <div class="bucket">
          <div class="bucket-header">
            <span class="verdict-icon icon-${items[0].compatibility.friendly_icon}">
              <span class="glyph">${ICON_GLYPH[items[0].compatibility.friendly_icon] || ""}</span>
              ${bucket.title}
            </span>
            <span class="bucket-count">— ${bucket.subtitle} (${items.length})</span>
          </div>
          <div class="bucket-grid">
            ${items.map((item) => `
              <div class="bucket-card" data-model-id="${encodeURIComponent(item.model.name)}">
                <div class="bucket-card-name">${item.model.name}</div>
                <div class="bucket-card-meta">${formatParams(item.model.parameters)} &middot; ${item.model.quantization}</div>
                <div class="bucket-card-meta">Est. ${formatSpeedRange(item.performance)}</div>
              </div>
            `).join("")}
          </div>
        </div>`;
    });

    if (!html) {
      html = `<div class="empty-note">No models found in the current catalog.</div>`;
    }

    container.innerHTML = html;

    container.querySelectorAll(".bucket-card").forEach((card) => {
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
      case "estimated_speed": return midpointSpeed(row.performance);
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
      tbody.innerHTML = `<tr><td colspan="11" class="empty-note">No models match the current filters.</td></tr>`;
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
          <td>${formatSpeedRange(row.performance)}</td>
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
      const p = detail.performance;
      const mem = detail.memory_breakdown;

      let simpleSection = `
        <div class="detail-title">${m.name}</div>
        <div class="detail-family">${m.family} &middot; ${m.architecture}</div>

        <div class="detail-section">
          ${verdictIcon(c)}
          <div class="model-meta">Estimated speed: ${formatSpeedRange(p)} (${p.confidence.toLowerCase()} confidence, not benchmarked)</div>
          ${reasonList(c.reasons)}
        </div>`;

      if (detail.alternative) {
        simpleSection += `
          <div class="detail-section">
            <div class="alternative-box" data-model-id="${encodeURIComponent(detail.alternative.name)}">
              <div class="alt-label">Try instead</div>
              <div class="alt-name">${detail.alternative.name}</div>
            </div>
          </div>`;
      }

      if (detail.run_commands && detail.run_commands.length > 0) {
        simpleSection += `
          <div class="detail-section">
            <h3>Run This Model</h3>
            ${detail.run_commands.map((rc) => `
              <div class="run-option">
                <div class="run-option-label">${rc.runtime}</div>
                <div class="run-command-box">
                  <code>${rc.command}</code>
                </div>
                <div class="run-command-note">${rc.note}</div>
              </div>
            `).join("")}
          </div>`;
      }

      const technicalSection = `
        <details class="tech-details">
          <summary>Technical details</summary>

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
            <h3>Reason (raw)</h3>
            <div class="detail-reason">${c.reason}</div>
          </div>

          <div class="detail-section">
            <h3>Performance</h3>
            <div class="detail-row"><span class="k">Estimated speed</span><span class="v">${formatSpeedRange(p)}</span></div>
            <div class="detail-row"><span class="k">Confidence</span><span class="v">${p.confidence}</span></div>
            <div class="detail-row"><span class="k">Source</span><span class="v">${p.source}</span></div>
            <div class="detail-reason">${p.explanation.join(" ")}</div>
          </div>
        </details>`;

      content.innerHTML = simpleSection + technicalSection;

      const altBox = content.querySelector(".alternative-box");
      if (altBox) {
        altBox.addEventListener("click", () => openDetail(altBox.dataset.modelId));
      }
    } catch (err) {
      content.innerHTML = `<div class="detail-reason">We couldn't load details for this model.<br>Reason: ${err.message}</div>`;
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

  function updateViewToggle() {
    document.getElementById("simple-view").hidden = state.advancedView;
    document.getElementById("advanced-view").hidden = !state.advancedView;
    document.getElementById("toggle-advanced-btn").textContent =
      state.advancedView ? "Simple view" : "Advanced view";
    document.getElementById("models-heading").textContent =
      state.advancedView ? "All Models" : "What Can I Run?";
  }

  async function loadScan() {
    setScanStatus("Checking your computer...");

    try {
      const scan = await fetchJSON("/api/scan");
      state.scan = scan;

      renderHero(scan);
      renderVerdictChart(scan.summary);
      renderBestForYou(scan.best_for_you);
      renderThroughputChart(scan.results);
      renderHardware(scan.hardware);
      renderBuckets(scan.results);
      populateFilterOptions(scan.results);
      renderTable();

      setScanStatus(`● Scanned ${formatScanTime(scan.scanned_at)} — ${scan.summary.total} models evaluated`);
    } catch (err) {
      setScanStatus(`Scan failed: ${err.message}`);
      document.getElementById("hero-summary").textContent =
        "We couldn't finish checking your computer. Try rescanning.";
    }
  }

  function setupControls() {
    document.getElementById("rescan-btn").addEventListener("click", loadScan);

    document.getElementById("hero-see-models-btn").addEventListener("click", () => {
      const target = document.getElementById("best-for-you-panel").hidden
        ? document.getElementById("models-panel")
        : document.getElementById("best-for-you-panel");
      target.scrollIntoView({ behavior: "smooth" });
    });

    document.getElementById("toggle-advanced-btn").addEventListener("click", () => {
      state.advancedView = !state.advancedView;
      updateViewToggle();
    });

    document.getElementById("throughput-advanced-link").addEventListener("click", (e) => {
      e.preventDefault();
      state.advancedView = true;
      updateViewToggle();
      document.getElementById("models-panel").scrollIntoView({ behavior: "smooth" });
    });

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
    updateViewToggle();
    loadScan();
  });
})();
