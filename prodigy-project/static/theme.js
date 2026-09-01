/*
 * static/theme.js
 *
 * Adapts the light/dark/pink theme cycle from ../../index.html
 * (cycleTheme()/setTheme()) into a standalone script Prodigy loads via the
 * recipe's "javascript" config key. Prodigy's own annotation page doesn't
 * have our theme button, so this script creates one and injects it into
 * <body>, then flips a `data-kmu-theme` attribute on <html> that
 * static/style.css keys off of for the widgets THIS project injects
 * (word buffer, extended player controls).
 *
 * IMPORTANT SCOPE NOTE: this only re-themes the CSS variables used by our
 * own injected widgets, not Prodigy's own closed-source Svelte UI chrome --
 * we have no live Prodigy instance in this environment to inspect what (if
 * anything) of Prodigy's own theme could be overridden the same way, so
 * that is NOT attempted here. Confirm against a real running instance
 * whether Prodigy's own "custom_theme" config (see prodigy.json) already
 * covers enough of the chrome to make this redundant.
 */
(function () {
  const ORDER = ["light", "dark", "pink"];
  const ICONS = { light: "☀️", dark: "🌙", pink: "🌸" };

  function currentTheme() {
    return document.documentElement.getAttribute("data-kmu-theme") || "light";
  }

  function setTheme(name) {
    document.documentElement.setAttribute("data-kmu-theme", name);
    try {
      localStorage.setItem("kmu_theme", name);
    } catch (e) {}
    const btn = document.getElementById("kmu-theme-btn");
    if (btn) btn.textContent = ICONS[name] || ICONS.light;
  }

  function cycleTheme() {
    const cur = currentTheme();
    const next = ORDER[(ORDER.indexOf(cur) + 1) % ORDER.length];
    setTheme(next);
  }

  function injectButton() {
    if (document.getElementById("kmu-theme-btn")) return;
    const btn = document.createElement("button");
    btn.id = "kmu-theme-btn";
    btn.title = "Switch theme [D]";
    btn.textContent = ICONS[currentTheme()];
    btn.addEventListener("click", cycleTheme);
    document.body.appendChild(btn);
  }

  function init() {
    let saved = "light";
    try {
      const s = localStorage.getItem("kmu_theme");
      if (s && ORDER.includes(s)) saved = s;
    } catch (e) {}
    setTheme(saved);
    injectButton();
  }

  // CONFIRM WITH YOUR PRODIGY VERSION: Prodigy's "javascript" hook is
  // documented to run once the page's own app has mounted, but the exact
  // timing/readiness guarantee (e.g. whether the DOM for the current
  // example is already rendered) differs by version. DOMContentLoaded is
  // the safe minimum; if the injected button/data attribute needs to exist
  // before Prodigy's own components read computed styles, this may need to
  // hook a Prodigy-specific "example loaded" event instead -- check your
  // version's docs at https://prodi.gy/docs/custom-interfaces.
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Hotkey: "d" cycles theme, mirroring index.html's [D] hotkey.
  document.addEventListener("keydown", (e) => {
    const tag = e.target && e.target.tagName;
    const inInput = tag === "TEXTAREA" || tag === "INPUT";
    if (!inInput && (e.key === "d" || e.key === "D")) {
      cycleTheme();
    }
  });

  window.KMU_THEME = { setTheme, cycleTheme, currentTheme };
})();
