"""Static checks for the Anipixels site (no browser).   python _dev/check.py

 1. every local href/src in every HTML page resolves to a file (and its #anchor exists)
 2. every absolute URL anywhere in the site is on the allowed list
 3. titles, descriptions and canonicals are unique and well-formed; Open Graph tags present
 4. JSON-LD parses and carries the required Product / WebApplication fields, with prices matching packs.py
 5. sitemap.xml parses and every <loc> maps to a page; robots.txt and llms.txt are consistent with it
 6. content rule: everything under samples/ is byte-identical to a file inside a *_Free_Sampler.zip
    (the MP3 fallbacks are the only derived files and must match a sampler sound by name);
    no archives and no WAVs are in the site
"""
import hashlib, json, os, re, sys, zipfile
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packs import PACKS, BUNDLE, GAMES, SITE, ITCH

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.dirname(OUT)
problems = []


def bad(msg):
    problems.append(msg)
    print("  FAIL", msg)


ALLOWED = set()
for p in PACKS:
    ALLOWED |= {ITCH + p["slug"], ITCH + p["slug"] + "-free"}
ALLOWED.add(BUNDLE["url"])
ALLOWED |= {ITCH + g[1] for g in GAMES}
assert len(ALLOWED) == 24
TECH = ("https://schema.org", "http://www.sitemaps.org/schemas/sitemap/0.9", "http://www.w3.org/2000/svg")


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs, self.ids, self.meta, self.title, self.ld, self._in, self._buf = [], set(), {}, "", [], None, ""
        self.canonical, self.h1 = None, 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        for k in ("href", "src"):
            if k in a and tag != "meta":
                self.refs.append((tag, a[k]))
        if tag == "meta" and ("name" in a or "property" in a):
            self.meta[a.get("name") or a.get("property")] = a.get("content", "")
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href")
        if tag == "h1":
            self.h1 += 1
        if tag == "title":
            self._in = "title"
        if tag == "script" and a.get("type") == "application/ld+json":
            self._in, self._buf = "ld", ""
        for m in re.finditer(r"url\(([^)]+)\)", a.get("style", "")):
            self.refs.append(("style", m.group(1).strip("'\"")))

    def handle_data(self, data):
        if self._in == "title":
            self.title += data
        elif self._in == "ld":
            self._buf += data

    def handle_endtag(self, tag):
        if tag == "title" and self._in == "title":
            self._in = None
        if tag == "script" and self._in == "ld":
            self.ld.append(self._buf)
            self._in = None


def site_files():
    for d, dirs, files in os.walk(OUT):
        dirs[:] = [x for x in dirs if x != ".git"]
        for f in files:
            yield os.path.join(d, f)


pages = {}
for f in site_files():
    if f.endswith(".html"):
        pg = Page()
        pg.feed(open(f, encoding="utf-8").read())
        pages[os.path.relpath(f, OUT).replace(os.sep, "/")] = pg

# 1 + 2 (HTML)
n_local = n_out = 0
out_used = set()
for rel, pg in pages.items():
    here = os.path.dirname(os.path.join(OUT, rel))
    for tag, ref in pg.refs:
        if ref.startswith(("http://", "https://")):
            if ref.startswith(SITE):
                continue
            n_out += 1
            out_used.add(ref)
            if ref not in ALLOWED:
                bad("%s: outbound URL not allowed: %s" % (rel, ref))
            continue
        if ref.startswith(("mailto:", "javascript:", "data:", "//")):
            bad("%s: unexpected URL scheme %s" % (rel, ref))
            continue
        n_local += 1
        path, _, frag = ref.partition("#")
        if rel == "404.html":
            target = os.path.join(OUT, path.lstrip("/")) if path else os.path.join(OUT, rel)
            if path.endswith("/") or path == "":
                target = os.path.join(OUT, path.lstrip("/"), "index.html") if path else target
        else:
            if path.startswith("/"):
                bad("%s: root-absolute link breaks on file://: %s" % (rel, ref))
            target = os.path.normpath(os.path.join(here, path)) if path else os.path.join(OUT, rel)
        if os.path.isdir(target):
            bad("%s: link to a folder (does not work from file://): %s" % (rel, ref))
            continue
        if not os.path.isfile(target):
            bad("%s: missing file for %s" % (rel, ref))
            continue
        if not os.path.abspath(target).startswith(OUT):
            bad("%s: link leaves the site folder: %s" % (rel, ref))
        if frag and target.endswith(".html"):
            trel = os.path.relpath(target, OUT).replace(os.sep, "/")
            if frag not in pages[trel].ids:
                bad("%s: missing anchor %s" % (rel, ref))
print("1. local references checked: %d in %d HTML pages" % (n_local, len(pages)))

# 2 (all text files)
url_re = re.compile(r"https?://[^\s\"'<>)\\]+")
n_urls = 0
for f in site_files():
    if not f.endswith((".html", ".js", ".css", ".txt", ".xml", ".json", ".svg", ".md", ".py", ".mjs")):
        continue
    rel = os.path.relpath(f, OUT).replace(os.sep, "/")
    if rel.startswith("_dev/") or rel == "TESTING.md":
        continue                                       # tooling and notes, not site content
    for u in url_re.findall(open(f, encoding="utf-8").read()):
        u = u.rstrip(".,;:")
        n_urls += 1
        if u.startswith(SITE) or u.startswith(TECH):
            continue
        out_used.add(u)
        if u not in ALLOWED:
            bad("%s: URL not on the allowed list: %s" % (rel, u))
print("2. absolute URLs found in site content: %d; distinct outbound: %d, all on the allowed list of %d: %s; allowed but unused: %s"
      % (n_urls, len(out_used), len(ALLOWED), out_used <= ALLOWED, sorted(ALLOWED - out_used) or "none"))

# 3
titles, descs = {}, {}
for rel, pg in sorted(pages.items()):
    t, d = pg.title.strip(), pg.meta.get("description", "")
    if not t or not d:
        bad("%s: missing title or description" % rel)
    if t in titles:
        bad("%s: duplicate title with %s" % (rel, titles[t]))
    if d in descs:
        bad("%s: duplicate description with %s" % (rel, descs[d]))
    titles[t], descs[d] = rel, rel
    if not 50 <= len(d) <= 170:
        bad("%s: description is %d characters" % (rel, len(d)))
    if len(t) > 90:
        bad("%s: title is %d characters" % (rel, len(t)))
    if pg.h1 != 1:
        bad("%s: %d h1" % (rel, pg.h1))
    if rel == "404.html":
        continue
    want = SITE + rel[:-len("index.html")]
    if pg.canonical != want:
        bad("%s: canonical %s, expected %s" % (rel, pg.canonical, want))
    for k in ("og:title", "og:description", "og:url", "og:image", "og:type", "og:image:alt"):
        if not pg.meta.get(k):
            bad("%s: missing %s" % (rel, k))
    img = pg.meta.get("og:image", "")
    if not img.startswith(SITE) or not os.path.isfile(os.path.join(OUT, img[len(SITE):])):
        bad("%s: og:image does not resolve: %s" % (rel, img))
    if pg.meta.get("og:url") != want:
        bad("%s: og:url %s" % (rel, pg.meta.get("og:url")))
print("3. %d pages: unique titles %d, unique descriptions %d" % (len(pages), len(titles), len(descs)))

# 4
n_prod = n_app = n_faq = 0
for rel, pg in sorted(pages.items()):
    for raw in pg.ld:
        try:
            data = json.loads(raw)
        except Exception as ex:
            bad("%s: JSON-LD does not parse: %s" % (rel, ex))
            continue
        if data.get("@context") != "https://schema.org":
            bad("%s: JSON-LD @context" % rel)
        for node in data.get("@graph", [data]):
            if node["@type"] == "Product":
                n_prod += 1
                slug = rel.split("/")[1]
                p = [x for x in PACKS if x["slug"] == slug][0]
                o = node["offers"]
                ok = (node["name"] == p["name"] and node["description"] and node["image"][0] == SITE + "assets/packs/%s/cover.png" % slug
                      and o["@type"] == "Offer" and o["price"] == p["price"] and o["priceCurrency"] == "USD" and o["url"] == ITCH + slug)
                if not ok:
                    bad("%s: Product JSON-LD fields wrong: %s" % (rel, json.dumps(node)[:200]))
                if not re.fullmatch(r"\d+\.\d\d", o["price"]):
                    bad("%s: price format %s" % (rel, o["price"]))
            elif node["@type"] == "WebApplication":
                n_app += 1
                if not (node["name"] and node["url"] == SITE + rel[:-len("index.html")] and node["offers"]["price"] == "0"
                        and node["offers"]["priceCurrency"] == "USD" and node["applicationCategory"] and node["operatingSystem"]):
                    bad("%s: WebApplication JSON-LD fields wrong" % rel)
            elif node["@type"] == "FAQPage":
                n_faq += 1
                html_text = open(os.path.join(OUT, rel), encoding="utf-8").read()
                import html as _h
                for q in node["mainEntity"]:
                    if _h.escape(q["name"]) not in html_text or _h.escape(q["acceptedAnswer"]["text"]) not in html_text:
                        bad("%s: FAQ JSON-LD entry is not visible on the page: %s" % (rel, q["name"]))
    if rel.startswith("packs/") and not any('"Product"' in r for r in pg.ld):
        bad("%s: no Product JSON-LD" % rel)
    if rel.startswith("tools/") and not any('"WebApplication"' in r for r in pg.ld):
        bad("%s: no WebApplication JSON-LD" % rel)
print("4. JSON-LD blocks parsed: %d (Product %d, WebApplication %d, FAQPage %d)" % (sum(len(p.ld) for p in pages.values()), n_prod, n_app, n_faq))

# 5
ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
tree = ET.parse(os.path.join(OUT, "sitemap.xml"))
locs = [x.text for x in tree.getroot().findall("s:url/s:loc", ns)]
for loc in locs:
    if not loc.startswith(SITE) or not os.path.isfile(os.path.join(OUT, loc[len(SITE):], "index.html")):
        bad("sitemap: %s has no page" % loc)
indexable = sorted(SITE + r[:-len("index.html")] for r in pages if r != "404.html")
if sorted(locs) != indexable:
    bad("sitemap does not list exactly the indexable pages")
robots = open(os.path.join(OUT, "robots.txt")).read()
if "Disallow" in robots or "Allow: /" not in robots or SITE + "sitemap.xml" not in robots:
    bad("robots.txt")
llms = open(os.path.join(OUT, "llms.txt"), encoding="utf-8").read()
for p in PACKS:
    for needle in (SITE + "packs/%s/" % p["slug"], ITCH + p["slug"] + " ", ITCH + p["slug"] + "-free", "$" + p["price"]):
        if needle not in llms:
            bad("llms.txt lacks %s" % needle)
if not os.path.isfile(os.path.join(OUT, ".nojekyll")):
    bad(".nojekyll missing")
print("5. sitemap.xml parsed: %d URLs, all map to pages; robots.txt allows all; llms.txt lists %d packs" % (len(locs), len(PACKS)))

# 6
sampler = {}          # sha1 -> member name, for every file in every released free sampler
wav_stems = {}
for p in PACKS:
    zpath = os.path.join(SRC, p["folder"], "release", p["zip"])
    assert zpath.endswith("_Free_Sampler.zip")
    with zipfile.ZipFile(zpath) as z:
        for n in z.namelist():
            if n.endswith("/"):
                continue
            sampler[hashlib.sha1(z.read(n)).hexdigest()] = n
            if n.endswith(".wav"):
                wav_stems.setdefault(p["slug"], set()).add(os.path.basename(n)[:-4])
counts = {}
for f in site_files():
    rel = os.path.relpath(f, OUT).replace(os.sep, "/")
    ext = rel.rsplit(".", 1)[-1].lower()
    if ext in ("zip", "wav", "unitypackage", "7z", "rar", "tscn", "gd"):
        bad("file type that should not be in the site: %s" % rel)
    if not rel.startswith("samples/"):
        continue
    counts[ext] = counts.get(ext, 0) + 1
    if ext == "mp3":
        slug, stem = rel.split("/")[2], os.path.basename(rel)[:-4]
        if stem not in wav_stems.get(slug, ()):
            bad("mp3 without a sampler sound: %s" % rel)
        continue
    if hashlib.sha1(open(f, "rb").read()).hexdigest() not in sampler:
        bad("not byte-identical to any free-sampler file: %s" % rel)
want = {"ogg": 89, "mp3": 89, "png": 109 + 8, "json": 3, "txt": 8}
if counts != want:
    bad("samples/ holds %s, expected %s" % (counts, want))
print("6. samples/: %s; every non-MP3 file is byte-identical to a free-sampler file; no archives or WAVs in the site" % counts)

print("\nSTATIC CHECKS PASSED" if not problems else "\nSTATIC CHECKS FAILED: %d" % len(problems))
sys.exit(1 if problems else 0)
