/* Anipixels VFX sprite sheet player: plays the 8 Crisp Juice free sampler sheets on a canvas.
   Plain JS, no dependencies, works from file://. Frame data comes from data.js, which is generated
   from the sampler's sheets.json (frames, cell, cols, rows, fps, loop and additive are copied unchanged). */
(function () {
  "use strict";
  var SHEETS = window.VFX_DATA.sheets, BASE = window.VFX_DATA.base;
  var $ = function (id) { return document.getElementById(id); };
  var stage = $("vx-stage"), canvas = $("vx-canvas"), ctx = canvas.getContext("2d");
  var playBtn = $("vx-play"), restartBtn = $("vx-restart");
  var frameIn = $("vx-frame"), frameOut = $("vx-frame-out"), fpsIn = $("vx-fps"), fpsOut = $("vx-fps-out");
  var loopIn = $("vx-loop"), blendIn = $("vx-blend"), scaleIn = $("vx-scale"), colorIn = $("vx-color");
  var status = $("vx-status"), code = $("vx-code"), sheetImg = $("vx-sheet-img"), cursor = $("vx-cursor");
  var info = { name: $("vx-i-name"), grid: $("vx-i-grid"), frames: $("vx-i-frames"), flags: $("vx-i-flags"), file: $("vx-i-file") };
  var picks = Array.prototype.slice.call(document.querySelectorAll(".vx-pick"));
  var images = {};
  var state = { i: 0, frame: 0, playing: true, last: 0, spawned: [], dpr: 1, dirty: true };
  var checker = null;

  function sheet() { return SHEETS[state.i]; }
  function image(s) {
    var im = images[s.name];
    if (!im) {
      im = new Image();
      im.onload = function () { state.dirty = true; };
      im.onerror = function () { status.textContent = "Could not load " + s.name + ".png"; };
      im.src = BASE + s.name + ".png";
      images[s.name] = im;
    }
    return im;
  }
  function bgMode() {
    var r = document.querySelector('input[name="vx-bg"]:checked');
    return r ? r.value : "dark";
  }
  function resize() {
    var dpr = Math.min(window.devicePixelRatio || 1, 3);
    var w = Math.max(1, Math.round(stage.clientWidth * dpr)), h = Math.max(1, Math.round(stage.clientHeight * dpr));
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
    state.dpr = dpr; state.dirty = true;
  }
  function drawSize(s) {
    var v = scaleIn.value;
    if (v === "fit") return Math.min(canvas.width, canvas.height) * 0.92;
    return s.cell * Number(v) * state.dpr;
  }
  function paintBackground() {
    var mode = bgMode();
    ctx.globalCompositeOperation = "source-over";
    if (mode === "checker") {
      if (!checker) {
        var c = document.createElement("canvas"); c.width = c.height = 32;
        var g = c.getContext("2d");
        g.fillStyle = "#2a2d36"; g.fillRect(0, 0, 32, 32);
        g.fillStyle = "#3a3e4a"; g.fillRect(0, 0, 16, 16); g.fillRect(16, 16, 16, 16);
        checker = ctx.createPattern(c, "repeat");
      }
      ctx.fillStyle = checker;
    } else if (mode === "light") ctx.fillStyle = "#eef0f5";
    else if (mode === "custom") ctx.fillStyle = colorIn.value;
    else ctx.fillStyle = "#12141a";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }
  function drawFrame(s, im, f, x, y, size) {
    if (!im.complete || !im.naturalWidth) return;
    var sx = (f % s.cols) * s.cell, sy = Math.floor(f / s.cols) * s.cell;
    ctx.drawImage(im, sx, sy, s.cell, s.cell, Math.round(x - size / 2), Math.round(y - size / 2), size, size);
  }
  function draw() {
    var s = sheet(), im = image(s), size = drawSize(s);
    paintBackground();
    ctx.globalCompositeOperation = blendIn.value === "additive" ? "lighter" : "source-over";
    ctx.imageSmoothingEnabled = true;
    var f = Math.floor(state.frame);
    if (f < s.frames) drawFrame(s, im, f, canvas.width / 2, canvas.height / 2, size);
    for (var k = 0; k < state.spawned.length; k++) {
      var sp = state.spawned[k];
      drawFrame(sp.s, image(sp.s), Math.floor(sp.frame), sp.x, sp.y, drawSize(sp.s));
    }
    ctx.globalCompositeOperation = "source-over";
    var shown = Math.min(f, s.frames - 1);
    frameIn.value = shown;
    frameOut.textContent = "Frame " + (shown + 1) + " of " + s.frames;
    cursor.style.left = (shown % s.cols) / s.cols * 100 + "%";
    cursor.style.top = Math.floor(shown / s.cols) / s.rows * 100 + "%";
  }
  function tick(now) {
    var dt = Math.min(0.1, (now - state.last) / 1000 || 0);
    state.last = now;
    var fps = Number(fpsIn.value), s = sheet();
    if (state.playing) {
      state.frame += dt * fps;
      if (state.frame >= s.frames) {
        if (loopIn.checked) state.frame = state.frame % s.frames;
        else { state.frame = s.frames - 1; state.playing = false; updatePlayButton(true); }
      }
      state.dirty = true;
    }
    if (state.spawned.length) {
      for (var k = state.spawned.length - 1; k >= 0; k--) {
        state.spawned[k].frame += dt * fps;
        if (state.spawned[k].frame >= state.spawned[k].s.frames) state.spawned.splice(k, 1);
      }
      state.dirty = true;
    }
    if (state.dirty) { state.dirty = false; draw(); }
    window.requestAnimationFrame(tick);
  }
  function updatePlayButton(ended) {
    playBtn.textContent = state.playing ? "Pause" : (ended ? "Replay" : "Play");
    playBtn.setAttribute("aria-pressed", state.playing ? "true" : "false");
  }
  function describe() {
    var s = sheet();
    info.name.textContent = s.name + " (" + s.category + ")";
    info.grid.textContent = s.cols + " columns x " + s.rows + " rows of " + s.cell + " x " + s.cell + " px cells (sheet " + s.cols * s.cell + " x " + s.rows * s.cell + " px)";
    info.frames.textContent = s.frames + " frames, drawn for " + s.fps + " fps = " + (s.frames / s.fps).toFixed(2) + " s";
    info.flags.textContent = (s.loop ? "seamless loop" : "plays once") + "; " + (s.additive ? "marked additive (best on dark backgrounds)" : "normal blending");
    info.file.textContent = "Sheets/" + s.category + "/" + s.name + ".png";
    code.textContent =
      "// " + s.name + ": frame i (0 to " + (s.frames - 1) + "), left to right, top to bottom\n" +
      "const cell = " + s.cell + ", cols = " + s.cols + ", frames = " + s.frames + ", fps = " + s.fps + ";\n" +
      "const sx = (i % cols) * cell;\n" +
      "const sy = Math.floor(i / cols) * cell;\n" +
      "ctx.drawImage(sheet, sx, sy, cell, cell, x, y, cell, cell);";
  }
  function select(i, announce) {
    state.i = i; state.frame = 0; state.playing = !reduceMotion || announce; state.dirty = true;
    var s = sheet();
    frameIn.max = s.frames - 1;
    fpsIn.value = s.fps; fpsOut.textContent = s.fps + " fps";
    blendIn.value = s.additive ? "additive" : "normal";
    sheetImg.src = BASE + s.name + ".png";
    sheetImg.width = s.cols * s.cell; sheetImg.height = s.rows * s.cell;
    sheetImg.alt = "The whole " + s.name + " sprite sheet: " + s.frames + " frames in a " + s.cols + " by " + s.rows + " grid";
    cursor.style.width = 100 / s.cols + "%"; cursor.style.height = 100 / s.rows + "%";
    picks.forEach(function (b, k) { b.setAttribute("aria-pressed", k === i ? "true" : "false"); });
    describe(); updatePlayButton(false);
    state.dirty = false; draw();                                   // show frame 1 and its read-out at once
    if (announce) status.textContent = "Playing " + s.name + ".";
  }

  var reduceMotion = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);

  picks.forEach(function (b, k) { b.addEventListener("click", function () { select(k, true); }); });
  playBtn.addEventListener("click", function () {
    var s = sheet();
    if (!state.playing && Math.floor(state.frame) >= s.frames - 1) state.frame = 0;
    state.playing = !state.playing; updatePlayButton(false);
  });
  restartBtn.addEventListener("click", function () { state.frame = 0; state.playing = true; updatePlayButton(false); });
  frameIn.addEventListener("input", function () { state.playing = false; state.frame = Number(frameIn.value); state.dirty = true; updatePlayButton(false); });
  fpsIn.addEventListener("input", function () { fpsOut.textContent = fpsIn.value + " fps"; });
  [loopIn, blendIn, scaleIn, colorIn].forEach(function (el) {
    el.addEventListener("input", function () { state.dirty = true; });
    el.addEventListener("change", function () { state.dirty = true; });
  });
  colorIn.addEventListener("input", function () {
    var r = document.querySelector('input[name="vx-bg"][value="custom"]');
    if (r) r.checked = true;
  });
  Array.prototype.forEach.call(document.querySelectorAll('input[name="vx-bg"]'), function (r) {
    r.addEventListener("change", function () { state.dirty = true; });
  });
  function spawnAt(clientX, clientY) {
    var r = canvas.getBoundingClientRect();
    if (state.spawned.length > 40) state.spawned.shift();
    state.spawned.push({ s: sheet(), frame: 0, x: (clientX - r.left) * state.dpr, y: (clientY - r.top) * state.dpr });
  }
  stage.addEventListener("pointerdown", function (e) { spawnAt(e.clientX, e.clientY); });
  stage.addEventListener("keydown", function (e) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      var r = canvas.getBoundingClientRect();
      spawnAt(r.left + r.width * (0.2 + 0.6 * Math.random()), r.top + r.height * (0.2 + 0.6 * Math.random()));
    }
  });
  document.addEventListener("keydown", function (e) {
    var t = e.target.tagName;
    if (t === "INPUT" || t === "SELECT" || t === "TEXTAREA" || t === "BUTTON" || e.target === stage) return;
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.key === "k" || e.key === "K") { playBtn.click(); }
    else if (e.key === "ArrowRight") { select((state.i + 1) % SHEETS.length, true); }
    else if (e.key === "ArrowLeft") { select((state.i + SHEETS.length - 1) % SHEETS.length, true); }
  });
  window.addEventListener("resize", resize);
  if (window.ResizeObserver) new ResizeObserver(resize).observe(stage);

  SHEETS.forEach(image);
  resize();
  select(0, false);
  window.requestAnimationFrame(function (t) { state.last = t; tick(t); });
})();
