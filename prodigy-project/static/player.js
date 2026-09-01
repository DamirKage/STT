/*
 * static/player.js
 *
 * Adapts the fine-grained player controls from ../../index.html (1%-step
 * volume/speed sliders, global-vs-per-clip mode toggle, 3-state repeat)
 * into a standalone script loaded via the recipe's "javascript" config key.
 *
 * Per DEV_HANDOFF.md point 2: Prodigy's built-in audio widget is a
 * closed-source Svelte component we can't edit, but it renders a plain
 * <audio> element underneath that we CAN control via its standard JS API
 * (.volume, .playbackRate, .loop, .currentTime) without touching Prodigy's
 * own code. This script builds our own control row (volume/speed sliders,
 * mode toggle, repeat button) and drives the real <audio> element via
 * document.querySelector -- this is the standard "headless" pattern for
 * extending Prodigy's audio UI, not a hack, but the CSS selector used to
 * *find* that <audio> element still needs verification against a live
 * instance (see findAudioEl() below).
 */
(function () {
  function findAudioEl() {
    // CONFIRM WITH YOUR PRODIGY VERSION / AGAINST A LIVE INSTANCE: this is
    // a best-documented guess at how Prodigy's audio block renders its
    // underlying <audio> tag. There is no running Prodigy instance in this
    // environment to inspect the real DOM, so before relying on this,
    // open a real annotation page and check with browser devtools, e.g.
    // `document.querySelectorAll('audio')`, and update the selector below
    // to match. Whether the audio recipe/block is core Prodigy or requires
    // the separate `prodigy-audio` plugin also needs confirming against
    // your installed version -- see recipes/audio_markup.py for the same
    // caveat on the block's view_id.
    return (
      document.querySelector(".prodigy-audio audio") ||
      document.querySelector("audio")
    );
  }

  function projKey() {
    let dataset = "default";
    try {
      if (window.prodigy && window.prodigy.dataset) dataset = window.prodigy.dataset;
    } catch (e) {}
    const mode = getMode();
    return mode === "clip" ? "kmu_vs_clip_" + dataset : "kmu_vs_global";
  }

  function getMode() {
    try {
      const m = localStorage.getItem("kmu_mode");
      if (m === "clip" || m === "global") return m;
    } catch (e) {}
    return "global";
  }
  function setMode(m) {
    try {
      localStorage.setItem("kmu_mode", m);
    } catch (e) {}
  }

  function saveVolSpd(vol, spd) {
    try {
      localStorage.setItem(projKey(), JSON.stringify({ vol, spd }));
    } catch (e) {}
  }
  function loadVolSpd() {
    try {
      const raw = localStorage.getItem(projKey());
      if (raw) return JSON.parse(raw);
    } catch (e) {}
    return { vol: 50, spd: 100 };
  }

  let repState = 0; // 0 off, 1 repeat this clip, 2 repeat all clips (loop)

  function applyToAudio(audio, vol, spd) {
    if (!audio) return;
    audio.volume = Math.max(0, Math.min(1, vol / 100));
    audio.playbackRate = spd / 100;
    audio.loop = repState > 0;
  }

  function buildUI() {
    if (document.getElementById("kmu-player")) return;
    const t = (window.KMU_I18N && window.KMU_I18N.t) || ((k) => k);
    const wrap = document.createElement("div");
    wrap.id = "kmu-player";
    wrap.innerHTML = `
      <div class="kmu-vr">
        <span class="kmu-lbl">${t("player.speed")}</span>
        <input type="range" class="kmu-slider" id="kmu-spd" min="50" max="200" step="1" value="100">
        <span class="kmu-pc" id="kmu-spd-pc">100%</span>
      </div>
      <div class="kmu-vr">
        <span class="kmu-lbl">${t("player.volume")}</span>
        <input type="range" class="kmu-slider" id="kmu-vol" min="0" max="100" step="1" value="50">
        <span class="kmu-pc" id="kmu-vol-pc">50%</span>
      </div>
      <button class="kmu-repbtn" id="kmu-rep" title="Repeat">↻</button>
      <button class="kmu-modebtn" id="kmu-mode" title="Volume/speed scope"></button>
    `;

    // CONFIRM WITH YOUR PRODIGY VERSION: same anchoring caveat as
    // buffer.js's injectPanel() -- appending to <body> is a safe fallback;
    // for a tighter layout this should be inserted right next to the
    // audio block's own container once that container's selector is
    // confirmed against a live instance.
    document.body.appendChild(wrap);

    const spd = wrap.querySelector("#kmu-spd");
    const vol = wrap.querySelector("#kmu-vol");
    const spdPc = wrap.querySelector("#kmu-spd-pc");
    const volPc = wrap.querySelector("#kmu-vol-pc");
    const repBtn = wrap.querySelector("#kmu-rep");
    const modeBtn = wrap.querySelector("#kmu-mode");

    function refreshFromStorage() {
      const saved = loadVolSpd();
      vol.value = saved.vol;
      spd.value = saved.spd;
      volPc.textContent = saved.vol + "%";
      spdPc.textContent = saved.spd + "%";
      applyToAudio(findAudioEl(), saved.vol, saved.spd);
    }
    function updateModeLabel() {
      const mode = getMode();
      modeBtn.classList.toggle("on", mode === "clip");
      modeBtn.textContent = mode === "clip" ? t("player.mode.clip") : t("player.mode.all");
    }

    spd.addEventListener("input", () => {
      spdPc.textContent = spd.value + "%";
      applyToAudio(findAudioEl(), vol.value, spd.value);
      saveVolSpd(vol.value, spd.value);
    });
    vol.addEventListener("input", () => {
      volPc.textContent = vol.value + "%";
      applyToAudio(findAudioEl(), vol.value, spd.value);
      saveVolSpd(vol.value, spd.value);
    });
    repBtn.addEventListener("click", () => {
      repState = (repState + 1) % 3;
      repBtn.classList.toggle("on", repState > 0);
      const audio = findAudioEl();
      if (audio) audio.loop = repState > 0;
      // repState === 2 ("repeat all clips") can't be fully implemented by
      // this script alone -- looping past the current example into the
      // next one requires hooking whatever Prodigy event fires when the
      // annotator answers and moves to the next task.
      // CONFIRM WITH YOUR PRODIGY VERSION: check for a `prodigy.events` /
      // custom-interface callback (e.g. an `update` hook firing per
      // example) to advance-and-replay across examples, per
      // https://prodi.gy/docs/custom-interfaces.
    });
    modeBtn.addEventListener("click", () => {
      setMode(getMode() === "clip" ? "global" : "clip");
      updateModeLabel();
      refreshFromStorage();
    });

    updateModeLabel();
    refreshFromStorage();
  }

  function init() {
    buildUI();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.KMU_PLAYER = { findAudioEl };
})();
