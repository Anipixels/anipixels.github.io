/* Anipixels UI kit preview: live 9-slice preview of the Crisp Kit, Crisp Quest and Crisp Pixel free sampler pieces.
   Plain JS, no dependencies, works from file://. Piece data comes from data.js, which is generated
   from each sampler's sheets.json (sizes, slice borders and content padding are copied unchanged).
   Each kit says which PNG scale it is drawn from (px: 2, or 1 for the pixel-art kit) and whether it is
   pixel art (pixel: true), in which case it is enlarged with image-rendering: pixelated, never smoothed. */
(function () {
  "use strict";
  var DATA = window.KIT_DATA;
  var $ = function (id) { return document.getElementById(id); };
  var stage = $("kp-stage"), box = $("kp-box"), img = $("kp-img"), label = $("kp-label"), handle = $("kp-handle");
  var wIn = $("kp-w"), hIn = $("kp-h"), wOut = $("kp-w-out"), hOut = $("kp-h-out");
  var showLabel = $("kp-showlabel"), labelText = $("kp-labeltext");
  var status = $("kp-status"), cssOut = $("kp-css"), copyBtn = $("kp-copy");
  var info = { name: $("kp-i-name"), size: $("kp-i-size"), slice: $("kp-i-slice"), type: $("kp-i-type"), files: $("kp-i-files"), note: $("kp-i-note") };
  var pieceButtons = Array.prototype.slice.call(document.querySelectorAll(".kp-piece"));
  var kitSections = Array.prototype.slice.call(document.querySelectorAll(".kp-kit"));
  var state = { kit: null, i: 0, w: 0, h: 0, sw: 0, sh: 0, zoom: 2 };

  function radioValue(name) {
    var r = document.querySelector('input[name="' + name + '"]:checked');
    return r ? r.value : null;
  }
  function piece() { return DATA[state.kit].pieces[state.i]; }
  function curKit() { return DATA[state.kit]; }
  function url(p) { return curKit().base + (curKit().px || 2) + "x/" + p.g + "/" + p.n + ".png"; }
  function fixedHeight(p) { return !!p.s && p.s[1] === 0 && p.s[3] === 0; }

  function limits(p) {
    var z = state.zoom;
    var room = Math.max(60, stage.clientWidth - 56);
    if (!p.s) return { wmin: p.w, wmax: p.w, hmin: p.h, hmax: p.h };
    var wmin = Math.max(p.s[0] + p.s[2], 8);
    var wmax = Math.max(wmin, Math.min(520, Math.floor(room / z)));
    var hmin = fixedHeight(p) ? p.h : Math.max(p.s[1] + p.s[3], 8);
    var hmax = fixedHeight(p) ? p.h : Math.max(hmin, Math.floor(300 / z) + 20);
    return { wmin: wmin, wmax: wmax, hmin: hmin, hmax: hmax };
  }

  function render() {
    var p = piece(), z = state.zoom, lim = limits(p), K = curKit().px || 2, pixel = !!curKit().pixel;
    box.style.imageRendering = img.style.imageRendering = pixel ? "pixelated" : "";
    // state.w / state.h hold the size that was asked for; w / h are what fits the stage right now.
    // The asked-for size is kept, so a narrow window only shrinks the piece until there is room again.
    var w = Math.max(lim.wmin, Math.min(lim.wmax, state.w));
    var h = Math.max(lim.hmin, Math.min(lim.hmax, state.h));
    state.sw = w; state.sh = h;
    wIn.min = lim.wmin; wIn.max = lim.wmax; wIn.value = w; wIn.disabled = !p.s;
    hIn.min = lim.hmin; hIn.max = lim.hmax; hIn.value = h; hIn.disabled = !p.s || fixedHeight(p);
    wOut.textContent = w + " px"; hOut.textContent = h + " px";
    handle.hidden = !p.s;

    box.style.width = w * z + "px";
    box.style.height = h * z + "px";
    var isButton = p.n.indexOf("button") === 0 && !!p.s;
    showLabel.disabled = !isButton;
    labelText.disabled = !isButton || !showLabel.checked;
    if (p.s) {
      var s = p.s;                                               // [left, top, right, bottom] in 1x pixels
      img.hidden = true;
      box.style.boxSizing = "border-box";
      box.style.borderWidth = s[1] * z + "px " + s[2] * z + "px " + s[3] * z + "px " + s[0] * z + "px";
      box.style.borderImageSource = 'url("' + url(p) + '")';
      box.style.borderImageSlice = s[1] * K + " " + s[2] * K + " " + s[3] * K + " " + s[0] * K + " fill";
      box.style.borderImageRepeat = "stretch";
      handle.style.right = -(s[2] * z + 12) + "px";             // sit on the outer corner, outside the border
      handle.style.bottom = -(s[3] * z + 12) + "px";
    } else {
      box.style.borderWidth = "0";
      box.style.borderImageSource = "none";
      img.hidden = false;
      img.src = url(p);
      img.width = p.w * z; img.height = p.h * z;
      img.alt = p.n;
    }
    if (isButton && showLabel.checked) {
      var pad = p.pad || p.s, sl = p.s;
      label.hidden = false;
      label.textContent = labelText.value || "Play";
      label.style.position = "absolute";
      label.style.left = (pad[0] - sl[0]) * z + "px";
      label.style.top = (pad[1] - sl[1]) * z + "px";
      label.style.right = (pad[2] - sl[2]) * z + "px";
      label.style.bottom = (pad[3] - sl[3]) * z + "px";
      label.style.display = "flex";
      label.style.alignItems = "center";
      label.style.justifyContent = "center";
      label.style.fontSize = Math.max(pixel ? 7 : 10, Math.min(18, (h - pad[1] - pad[3]) * 0.62)) * z + "px";
      label.style.maxWidth = "none";
    } else {
      label.hidden = true;
    }

    info.name.textContent = p.n + " (" + p.c + ")";
    info.size.textContent = p.w + " x " + p.h + " px at 1x, " + p.w * 2 + " x " + p.h * 2 + " px at 2x";
    if (p.s) {
      info.type.textContent = fixedHeight(p) ? "3-slice: stretches sideways only (fixed height)" : "9-slice: stretches in both directions";
      info.slice.textContent = "left " + p.s[0] + ", top " + p.s[1] + ", right " + p.s[2] + ", bottom " + p.s[3] + " px (1x); double them for the 2x PNG";
    } else {
      info.type.textContent = "Fixed size: no slice borders, use it at its own size";
      info.slice.textContent = "none";
    }
    info.files.textContent = pixel
      ? "PNG/1x/" + p.g + "/" + p.n + ".png, and the same name under PNG/2x, PNG/3x and PNG/4x"
      : "PNG/1x/" + p.g + "/" + p.n + ".png, PNG/2x/" + p.g + "/" + p.n + ".png, SVG/" + p.g + "/" + p.n + ".svg";
    info.note.textContent = p.note || "-";
    if (p.s) {
      cssOut.textContent =
        "/* " + p.n + ".png (1x) drawn at " + w + " x " + h + " px */\n" +
        ".piece {\n" +
        "  box-sizing: border-box;\n" +
        "  width: " + w + "px;\n" +
        "  height: " + h + "px;\n" +
        "  border-style: solid;\n" +
        "  border-width: " + p.s[1] + "px " + p.s[2] + "px " + p.s[3] + "px " + p.s[0] + "px;\n" +
        '  border-image: url("' + p.n + '.png") ' + p.s[1] + " " + p.s[2] + " " + p.s[3] + " " + p.s[0] + " fill stretch;\n" +
        (pixel ? "  image-rendering: pixelated; /* pixel art: scale by whole numbers, no smoothing */\n" : "") +
        "}";
      copyBtn.disabled = false;
    } else {
      cssOut.textContent = "/* " + p.n + ".png is a fixed-size piece: draw it at " + p.w + " x " + p.h + " px. */";
      copyBtn.disabled = true;
    }
  }

  function select(kit, i, resetSize) {
    state.kit = kit; state.i = i;
    var p = piece();
    if (resetSize) {
      state.w = p.s ? Math.max(p.w, Math.min(p.w * 1.5, 240) | 0) : p.w;
      state.h = p.s && !fixedHeight(p) ? p.h : p.h;
      var roomy = curKit().pixel ? [96, 56] : [200, 110];           // pixel-art pieces are drawn several times smaller
      if (p.s && !fixedHeight(p) && p.n.indexOf("button") !== 0 && p.h < roomy[1] + 10) state.h = Math.max(p.h, roomy[1]);
      if (p.s && p.n.indexOf("button") !== 0 && p.w < roomy[0]) state.w = Math.max(p.w, roomy[0]);
      if (p.n.indexOf("slot") !== -1 || p.n.indexOf("portrait") !== -1) { state.w = p.w; state.h = p.h; }
    }
    pieceButtons.forEach(function (b) {
      var on = b.getAttribute("data-kit") === kit && Number(b.getAttribute("data-i")) === i;
      b.setAttribute("aria-pressed", on ? "true" : "false");
    });
    kitSections.forEach(function (sec) { sec.hidden = sec.getAttribute("data-kit") !== kit; });
    render();
    status.textContent = "Showing " + p.n + " from " + DATA[kit].name + ".";
  }

  function setBg() {
    var bg = radioValue("kp-bg") || "dark";
    stage.className = "kp-stage bg-" + bg;
    Array.prototype.forEach.call(document.querySelectorAll(".kp-thumb"), function (t) { t.className = "kp-thumb bg-" + bg; });
  }

  pieceButtons.forEach(function (b) {
    b.addEventListener("click", function () {
      select(b.getAttribute("data-kit"), Number(b.getAttribute("data-i")), true);
      if (stage.getBoundingClientRect().top < 0) stage.scrollIntoView({ block: "start" });
    });
  });
  Array.prototype.forEach.call(document.querySelectorAll('input[name="kp-kit"]'), function (r) {
    r.addEventListener("change", function () { select(r.value, 0, true); });
  });
  Array.prototype.forEach.call(document.querySelectorAll('input[name="kp-zoom"]'), function (r) {
    r.addEventListener("change", function () { state.zoom = Number(r.value); render(); });
  });
  Array.prototype.forEach.call(document.querySelectorAll('input[name="kp-bg"]'), function (r) {
    r.addEventListener("change", setBg);
  });
  wIn.addEventListener("input", function () { state.w = Number(wIn.value); render(); });
  hIn.addEventListener("input", function () { state.h = Number(hIn.value); render(); });
  showLabel.addEventListener("change", render);
  labelText.addEventListener("input", render);
  window.addEventListener("resize", render);
  if (window.ResizeObserver) {
    var lastStageWidth = stage.clientWidth;
    new ResizeObserver(function () {
      if (stage.clientWidth !== lastStageWidth) { lastStageWidth = stage.clientWidth; render(); }
    }).observe(stage);
  }

  // Drag the round handle to resize. The box is centred, so it grows on both sides.
  var drag = null;
  handle.addEventListener("pointerdown", function (e) {
    drag = { x: e.clientX, y: e.clientY, w: state.sw, h: state.sh };
    handle.setPointerCapture(e.pointerId);
    e.preventDefault();
  });
  handle.addEventListener("pointermove", function (e) {
    if (!drag) return;
    state.w = Math.round(drag.w + 2 * (e.clientX - drag.x) / state.zoom);
    state.h = Math.round(drag.h + 2 * (e.clientY - drag.y) / state.zoom);
    render();
  });
  function endDrag() { drag = null; }
  handle.addEventListener("pointerup", endDrag);
  handle.addEventListener("pointercancel", endDrag);
  handle.addEventListener("keydown", function (e) {
    var step = e.shiftKey ? 10 : 2, used = true;
    if (e.key === "ArrowRight") state.w = state.sw + step;
    else if (e.key === "ArrowLeft") state.w = state.sw - step;
    else if (e.key === "ArrowDown") state.h = state.sh + step;
    else if (e.key === "ArrowUp") state.h = state.sh - step;
    else used = false;
    if (used) { e.preventDefault(); render(); }
  });

  copyBtn.addEventListener("click", function () {
    var text = cssOut.textContent;
    var done = function () { status.textContent = "CSS copied."; };
    var fail = function () { status.textContent = "Copy failed. Select the CSS and copy it by hand."; };
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, fail);
    else {
      var t = document.createElement("textarea");
      t.value = text; t.style.position = "fixed"; t.style.opacity = "0";
      document.body.appendChild(t); t.select();
      try { if (document.execCommand("copy")) done(); else fail(); } catch (e) { fail(); }
      document.body.removeChild(t);
    }
  });

  state.zoom = Number(radioValue("kp-zoom") || 2);
  setBg();
  select(radioValue("kp-kit") || Object.keys(DATA)[0], 0, true);
})();
