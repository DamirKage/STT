/*
 * static/buffer.js
 *
 * Adapts the "word buffer" feature from ../../index.html (snippets grid +
 * Ctrl+Shift+1-9 insertion, see DEV_HANDOFF.md point 1) into a standalone
 * script loaded via the recipe's "javascript" config key.
 *
 * Per DEV_HANDOFF.md point 1: this deliberately does NOT need a new DB
 * table or API -- it reads/writes localStorage directly in the browser,
 * scoped per Prodigy dataset (so different projects/datasets keep separate
 * buffers), exactly like index.html's per-project snippet list.
 */
(function () {
  const DEFAULTS = [
    { t: "саламатсыз ба", k: "1" },
    { t: "сәлеметсіз бе", k: "2" },
    { t: "каспи голд", k: "3" },
  ];

  function datasetKey() {
    // CONFIRM WITH YOUR PRODIGY VERSION: Prodigy exposes the current
    // dataset name to frontend JS via a global, but the exact global name
    // has changed across versions (older Prodigy exposed `window.prodigy`
    // with a `dataset` field; check yours with
    // `console.log(window.prodigy)` in the browser devtools on a running
    // instance, or grep the installed prodigy package's bundled JS). This
    // falls back to a fixed key so the buffer still works (just shared
    // across datasets) if the global isn't found.
    try {
      if (window.prodigy && window.prodigy.dataset) {
        return "kmu_buf_" + window.prodigy.dataset;
      }
    } catch (e) {}
    return "kmu_buf_default";
  }

  function loadSnips() {
    try {
      const raw = localStorage.getItem(datasetKey());
      if (raw) return JSON.parse(raw);
    } catch (e) {}
    return DEFAULTS.slice();
  }

  function saveSnips(snips) {
    try {
      localStorage.setItem(datasetKey(), JSON.stringify(snips));
    } catch (e) {}
  }

  function esc(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function findTextInput() {
    // CONFIRM WITH YOUR PRODIGY VERSION: this needs to match whatever DOM
    // element Prodigy's text_input block actually renders (likely a
    // <textarea>, possibly with a Prodigy-specific class like
    // `.prodigy-text-input textarea` -- there is no live Prodigy instance
    // in this environment to inspect, so the selector below is a
    // best-documented guess and MUST be verified against a real rendered
    // annotation page before relying on it, e.g. via browser devtools:
    // `document.querySelectorAll('textarea')`.
    return (
      document.querySelector(".prodigy-text-input textarea") ||
      document.querySelector('textarea[placeholder]') ||
      document.querySelector("textarea")
    );
  }

  function insertIntoTextarea(ta, text) {
    if (!ta) return;
    ta.focus();
    const s = ta.selectionStart ?? ta.value.length;
    const e = ta.selectionEnd ?? ta.value.length;
    const before = ta.value.substring(0, s);
    const after = ta.value.substring(e);
    const sep = before.length > 0 && !before.endsWith(" ") ? " " : "";
    ta.value = before + sep + text + " " + after;
    const pos = s + sep.length + text.length + 1;
    ta.setSelectionRange(pos, pos);
    // Fire an input event so any framework-bound state (Prodigy's Svelte
    // component included) picks up the programmatic change.
    ta.dispatchEvent(new Event("input", { bubbles: true }));
  }

  function render() {
    const panel = document.getElementById("kmu-buffer");
    if (!panel) return;
    const t = (window.KMU_I18N && window.KMU_I18N.t) || ((k) => k);
    const snips = loadSnips();
    const grid = panel.querySelector(".kmu-grid");
    grid.innerHTML = "";
    snips.forEach((s, i) => {
      const chip = document.createElement("div");
      chip.className = "kmu-chip";
      chip.innerHTML = `<span class="kmu-badge">${esc(s.k)}</span><span>${esc(
        s.t
      )}</span><button class="kmu-del" data-i="${i}">×</button>`;
      chip.addEventListener("click", (e) => {
        if (e.target.classList.contains("kmu-del")) return;
        insertIntoTextarea(findTextInput(), s.t);
      });
      chip.querySelector(".kmu-del").addEventListener("click", (e) => {
        e.stopPropagation();
        const idx = parseInt(e.target.dataset.i, 10);
        snips.splice(idx, 1);
        snips.forEach((sn, j) => (sn.k = String(j + 1)));
        saveSnips(snips);
        render();
      });
      grid.appendChild(chip);
    });
  }

  function injectPanel() {
    if (document.getElementById("kmu-buffer")) return;
    const t = (window.KMU_I18N && window.KMU_I18N.t) || ((k) => k);
    const panel = document.createElement("div");
    panel.id = "kmu-buffer";
    panel.innerHTML = `
      <div class="kmu-h">
        <span class="kmu-title">${t("buffer.title")}</span>
        <span class="kmu-hint">${t("buffer.hint")}</span>
      </div>
      <div class="kmu-grid"></div>
      <div class="kmu-addrow">
        <input type="text" id="kmu-buf-in" placeholder="${t(
          "buffer.placeholder"
        )}">
        <button id="kmu-buf-add">${t("buffer.add")}</button>
      </div>
    `;

    // CONFIRM WITH YOUR PRODIGY VERSION: anchoring point for where this
    // panel gets inserted into Prodigy's page. Appending to <body> is a
    // safe fallback that always works visually (fixed/floating), but for
    // a tighter layout next to the transcription box you'd want to insert
    // it right after the text_input block's container -- that container's
    // selector needs the same live-instance verification noted in
    // findTextInput() above.
    document.body.appendChild(panel);

    panel.querySelector("#kmu-buf-add").addEventListener("click", () => {
      const input = panel.querySelector("#kmu-buf-in");
      const val = input.value.trim();
      if (!val) return;
      const snips = loadSnips();
      snips.push({ t: val, k: String(snips.length + 1) });
      saveSnips(snips);
      input.value = "";
      render();
    });

    render();
  }

  function init() {
    injectPanel();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Ctrl+Shift+1-9 inserts the matching snippet, mirroring index.html.
  document.addEventListener("keydown", (e) => {
    if (e.ctrlKey && e.shiftKey && /^Digit[1-9]$/.test(e.code)) {
      const key = e.code.slice(5);
      const snip = loadSnips().find((s) => s.k === key);
      if (snip) {
        e.preventDefault();
        insertIntoTextarea(findTextInput(), snip.t);
      }
    }
  });

  window.KMU_BUFFER = { render, loadSnips, saveSnips };
})();
