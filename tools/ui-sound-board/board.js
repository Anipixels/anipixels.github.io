/* Anipixels UI sound board. Plain JS, no dependencies, works from file://.
   The list of sounds is static HTML; this script adds playback, search, filters and copy. */
(function () {
  "use strict";
  var probe = document.createElement("audio");
  var canOgg = !!(probe.canPlayType && probe.canPlayType('audio/ogg; codecs="vorbis"'));
  var EXT = canOgg ? "ogg" : "mp3";

  var items = Array.prototype.slice.call(document.querySelectorAll(".sb-item"));
  var packs = Array.prototype.slice.call(document.querySelectorAll(".sb-pack"));
  var search = document.getElementById("sb-search");
  var vol = document.getElementById("sb-vol");
  var volOut = document.getElementById("sb-vol-out");
  var fmt = document.getElementById("sb-fmt");
  var status = document.getElementById("sb-status");
  var count = document.getElementById("sb-count");
  var empty = document.getElementById("sb-empty");
  var stopBtn = document.getElementById("sb-stop");
  var packRadios = Array.prototype.slice.call(document.querySelectorAll('input[name="sb-pack"]'));
  var players = {};   // src -> HTMLAudioElement

  document.getElementById("sb-format-note").textContent =
    "Your browser is playing the " + (canOgg ? "OGG Vorbis files (the same files as in the samplers)." : "MP3 fallback copies (this browser cannot play OGG Vorbis).");

  function store(key, value) {
    try {
      if (value === undefined) return window.localStorage.getItem(key);
      window.localStorage.setItem(key, value);
    } catch (e) { /* storage blocked: settings just do not persist */ }
    return null;
  }
  function say(text) { status.textContent = text; }
  function volume() { return Math.max(0, Math.min(1, Number(vol.value) / 100)); }

  function getPlayer(btn) {
    var src = btn.getAttribute("data-src") + "." + EXT;
    var a = players[src];
    if (!a) {
      a = new Audio();
      a.preload = "auto";
      a.src = src;
      var li = btn.parentNode;
      a.addEventListener("playing", function () { li.classList.add("is-playing"); });
      a.addEventListener("pause", function () { li.classList.remove("is-playing"); });
      a.addEventListener("ended", function () { li.classList.remove("is-playing"); });
      a.addEventListener("error", function () {
        li.classList.remove("is-playing");
        say("Could not load " + btn.getAttribute("data-name") + "." + EXT);
      });
      players[src] = a;
    }
    return a;
  }
  function play(btn) {
    var a = getPlayer(btn);
    a.volume = volume();
    try { a.currentTime = 0; } catch (e) { /* not loaded yet */ }
    var p = a.play();
    if (p && p.catch) p.catch(function () { say("Playback was blocked by the browser. Click a sound to try again."); });
    say("Playing " + btn.getAttribute("data-name"));
  }
  function stopAll() {
    Object.keys(players).forEach(function (k) { players[k].pause(); });
    say("Stopped.");
  }

  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).catch(function () { return legacyCopy(text); });
    }
    return legacyCopy(text);
  }
  function legacyCopy(text) {
    return new Promise(function (resolve, reject) {
      var t = document.createElement("textarea");
      t.value = text; t.setAttribute("readonly", "");
      t.style.position = "fixed"; t.style.opacity = "0";
      document.body.appendChild(t); t.select();
      var ok = false;
      try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
      document.body.removeChild(t);
      if (ok) resolve(); else reject(new Error("copy failed"));
    });
  }
  function fileName(name) {
    var f = fmt.value;
    return f === "none" ? name : name + "." + f;
  }

  function applyFilter() {
    var q = search.value.trim().toLowerCase();
    var words = q ? q.split(/\s+/) : [];
    var pack = "all";
    packRadios.forEach(function (r) { if (r.checked) pack = r.value; });
    var shown = 0;
    items.forEach(function (li) {
      var hay = li.getAttribute("data-hay");
      var ok = (pack === "all" || li.getAttribute("data-pack") === pack);
      for (var i = 0; ok && i < words.length; i++) if (hay.indexOf(words[i]) === -1) ok = false;
      li.hidden = !ok;
      if (ok) shown++;
    });
    packs.forEach(function (sec) {
      sec.hidden = !sec.querySelector(".sb-item:not([hidden])");
    });
    count.textContent = shown + " of " + items.length + " sounds shown";
    empty.hidden = shown !== 0;
  }

  function visiblePlayButtons() {
    return items.filter(function (li) { return !li.hidden; }).map(function (li) { return li.querySelector(".sb-play"); });
  }
  function moveFocus(from, key) {
    var list = visiblePlayButtons();
    var i = list.indexOf(from);
    if (i === -1) return false;
    var target = null;
    if (key === "ArrowRight") target = list[i + 1];
    else if (key === "ArrowLeft") target = list[i - 1];
    else if (key === "Home") target = list[0];
    else if (key === "End") target = list[list.length - 1];
    else {
      var r = from.getBoundingClientRect();
      var cx = r.left + r.width / 2, best = Infinity, dir = key === "ArrowDown" ? 1 : -1;
      for (var j = i + dir; j >= 0 && j < list.length; j += dir) {
        var b = list[j].getBoundingClientRect();
        if (Math.abs(b.top - r.top) < 4) continue;                 // same row
        var rowGap = Math.abs(b.top - r.top);
        var d = rowGap * 1000 + Math.abs(b.left + b.width / 2 - cx);
        if (d < best) { best = d; target = list[j]; }
        else if (target && rowGap > Math.abs(target.getBoundingClientRect().top - r.top) + 4) break;
      }
    }
    if (target) { target.focus(); return true; }
    return false;
  }

  document.addEventListener("click", function (e) {
    var t = e.target;
    var playBtn = t.closest ? t.closest(".sb-play") : null;
    if (playBtn) { play(playBtn); return; }
    var copyBtn = t.closest ? t.closest(".sb-copy") : null;
    if (copyBtn) {
      var text = fileName(copyBtn.getAttribute("data-name"));
      copyText(text).then(function () { say("Copied " + text); }, function () { say("Copy failed. The file name is " + text); });
    }
  });
  document.addEventListener("pointerover", function (e) {
    var b = e.target.closest ? e.target.closest(".sb-play") : null;
    if (b) getPlayer(b);                                           // start loading on hover
  });
  document.addEventListener("focusin", function (e) {
    if (e.target.classList && e.target.classList.contains("sb-play")) getPlayer(e.target);
  });
  document.addEventListener("keydown", function (e) {
    var t = e.target;
    var typing = t === search || t.tagName === "SELECT" || t.tagName === "TEXTAREA";
    if (e.key === "/" && !typing && !e.ctrlKey && !e.metaKey && !e.altKey) { e.preventDefault(); search.focus(); search.select(); return; }
    if (e.key === "Escape") {
      if (t === search && search.value) { search.value = ""; applyFilter(); }
      else stopAll();
      return;
    }
    if (t === search && e.key === "ArrowDown") {
      var first = visiblePlayButtons()[0];
      if (first) { e.preventDefault(); first.focus(); }
      return;
    }
    if (t.classList && t.classList.contains("sb-play")) {
      if (["ArrowRight", "ArrowLeft", "ArrowDown", "ArrowUp", "Home", "End"].indexOf(e.key) !== -1) {
        if (moveFocus(t, e.key)) e.preventDefault();
      } else if ((e.key === "c" || e.key === "C") && !e.ctrlKey && !e.metaKey && !e.altKey) {
        var text = fileName(t.getAttribute("data-name"));
        copyText(text).then(function () { say("Copied " + text); }, function () { say("Copy failed. The file name is " + text); });
      }
    }
  });

  search.addEventListener("input", applyFilter);
  packRadios.forEach(function (r) { r.addEventListener("change", applyFilter); });
  stopBtn.addEventListener("click", stopAll);
  vol.addEventListener("input", function () {
    volOut.textContent = vol.value + "%";
    var v = volume();
    Object.keys(players).forEach(function (k) { players[k].volume = v; });
    store("anipixels-sb-vol", vol.value);
  });
  fmt.addEventListener("change", function () { store("anipixels-sb-fmt", fmt.value); });

  var savedVol = store("anipixels-sb-vol");
  if (savedVol !== null && savedVol !== "" && !isNaN(Number(savedVol))) vol.value = savedVol;
  volOut.textContent = vol.value + "%";
  var savedFmt = store("anipixels-sb-fmt");
  if (savedFmt === "ogg" || savedFmt === "wav" || savedFmt === "none") fmt.value = savedFmt;
  applyFilter();
})();
