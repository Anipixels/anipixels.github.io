# Testing notes

How this site was tested on 6 October 2026, with the real commands and their output.
This file is not linked from any page. It is harmless if GitHub Pages serves it.

## Environment

- Windows 11, Microsoft Edge 154.0.4258.53 (headless, `--headless=new`), driven over the Chrome DevTools Protocol
- Node v24.19.0 (built-in `WebSocket` and `fetch`; no npm packages), Python 3.12.10 with Pillow 12.3.0, ffmpeg N-125875

## Commands

Run from the site folder (`C:\Claude Code\AssetPacks\site`):

```
python _dev/build.py                   # regenerate the pages and copy the sampler files
python _dev/check.py                   # static checks, no browser
node _dev/test.mjs <screenshot-folder> # browser checks in headless Edge
```

`_dev/test.mjs` starts Edge itself (`msedge.exe --headless=new --remote-debugging-port=9377 --user-data-dir=<temp>
--disable-gpu --hide-scrollbars --autoplay-policy=no-user-gesture-required`) and a static file server on
`127.0.0.1:8765` that stands in for the domain root.

## 1. Static checks: `python _dev/check.py`

```
1. local references checked: 446 in 13 HTML pages
2. absolute URLs found in site content: 276; distinct outbound: 24, all on the allowed list of 24: True; allowed but unused: none
3. 13 pages: unique titles 13, unique descriptions 13
4. JSON-LD blocks parsed: 12 (Product 8, WebApplication 3, FAQPage 8)
5. sitemap.xml parsed: 12 URLs, all map to pages; robots.txt allows all; llms.txt lists 8 packs
6. samples/: {'txt': 8, 'mp3': 89, 'ogg': 89, 'json': 3, 'png': 117}; every non-MP3 file is byte-identical to a free-sampler file; no archives or WAVs in the site

STATIC CHECKS PASSED
```

What each line means:

1. Every `href`, `src` and inline `url(...)` in every HTML page points at a file that exists, every `#anchor` exists
   in its target page, and no link points at a bare folder (which would not work from `file://`).
2. Every absolute URL in the site's HTML, JS, CSS, TXT, XML, JSON and SVG files is either under
   `https://anipixels.github.io/`, a schema / XML namespace, or one of the 24 allowed itch.io URLs
   (8 paid pack pages, 8 free pack pages, the Crisp Everything Bundle, 7 games). All 24 are used.
3. Titles and meta descriptions are unique; canonicals, `og:url` and `og:image` are checked per page
   (the `og:image` file must exist).
4. Each JSON-LD block is parsed with `json.loads`. Each `Product` must carry the pack's name, a description, the cover
   image, and an offer with the price from `_dev/packs.py`, `priceCurrency` USD and the paid itch.io URL. Each
   `WebApplication` must carry name, URL, category, operating system and a 0 USD offer. Every `FAQPage` question
   and answer must also be visible in the page's HTML.
5. `sitemap.xml` is parsed with `xml.etree.ElementTree` and must list exactly the 12 indexable pages.
6. The content rule: every file under `samples/` is compared by SHA-1 with the files inside the eight
   `*_Free_Sampler.zip` archives and must be byte-identical to one of them. The 89 MP3 fallbacks are the only derived
   files; each must match a sampler sound by name. The site holds no zip, WAV, unitypackage or Godot files.

## 2. Browser checks: `node _dev/test.mjs`

12 pages x 2 ways of loading (`file://` and `http://127.0.0.1:8765/`) x 2 widths (375 px and 1280 px) = 48 page loads,
plus 3 clean folder URLs and `404.html` over http. Result of the final run:

```
browser: Edg/154.0.4258.53
PASS file 375px index.html  requests=12 links=59 console=0 failed=0 overflow=0px
PASS file 375px packs/crisp-ui/index.html  requests=6 links=26 console=0 failed=0 overflow=0px
... (48 lines, all PASS; the three tool pages on each of the four passes:)
PASS file 375px tools/ui-sound-board/index.html  requests=187 links=24 console=0 failed=0 overflow=0px
PASS file 375px tools/ui-kit-preview/index.html  requests=114 links=15 console=0 failed=0 overflow=0px
PASS file 375px tools/vfx-player/index.html  requests=13 links=12 console=0 failed=0 overflow=0px
PASS http 1280px tools/ui-sound-board/index.html  requests=365 links=24 console=0 failed=0 overflow=0px
PASS http 1280px tools/ui-kit-preview/index.html  requests=114 links=15 console=0 failed=0 overflow=0px
PASS http 1280px tools/vfx-player/index.html  requests=13 links=12 console=0 failed=0 overflow=0px
PASS? http 1280px / (folder URL) - failures so far: 0
PASS? http 1280px /packs/crisp-ui/ (folder URL) - failures so far: 0
PASS? http 1280px /tools/vfx-player/ (folder URL) - failures so far: 0
PASS? http 1280px 404.html title="Page not found | Anipixels" - failures so far: 0
links: 130 distinct internal (all resolve: true), 24 distinct outbound, 24 of 24 allowed itch URLs used
pages opened: 52, requests seen: 1878

ALL BROWSER CHECKS PASSED
```

Checked on every page load:

- console: no `console.error` / `console.warn`, no uncaught exception, no browser log entry at warning or error level
- network: no failed request, no HTTP status of 400 or more, and no request to anything outside the site folder
  (`file:///C:/Claude%20Code/AssetPacks/site/` or `http://127.0.0.1:8765/`). 1878 requests were seen in total; all local
- images: every `<img>` is switched to eager loading and decoded, so a broken lazy image below the fold cannot hide
- layout: the page does not scroll sideways (`scrollWidth - clientWidth` is 0 on all 48 loads) and no element sticks
  out past the right edge of the viewport
- one `<h1>` per page, every image has an `alt` attribute, every input / select / button has a label, JSON-LD parses
- links: every `<a href>` is collected; the 130 distinct internal ones resolve to files (and anchors), the 24 distinct
  outbound ones are exactly the 24 allowed itch.io URLs

The harness was also checked against a deliberately broken copy of one page (an external image, a missing image, a
broken link, an itch.io link that is not on the list, a `console.error` and a 2000 px wide box). It reported each of
them and exited with status 1. The page was then regenerated and the run above repeated. (That one deliberate test
is the only time anything on this site asked for an outside address: `https://example.com/x.png`.)

### UI sound board

Results were the same on all four passes unless noted.

- All 89 sounds load in an `<audio>` element and report a duration, in both formats: `ogg: 89, mp3: 89, bad: 0`
  (shortest 0.25 s, longest 5.35 s).
- Over http, all 178 files are fetched and decoded to PCM with `decodeAudioData`, and each has a non-silent peak:
  `ogg: 89, mp3: 89`, 104.6 s of audio in total. (From `file://` the browser does not allow `fetch`, so this step
  runs over http only. The `<audio>` check above runs on both.)
- A real mouse click on `level_up` starts playback: the tile gets its playing state and the status reads
  `Playing level_up`.
- Search: `coin` leaves 3 sounds (`coin_ping_01`, `dice_roll_01` from the "Dice & Coins" folder, `coin_01`) in 3 packs;
  `zzzz` leaves 0 and shows the "no match" message; the Crisp Jingles filter leaves 9; "All" brings back 89.
- Keyboard: Right arrow moves from `click_soft_01` to `click_wood_01`; Down moves one row down (`toggle_off` at 1280 px,
  `hover_soft_01` at 375 px, where the grid has one column); Enter plays the focused sound; `C` copies its file name
  (status `Copied toggle_off.ogg`); `/` moves focus to the search box.
- Volume slider set to 35 shows `35%`.

### UI kit preview

- All 109 pieces were selected one by one: 46 sliced, 63 fixed size. For each one the 2x PNG loads and its pixel size
  equals `size_2x` from sheets.json. For each sliced piece the stage's computed `border-image-source` is that PNG,
  `border-image-slice` equals `slice_2x` (top right bottom left, fill) and the border widths equal `slice_1x` times
  the zoom. Fixed pieces are shown as an image at their own size. No mismatch (`bad: []`).
- Sliders: the first Crisp Kit button goes from 432 x 104 px on screen to 352 x 164 px (1280 px pass) when the width
  slider is lowered by 40 and the height slider raised by 30 at 2x zoom.
- Dragging the round handle with real mouse events (30 px left, 24 px down) changes the box from 576 x 138 to
  516 x 186 px at 3x zoom.
- The CSS box shows `border-image: url("button_medium_normal.png") 16 17 18 17 fill stretch`, which matches
  sheets.json (left 17, top 16, right 17, bottom 18).
- Light background gives `rgb(238, 240, 245)` on the stage; 3x zoom gives exactly 3 screen pixels per piece pixel;
  switching to Crisp Quest shows its gallery and loads `wood/button_medium_normal.png`.

### VFX sprite sheet player

- All 8 sheets load and their pixel size equals `cols x cell` by `rows x cell` from sheets.json.
- For each sheet the frame read-out advances while playing (two readings 200 ms apart differ and end in the right
  frame count).
- Over http, every frame of every sheet was stepped with the frame slider and the canvas pixels were read back and
  compared with the dark background (frames that draw something / frames in the sheet, largest pixel count):
  gem_burst_blue 19/20 (20324 px), match_pop_pink 15/16 (6032), star_burst_gold 23/24 (12828),
  coin_burst_gold 28/30 (13745), confetti_burst_01 35/36 (6140), ring_shockwave_white 15/16 (14492),
  tap_ripple 13/14 (2368), sparkle_twinkle_white_loop 24/24 (1048). The frames that draw nothing are the faded-out
  last frames of the one-shot effects. Every sheet gave a different pixel count on (almost) every frame, so the
  animation really changes.
- From `file://` the canvas cannot be read back (a local image taints the canvas; this is a browser rule, and the
  player itself never reads pixels), so on `file://` the drawing was confirmed by the frame read-out and by eye.
- Controls: with Loop off at 60 fps the 16-frame effect stops on `Frame 16 of 16` and the button reads `Replay`;
  Restart sets it back to `Pause`; the Light background makes the canvas corner pixel `238,240,245`; selecting the
  sparkle sheet switches Blend to `additive` because its sheets.json entry says so.
- A real mouse click on the stage spawns the effect at the click: 3619 changed pixels in the 140 x 140 px area around
  the click point at 1280 px (6580 at 375 px).

## 3. Screenshots that were looked at

`test.mjs` saves full-page screenshots (over http) of the home page, the Crisp Quest pack page and the three tools,
at 375 px and 1280 px, plus each tool again after the tests have used it. All of them were opened and read.
Things that were found by looking and then fixed:

- UI kit preview: a leftover icon image and a second "Play" label were drawn on top of the selected button
  (`hidden` was being overridden by a `display` rule). Fixed with a global `[hidden] { display: none !important }`
  and a test for it.
- UI kit preview: the resize handle sat inside the button's border instead of on its outer corner.
- UI kit preview: the piece started at its smallest width when the page was laid out before the stage had a width.
  The asked-for size is now kept and re-applied when the stage gets room (a `ResizeObserver` was added).
- Sound board: the sticky control bar covered about half of a phone screen. It is now sticky only on screens at least
  760 px wide and 600 px tall.
- Range sliders were not labelled for screen readers, because each `<label>` also contained an `<output>`, which
  takes the label. The labels now use `for=`.
- Tool pages scrolled sideways at 375 px (a grid column without `minmax(0, 1fr)`).
- Smaller things: the arrow after external links could wrap onto its own line; the home page footer repeated the two
  sections directly above it.

## 4. What was not tested

- **Safari and Firefox.** Only Chromium (Edge) was available. The sound board plays the samplers' OGG Vorbis files
  and falls back to MP3 copies when `canPlayType('audio/ogg; codecs="vorbis"')` is empty, which is the case in older
  Safari versions. The MP3 files were checked to decode in Edge, but the fallback path itself has not been run in a
  real Safari.
- **A real phone.** 375 px was emulated in desktop Edge (device metrics override with the mobile flag). Touch dragging
  of the resize handle uses pointer events and was only exercised with mouse events.
- **The live site.** Nothing was pushed or deployed. The canonical URLs, sitemap, robots.txt and Open Graph image
  URLs all assume the site is served at `https://anipixels.github.io/`; they were checked for consistency, not fetched.
- **Whether the outbound itch.io pages are up.** The 24 URLs were compared with the list, not requested.
- **Screen readers.** Labels, roles, `aria-live` status lines and keyboard paths are in place and partly machine
  checked, but no screen reader was run.
- **How search engines or assistants treat the structured data.** The JSON-LD parses and has the fields listed above;
  it was not run through Google's Rich Results Test or the schema.org validator (both are online tools).
- **Listening.** The sounds were verified to decode and to be non-silent; nobody listened to them through this page.
