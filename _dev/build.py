"""Regenerates the static Anipixels site (the folder above this one).

    python _dev/build.py

Inputs (read-only): the released pack folders next to the site folder, i.e. ../Crisp*/release and ../Crisp*/dist.
ONLY these things are copied into the site:
  - files from each *_Free_Sampler.zip (sounds, UI pieces, VFX sheets, sheets.json, LICENSE.txt)
  - marketing images: release/cover.png and release/screenshot_*.png
The full packs and the *_Web_Demo.zip files (which embed every asset of the paid packs) are never opened.
The published site needs no build step: this script only saves retyping when a pack changes.
Needs Python 3.10+, Pillow, and ffmpeg on PATH (for the MP3 fallback copies of the sampler sounds).
"""
import html, io, json, os, re, shutil, subprocess, sys, tempfile, wave, zipfile
from collections import OrderedDict
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packs import (PACKS, BUNDLE, GAMES, SITE, ITCH, PRICE_DATE, SOUND_LICENCE, VFX_LICENCE, UI_LICENCE,
                   SOUND_MADE, VFX_MADE, UI_MADE, SOUND_FORMATS)

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.dirname(OUT)
LASTMOD = "2026-10-06"
SOUND_SLUGS = ["crisp-ui", "crisp-puzzle", "crisp-jingles", "crisp-cards", "crisp-cozy"]
BY_SLUG = {p["slug"]: p for p in PACKS}
e = html.escape


def out(*parts):
    p = os.path.join(OUT, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def write(rel, text):
    with open(out(*rel.split("/")), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def sampler_zip(p):
    path = os.path.join(SRC, p["folder"], "release", p["zip"])
    assert path.endswith("_Free_Sampler.zip"), path          # the only archives this script may open
    return zipfile.ZipFile(path)


def paid(p): return ITCH + p["slug"]
def free(p): return ITCH + p["slug"] + "-free"
def money(v): return "$" + v


# ------------------------------------------------------------------ assets copied from the samplers
def readme_order(z):
    """Category order and names from the sampler README's CONTENTS block."""
    name = [n for n in z.namelist() if n.endswith("/README.txt") and n.count("/") == 1][0]
    text = z.read(name).decode("utf-8")
    cats, cur, on = OrderedDict(), None, False
    for line in text.splitlines():
        if line.strip() == "CONTENTS":
            on = True
            continue
        if not on:
            continue
        m = re.match(r"^  (\S.*?) \((\d+)\)\s*$", line)
        if m:
            cur = m.group(1)
            cats[cur] = []
        elif cur and re.match(r"^    \S", line):
            cats[cur].append(line.split()[0])
    return cats


def build_sounds():
    """Copies the sampler OGGs unchanged and makes an MP3 fallback from each sampler WAV."""
    data = []
    for slug in SOUND_SLUGS:
        p = BY_SLUG[slug]
        z = sampler_zip(p)
        names = z.namelist()
        cats = readme_order(z)
        sounds = []
        for cat, items in cats.items():
            for n in items:
                ogg = [x for x in names if x.endswith("/OGG/%s/%s.ogg" % (cat, n))]
                wav = [x for x in names if x.endswith("/WAV/%s/%s.wav" % (cat, n))]
                assert len(ogg) == 1 and len(wav) == 1, (slug, cat, n)
                wav_bytes = z.read(wav[0])
                with wave.open(io.BytesIO(wav_bytes)) as w:
                    secs = w.getnframes() / w.getframerate()
                dst = out("samples", "sounds", slug, n + ".ogg")
                with open(dst, "wb") as f:
                    f.write(z.read(ogg[0]))
                mp3 = out("samples", "sounds", slug, n + ".mp3")
                if not os.path.exists(mp3):
                    with tempfile.TemporaryDirectory() as td:
                        tmp = os.path.join(td, "in.wav")
                        with open(tmp, "wb") as f:
                            f.write(wav_bytes)
                        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-codec:a", "libmp3lame", "-q:a", "4",
                                        "-map_metadata", "-1", "-id3v2_version", "0", "-write_xing", "1", mp3], check=True)
                sounds.append(dict(name=n, cat=cat, secs=secs))
        assert len(sounds) == p["sampler_n"], (slug, len(sounds))
        assert len({s["name"] for s in sounds}) == len(sounds), slug
        n_ogg = len([x for x in names if x.endswith(".ogg")])
        assert n_ogg == len(sounds), (slug, n_ogg)
        data.append((p, sounds))
        copy_licence(p, z)
    return data


def copy_licence(p, z):
    name = [n for n in z.namelist() if n.endswith("/LICENSE.txt") and n.count("/") == 1][0]
    with open(out("samples", "licences", p["slug"] + ".txt"), "wb") as f:
        f.write(z.read(name))


def build_ui():
    kits = OrderedDict()
    for slug in ("crisp-kit", "crisp-quest"):
        p = BY_SLUG[slug]
        z = sampler_zip(p)
        root = z.namelist()[0].split("/")[0]
        sheets = json.loads(z.read(root + "/sheets.json"))
        assert len(sheets) == p["sampler_n"], (slug, len(sheets))
        with open(out("samples", "ui", slug, "sheets.json"), "wb") as f:
            f.write(z.read(root + "/sheets.json"))
        pieces = []
        for s in sheets:
            with open(out("samples", "ui", slug, "2x", s["group"], s["name"] + ".png"), "wb") as f:
                f.write(z.read(root + "/" + s["png_2x"]))
            sl, pad = s.get("slice_1x"), s.get("content_padding_1x")
            pieces.append(dict(
                g=s["group"], n=s["name"], c=s["category"], w=s["size_1x"][0], h=s["size_1x"][1],
                s=[sl["left"], sl["top"], sl["right"], sl["bottom"]] if sl else None,
                pad=[pad["left"], pad["top"], pad["right"], pad["bottom"]] if pad else None,
                note=s.get("note") or ""))
            if sl:
                assert s["slice_2x"] == {k: v * 2 for k, v in sl.items()}, (slug, s["name"])
        kits[slug] = dict(name=p["name"], base="../../samples/ui/%s/" % slug, pieces=pieces)
        copy_licence(p, z)
    write("tools/ui-kit-preview/data.js",
          "/* Generated by _dev/build.py from the sheets.json of the Crisp Kit and Crisp Quest free samplers. */\n"
          "window.KIT_DATA = " + json.dumps(kits, indent=1) + ";\n")
    return kits


def build_vfx():
    p = BY_SLUG["crisp-juice"]
    z = sampler_zip(p)
    root = z.namelist()[0].split("/")[0]
    sheets = json.loads(z.read(root + "/sheets.json"))
    assert len(sheets) == p["sampler_n"]
    with open(out("samples", "vfx", "sheets.json"), "wb") as f:
        f.write(z.read(root + "/sheets.json"))
    for s in sheets:
        raw = z.read("%s/Sheets/%s/%s.png" % (root, s["category"], s["name"]))
        im = Image.open(io.BytesIO(raw))
        assert im.size == (s["cols"] * s["cell"], s["rows"] * s["cell"]), s["name"]
        with open(out("samples", "vfx", s["name"] + ".png"), "wb") as f:
            f.write(raw)
    copy_licence(p, z)
    write("tools/vfx-player/data.js",
          "/* Generated by _dev/build.py from sheets.json in the Crisp Juice free sampler. */\n"
          "window.VFX_DATA = " + json.dumps(dict(base="../../samples/vfx/", sheets=sheets), indent=1) + ";\n")
    return sheets


def build_images():
    shots = {}
    for p in PACKS:
        rel = os.path.join(SRC, p["folder"], "release")
        shutil.copyfile(os.path.join(rel, "cover.png"), out("assets", "packs", p["slug"], "cover.png"))
        assert Image.open(os.path.join(rel, "cover.png")).size == (630, 500)
        shots[p["slug"]] = []
        for fn, alt in p["shots"]:
            im = Image.open(os.path.join(rel, fn)).convert("RGB")
            base = fn.replace("screenshot_", "").replace(".png", "")
            full = im.copy()
            full.thumbnail((1600, 2400), Image.LANCZOS)
            full.save(out("assets", "packs", p["slug"], base + ".webp"), "WEBP", quality=82, method=6)
            th = im.copy()
            th.thumbnail((640, 4000), Image.LANCZOS)
            th = th.crop((0, 0, th.width, min(th.height, 400)))
            th.save(out("assets", "packs", p["slug"], base + "-thumb.webp"), "WEBP", quality=78, method=6)
            shots[p["slug"]].append(dict(full=base + ".webp", thumb=base + "-thumb.webp", alt=alt,
                                         w=full.width, h=full.height, tw=th.width, th=th.height))
    # Open Graph image for the home page: the eight covers in a grid.
    og = Image.new("RGB", (1200, 630), (18, 20, 26))
    for i, p in enumerate(PACKS):
        c = Image.open(os.path.join(SRC, p["folder"], "release", "cover.png")).convert("RGB").resize((290, 230), Image.LANCZOS)
        og.paste(c, (14 + (i % 4) * 294, 132 + (i // 4) * 242))
    d = ImageDraw.Draw(og)
    try:
        big = ImageFont.truetype(r"C:\Windows\Fonts\seguibl.ttf", 62)
        small = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 30)
    except OSError:
        big = small = ImageFont.load_default()
    d.text((16, 14), "ANIPIXELS", font=big, fill=(241, 242, 246))
    d.text((18, 86), "Game asset packs: UI sounds, UI kits, VFX sprite sheets", font=small, fill=(167, 174, 194))
    og.save(out("assets", "og-home.png"), optimize=True)
    # Favicon: three rounded bars, like the waveforms on the sound-pack covers.
    write("assets/favicon.svg",
          '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#12141a"/>'
          '<rect x="13" y="24" width="9" height="16" rx="4.5" fill="#6ee7b7"/><rect x="27.5" y="12" width="9" height="40" rx="4.5" fill="#6ee7b7"/>'
          '<rect x="42" y="20" width="9" height="24" rx="4.5" fill="#6ee7b7"/></svg>\n')
    ico = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    d = ImageDraw.Draw(ico)
    d.rounded_rectangle((0, 0, 255, 255), 56, fill=(18, 20, 26, 255))
    for x, y0, y1 in ((52, 96, 160), (110, 48, 208), (168, 80, 176)):
        d.rounded_rectangle((x, y0, x + 36, y1), 18, fill=(110, 231, 183, 255))
    ico.save(out("favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48)])
    return shots


# ------------------------------------------------------------------ checks against the packs' own manifests
def manifest(p):
    with open(os.path.join(SRC, p["folder"], "dist", "manifest.json"), encoding="utf-8") as f:
        return json.load(f)


def manifest_groups(p):
    """{category: [(base name, count)]} with the numbered variations folded together."""
    cats = OrderedDict()
    for x in manifest(p):
        base = re.sub(r"_\d+$", "", x["name"])
        cats.setdefault(x["category"], OrderedDict())
        cats[x["category"]][base] = cats[x["category"]].get(base, 0) + 1
    return cats


def verify_counts():
    for p in PACKS:
        if not p["manifest"]:
            continue
        m = manifest(p)
        assert len(m) == p["total"], (p["slug"], len(m))
        got = OrderedDict()
        for x in m:
            got[x["category"]] = got.get(x["category"], 0) + 1
        want = OrderedDict((c[0], c[1]) for c in p["cats"])
        assert got == want, (p["slug"], got, want)


# ------------------------------------------------------------------ page shell
def ld(obj):
    return '<script type="application/ld+json">\n' + json.dumps(obj, indent=1, ensure_ascii=False).replace("</", "<\\/") + "\n</script>"


def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s))


FOOT_MADE = ("Every asset is generated procedurally by code that was written with an AI assistant (Claude): the sounds are synthesised "
             "from scratch and the graphics are drawn by code. No AI image generators, no AI audio generators, no recorded samples and no third-party art.")
FOOT_LICENCE = ("The free sampler files used on this site may be used in any number of commercial and non-commercial projects, "
                "modified freely, and credit is not required. They may not be resold, redistributed or given away as files, on their own or "
                "inside another asset pack, sound library, UI kit or template.")


def page(path, title, desc, body, *, og_image, og_alt, jsonld, og_type="website", accent=None, nav=None, scripts=(), absolute=False,
         noindex=False, short_foot=False):
    depth = 0 if path in ("", "404.html") else path.strip("/").count("/") + 1
    root = "/" if absolute else "../" * depth
    home = root + "index.html" if not absolute else "/"
    canonical = SITE + path
    style = ' style="--accent:%s"' % accent if accent else ""
    def cur(k): return ' aria-current="page"' if nav == k else ""
    head = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
""" + ('<meta name="robots" content="noindex">\n' if noindex else f'<link rel="canonical" href="{canonical}">\n') + f"""<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="Anipixels">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}{og_image[0]}">
<meta property="og:image:width" content="{og_image[1]}">
<meta property="og:image:height" content="{og_image[2]}">
<meta property="og:image:alt" content="{e(og_alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#12141a">
<link rel="icon" href="{root}assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="{root}assets/site.css">
""" + (ld(jsonld) + "\n" if jsonld else "") + f"""</head>
<body{style}>
<a class="skip" href="#main">Skip to content</a>
<header class="site-head">
<div class="wrap">
<a class="brand" href="{home}"><img src="{root}assets/favicon.svg" alt="" width="30" height="30">ANIPIXELS</a>
<nav aria-label="Main">
<ul class="nav">
<li><a href="{home}#packs"{cur('packs')}>Packs</a></li>
<li><a href="{home}#tools"{cur('tools')}>Free tools</a></li>
<li><a href="{home}#games">Games</a></li>
<li><a href="{home}#about">About</a></li>
</ul>
</nav>
</div>
</header>
<main id="main">
<div class="wrap">
"""
    foot = f"""</div>
</main>
<footer class="site-foot">
<div class="wrap">
""" + ("" if short_foot else f"""<div class="cols">
<div>
<h2>How these are made</h2>
<p>{FOOT_MADE}</p>
</div>
<div>
<h2>Licence for the sampler files on this site</h2>
<p>{FOOT_LICENCE} <a href="{home}#licence">Full licence texts</a>.</p>
</div>
</div>
""") + f"""<p>Anipixels sells its packs on itch.io. Prices are in US dollars as listed on itch.io on {PRICE_DATE}; the itch.io page always shows the current price.
This site makes no external requests and uses no cookies, analytics or trackers.</p>
</div>
</footer>
""" + "".join(f'<script src="{s}"></script>\n' for s in scripts) + "</body>\n</html>\n"
    write(path + "index.html" if not path.endswith(".html") else path, head + body + foot)


def bundle_block(root_home=None):
    b = BUNDLE
    return f"""<div class="card bundle">
<div>
<h2>{b['name']}: all 8 packs for {money(b['price'])}</h2>
<p class="muted">Five sound packs, two UI kits and the VFX sprite sheets in one purchase on itch.io. Bought one by one, the eight packs add up to {money(b['singles'])}.</p>
</div>
<div>
<p style="margin-bottom:10px"><span class="price-big">{money(b['price'])}</span><span class="price-was">{money(b['singles'])}</span></p>
<a class="btn btn-primary ext" href="{b['url']}" rel="noopener">View the bundle on itch.io</a>
</div>
</div>"""


# ------------------------------------------------------------------ home
TOOLS = [
    dict(slug="ui-sound-board", name="UI sound board",
         card="Play the 89 free sampler sounds from the five sound packs. Search, filter by pack, set the volume and copy file names.",
         cover="crisp-ui"),
    dict(slug="ui-kit-preview", name="UI kit 9-slice preview",
         card="Resize the Crisp Kit and Crisp Quest sampler buttons and panels live to see how their 9-slice borders stretch, on light or dark.",
         cover="crisp-kit"),
    dict(slug="vfx-player", name="VFX sprite sheet player",
         card="Play the 8 Crisp Juice sampler sprite sheets on a canvas with speed, loop, blend and background controls.",
         cover="crisp-juice"),
]


def build_home(n_sounds):
    cards = []
    for p in PACKS:
        cards.append(f"""<li class="card pack-card" style="--accent:{p['accent']}">
<a class="cover" href="packs/{p['slug']}/index.html" tabindex="-1" aria-hidden="true"><img src="assets/packs/{p['slug']}/cover.png" alt="" width="630" height="500" loading="lazy"></a>
<div class="body">
<span class="kind">{e(p['kind'])}</span>
<h3><a href="packs/{p['slug']}/index.html">{e(p['name'])}</a></h3>
<p>{e(p['card'])}</p>
<div class="price">{money(p['price'])}</div>
<div class="btn-row">
<a class="btn btn-primary ext" href="{paid(p)}" rel="noopener" aria-label="View {e(p['name'])} on itch.io">View on itch</a>
<a class="btn btn-ghost ext" href="{free(p)}" rel="noopener" aria-label="{e(p['name'])} free sampler on itch.io">Free sampler</a>
</div>
</div>
</li>""")
    tools = []
    for t in TOOLS:
        tools.append(f"""<li class="card tool-card">
<h3>{e(t['name'])}</h3>
<p>{e(t['card'])}</p>
<a class="btn btn-ghost" href="tools/{t['slug']}/index.html">Open the {e(t['name'])}</a>
</li>""")
    games = "".join(f'<li><a class="card game-link ext" href="{ITCH}{slug}" rel="noopener"><strong>{e(n)}</strong><span>{e(d)}</span></a></li>\n'
                    for n, slug, d in GAMES)
    licences = "".join(f'<li><a href="samples/licences/{p["slug"]}.txt">{e(p["name"])} sampler licence</a></li>\n' for p in PACKS)
    body = f"""<section class="hero">
<span class="pill">Game asset packs</span>
<h1>Anipixels</h1>
<p class="lead">Anipixels makes royalty-free asset packs for casual and 2D games (UI sound effects, music jingles, UI kits and VFX sprite sheets), all generated by code and sold on itch.io.</p>
<div class="btn-row">
<a class="btn btn-primary" href="#packs">See the 8 packs</a>
<a class="btn btn-ghost" href="#tools">Try the free tools</a>
</div>
</section>

<section aria-label="Bundle offer">
{bundle_block()}
</section>

<section id="packs">
<h2>The packs</h2>
<p class="muted">Each pack has a paid page and a free page on itch.io. The free page has a browser demo of the whole pack and a sampler you can download and use.</p>
<ul class="grid grid-packs" style="list-style:none;padding:0;margin:0">
{chr(10).join(cards)}
</ul>
</section>

<section id="tools">
<h2>Free tools</h2>
<p class="muted">Three small browser tools built only from the free sampler files. No sign-up, no downloads, nothing is uploaded.</p>
<ul class="grid grid-3" style="list-style:none;padding:0;margin:0">
{chr(10).join(tools)}
</ul>
</section>

<section id="games">
<h2>Games</h2>
<p class="muted">Seven free browser games by Anipixels, playable on itch.io.</p>
<ul class="grid grid-games" style="list-style:none;padding:0;margin:0">
{games}</ul>
</section>

<section id="about">
<h2>How these are made</h2>
<p>{FOOT_MADE}</p>
<p>The sound packs are synthesised by code (no recordings). The UI kits and VFX sheets are drawn shape by shape by code (no image generators).
The store pages on itch.io carry the same disclosure.</p>
</section>

<section id="licence">
<h2>Licence for the free sampler files</h2>
<p>This site hosts only the free sampler of each pack: {n_sounds} sounds, 109 UI pieces and 8 VFX sprite sheets, plus cover images and screenshots. The full packs are sold on itch.io and are not on this site.</p>
<p>{FOOT_LICENCE}</p>
<p>Those are the terms of the LICENSE.txt that ships inside each sampler. The exact texts:</p>
<ul>
{licences}</ul>
</section>
"""
    jsonld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Organization", "@id": SITE + "#org", "name": "Anipixels", "url": SITE, "logo": SITE + "assets/og-home.png",
         "description": "Anipixels makes royalty-free game asset packs (UI sound effects, music jingles, UI kits and VFX sprite sheets) generated by code and sold on itch.io."},
        {"@type": "WebSite", "@id": SITE + "#site", "name": "Anipixels", "url": SITE, "publisher": {"@id": SITE + "#org"}, "inLanguage": "en"},
        {"@type": "ItemList", "name": "Anipixels asset packs", "numberOfItems": len(PACKS),
         "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": p["name"], "url": SITE + "packs/%s/" % p["slug"]}
                             for i, p in enumerate(PACKS)]},
    ]}
    page("", "Anipixels - Game UI Sound Effects, UI Kits and VFX Sprite Sheets",
         "Anipixels makes royalty-free game asset packs: UI sound effects, music jingles, UI kits and VFX sprite sheets. 8 packs on itch.io, free samplers and free browser tools.",
         body, og_image=("assets/og-home.png", 1200, 630), og_alt="The covers of the eight Anipixels asset packs", jsonld=jsonld, short_foot=True)


# ------------------------------------------------------------------ pack pages
def nice(name): return name.replace("_", " ")


def included_block(p):
    if "included_html" in p:
        return "<ul>\n" + "".join("<li>%s</li>\n" % x for x in p["included_html"]) + "</ul>"
    groups = manifest_groups(p)
    if p["slug"] == "crisp-jingles":
        moments = sorted({re.sub(r"_(chip|cozy|synth)$", "", x["name"]) for x in manifest(p)})
        assert len(moments) == 15
        secs = [x["seconds"] for x in manifest(p)]
        return (f"<p>The 15 moments: {e(', '.join(nice(m) for m in moments))}.</p>\n"
                f"<p>Each one comes in three styles, 15 files per folder. The jingles are {min(secs):.1f} to {max(secs):.1f} seconds long.</p>\n"
                '<ul class="contents-list">\n'
                + "".join(f'<li><strong>{e(c)}</strong> <span class="n">({n})</span> - file names end in _{suffix}</li>\n'
                          for (c, n), suffix in zip([(c[0], c[1]) for c in p["cats"]], ("chip", "cozy", "synth")))
                + "</ul>")
    rows = []
    for c in p["cats"]:
        cat, n = c[0], c[1]
        if len(c) > 2:
            desc = e(c[2])
        else:
            desc = e(", ".join(nice(b) + (" x%d" % k if k > 1 else "") for b, k in groups[cat].items()))
        rows.append(f'<li><strong>{e(cat)}</strong> <span class="n">({n})</span> - {desc}</li>\n')
    note = ""
    if len(p["cats"][0]) == 2 and p["licence"] == "sound":
        note = '<p class="muted small">Names are the file names without the trailing number; "x5" means five numbered files of that sound (variations, or tuned steps such as star 1-2-3).</p>\n'
    return '<ul class="contents-list">\n' + "".join(rows) + "</ul>\n" + note


def pack_tool(p):
    if p["slug"] in SOUND_SLUGS:
        return ("../../tools/ui-sound-board/index.html", "Play the %d sampler %s in the UI sound board" % (p["sampler_n"], p["unit"]))
    if p["slug"] == "crisp-juice":
        return ("../../tools/vfx-player/index.html", "Play the 8 sampler effects in the VFX sprite sheet player")
    return ("../../tools/ui-kit-preview/index.html", "Resize the sampler pieces in the UI kit 9-slice preview")


def build_pack(p, shots):
    licence = {"sound": SOUND_LICENCE, "vfx": VFX_LICENCE, "ui": UI_LICENCE}[p["licence"]]
    made = {"sound": SOUND_MADE, "vfx": VFX_MADE, "ui": UI_MADE}[p["licence"]]
    faq = p["faq"]()
    tool_href, tool_text = pack_tool(p)
    if p["licence"] == "sound":
        formats = "<ul>\n" + "".join("<li>%s</li>\n" % e(x) for x in SOUND_FORMATS) + "</ul>\n"
        engines = p.get("engines") or "Any engine or tool that plays WAV or OGG files. The pack's README names Godot, Unity, GameMaker and web."
        fact_formats = "WAV (44.1 kHz, 16-bit, stereo) and OGG Vorbis"
        if p["slug"] == "crisp-jingles":
            fact_contents = "45 jingles: 15 moments x 3 styles (chiptune, cozy, synth-pop)"
        else:
            fact_contents = "%d sounds in %d folders" % (p["total"], len(p["cats"]))
    elif p["licence"] == "vfx":
        formats = "<ul>\n<li>Transparent PNG sprite sheets, sorted by category, usable in any engine.</li>\n<li>sheets.json with frame count, cell size, columns, rows, fps and loop flag for every sheet.</li>\n<li>A Godot 4 project you can open and play, with the addon in Godot/addons/crisp_vfx.</li>\n</ul>\n"
        engines = p["engines"]
        fact_formats = "Transparent PNG sprite sheets, sheets.json, Godot 4 project"
        fact_contents = "68 sprite-sheet effects in 6 folders"
    else:
        formats = "<ul>\n<li>PNG at 1x (made for roughly 960 x 540 to 1280 x 720 layouts) and 2x (1080p and up, phones, HiDPI).</li>\n<li>SVG vector files of the same pieces.</li>\n<li>sheets.json listing every piece: file paths, sizes, 9-slice borders, content padding and notes.</li>\n<li>Godot 4 Theme resources and a demo scene.</li>\n</ul>\n"
        engines = p["engines"]
        fact_formats = "PNG 1x + 2x, SVG, sheets.json, Godot 4 themes"
        fact_contents = "%d images: %s" % (p["total"], "100 pieces x 8 themes, 127 icons, 93 input prompts, 15 colour pieces" if p["slug"] == "crisp-kit"
                                           else "135 pieces x 6 themes, 147 icons in white and dark, 37 colour icons")
    shots_html = "".join(
        f'<a href="../../assets/packs/{p["slug"]}/{s["full"]}"><img src="../../assets/packs/{p["slug"]}/{s["thumb"]}" alt="{e(s["alt"])}" width="{s["tw"]}" height="{s["th"]}" loading="lazy"></a>\n'
        for s in shots)
    faq_html = "".join(f"<h3>{e(q)}</h3>\n<p>{e(a)}</p>\n" for q, a in faq)
    others = "".join(f'<li><a href="../{o["slug"]}/index.html">{e(o["name"])}</a></li>\n' for o in PACKS if o is not p)
    b = BUNDLE
    body = f"""<nav class="crumbs" aria-label="Breadcrumb"><ol><li><a href="../../index.html">Anipixels</a></li><li><a href="../../index.html#packs">Packs</a></li><li aria-current="page">{e(p['name'])}</li></ol></nav>
<div class="pack-hero">
<div>
<span class="pill">{e(p['kind'])}</span>
<h1>{e(p['h1'])}</h1>
<p class="lead">{p['lead']}</p>
<div class="btn-row">
<a class="btn btn-primary ext" href="{paid(p)}" rel="noopener">Get {e(p['name'])} on itch.io: {money(p['price'])}</a>
<a class="btn btn-ghost ext" href="{free(p)}" rel="noopener">Free sampler and demo</a>
</div>
</div>
<img src="../../assets/packs/{p['slug']}/cover.png" alt="{e(p['name'])} cover image" width="630" height="500">
</div>

<section aria-label="Key facts">
<dl class="facts">
<dt>Contents</dt><dd>{e(fact_contents)}</dd>
<dt>Formats</dt><dd>{e(fact_formats)}</dd>
<dt>Price</dt><dd>{money(p['price'])} on itch.io (<a class="ext" href="{paid(p)}" rel="noopener">{paid(p).replace('https://', '')}</a>)</dd>
<dt>Free sampler</dt><dd>{p['sampler_n']} {e(p['unit'])}, free on itch.io (<a class="ext" href="{free(p)}" rel="noopener">{free(p).replace('https://', '')}</a>)</dd>
<dt>Licence</dt><dd>Royalty-free for commercial and non-commercial projects, no credit required, no reselling or redistribution of the files</dd>
<dt>Made by</dt><dd>Anipixels, with procedural code written with an AI assistant (Claude)</dd>
</dl>
</section>

<section>
<h2>What is included</h2>
{included_block(p)}
</section>

<section>
<h2>Details</h2>
<ul>
{''.join('<li>%s</li>' % e(x) + chr(10) for x in p['specs'])}</ul>
</section>

<section>
<h2>Formats and engines</h2>
{formats}<p><strong>Works with:</strong> {e(engines)}</p>
</section>

<section>
<h2>Free sampler</h2>
<p>{e(p['sampler'])}</p>
<div class="btn-row">
<a class="btn btn-ghost ext" href="{free(p)}" rel="noopener">Download the sampler on itch.io</a>
<a class="btn btn-ghost" href="{tool_href}">{e(tool_text)}</a>
</div>
<p class="muted small">The free itch.io page also hosts the playable browser demo of the full pack.</p>
</section>

<section>
<h2>Licence</h2>
<p>{e(licence)}</p>
<p class="muted small">This is a summary of the LICENSE.txt inside the download. The sampler's copy of that file: <a href="../../samples/licences/{p['slug']}.txt">{p['slug']}.txt</a>.</p>
</section>

<section class="faq">
<h2>Questions</h2>
{faq_html}</section>

<section>
<h2>Screenshots</h2>
<div class="shots">
{shots_html}</div>
</section>

<section>
<h2>How it was made</h2>
<p>{e(made)}</p>
</section>

<section aria-label="Bundle and other packs">
<div class="card callout">
<p><strong>{e(p['name'])} is part of the {b['name']}</strong>: all 8 Crisp packs for {money(b['price'])} instead of {money(b['singles'])} bought one by one.
<a class="ext" href="{b['url']}" rel="noopener">View the bundle on itch.io</a></p>
</div>
<h2 style="margin-top:28px">Other packs</h2>
<ul class="more-packs">
{others}</ul>
</section>
"""
    url = SITE + "packs/%s/" % p["slug"]
    cover = SITE + "assets/packs/%s/cover.png" % p["slug"]
    jsonld = {"@context": "https://schema.org", "@graph": [
        {"@type": "Product", "@id": url + "#product", "name": p["name"], "description": p["meta"], "image": [cover], "url": url,
         "category": p["kind"], "brand": {"@type": "Brand", "name": "Anipixels"},
         "offers": {"@type": "Offer", "price": p["price"], "priceCurrency": "USD", "url": paid(p),
                    "availability": "https://schema.org/InStock",
                    "seller": {"@type": "Organization", "name": "Anipixels"}}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Anipixels", "item": SITE},
            {"@type": "ListItem", "position": 2, "name": p["name"], "item": url}]},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]},
    ]}
    page("packs/%s/" % p["slug"], p["title"], p["meta"], body, og_image=("assets/packs/%s/cover.png" % p["slug"], 630, 500),
         og_alt=p["name"] + " cover image", jsonld=jsonld, og_type="product", accent=p["accent"], nav="packs")


# ------------------------------------------------------------------ tools
def tool_ld(slug, name, desc, cover, category, features):
    url = SITE + "tools/%s/" % slug
    return {"@context": "https://schema.org", "@graph": [
        {"@type": "WebApplication", "@id": url + "#app", "name": name, "url": url, "description": desc,
         "applicationCategory": category, "operatingSystem": "Any (runs in a web browser)", "browserRequirements": "Requires JavaScript",
         "isAccessibleForFree": True, "inLanguage": "en", "image": SITE + "assets/packs/%s/cover.png" % cover,
         "featureList": features,
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
         "creator": {"@type": "Organization", "name": "Anipixels", "url": SITE}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Anipixels", "item": SITE},
            {"@type": "ListItem", "position": 2, "name": name, "item": url}]},
    ]}


def crumbs(name):
    return (f'<nav class="crumbs" aria-label="Breadcrumb"><ol><li><a href="../../index.html">Anipixels</a></li>'
            f'<li><a href="../../index.html#tools">Free tools</a></li><li aria-current="page">{e(name)}</li></ol></nav>\n')


def build_sound_board(data):
    total = sum(len(s) for _, s in data)
    radios = '<label><input type="radio" name="sb-pack" value="all" checked><span>All</span></label>\n' + "".join(
        f'<label><input type="radio" name="sb-pack" value="{p["slug"]}"><span>{e(p["name"])}</span></label>\n' for p, _ in data)
    sections = []
    for p, sounds in data:
        items = []
        for s in sounds:
            hay = e(("%s %s %s" % (s["name"], s["cat"], p["name"])).lower().replace("_", " ") + " " + s["name"].lower())
            items.append(
                f'<li class="sb-item" data-pack="{p["slug"]}" data-hay="{hay}">'
                f'<button type="button" class="sb-play" data-name="{s["name"]}" data-src="../../samples/sounds/{p["slug"]}/{s["name"]}" '
                f'aria-label="Play {s["name"]}, {e(s["cat"])}, {s["secs"]:.2f} seconds">'
                f'<span class="sb-ico" aria-hidden="true"></span><span class="sb-name">{s["name"]}</span>'
                f'<span class="sb-meta">{e(s["cat"])} - {s["secs"]:.2f} s</span></button>'
                f'<button type="button" class="sb-copy" data-name="{s["name"]}" aria-label="Copy the file name of {s["name"]}" title="Copy file name">COPY</button></li>')
        sections.append(f"""<section class="sb-pack" id="{p['slug']}" style="--pc:{p['accent']}">
<div class="sb-pack-head"><h2>{e(p['name'])}</h2><span class="muted">{len(sounds)} free sampler {p['unit']} of the {p['total']} in the full pack</span></div>
<div class="sb-pack-links">
<a class="ext" href="{free(p)}" rel="noopener">Download this sampler (WAV + OGG) on itch.io</a>
<a class="ext" href="{paid(p)}" rel="noopener">Full pack: {p['total']} {p['unit']}, {money(p['price'])}</a>
<a href="../../packs/{p['slug']}/index.html">About {e(p['name'])}</a>
</div>
<ul class="sb-grid">
{chr(10).join(items)}
</ul>
</section>""")
    name = "UI sound board"
    desc = (f"Free UI sound board: play {total} game UI sound effects and jingles from the Anipixels free samplers in your browser. "
            "Search, filter by pack, set the volume, copy file names.")
    body = crumbs(name) + f"""<div class="tool-head">
<span class="pill">Free tool</span>
<h1>UI sound board: {total} free game UI sounds</h1>
<p class="lead">Play the free sampler sounds from the five Anipixels sound packs in your browser: clicks, toggles, confirm and error sounds, coins, puzzle combos, card and casino sounds and short music jingles. Click a sound to hear it, and copy its file name when you find the one you want.</p>
</div>

<div class="panel sb-bar" role="search" aria-label="Sound board controls">
<div class="controls">
<label class="field field-search"><span>Search sounds (press <kbd>/</kbd>)</span><input type="search" id="sb-search" placeholder="click, coin, level up, cards..." autocomplete="off"></label>
<div class="field field-vol"><span><label for="sb-vol">Volume</label> <output id="sb-vol-out" for="sb-vol">80%</output></span><input type="range" id="sb-vol" min="0" max="100" step="1" value="80"></div>
<label class="field"><span>Copy file name as</span><select id="sb-fmt"><option value="ogg">name.ogg</option><option value="wav">name.wav</option><option value="none">name only</option></select></label>
<button type="button" class="btn btn-ghost" id="sb-stop">Stop all</button>
</div>
<div class="sb-filters">
<div class="seg" role="radiogroup" aria-label="Show pack">
{radios}</div>
</div>
<p class="status small" style="margin:10px 0 0"><span id="sb-count" class="muted">{total} of {total} sounds shown</span> &nbsp; <span id="sb-status" role="status" aria-live="polite"></span></p>
</div>

<p id="sb-empty" class="muted" hidden>No sampler sound matches that search. Try a shorter word, or clear the search with <kbd>Esc</kbd>.</p>

{chr(10).join(sections)}

<section>
<h2>How to use it</h2>
<ul>
<li>Click or tap a sound to play it. Click it again to restart it.</li>
<li>Keyboard: <kbd>Tab</kbd> to a sound and press <kbd>Enter</kbd> or <kbd>Space</kbd> to play it; the arrow keys move between sounds; <kbd>C</kbd> copies the focused sound's file name; <kbd>/</kbd> jumps to the search box; <kbd>Esc</kbd> clears the search or stops all sounds.</li>
<li>The COPY button next to each sound copies its file name (for example <code>click_soft_01.ogg</code>), which is the name the file has inside the sampler zip.</li>
<li>To use a sound in your game, download that pack's free sampler from its itch.io page. It contains every sound here as WAV and OGG.</li>
</ul>
</section>

<section>
<h2>About the sounds</h2>
<p>These are the {total} sounds of the five free samplers: {', '.join('%d from %s' % (len(s), p['name']) for p, s in data)}. The full packs have {sum(p['total'] for p, _ in data)} sounds between them and are sold on itch.io; they are not on this site.</p>
<p>The sampler files are WAV (44.1 kHz, 16-bit, stereo) and OGG Vorbis. This page plays the sampler's OGG files unchanged. For browsers that cannot play OGG Vorbis there is an MP3 copy of each sound, encoded from the sampler's WAV. <span id="sb-format-note"></span></p>
<p><strong>Licence:</strong> {e(SOUND_LICENCE)}</p>
<p>{e(SOUND_MADE)}</p>
</section>
"""
    page("tools/ui-sound-board/", "Free UI Sound Board - %d Game UI Sound Effects to Play Online | Anipixels" % total, desc, body,
         og_image=("assets/packs/crisp-ui/cover.png", 630, 500), og_alt="Crisp UI cover image",
         jsonld=tool_ld("ui-sound-board", "Anipixels UI sound board", desc, "crisp-ui", "MultimediaApplication",
                        ["Play %d free game UI sound effects and jingles" % total, "Search and filter by pack", "Keyboard control",
                         "Volume control", "Copy file names"]),
         nav="tools", scripts=["board.js"])
    return total


def build_kit_preview(kits):
    sections = []
    group_names = {"mint": "Mint theme pieces", "common": "Colour pieces", "icons_white": "White icons", "prompts_light": "Input prompts (light style)",
                   "wood": "Carved Wood theme pieces", "icons_colour": "Colour icons"}
    for slug, kit in kits.items():
        p = BY_SLUG[slug]
        groups = OrderedDict()
        for i, pc in enumerate(kit["pieces"]):
            groups.setdefault(pc["g"], []).append((i, pc))
        parts = []
        for g, items in groups.items():
            lis = []
            for i, pc in items:
                kind = "9-slice" if pc["s"] and not (pc["s"][1] == 0 and pc["s"][3] == 0) else ("3-slice" if pc["s"] else "fixed size")
                lis.append(
                    f'<li><button type="button" class="kp-piece" data-kit="{slug}" data-i="{i}" aria-pressed="false" '
                    f'aria-label="Preview {pc["n"]}, {pc["w"]} by {pc["h"]} pixels, {kind}">'
                    f'<span class="kp-thumb bg-dark"><img src="{kit["base"]}2x/{pc["g"]}/{pc["n"]}.png" alt="" style="width:{pc["w"]}px;height:{pc["h"]}px" loading="lazy"></span>'
                    f'<span class="kp-pname">{pc["n"]}</span><span class="kp-psize">{pc["w"]} x {pc["h"]} px - {kind}</span></button></li>')
            parts.append(f'<h3 class="kp-group-title">{e(group_names[g])} ({len(items)})</h3>\n<ul class="kp-gallery">\n' + "\n".join(lis) + "\n</ul>")
        sections.append(f"""<div class="kp-kit" data-kit="{slug}">
<p><strong>{e(p['name'])} free sampler:</strong> {len(kit['pieces'])} pieces.
<a class="ext" href="{free(p)}" rel="noopener">Download the sampler (PNG 1x + 2x, SVG) on itch.io</a> -
<a class="ext" href="{paid(p)}" rel="noopener">Full kit: {p['total']} images, {money(p['price'])}</a> -
<a href="../../packs/{slug}/index.html">About {e(p['name'])}</a></p>
{chr(10).join(parts)}
</div>""")
    n_total = sum(len(k["pieces"]) for k in kits.values())
    n_slice = sum(1 for k in kits.values() for pc in k["pieces"] if pc["s"])
    name = "UI kit 9-slice preview"
    desc = (f"Free 9-slice preview tool: resize {n_slice} game UI buttons, panels and frames from the Crisp Kit and Crisp Quest samplers live, "
            "on light or dark backgrounds.")
    body = crumbs(name) + f"""<div class="tool-head">
<span class="pill">Free tool</span>
<h1>UI kit preview: resize 9-slice buttons and panels live</h1>
<p class="lead">Pick a piece from the Crisp Kit (casual) or Crisp Quest (fantasy RPG) free sampler and drag it to any size. The corners stay sharp and only the middle stretches, exactly as the 9-slice borders in each sampler's sheets.json say. Use it to check a piece at the size you need, and to read off its border values.</p>
</div>

<div class="panel" style="margin-bottom:20px">
<div class="controls">
<div class="field"><span id="kp-kit-l">Kit</span>
<div class="seg" role="radiogroup" aria-labelledby="kp-kit-l">
<label><input type="radio" name="kp-kit" value="crisp-kit" checked><span>Crisp Kit</span></label>
<label><input type="radio" name="kp-kit" value="crisp-quest"><span>Crisp Quest</span></label>
</div></div>
<div class="field"><span id="kp-bg-l">Background</span>
<div class="seg" role="radiogroup" aria-labelledby="kp-bg-l">
<label><input type="radio" name="kp-bg" value="dark" checked><span>Dark</span></label>
<label><input type="radio" name="kp-bg" value="light"><span>Light</span></label>
<label><input type="radio" name="kp-bg" value="checker"><span>Checker</span></label>
</div></div>
<div class="field"><span id="kp-zoom-l">Zoom</span>
<div class="seg" role="radiogroup" aria-labelledby="kp-zoom-l">
<label><input type="radio" name="kp-zoom" value="1"><span>1x</span></label>
<label><input type="radio" name="kp-zoom" value="2" checked><span>2x</span></label>
<label><input type="radio" name="kp-zoom" value="3"><span>3x</span></label>
</div></div>
</div>
</div>

<div class="kp-layout">
<div>
<div class="kp-stage bg-dark" id="kp-stage">
<div class="kp-box" id="kp-box"><img id="kp-img" alt="" hidden><span class="kp-label" id="kp-label" hidden></span>
<button type="button" class="kp-handle" id="kp-handle" aria-label="Resize handle: drag, or use the arrow keys"></button></div>
</div>
<div class="panel" style="margin-top:12px">
<div class="controls">
<div class="field" style="flex:1 1 160px"><span><label for="kp-w">Width</label> <output id="kp-w-out" for="kp-w"></output></span><input type="range" id="kp-w" min="8" max="480" step="1" value="144"></div>
<div class="field" style="flex:1 1 160px"><span><label for="kp-h">Height</label> <output id="kp-h-out" for="kp-h"></output></span><input type="range" id="kp-h" min="8" max="320" step="1" value="52"></div>
</div>
<div class="controls" style="margin-top:8px">
<label class="check"><input type="checkbox" id="kp-showlabel" checked> Show a text label on buttons</label>
<label class="field" style="flex:1 1 140px"><span>Label text</span><input type="text" id="kp-labeltext" value="Play" maxlength="24"></label>
</div>
<p class="status small" id="kp-status" role="status" aria-live="polite" style="margin:8px 0 0"></p>
</div>
</div>
<div class="panel">
<h2 style="font-size:1.15rem">Selected piece</h2>
<dl class="kv">
<dt>Name</dt><dd id="kp-i-name"></dd>
<dt>Size</dt><dd id="kp-i-size"></dd>
<dt>Type</dt><dd id="kp-i-type"></dd>
<dt>Borders</dt><dd id="kp-i-slice"></dd>
<dt>Files</dt><dd id="kp-i-files" style="font-family:var(--mono);font-size:0.82rem;word-break:break-all"></dd>
<dt>Note</dt><dd id="kp-i-note"></dd>
</dl>
<pre><code id="kp-css"></code></pre>
<button type="button" class="btn btn-ghost" id="kp-copy">Copy CSS</button>
</div>
</div>

<section>
<h2>Sampler pieces</h2>
{chr(10).join(sections)}
</section>

<section>
<h2>How it works</h2>
<ul>
<li>A 9-slice piece is cut by four border lines into nine regions. The four corners are drawn at their own size, the edges stretch in one direction and the middle stretches in both.</li>
<li>This page draws each piece with CSS <code>border-image</code>, using the <code>slice_1x</code> and <code>slice_2x</code> values from the sampler's <code>sheets.json</code> unchanged. The same four numbers go into the nine-slice or nine-patch settings of Godot, Unity, GameMaker, Construct or Phaser.</li>
<li>Pieces marked 3-slice have no top or bottom border: they stretch sideways only and keep their height.</li>
<li>Fixed-size pieces (icons, check boxes, knobs, prompts) have no borders and are shown at their own size.</li>
<li>The text label on buttons sits inside the piece's <code>content_padding_1x</code> from sheets.json. The label is drawn by your browser; no font is included in the kits.</li>
<li>Keyboard: focus the round handle and use the arrow keys to resize (hold <kbd>Shift</kbd> for bigger steps), or use the width and height sliders.</li>
</ul>
</section>

<section>
<h2>About the pieces</h2>
<p>These are the {n_total} pieces of the two free samplers (57 from Crisp Kit, 52 from Crisp Quest); {n_slice} of them are 9-slice or 3-slice. The page shows the samplers' 2x PNGs. The samplers on itch.io also contain the 1x PNGs and the SVGs. The full kits (all themes, all icons, Godot 4 themes) are sold on itch.io and are not on this site.</p>
<p><strong>Licence:</strong> {e(UI_LICENCE)}</p>
<p>{e(UI_MADE)}</p>
</section>
"""
    page("tools/ui-kit-preview/", "9-Slice UI Preview Tool - Resize Game UI Buttons and Panels Online | Anipixels", desc, body,
         og_image=("assets/packs/crisp-kit/cover.png", 630, 500), og_alt="Crisp Kit cover image",
         jsonld=tool_ld("ui-kit-preview", "Anipixels UI kit 9-slice preview", desc, "crisp-kit", "DesignApplication",
                        ["Live 9-slice resize of game UI buttons, panels and frames", "Light, dark and checker backgrounds",
                         "Shows piece sizes and slice borders", "Copy CSS border-image code"]),
         nav="tools", scripts=["data.js", "preview.js"])


def build_vfx_player(sheets):
    p = BY_SLUG["crisp-juice"]
    picks = []
    for i, s in enumerate(sheets):
        f = s["frames"] // 3
        col, row = f % s["cols"], f // s["cols"]
        picks.append(
            f'<li><button type="button" class="vx-pick" data-i="{i}" aria-pressed="false" aria-label="Play {s["name"]}, {s["frames"]} frames, {s["cell"]} pixel cells">'
            f'<span class="vx-thumb" style="background-image:url(../../samples/vfx/{s["name"]}.png);background-size:{s["cols"] * 84}px {s["rows"] * 84}px;'
            f'background-position:-{col * 84}px -{row * 84}px"></span>'
            f'<span class="vx-pname">{s["name"]}</span><span class="vx-psize">{s["frames"]} frames - {s["cell"]} px</span></button></li>')
    name = "VFX sprite sheet player"
    desc = ("Free sprite sheet player: play 8 game VFX sprite sheets (gem burst, coins, confetti, shockwave, sparkle) on a canvas "
            "with speed, loop, blend and background controls.")
    body = crumbs(name) + f"""<div class="tool-head">
<span class="pill">Free tool</span>
<h1>VFX sprite sheet player: 8 free game effects</h1>
<p class="lead">Play the 8 sprite sheets of the Crisp Juice free sampler on a canvas: a gem burst, a match pop, star and coin bursts, confetti, a shockwave ring, a tap ripple and a looping sparkle. Change the speed, loop, blend mode and background, step through the frames, and click the stage to spawn the effect where you click.</p>
</div>

<ul class="vx-list" aria-label="Effects">
{chr(10).join(picks)}
</ul>

<div class="vx-layout">
<div>
<div class="vx-stage" id="vx-stage" tabindex="0" role="button" aria-label="Effect stage. Click, or press Enter, to spawn the effect."><canvas id="vx-canvas" width="640" height="400"></canvas></div>
<div class="panel" style="margin-top:12px">
<div class="controls">
<button type="button" class="btn btn-primary" id="vx-play" aria-pressed="true" style="min-width:96px">Pause</button>
<button type="button" class="btn btn-ghost" id="vx-restart">Restart</button>
<label class="check"><input type="checkbox" id="vx-loop" checked> Loop</label>
<div class="field" style="flex:1 1 180px"><span><output id="vx-frame-out" for="vx-frame">Frame 1</output></span><input type="range" id="vx-frame" min="0" max="19" step="1" value="0" aria-label="Frame"></div>
</div>
<div class="controls" style="margin-top:8px">
<div class="field" style="flex:1 1 160px"><span><label for="vx-fps">Speed</label> <output id="vx-fps-out" for="vx-fps">30 fps</output></span><input type="range" id="vx-fps" min="1" max="60" step="1" value="30"></div>
<label class="field"><span>Size</span><select id="vx-scale"><option value="0.5">0.5x</option><option value="1" selected>1x</option><option value="2">2x</option><option value="fit">Fit stage</option></select></label>
<label class="field"><span>Blend</span><select id="vx-blend"><option value="normal">Normal</option><option value="additive">Additive</option></select></label>
</div>
<div class="controls" style="margin-top:8px">
<div class="field"><span id="vx-bg-l">Background</span>
<div class="seg" role="radiogroup" aria-labelledby="vx-bg-l">
<label><input type="radio" name="vx-bg" value="dark" checked><span>Dark</span></label>
<label><input type="radio" name="vx-bg" value="light"><span>Light</span></label>
<label><input type="radio" name="vx-bg" value="checker"><span>Checker</span></label>
<label><input type="radio" name="vx-bg" value="custom"><span>Custom</span></label>
</div></div>
<label class="field"><span>Custom colour</span><input type="color" id="vx-color" value="#2b1f4d"></label>
</div>
<p class="status small" id="vx-status" role="status" aria-live="polite" style="margin:8px 0 0"></p>
</div>
</div>
<div class="panel">
<h2 style="font-size:1.15rem">Selected sheet</h2>
<dl class="kv">
<dt>Name</dt><dd id="vx-i-name"></dd>
<dt>Grid</dt><dd id="vx-i-grid"></dd>
<dt>Length</dt><dd id="vx-i-frames"></dd>
<dt>Flags</dt><dd id="vx-i-flags"></dd>
<dt>File</dt><dd id="vx-i-file" style="font-family:var(--mono);font-size:0.82rem;word-break:break-all"></dd>
</dl>
<div class="vx-sheet bg-checker"><img id="vx-sheet-img" alt="" src="../../samples/vfx/{sheets[0]['name']}.png" width="{sheets[0]['cols'] * sheets[0]['cell']}" height="{sheets[0]['rows'] * sheets[0]['cell']}"><span class="vx-cursor" id="vx-cursor"></span></div>
<p class="muted small" style="margin-top:8px">The whole sheet. The outlined cell is the frame being drawn.</p>
<pre><code id="vx-code"></code></pre>
</div>
</div>

<section>
<h2>The 8 sampler effects</h2>
<div style="overflow-x:auto">
<table style="border-collapse:collapse;width:100%;min-width:520px">
<thead><tr style="text-align:left;color:var(--muted)"><th style="padding:6px 10px 6px 0">Effect</th><th style="padding:6px 10px">Folder</th><th style="padding:6px 10px">Frames</th><th style="padding:6px 10px">Cell</th><th style="padding:6px 10px">Grid</th><th style="padding:6px 10px">Loop</th><th style="padding:6px 10px">Additive</th></tr></thead>
<tbody>
{''.join(f'<tr style="border-top:1px solid var(--line)"><td style="padding:6px 10px 6px 0;font-family:var(--mono);font-size:0.86rem">{s["name"]}</td><td style="padding:6px 10px">{s["category"]}</td><td style="padding:6px 10px">{s["frames"]}</td><td style="padding:6px 10px">{s["cell"]} px</td><td style="padding:6px 10px">{s["cols"]} x {s["rows"]}</td><td style="padding:6px 10px">{"yes" if s["loop"] else "no"}</td><td style="padding:6px 10px">{"yes" if s["additive"] else "no"}</td></tr>' + chr(10) for s in sheets)}</tbody>
</table>
</div>
<p class="muted small" style="margin-top:10px">Values are copied from the sampler's sheets.json. All eight are drawn for 30 frames per second.</p>
<div class="btn-row">
<a class="btn btn-ghost ext" href="{free(p)}" rel="noopener">Download the sampler on itch.io</a>
<a class="btn btn-primary ext" href="{paid(p)}" rel="noopener">Full pack: 68 effects, {money(p['price'])}</a>
<a class="btn btn-ghost" href="../../packs/crisp-juice/index.html">About Crisp Juice</a>
</div>
</section>

<section>
<h2>How to use it</h2>
<ul>
<li>Pick an effect above. It plays in the middle of the stage; click or tap anywhere on the stage to spawn more copies.</li>
<li>Drag the frame slider to step through the frames one by one. Speed changes the playback rate from 1 to 60 frames per second.</li>
<li>Additive blending adds the effect's colours to the background, which suits glows and sparkles on dark backgrounds. The player starts each sheet with the blend mode its sheets.json entry asks for.</li>
<li>Keyboard: <kbd>K</kbd> plays or pauses, <kbd>Left</kbd> and <kbd>Right</kbd> change effect, and <kbd>Enter</kbd> on the stage spawns a copy.</li>
<li>In your own engine, slice the sheet as a grid with the cell size shown and play the frames left to right, top to bottom. The code box shows the frame arithmetic.</li>
</ul>
</section>

<section>
<h2>About the effects</h2>
<p>These are the 8 sprite sheets of the Crisp Juice free sampler, unchanged: transparent PNGs with straight alpha. The sampler on itch.io also includes sheets.json and a Godot 4 project with a scene per effect. The full pack has 68 effects and is sold on itch.io; it is not on this site.</p>
<p><strong>Licence:</strong> {e(VFX_LICENCE)}</p>
<p>{e(VFX_MADE)}</p>
</section>
"""
    page("tools/vfx-player/", "Sprite Sheet Player - Play 8 Free Game VFX Sprite Sheets Online | Anipixels", desc, body,
         og_image=("assets/packs/crisp-juice/cover.png", 630, 500), og_alt="Crisp Juice cover image",
         jsonld=tool_ld("vfx-player", "Anipixels VFX sprite sheet player", desc, "crisp-juice", "MultimediaApplication",
                        ["Play 8 free game VFX sprite sheets on a canvas", "Speed, loop, size and blend controls", "Light, dark, checker and custom backgrounds",
                         "Frame-by-frame scrubbing", "Shows grid, cell size and frame arithmetic"]),
         nav="tools", scripts=["data.js", "player.js"])


# ------------------------------------------------------------------ root files
def build_root_files(n_sounds):
    urls = [""] + ["packs/%s/" % p["slug"] for p in PACKS] + ["tools/%s/" % t["slug"] for t in TOOLS]
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
          + "".join(f"<url><loc>{SITE}{u}</loc><lastmod>{LASTMOD}</lastmod></url>\n" for u in urls) + "</urlset>\n")
    write("robots.txt", f"User-agent: *\nAllow: /\n\nSitemap: {SITE}sitemap.xml\n")
    write(".nojekyll", "")
    b = BUNDLE
    lines = ["# Anipixels", "",
             "> Anipixels makes royalty-free game asset packs (UI sound effects, music jingles, UI kits and VFX sprite sheets). "
             "The packs are sold on itch.io; each has a free sampler and a playable browser demo. This site describes each pack and offers "
             "three free browser tools built from the free samplers.", "",
             "All assets are generated procedurally by code written with an AI assistant (Claude). No AI image or audio generators, "
             "no recorded samples, no third-party art.",
             "Licence (all packs and samplers): use in any number of commercial and non-commercial projects, modify freely, credit not required; "
             "no reselling or redistribution of the files themselves.",
             f"Prices are in US dollars as listed on itch.io on {PRICE_DATE}.", "",
             "## Asset packs", ""]
    for p in PACKS:
        lines.append(f"- [{p['name']}]({SITE}packs/{p['slug']}/): {p['card']} Price {money(p['price'])}. "
                     f"Buy: {paid(p)} . Free sampler ({p['sampler_n']} {p['unit']}) and browser demo: {free(p)}")
    lines += ["", "## Bundle", "",
              f"- [{b['name']}]({b['url']}): all 8 packs above for {money(b['price'])} (the single prices add up to {money(b['singles'])}).",
              "", "## Free browser tools", "",
              f"- [UI sound board]({SITE}tools/ui-sound-board/): plays the {n_sounds} free sampler sounds from the five sound packs, with search, pack filter, volume and copy-file-name.",
              f"- [UI kit 9-slice preview]({SITE}tools/ui-kit-preview/): live resize of the Crisp Kit and Crisp Quest sampler pieces using their 9-slice borders, on light or dark.",
              f"- [VFX sprite sheet player]({SITE}tools/vfx-player/): plays the 8 Crisp Juice sampler sprite sheets on a canvas with speed, loop, blend and background controls.",
              "", "## Free browser games (on itch.io)", ""]
    for n, slug, d in GAMES:
        lines.append(f"- [{n}]({ITCH}{slug}): {d}")
    write("llms.txt", "\n".join(lines) + "\n")
    # 404 page: GitHub Pages serves it for any missing path, so its links are root-absolute.
    body = """<section class="hero">
<span class="pill">404</span>
<h1>Page not found</h1>
<p class="lead">That address does not exist on this site.</p>
<div class="btn-row"><a class="btn btn-primary" href="/">Go to the Anipixels home page</a></div>
</section>
"""
    page("404.html", "Page not found | Anipixels", "This page does not exist on the Anipixels site. Go to the home page for the asset packs and free tools.", body,
         og_image=("assets/og-home.png", 1200, 630), og_alt="The covers of the eight Anipixels asset packs", jsonld=None, absolute=True, noindex=True)


def main():
    verify_counts()
    shots = build_images()
    sound_data = build_sounds()
    kits = build_ui()
    sheets = build_vfx()
    n_sounds = build_sound_board(sound_data)
    assert n_sounds == 89
    assert sum(len(k["pieces"]) for k in kits.values()) == 109
    build_kit_preview(kits)
    build_vfx_player(sheets)
    for p in PACKS:
        build_pack(p, shots[p["slug"]])
    build_home(n_sounds)
    build_root_files(n_sounds)
    size = 0
    count = 0
    for d, dirs, files in os.walk(OUT):
        if ".git" in d.split(os.sep):
            continue
        for f in files:
            size += os.path.getsize(os.path.join(d, f)); count += 1
    print("built %d files, %.2f MB" % (count, size / 1e6))


if __name__ == "__main__":
    main()
