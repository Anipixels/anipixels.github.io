// Browser test for the Anipixels site. Drives headless Edge over the Chrome DevTools Protocol
// using only Node built-ins (Node 22+: global WebSocket and fetch). No npm packages.
//
//   node _dev/test.mjs [screenshot-dir]
//
// Every page is opened four times: from file:// and from a local static server on 127.0.0.1 (which stands
// in for the domain root), at 375 px and 1280 px wide. See TESTING.md for what is checked.
import { spawn } from "node:child_process";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const SITE = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SHOTS = path.resolve(process.argv[2] || path.join(os.tmpdir(), "anipixels-site-shots"));
const EDGE = process.env.EDGE || "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const HTTP_PORT = 8765, CDP_PORT = 9377;
const HTTP = `http://127.0.0.1:${HTTP_PORT}/`;
const FILE = pathToFileURL(SITE).href + "/";
const PACKS = ["crisp-ui", "crisp-puzzle", "crisp-jingles", "crisp-cards", "crisp-cozy", "crisp-juice", "crisp-kit", "crisp-quest"];
const TOOLS = ["ui-sound-board", "ui-kit-preview", "vfx-player"];
const PAGES = ["index.html", ...PACKS.map(p => `packs/${p}/index.html`), ...TOOLS.map(t => `tools/${t}/index.html`)];
const SHOT_PAGES = new Set(["index.html", "packs/crisp-quest/index.html", ...TOOLS.map(t => `tools/${t}/index.html`)]);
const ALLOWED_OUT = new Set([
  ...PACKS.flatMap(p => [`https://anipixels.itch.io/${p}`, `https://anipixels.itch.io/${p}-free`]),
  "https://itch.io/s/203391/crisp-everything-bundle",
  ...["tune-trail", "chime-gems", "chime-blocks", "chime-sort", "chime-tiles", "chime-drop", "chime-connect"].map(g => `https://anipixels.itch.io/${g}`),
]);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const failures = [];
const fail = (where, what) => { failures.push(`${where}: ${what}`); console.log(`  FAIL ${where}: ${what}`); };

// ---------------------------------------------------------------- CDP plumbing
let ws, nextId = 1;
const pending = new Map(), listeners = new Map();
function send(method, params = {}, sessionId) {
  const id = nextId++;
  ws.send(JSON.stringify({ id, method, params, sessionId }));
  return new Promise((resolve, reject) => pending.set(id, { resolve, reject, method }));
}
function onEvent(sessionId, fn) { listeners.set(sessionId, fn); }
async function connect() {
  let info;
  for (let i = 0; i < 100; i++) {
    try { info = await (await fetch(`http://127.0.0.1:${CDP_PORT}/json/version`)).json(); break; } catch { await sleep(200); }
  }
  if (!info) throw new Error("Edge did not open its DevTools port");
  ws = new WebSocket(info.webSocketDebuggerUrl);
  await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (m.id) {
      const p = pending.get(m.id); pending.delete(m.id);
      if (m.error) p.reject(new Error(`${p.method}: ${m.error.message}`)); else p.resolve(m.result);
    } else if (m.sessionId && listeners.has(m.sessionId)) listeners.get(m.sessionId)(m.method, m.params);
  };
  return info;
}

async function openPage(url, width, height = 800) {
  const { targetId } = await send("Target.createTarget", { url: "about:blank" });
  const { sessionId } = await send("Target.attachToTarget", { targetId, flatten: true });
  const log = { console: [], requests: [], failed: [], bad: [], loaded: false };
  onEvent(sessionId, (method, p) => {
    if (method === "Runtime.consoleAPICalled" && (p.type === "error" || p.type === "warning" || p.type === "assert"))
      log.console.push(`${p.type}: ${p.args.map(a => a.value ?? a.description ?? "").join(" ")}`);
    else if (method === "Runtime.exceptionThrown") log.console.push(`exception: ${p.exceptionDetails.exception?.description || p.exceptionDetails.text}`);
    else if (method === "Log.entryAdded" && (p.entry.level === "error" || p.entry.level === "warning")) log.console.push(`log ${p.entry.level}: ${p.entry.text} ${p.entry.url || ""}`);
    else if (method === "Network.requestWillBeSent") log.requests.push(p.request.url);
    else if (method === "Network.loadingFailed" && !p.canceled) log.failed.push(`${p.errorText} (${p.type})`);
    else if (method === "Network.responseReceived" && p.response.status >= 400) log.bad.push(`${p.response.status} ${p.response.url}`);
    else if (method === "Page.loadEventFired") log.loaded = true;
  });
  const S = (m, p) => send(m, p, sessionId);
  await S("Page.enable"); await S("Runtime.enable"); await S("Network.enable"); await S("Log.enable");
  await S("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: width < 600 });
  await S("Page.navigate", { url });
  for (let i = 0; i < 100 && !log.loaded; i++) await sleep(100);
  if (!log.loaded) log.console.push("load event never fired");
  const ev = async (expression) => {
    const r = await S("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true, userGesture: true });
    if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
    return r.result.value;
  };
  const close = () => send("Target.closeTarget", { targetId });
  return { S, ev, log, close, sessionId };
}

async function screenshot(pg, file, width) {
  const m = await pg.S("Page.getLayoutMetrics");
  const h = Math.ceil(m.cssContentSize.height);
  const r = await pg.S("Page.captureScreenshot", { format: "png", captureBeyondViewport: true, clip: { x: 0, y: 0, width, height: h, scale: 1 } });
  fs.writeFileSync(file, Buffer.from(r.data, "base64"));
  return h;
}

// ---------------------------------------------------------------- per-page checks
const allLinks = new Map();   // href -> first page seen on
async function checkPage(rel, base, mode, width) {
  const where = `${mode} ${width}px ${rel}`;
  const pg = await openPage(base + rel, width);
  // Load every lazy image so a missing one cannot hide below the fold.
  const brokenImgs = await pg.ev(`Promise.all([...document.images].map(i => { i.loading = "eager"; return i.decode().then(() => null, () => i.currentSrc || i.src); })).then(a => a.filter(Boolean))`);
  await sleep(400);
  const info = await pg.ev(`({
    title: document.title,
    desc: document.querySelector('meta[name="description"]')?.content || "",
    canonical: document.querySelector('link[rel="canonical"]')?.href || "",
    ogImage: document.querySelector('meta[property="og:image"]')?.content || "",
    h1: document.querySelectorAll("h1").length,
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    wide: [...document.querySelectorAll("body *")].filter(el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.right > document.documentElement.clientWidth + 1 && !el.closest("pre, [style*='overflow-x'], .kp-stage, .vx-sheet, .sr-only, .skip"); }).slice(0, 5).map(el => el.tagName + "." + el.className),
    links: [...document.querySelectorAll("a[href]")].map(a => a.href),
    ld: [...document.querySelectorAll('script[type="application/ld+json"]')].map(s => { try { JSON.parse(s.textContent); return "ok"; } catch (e) { return String(e); } }),
    noAlt: [...document.images].filter(i => !i.hasAttribute("alt")).length,
    unlabeled: [...document.querySelectorAll("input, select, button")].filter(el => !(el.labels && el.labels.length) && !el.getAttribute("aria-label") && !el.textContent.trim()).map(el => el.outerHTML.slice(0, 90)),
  })`);
  if (brokenImgs.length) fail(where, `images failed to load: ${brokenImgs.join(", ")}`);
  if (pg.log.console.length) fail(where, `console: ${pg.log.console.join(" | ")}`);
  if (pg.log.failed.length) fail(where, `failed requests: ${pg.log.failed.join(" | ")}`);
  if (pg.log.bad.length) fail(where, `HTTP errors: ${pg.log.bad.join(" | ")}`);
  const external = pg.log.requests.filter(u => !u.startsWith(base) && !/^(data|blob|about):/.test(u));
  if (external.length) fail(where, `requests outside the site: ${[...new Set(external)].join(", ")}`);
  if (info.overflow > 0) fail(where, `page scrolls sideways by ${info.overflow}px`);
  if (info.wide.length) fail(where, `elements wider than the viewport: ${info.wide.join(", ")}`);
  if (info.h1 !== 1) fail(where, `${info.h1} h1 elements`);
  if (info.noAlt) fail(where, `${info.noAlt} images without an alt attribute`);
  if (info.unlabeled.length) fail(where, `form controls without a label: ${info.unlabeled.join(" ; ")}`);
  if (info.ld.some(x => x !== "ok")) fail(where, `JSON-LD does not parse: ${info.ld.join(", ")}`);
  for (const l of info.links) if (!allLinks.has(l)) allLinks.set(l, where);
  return { pg, info, requests: pg.log.requests.length };
}

async function click(pg, selector) {   // a real mouse click through the input pipeline
  const r = await pg.ev(`(() => { const el = document.querySelector(${JSON.stringify(selector)}); el.scrollIntoView({ block: "center", behavior: "instant" }); const b = el.getBoundingClientRect(); return { x: b.left + b.width / 2, y: b.top + b.height / 2 }; })()`);
  await pg.S("Input.dispatchMouseEvent", { type: "mousePressed", x: r.x, y: r.y, button: "left", clickCount: 1 });
  await pg.S("Input.dispatchMouseEvent", { type: "mouseReleased", x: r.x, y: r.y, button: "left", clickCount: 1 });
}
async function key(pg, k, code, vk, text) {   // text is only passed for Enter, which activates a button on keypress
  const base = { key: k, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk };
  await pg.S("Input.dispatchKeyEvent", text ? { type: "keyDown", text, ...base } : { type: "rawKeyDown", ...base });
  await pg.S("Input.dispatchKeyEvent", { type: "keyUp", ...base });
}

// ---------------------------------------------------------------- tool tests
async function testSoundBoard(pg, mode, where) {
  const out = {};
  // 1. every sampler sound, in both formats, loads in an <audio> element and reports a duration
  out.audio = await pg.ev(`(async () => {
    const res = { ogg: 0, mp3: 0, bad: [], shortest: 99, longest: 0 };
    for (const b of document.querySelectorAll(".sb-play")) for (const ext of ["ogg", "mp3"]) {
      const src = b.dataset.src + "." + ext;
      const d = await new Promise(r => { const a = new Audio(); a.preload = "auto"; a.onloadedmetadata = () => r(a.duration); a.onerror = () => r(-1); a.src = src; setTimeout(() => r(-2), 8000); });
      if (d > 0 && isFinite(d)) { res[ext]++; if (ext === "ogg") { res.shortest = Math.min(res.shortest, d); res.longest = Math.max(res.longest, d); } } else res.bad.push(src + " -> " + d);
    }
    return res; })()`);
  if (out.audio.ogg !== 89 || out.audio.mp3 !== 89 || out.audio.bad.length) fail(where, `audio elements: ${JSON.stringify(out.audio)}`);
  // 2. full decode to PCM with Web Audio (needs fetch, so http only)
  if (mode === "http") {
    out.decode = await pg.ev(`(async () => {
      const ctx = new OfflineAudioContext(2, 44100, 44100); const res = { ogg: 0, mp3: 0, bad: [], seconds: 0 };
      for (const b of document.querySelectorAll(".sb-play")) for (const ext of ["ogg", "mp3"]) {
        try { const buf = await ctx.decodeAudioData(await (await fetch(b.dataset.src + "." + ext)).arrayBuffer());
          let peak = 0; const ch = buf.getChannelData(0); for (let i = 0; i < ch.length; i += 7) peak = Math.max(peak, Math.abs(ch[i]));
          if (buf.length > 0 && peak > 0.01) { res[ext]++; if (ext === "ogg") res.seconds += buf.duration; } else res.bad.push(b.dataset.name + "." + ext + " silent");
        } catch (e) { res.bad.push(b.dataset.name + "." + ext + " " + e); }
      }
      res.seconds = Math.round(res.seconds * 10) / 10; return res; })()`);
    if (out.decode.ogg !== 89 || out.decode.mp3 !== 89 || out.decode.bad.length) fail(where, `decodeAudioData: ${JSON.stringify(out.decode)}`);
  }
  // 3. a real click plays a sound
  await click(pg, '.sb-play[data-name="level_up"]');
  let playing = false;
  for (let i = 0; i < 30 && !playing; i++) { await sleep(100); playing = await pg.ev(`!!document.querySelector(".sb-item.is-playing")`); }
  out.clickPlays = playing; out.status = await pg.ev(`document.getElementById("sb-status").textContent`);
  if (!playing) fail(where, `clicking a sound did not start playback (status: ${out.status})`);
  await pg.ev(`document.getElementById("sb-stop").click()`);
  // 4. search and pack filter
  out.search = await pg.ev(`(() => { const s = document.getElementById("sb-search"); const vis = () => document.querySelectorAll(".sb-item:not([hidden])").length;
    const r = { all: vis() }; s.value = "coin"; s.dispatchEvent(new Event("input", { bubbles: true })); r.coin = vis(); r.coinNames = [...document.querySelectorAll(".sb-item:not([hidden]) .sb-name")].map(n => n.textContent);
    r.packsShown = document.querySelectorAll(".sb-pack:not([hidden])").length; s.value = "zzzz"; s.dispatchEvent(new Event("input", { bubbles: true })); r.none = vis(); r.emptyMsg = !document.getElementById("sb-empty").hidden;
    s.value = ""; s.dispatchEvent(new Event("input", { bubbles: true }));
    const radio = document.querySelector('input[name="sb-pack"][value="crisp-jingles"]'); radio.checked = true; radio.dispatchEvent(new Event("change", { bubbles: true })); r.jingles = vis();
    const all = document.querySelector('input[name="sb-pack"][value="all"]'); all.checked = true; all.dispatchEvent(new Event("change", { bubbles: true })); r.back = vis(); r.count = document.getElementById("sb-count").textContent; return r; })()`);
  if (out.search.all !== 89 || out.search.coin < 1 || out.search.coin > 20 || out.search.none !== 0 || !out.search.emptyMsg || out.search.jingles !== 9 || out.search.back !== 89) fail(where, `search/filter: ${JSON.stringify(out.search)}`);
  // 5. keyboard: arrows move, Enter plays, "/" focuses search, C copies
  await pg.ev(`document.querySelector(".sb-play").focus()`);
  await key(pg, "ArrowRight", "ArrowRight", 39);
  const k1 = await pg.ev(`document.activeElement.dataset.name`);
  await key(pg, "ArrowDown", "ArrowDown", 40);
  const k2 = await pg.ev(`document.activeElement.dataset.name`);
  await key(pg, "Enter", "Enter", 13, String.fromCharCode(13));
  await sleep(300);
  const k3 = await pg.ev(`document.getElementById("sb-status").textContent`);
  await key(pg, "c", "KeyC", 67);
  await sleep(300);
  const k4 = await pg.ev(`document.getElementById("sb-status").textContent`);
  await key(pg, "/", "Slash", 191);
  const k5 = await pg.ev(`document.activeElement.id`);
  out.keyboard = { afterRight: k1, afterDown: k2, afterEnter: k3, afterC: k4, afterSlash: k5 };
  const order = await pg.ev(`[...document.querySelectorAll(".sb-play")].map(b => b.dataset.name)`);
  if (k1 !== order[1] || !k2 || k2 === k1 || !k3.startsWith("Playing " + k2) || k5 !== "sb-search") fail(where, `keyboard: ${JSON.stringify(out.keyboard)}`);
  if (!k4.startsWith("Copied " + k2 + ".ogg")) fail(where, `copy file name: status was "${k4}"`);
  // 6. volume
  out.volume = await pg.ev(`(() => { const v = document.getElementById("sb-vol"); v.value = 35; v.dispatchEvent(new Event("input", { bubbles: true })); return document.getElementById("sb-vol-out").textContent; })()`);
  if (out.volume !== "35%") fail(where, `volume readout ${out.volume}`);
  return out;
}

async function testKitPreview(pg, mode, where) {
  const out = await pg.ev(`(async () => {
    const res = { pieces: 0, sliced: 0, fixed: 0, bad: [] };
    const box = document.getElementById("kp-box"), img = document.getElementById("kp-img");
    const probe = document.createElement("div"); document.body.appendChild(probe);
    for (const b of document.querySelectorAll(".kp-piece")) {
      b.click(); res.pieces++;
      const p = window.KIT_DATA[b.dataset.kit].pieces[+b.dataset.i], cs = getComputedStyle(box), r = box.getBoundingClientRect();
      const src = window.KIT_DATA[b.dataset.kit].base + "2x/" + p.g + "/" + p.n + ".png";
      const nat = await new Promise(ok => { const im = new Image(); im.onload = () => ok([im.naturalWidth, im.naturalHeight]); im.onerror = () => ok([0, 0]); im.src = src; });
      if (nat[0] !== p.w * 2 || nat[1] !== p.h * 2) res.bad.push(p.n + " png is " + nat + ", sheets.json says " + [p.w * 2, p.h * 2]);
      if (p.s) {
        res.sliced++;
        if (!cs.borderImageSource.includes(p.n + ".png")) res.bad.push(p.n + " border-image-source " + cs.borderImageSource);
        probe.style.borderImageSlice = [p.s[1] * 2, p.s[2] * 2, p.s[3] * 2, p.s[0] * 2].join(" ") + " fill";   // top right bottom left, from sheets.json
        const want = getComputedStyle(probe).borderImageSlice;
        if (cs.borderImageSlice !== want) res.bad.push(p.n + " slice " + cs.borderImageSlice + " want " + want);
        const bw = [cs.borderTopWidth, cs.borderRightWidth, cs.borderBottomWidth, cs.borderLeftWidth].map(parseFloat).join(" ");
        if (bw !== [p.s[1] * 2, p.s[2] * 2, p.s[3] * 2, p.s[0] * 2].join(" ")) res.bad.push(p.n + " border widths " + bw);
        if (Math.abs(r.width - +document.getElementById("kp-w").value * 2) > 1) res.bad.push(p.n + " width " + r.width);
        if (getComputedStyle(img).display !== "none") res.bad.push(p.n + ": the fixed-size image is still visible on a 9-slice piece");
        const lab = document.getElementById("kp-label"), isBtn = p.n.startsWith("button");
        if ((getComputedStyle(lab).display !== "none") !== isBtn) res.bad.push(p.n + ": label visibility wrong");
      } else {
        res.fixed++;
        if (img.hidden || !img.src.includes(p.n + ".png") || Math.abs(img.getBoundingClientRect().width - p.w * 2) > 1) res.bad.push(p.n + " fixed image not shown at 2x");
        if (getComputedStyle(document.getElementById("kp-label")).display !== "none" || getComputedStyle(document.getElementById("kp-handle")).display !== "none") res.bad.push(p.n + ": label or handle visible on a fixed piece");
      }
    }
    // resize the first Crisp Kit button with the sliders and the keyboard handle
    document.querySelector('.kp-piece[data-kit="crisp-kit"][data-i="0"]').click();
    const w = document.getElementById("kp-w"), h = document.getElementById("kp-h");
    const before = box.getBoundingClientRect();
    w.value = Math.min(+w.max, +w.value - 40 > +w.min ? +w.value - 40 : +w.value + 20); w.dispatchEvent(new Event("input", { bubbles: true }));
    h.value = +h.value + 30; h.dispatchEvent(new Event("input", { bubbles: true }));
    const after = box.getBoundingClientRect();
    res.resize = { before: [before.width, before.height], after: [after.width, after.height], sliders: [+w.value, +h.value] };
    if (after.width !== +w.value * 2 || after.height !== +h.value * 2 || after.height === before.height) res.bad.push("slider resize " + JSON.stringify(res.resize));
    res.label = document.getElementById("kp-label").hidden ? null : document.getElementById("kp-label").textContent;
    res.css = document.getElementById("kp-css").textContent.includes("border-image: url(\\"button_medium_normal.png\\") 16 17 18 17 fill stretch");
    if (!res.css) res.bad.push("CSS snippet: " + document.getElementById("kp-css").textContent);
    const light = document.querySelector('input[name="kp-bg"][value="light"]'); light.checked = true; light.dispatchEvent(new Event("change", { bubbles: true }));
    res.lightBg = getComputedStyle(document.getElementById("kp-stage")).backgroundColor;
    if (res.lightBg !== "rgb(238, 240, 245)") res.bad.push("light background " + res.lightBg);
    const z3 = document.querySelector('input[name="kp-zoom"][value="3"]'); z3.checked = true; z3.dispatchEvent(new Event("change", { bubbles: true }));
    res.zoom3 = box.getBoundingClientRect().width / +w.value;
    const quest = document.querySelector('input[name="kp-kit"][value="crisp-quest"]'); quest.checked = true; quest.dispatchEvent(new Event("change", { bubbles: true }));
    res.questShown = !document.querySelector('.kp-kit[data-kit="crisp-quest"]').hidden && document.querySelector('.kp-kit[data-kit="crisp-kit"]').hidden;
    res.questSource = getComputedStyle(box).borderImageSource.split("/").slice(-3).join("/");
    if (!res.questShown || !res.questSource.includes("wood/button_medium_normal.png")) res.bad.push("kit switch");
    return res; })()`);
  if (out.pieces !== 109 || out.bad.length || out.zoom3 !== 3) fail(where, `kit preview: ${JSON.stringify(out)}`);
  // drag the handle with real mouse events
  const start = await pg.ev(`(() => { const hd = document.getElementById("kp-handle"); hd.scrollIntoView({ block: "center", behavior: "instant" }); const b = hd.getBoundingClientRect(), r = document.getElementById("kp-box").getBoundingClientRect(); return { x: b.left + b.width / 2, y: b.top + b.height / 2, w: r.width, h: r.height }; })()`);
  await pg.S("Input.dispatchMouseEvent", { type: "mousePressed", x: start.x, y: start.y, button: "left", clickCount: 1 });
  await pg.S("Input.dispatchMouseEvent", { type: "mouseMoved", x: start.x - 30, y: start.y + 24, button: "left", buttons: 1 });
  await pg.S("Input.dispatchMouseEvent", { type: "mouseReleased", x: start.x - 30, y: start.y + 24, button: "left", clickCount: 1 });
  const end = await pg.ev(`(() => { const r = document.getElementById("kp-box").getBoundingClientRect(); return { w: r.width, h: r.height }; })()`);
  out.drag = { from: [start.w, start.h], to: [end.w, end.h] };
  if (!(end.w < start.w && end.h > start.h)) fail(where, `drag handle did not resize: ${JSON.stringify(out.drag)}`);
  return out;
}

async function testVfxPlayer(pg, mode, where) {
  const out = { sheets: [] };
  const n = await pg.ev(`document.querySelectorAll(".vx-pick").length`);
  for (let i = 0; i < n; i++) {
    await pg.ev(`document.querySelectorAll(".vx-pick")[${i}].click()`);
    await sleep(80);
    const a = await pg.ev(`document.getElementById("vx-frame-out").textContent`);
    await sleep(200);
    const r = await pg.ev(`(() => {
      const c = document.getElementById("vx-canvas"), s = window.VFX_DATA.sheets[${i}], res = { name: s.name, frameText: document.getElementById("vx-frame-out").textContent, canvas: [c.width, c.height] };
      res.sheetPx = [document.getElementById("vx-sheet-img").naturalWidth, document.getElementById("vx-sheet-img").naturalHeight]; res.sheetWant = [s.cols * s.cell, s.rows * s.cell];
      return res; })()`);
    r.frameBefore = a;
    out.sheets.push(r);
    if (r.sheetPx[0] !== r.sheetWant[0] || r.sheetPx[1] !== r.sheetWant[1]) fail(where, `${r.name}: sheet is ${r.sheetPx}, sheets.json says ${r.sheetWant}`);
    const total = await pg.ev(`window.VFX_DATA.sheets[${i}].frames`);
    if (r.frameText === a || !a.endsWith(" of " + total) || !r.frameText.endsWith(" of " + total)) fail(where, `${r.name}: frame read-out did not advance (${a} -> ${r.frameText})`);
    if (mode === "http") {
      // step through every frame and count canvas pixels that differ from the dark background
      const px = await pg.ev(`(async () => {
        const c = document.getElementById("vx-canvas"), s = window.VFX_DATA.sheets[${i}], f = document.getElementById("vx-frame");
        const t = document.createElement("canvas"); t.width = c.width; t.height = c.height; const g = t.getContext("2d", { willReadFrequently: true });
        const counts = [];
        for (let k = 0; k < s.frames; k++) {
          f.value = k; f.dispatchEvent(new Event("input", { bubbles: true }));
          await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
          g.drawImage(c, 0, 0); const d = g.getImageData(0, 0, c.width, c.height).data; let n = 0;
          for (let j = 0; j < d.length; j += 4) if (Math.abs(d[j] - 18) + Math.abs(d[j + 1] - 20) + Math.abs(d[j + 2] - 26) > 24) n++;
          counts.push(n);
        }
        return { framesWithPixels: counts.filter(x => x > 20).length, frames: s.frames, maxPixels: Math.max(...counts), distinct: new Set(counts).size };
      })()`);
      Object.assign(r, px);
      if (px.framesWithPixels < px.frames * 0.6 || px.distinct < px.frames * 0.5) fail(where, `${r.name}: canvas frames look empty or identical: ${JSON.stringify(px)}`);
    }
  }
  // controls: loop off stops at the end, restart, speed, background, blend, click-to-spawn
  out.controls = await pg.ev(`(async () => {
    const wait = ms => new Promise(r => setTimeout(r, ms)), $ = id => document.getElementById(id), res = {};
    document.querySelectorAll(".vx-pick")[1].click();          // match_pop_pink: 16 frames
    $("vx-loop").checked = false; $("vx-loop").dispatchEvent(new Event("change", { bubbles: true }));
    $("vx-fps").value = 60; $("vx-fps").dispatchEvent(new Event("input", { bubbles: true }));
    await wait(900);
    res.afterOnce = [$("vx-frame-out").textContent, $("vx-play").textContent];
    $("vx-restart").click(); await wait(60); res.afterRestart = $("vx-play").textContent;
    $("vx-loop").checked = true;
    const light = document.querySelector('input[name="vx-bg"][value="light"]'); light.checked = true; light.dispatchEvent(new Event("change", { bubbles: true }));
    await wait(120);
    try { const c = $("vx-canvas"), t = document.createElement("canvas"); t.width = t.height = 4; const g = t.getContext("2d", { willReadFrequently: true }); g.drawImage(c, 0, 0); res.lightCorner = [...g.getImageData(2, 2, 1, 1).data]; } catch (e) { res.lightCorner = "blocked on file://"; }
    document.querySelectorAll(".vx-pick")[7].click(); res.sparkleBlend = $("vx-blend").value; res.sparkleFps = $("vx-fps-out").textContent;
    return res; })()`);
  if (out.controls.afterOnce[1] !== "Replay" || out.controls.afterOnce[0] !== "Frame 16 of 16" || out.controls.afterRestart !== "Pause" || out.controls.sparkleBlend !== "additive")
    fail(where, `player controls: ${JSON.stringify(out.controls)}`);
  if (mode === "http" && JSON.stringify(out.controls.lightCorner) !== "[238,240,245,255]") fail(where, `light background pixel ${out.controls.lightCorner}`);
  if (mode === "http") {
    await pg.ev(`(() => { const d = document.querySelector('input[name="vx-bg"][value="dark"]'); d.checked = true; d.dispatchEvent(new Event("change", { bubbles: true })); document.querySelectorAll(".vx-pick")[3].click(); document.getElementById("vx-play").click(); document.getElementById("vx-stage").scrollIntoView({ block: "center", behavior: "instant" }); })()`);
    const pos = await pg.ev(`(() => { const b = document.getElementById("vx-canvas").getBoundingClientRect(); return { x: b.left + 70, y: b.top + 70 }; })()`);
    await pg.S("Input.dispatchMouseEvent", { type: "mousePressed", x: pos.x, y: pos.y, button: "left", clickCount: 1 });
    await pg.S("Input.dispatchMouseEvent", { type: "mouseReleased", x: pos.x, y: pos.y, button: "left", clickCount: 1 });
    await sleep(250);
    out.spawn = await pg.ev(`(() => { const c = document.getElementById("vx-canvas"), t = document.createElement("canvas"); t.width = t.height = 140; const g = t.getContext("2d", { willReadFrequently: true }); g.drawImage(c, 0, 0); const d = g.getImageData(0, 0, 140, 140).data; let n = 0; for (let j = 0; j < d.length; j += 4) if (Math.abs(d[j] - 18) + Math.abs(d[j + 1] - 20) + Math.abs(d[j + 2] - 26) > 24) n++; return n; })()`);
    if (out.spawn < 30) fail(where, `click-to-spawn drew ${out.spawn} pixels near the click`);
  }
  return out;
}

// ---------------------------------------------------------------- run
fs.mkdirSync(SHOTS, { recursive: true });
const profile = fs.mkdtempSync(path.join(os.tmpdir(), "anipixels-edge-"));
// A plain static file server for the site folder, standing in for the domain root. (python -m http.server was tried first,
// but it refuses connections when the kit preview asks for its 109 images at once.)
const TYPES = { ".html": "text/html; charset=utf-8", ".css": "text/css", ".js": "text/javascript", ".json": "application/json", ".png": "image/png",
  ".webp": "image/webp", ".svg": "image/svg+xml", ".ico": "image/x-icon", ".ogg": "audio/ogg", ".mp3": "audio/mpeg", ".txt": "text/plain; charset=utf-8", ".xml": "application/xml" };
const server = http.createServer((req, res) => {
  let rel = decodeURIComponent(new URL(req.url, HTTP).pathname);
  if (rel.endsWith("/")) rel += "index.html";
  const file = path.join(SITE, rel);
  if (!file.startsWith(SITE) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404, { "content-type": "text/html" }); res.end(fs.readFileSync(path.join(SITE, "404.html"))); return; }
  const body = fs.readFileSync(file);
  res.writeHead(200, { "content-type": TYPES[path.extname(file)] || "application/octet-stream", "content-length": body.length, "accept-ranges": "bytes" });
  res.end(body);
});
await new Promise(r => server.listen(HTTP_PORT, "127.0.0.1", r));
const edge = spawn(EDGE, ["--headless=new", `--remote-debugging-port=${CDP_PORT}`, `--user-data-dir=${profile}`, "--no-first-run", "--disable-gpu",
  "--hide-scrollbars", "--autoplay-policy=no-user-gesture-required", "about:blank"], { stdio: "ignore" });
let exitCode = 1;
try {
  const info = await connect();
  console.log(`browser: ${info.Browser}`);
  await send("Browser.grantPermissions", { permissions: ["clipboardReadWrite", "clipboardSanitizedWrite"] }).catch(e => console.log("  (clipboard permission not granted: " + e.message + ")"));
  for (let i = 0; i < 50; i++) { try { if ((await fetch(HTTP + "robots.txt")).ok) break; } catch { await sleep(100); } }
  const toolResults = {};
  let pagesOpened = 0, totalRequests = 0;
  for (const [mode, base] of [["file", FILE], ["http", HTTP]]) {
    for (const width of [375, 1280]) {
      for (const rel of PAGES) {
        const failedBefore = failures.length;
        const { pg, info: meta, requests } = await checkPage(rel, base, mode, width);
        pagesOpened++; totalRequests += requests;
        const where = `${mode} ${width}px ${rel}`;
        if (SHOT_PAGES.has(rel) && mode === "http") {
          const name = rel.replace(/\/index\.html$/, "").replace(/[\/.]/g, "_") + `_${width}.png`;
          const h = await screenshot(pg, path.join(SHOTS, name), width);
          console.log(`  screenshot ${name} ${width}x${h}`);
        }
        const tool = TOOLS.find(t => rel.includes(t));
        if (tool) {
          const fn = { "ui-sound-board": testSoundBoard, "ui-kit-preview": testKitPreview, "vfx-player": testVfxPlayer }[tool];
          try { toolResults[`${tool} ${mode} ${width}`] = await fn(pg, mode, where); } catch (e) { fail(where, `tool test crashed: ${e.message}`); }
          if (pg.log.console.length) fail(where, `console after using the tool: ${pg.log.console.join(" | ")}`);
          const ext = pg.log.requests.filter(u => !u.startsWith(base) && !/^(data|blob|about):/.test(u));
          if (ext.length) fail(where, `requests outside the site after using the tool: ${[...new Set(ext)].join(", ")}`);
          if (pg.log.failed.length || pg.log.bad.length) fail(where, `failed requests after using the tool: ${[...pg.log.failed, ...pg.log.bad].join(" | ")}`);
          if (mode === "http") {
            const name = `tools_${tool}_${width}_used.png`;
            await pg.ev(`window.scrollTo(0, 0)`);
            await screenshot(pg, path.join(SHOTS, name), width);
          }
        }
        console.log(`${failures.length === failedBefore ? "PASS" : "FAIL"} ${where}  requests=${pg.log.requests.length} links=${meta.links.length} console=${pg.log.console.length} failed=${pg.log.failed.length + pg.log.bad.length} overflow=${meta.overflow}px`);
        totalRequests += pg.log.requests.length - requests;
        await pg.close();
      }
    }
  }
  // clean folder URLs, as GitHub Pages serves them
  for (const rel of ["", "packs/crisp-ui/", "tools/vfx-player/"]) { const { pg } = await checkPage(rel, HTTP, "http", 1280); pagesOpened++; console.log(`PASS? http 1280px /${rel} (folder URL) - failures so far: ${failures.length}`); await pg.close(); }
  // 404 page (root-absolute links, so http only)
  { const { pg, info: meta } = await checkPage("404.html", HTTP, "http", 1280); pagesOpened++; console.log(`PASS? http 1280px 404.html title="${meta.title}" - failures so far: ${failures.length}`); await pg.close(); }

  // links: every internal link must resolve (file + anchor), every external link must be on the allowed list
  let internal = 0, external = 0;
  const outSeen = new Set();
  for (const [href, where] of allLinks) {
    const u = new URL(href);
    if (u.protocol === "https:" || (u.protocol === "http:" && u.host !== `127.0.0.1:${HTTP_PORT}`)) {
      external++; outSeen.add(href);
      if (!ALLOWED_OUT.has(href)) fail(where, `outbound link not on the allowed list: ${href}`);
      continue;
    }
    internal++;
    let file = u.protocol === "file:" ? fileURLToPath(href.split("#")[0]) : path.join(SITE, decodeURIComponent(u.pathname));
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) {
      if (u.protocol === "file:") fail(where, `link to a folder does not work from file://: ${href}`);
      file = path.join(file, "index.html");
    }
    if (!fs.existsSync(file)) { fail(where, `broken link ${href}`); continue; }
    if (u.hash && file.endsWith(".html")) {
      const id = decodeURIComponent(u.hash.slice(1));
      if (!new RegExp(`id="${id}"`).test(fs.readFileSync(file, "utf8"))) fail(where, `missing anchor ${href}`);
    }
  }
  const unusedOut = [...ALLOWED_OUT].filter(x => !outSeen.has(x));
  console.log(`links: ${internal} distinct internal (all resolve: ${!failures.some(f => /broken link|missing anchor|folder/.test(f))}), ${external} distinct outbound, ${outSeen.size} of ${ALLOWED_OUT.size} allowed itch URLs used` + (unusedOut.length ? `, unused: ${unusedOut.join(", ")}` : ""));
  console.log(`pages opened: ${pagesOpened}, requests seen: ${totalRequests}`);
  console.log("TOOL RESULTS " + JSON.stringify(toolResults, null, 1));
  console.log(failures.length ? `\nFAILED: ${failures.length} problem(s)\n` + failures.join("\n") : "\nALL BROWSER CHECKS PASSED");
  exitCode = failures.length ? 1 : 0;
} catch (e) {
  console.log("TEST RUN CRASHED: " + (e.stack || e));
} finally {
  try { ws && ws.close(); } catch {}
  edge.kill(); server.close(); server.closeAllConnections();
  await sleep(500);
  try { fs.rmSync(profile, { recursive: true, force: true }); } catch {}
}
process.exit(exitCode);
