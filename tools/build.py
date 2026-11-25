#!/usr/bin/env python3
"""Build andrewsteck.github.io.

    python3 tools/build.py        (run from anywhere)

Reads   content.toml      everything that changes: bio, links, papers, teaching
        tools/style.css   the design
        fonts/            the typeface (referred to by style.css)
Writes  index.html        the whole site, one page
        research.html     redirects, so old links to /research and /code
        code.html         still reach the home page

Needs Python 3.11 or later and nothing else. See README.md for the routine.
"""
import datetime
import html
import os
import re
import sys
import tomllib

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)

# The Newsreader font files are in fonts/ and are declared at the top of style.css.
# This line only asks the browser to fetch the main one early, so text appears in it sooner.
FONTS = '<link rel="preload" href="fonts/newsreader-latin.woff2" as="font" type="font/woff2" crossorigin>'

# Runs before the page paints: applies a remembered light or dark choice, if there is one.
THEME_HEAD = """<script>
(function () { try { var t = localStorage.getItem('theme'); if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t); } catch (err) {} })();
</script>"""

# The button follows the system setting until it is pressed. Pressing it back to the
# system's own setting forgets the choice, so the page is automatic again.
# Without JavaScript the button stays hidden and the page follows the system setting.
THEME_BUTTON = """<script>
(function () {
  var root = document.documentElement, btn = document.getElementById('theme');
  var mq = window.matchMedia('(prefers-color-scheme: dark)');
  function system() { return mq.matches ? 'dark' : 'light'; }
  function current() { return root.getAttribute('data-theme') || system(); }
  function label() { btn.textContent = current() === 'dark' ? 'Light mode' : 'Dark mode'; }
  btn.hidden = false;
  btn.addEventListener('click', function () {
    var next = current() === 'dark' ? 'light' : 'dark';
    try {
      if (next === system()) { root.removeAttribute('data-theme'); localStorage.removeItem('theme'); }
      else { root.setAttribute('data-theme', next); localStorage.setItem('theme', next); }
    } catch (err) { root.setAttribute('data-theme', next); }
    label();
  });
  if (mq.addEventListener) mq.addEventListener('change', label);
  label();
})();
</script>"""


def e(s):
    return html.escape(str(s), quote=True)


def is_local(url):
    return not re.match(r"^([a-z][a-z0-9+.-]*:|#|//)", url, re.I)


# --------------------------------------------------------------------------- checks

def check(c, css):
    """Return (errors, warnings, notes). Errors stop the build."""
    errors, warnings, notes = [], [], []
    for key in ("name", "role", "description", "url", "photo", "cv", "email", "bio", "interests", "section", "paper"):
        if key not in c:
            errors.append("content.toml has no '%s'." % key)
    if errors:
        return errors, warnings, notes

    ids = [s.get("id") for s in c["section"]]
    for n, p in enumerate(c["paper"], 1):
        name = "paper %d (%s)" % (n, p.get("title", "no title"))
        for key in ("section", "title", "year"):
            if key not in p:
                errors.append("%s has no '%s'." % (name, key))
        if p.get("section") not in ids:
            errors.append("%s is in section '%s', which is not one of: %s." % (name, p.get("section"), ", ".join(ids)))
        if "journal" in p and "status" in p:
            warnings.append("%s has both a journal and a status; only the journal is shown." % name)
        for link in p.get("links", []):
            if "label" not in link or "url" not in link:
                errors.append("%s has a link without a label or a url." % name)
            elif is_local(link["url"]) and not os.path.exists(os.path.join(ROOT, link["url"])):
                warnings.append("%s links to '%s', which is not in the site folder." % (name, link["url"]))
    for key in ("photo", "cv"):
        if is_local(c[key]) and not os.path.exists(os.path.join(ROOT, c[key])):
            warnings.append("%s = '%s' is not in the site folder." % (key, c[key]))

    known = c.get("coauthors", {})
    for name, v in known.items():
        if not isinstance(v, str) and not (isinstance(v, dict) and v.get("url")):
            errors.append("[coauthors] entry for %s needs an address: either \"...\" or { url = \"...\" }." % name)
        elif isinstance(v, dict) and bool(v.get("also")) != bool(v.get("also_url")):
            errors.append("[coauthors] entry for %s needs both 'also' (the label) and 'also_url', or neither." % name)
    unlinked = sorted({a for p in c["paper"] for a in p.get("authors", []) if a not in known})
    if unlinked:
        notes.append("co-authors shown without a link: " + ", ".join(unlinked))
    used = {a for p in c["paper"] for a in p.get("authors", [])}
    unused = sorted(set(known) - used)
    if unused:
        notes.append("co-author links not used by any paper: " + ", ".join(unused))

    # The dark palette appears twice in style.css and must be the same both times.
    blocks = re.findall(r'\[data-theme="(?:light|dark)"\]\)?\s*\{([^}]*)\}', css)
    if len(blocks) != 2 or " ".join(blocks[0].split()) != " ".join(blocks[1].split()):
        errors.append("tools/style.css: the two dark-palette blocks differ (or one is missing). Make them identical.")
    return errors, warnings, notes


# --------------------------------------------------------------------------- page

def author(name, links):
    """A co-author's name, linked if content.toml has an entry for it.

    The entry is either one address, or a table with url and, optionally, a second
    address shown in brackets after the name:  { url = "...", also = "Emory", also_url = "..." }
    """
    v = links.get(name)
    if v is None:
        return e(name)
    if isinstance(v, str):
        return '<a href="%s">%s</a>' % (e(v), e(name))
    s = '<a href="%s">%s</a>' % (e(v["url"]), e(name))
    if v.get("also_url"):
        s += ' (<a href="%s">%s</a>)' % (e(v["also_url"]), e(v.get("also", "also")))
    return s


def authors(p, links):
    names = p.get("authors", [])
    if not names:
        return ""
    parts = [author(n, links) for n in names]
    if len(parts) == 1:
        s = parts[0]
    elif len(parts) == 2:
        s = parts[0] + " and " + parts[1]
    else:
        s = ", ".join(parts[:-1]) + ", and " + parts[-1]
    return "with " + s


def venue(p):
    if p.get("journal"):
        detail = ", " + e(p["journal_detail"]) if p.get("journal_detail") else ""
        return "<em>%s</em>%s" % (e(p["journal"]), detail)
    return e(p.get("status", ""))


def row(p, c):
    meta = [x for x in [authors(p, c.get("coauthors", {})), venue(p)] + [e(n) for n in p.get("notes", [])] if x]
    out = ['<div class="row"><div class="yr">%s</div><div>' % e(p["year"]), "<h3>%s</h3>" % e(p["title"])]
    if meta:
        out.append('<p class="m">%s</p>' % "<br>".join(meta))
    if p.get("links"):
        out.append('<div class="l">%s</div>' % "".join('<a href="%s">%s</a>' % (e(l["url"]), e(l["label"])) for l in p["links"]))
    if p.get("abstract", "").strip():
        out.append("<details><summary>Abstract</summary><p>%s</p></details>" % e(" ".join(p["abstract"].split())))
    if c.get("show_topics", True) and p.get("topics"):
        out.append('<p class="tags caps">%s</p>' % " · ".join(e(t) for t in p["topics"]))
    out.append("</div></div>")
    return "".join(out)


def email_item(address):
    """The email line of the sidebar, written so that simple address harvesters miss it.

    The page source holds the address only in pieces and as "name(at)site(dot)ca".
    EMAIL_SCRIPT puts the pieces together in the reader's browser, so a person sees
    the normal address and can click it. Without JavaScript the (at)/(dot) text stays.
    """
    user, domain = address.split("@")
    shown = address.replace("@", "(at)").replace(".", "(dot)")
    return '<li><a class="em" data-u="%s" data-d="%s">%s</a></li>' % (e(user), e(domain), e(shown))


EMAIL_SCRIPT = """<script>
document.querySelectorAll('a.em').forEach(function (a) {
  var m = a.dataset.u + String.fromCharCode(64) + a.dataset.d;
  a.href = 'mailto:' + m; a.textContent = m;
});
</script>"""


def render(c, css, updated):
    name = e(c["name"])
    side = ['<li class="cv"><a class="caps" href="%s">Curriculum vitae (PDF)</a></li>' % e(c["cv"]),
            email_item(c["email"])]
    side += ['<li><a href="%s">%s</a></li>' % (e(l["url"]), e(l["label"])) for l in c.get("link", [])]

    jump, main = [], []
    for s in c["section"]:
        papers = [p for p in c["paper"] if p["section"] == s["id"]]
        if not papers:
            continue
        jump.append((s["id"], s["title"]))
        main.append('<h2 id="%s"><span>%s</span></h2>' % (e(s["id"]), e(s["title"])))
        main += [row(p, c) for p in papers]
    t = c.get("teaching")
    if t and t.get("courses"):
        jump.append(("teaching", "Teaching"))
        main.append('<h2 id="teaching"><span>Teaching</span></h2>')
        if t.get("where"):
            main.append('<p class="where">%s</p>' % e(t["where"]))
        main.append('<ul class="courses">%s</ul>' % "".join("<li>%s</li>" % e(x) for x in t["courses"]))
    if c.get("address"):
        jump.append(("contact", "Contact"))
        main.append('<h2 id="contact"><span>Contact</span></h2>')
        main.append('<div class="contact">%s</div>' % "".join(
            "<div><b>%s</b>%s</div>" % (e(a["title"]), "<br>".join(e(x) for x in a["lines"])) for a in c["address"]))

    nav = "".join('<a class="caps" href="#%s">%s</a>' % (e(k), e(label)) for k, label in jump)
    photo_url = c["url"].rstrip("/") + "/" + c["photo"] if is_local(c["photo"]) else c["photo"]
    return f"""<!doctype html>
<!-- Generated by tools/build.py from content.toml. Do not edit this file by hand: edit content.toml and run the script. -->
<html lang="en-CA">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{name}</title>
<meta name="description" content="{e(c["description"])}">
<meta name="color-scheme" content="light dark">
<link rel="canonical" href="{e(c["url"])}">
<meta property="og:type" content="website">
<meta property="og:title" content="{name}">
<meta property="og:description" content="{e(c["description"])}">
<meta property="og:url" content="{e(c["url"])}">
<meta property="og:image" content="{e(photo_url)}">
{FONTS}
<style>
{css}</style>
{THEME_HEAD}
</head>
<body>
<div class="wrap">
<aside>
  <img src="{e(c["photo"])}" alt="{name}">
  <h1>{name}</h1>
  <p class="role caps">{"<br>".join(e(r) for r in c["role"])}</p>
  <ul class="links">{"".join(side)}</ul>
  <nav>{nav}</nav>
  <div class="bottom">
    <button id="theme" type="button" hidden>Dark mode</button>
    <p class="caps">Updated {e(updated)}</p>
  </div>
</aside>
<main>
  <p class="lead">{" ".join(c["bio"].split())}</p>
  <p class="int"><b>Research interests:</b> {", ".join(e(i) for i in c["interests"])}.</p>
  {chr(10).join(main)}
  <p class="upd caps">Updated {e(updated)}</p>
</main>
</div>
{THEME_BUTTON}
{EMAIL_SCRIPT}
</body>
</html>
"""


def redirect(c, title, target):
    """A page that forwards an address of the old site to the home page."""
    name = e(c["name"])
    return f"""<!doctype html>
<!-- Generated by tools/build.py. The site is now one page; this keeps old links to this address working. -->
<html lang="en-CA">
<head>
<meta charset="utf-8">
<title>{e(title)} · {name}</title>
<link rel="canonical" href="{e(c["url"])}">
<meta http-equiv="refresh" content="0; url={e(target)}">
</head>
<body><p>This page is now part of <a href="{e(target)}">the home page</a>.</p></body>
</html>
"""


def main():
    with open(os.path.join(ROOT, "content.toml"), "rb") as f:
        try:
            c = tomllib.load(f)
        except tomllib.TOMLDecodeError as err:
            sys.exit("content.toml could not be read: %s\nNothing was written." % err)
    with open(os.path.join(TOOLS, "style.css"), encoding="utf-8") as f:
        css = f.read()

    errors, warnings, notes = check(c, css)
    for w in warnings:
        print("warning:", w)
    for n in notes:
        print("note:", n)
    if errors:
        for err in errors:
            print("error:", err)
        sys.exit("Nothing was written. Fix the errors above and run the script again.")

    updated = c.get("updated") or datetime.date.today().strftime("%B %Y")
    first = next(s["id"] for s in c["section"] if any(p["section"] == s["id"] for p in c["paper"]))
    pages = (("index.html", render(c, css, updated)),
             ("research.html", redirect(c, "Research", "./#" + first)),   # the old research page
             ("code.html", redirect(c, "Code", "./")))                    # the old code page, dropped November 2026
    for rel, text in pages:
        with open(os.path.join(ROOT, rel), "w", encoding="utf-8") as f:
            f.write(text)
        print("wrote", rel)
    print("%d papers in %d sections; page dated %s." % (len(c["paper"]), len({p["section"] for p in c["paper"]}), updated))


if __name__ == "__main__":
    main()
