/*
 * static/i18n.js
 *
 * Small translation table for the UI strings THIS project injects on top
 * of Prodigy (word buffer, extended player controls, theme button). This
 * does NOT localize Prodigy's own built-in UI -- Prodigy's own interface
 * strings are out of scope here; this only covers the kz/ru/en/tr labels
 * for the extra widgets, mirroring the language table in ../../index.html.
 *
 * Loaded as one of the files concatenated into the recipe's "javascript"
 * config key (see recipes/audio_markup.py) -- so it must not use ES module
 * import/export syntax, just attach to a shared global (window.KMU_I18N).
 */
(function () {
  const I18N = {
    kz: {
      "buffer.title": "Сөздер буфері",
      "buffer.hint": "Ctrl+Shift+1-9",
      "buffer.placeholder": "Сөз немесе фраза",
      "buffer.add": "+ Қосу",
      "player.speed": "Жылдамдық",
      "player.volume": "Дауыс",
      "player.mode.clip": "Осы клип",
      "player.mode.all": "Барлық клиптер",
      "player.repeat.off": "Қайталау өшірулі",
      "player.repeat.clip": "Қайталау: осы клип",
      "player.repeat.all": "Қайталау: барлық клиптер",
    },
    ru: {
      "buffer.title": "Буфер слов",
      "buffer.hint": "Ctrl+Shift+1-9",
      "buffer.placeholder": "Слово или фраза",
      "buffer.add": "+ Добавить",
      "player.speed": "Скорость",
      "player.volume": "Громкость",
      "player.mode.clip": "Этот клип",
      "player.mode.all": "Все клипы",
      "player.repeat.off": "Повтор выключен",
      "player.repeat.clip": "Повтор: этот клип",
      "player.repeat.all": "Повтор: все клипы",
    },
    en: {
      "buffer.title": "Word buffer",
      "buffer.hint": "Ctrl+Shift+1-9",
      "buffer.placeholder": "Word or phrase",
      "buffer.add": "+ Add",
      "player.speed": "Speed",
      "player.volume": "Volume",
      "player.mode.clip": "This clip",
      "player.mode.all": "All clips",
      "player.repeat.off": "Repeat off",
      "player.repeat.clip": "Repeat: this clip",
      "player.repeat.all": "Repeat: all clips",
    },
    tr: {
      "buffer.title": "Kelime tamponu",
      "buffer.hint": "Ctrl+Shift+1-9",
      "buffer.placeholder": "Kelime veya ifade",
      "buffer.add": "+ Ekle",
      "player.speed": "Hız",
      "player.volume": "Ses",
      "player.mode.clip": "Bu klip",
      "player.mode.all": "Tüm klipler",
      "player.repeat.off": "Tekrar kapalı",
      "player.repeat.clip": "Tekrar: bu klip",
      "player.repeat.all": "Tekrar: tüm klipler",
    },
  };

  let lang = "ru";
  try {
    const saved = localStorage.getItem("kmu_lang");
    if (saved && I18N[saved]) lang = saved;
  } catch (e) {}

  function t(key) {
    return (I18N[lang] && I18N[lang][key]) || I18N.ru[key] || key;
  }
  function setLang(code) {
    if (!I18N[code]) return;
    lang = code;
    try {
      localStorage.setItem("kmu_lang", code);
    } catch (e) {}
  }

  window.KMU_I18N = { t, setLang, get lang() { return lang; } };
})();
