# /// script
# requires-python = ">=3.12"
# dependencies = ["pyyaml", "qrcode"]
# ///
#
# --- How to run ---
# uv run scripts/build.py
# python3 -m http.server 8765 --directory dist --bind 127.0.0.1

from __future__ import annotations

import io
import os
import re
import shutil
from pathlib import Path
from html import escape

import qrcode
import qrcode.image.svg
import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "links.yaml"
ASSETS_DIR = ROOT / "assets"
CNAME_FILE = ROOT / "CNAME"
DIST_DIR = ROOT / "dist"

# Icon paths follow the same convention as year-in-review's profile-link
# strip: 24x24 viewBox, stroke currentColor width 2 unless it's a brand
# mark (fill currentColor). Brand marks (linkedin, github) are reused
# verbatim from year-in-review for visual continuity across gkt.sh sites.
ICONS: dict[str, str] = {
    "website": '<path fill="none" stroke="currentColor" stroke-width="2" d="M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm0 0c2.4 2.4 3.6 5.4 3.6 9S14.4 18.6 12 21m0-18C9.6 5.4 8.4 8.4 8.4 12s1.2 6.6 3.6 9M3.6 9h16.8M3.6 15h16.8"/>',
    "institution": '<path fill="none" stroke="currentColor" stroke-width="2" d="M4 21h16M6 21V9l6-4 6 4v12M9 21v-6h6v6M8 11h.01M12 11h.01M16 11h.01"/>',
    "lab": '<path fill="none" stroke="currentColor" stroke-width="2" d="M5 20h14M7 20V8h10v12M9 8V5h6v3M10 12h4M10 16h4M17 11h2v9M5 11h2v9"/>',
    "scholar": '<path fill="none" stroke="currentColor" stroke-width="2" d="M4 7 12 3l8 4-8 4-8-4Zm3 4v5c0 1.7 2.2 3 5 3s5-1.3 5-3v-5M20 8v7"/>',
    "linkedin": '<path fill="currentColor" d="M6.9 8.8H3.7V20h3.2V8.8ZM5.3 4a1.9 1.9 0 1 0 0 3.8 1.9 1.9 0 0 0 0-3.8ZM20.3 13.8c0-3.4-1.8-5.2-4.4-5.2-1.9 0-2.8 1.1-3.3 1.8V8.8H9.5V20h3.2v-5.9c0-1.6.3-3 2.2-3 1.8 0 1.9 1.7 1.9 3.1V20H20v-6.2h.3Z"/>',
    "github": '<path fill="currentColor" d="M12 .9a11.1 11.1 0 0 0-3.5 21.6c.6.1.8-.2.8-.6v-2c-3.2.7-3.9-1.4-3.9-1.4-.5-1.3-1.3-1.7-1.3-1.7-1-.7.1-.7.1-.7 1.1.1 1.8 1.2 1.8 1.2 1 .1.6 2.1 3.4 1.5.1-.8.4-1.3.7-1.6-2.6-.3-5.3-1.3-5.3-5.5 0-1.2.4-2.2 1.2-3-.1-.3-.5-1.5.1-3 0 0 1-.3 3.2 1.2a11 11 0 0 1 5.8 0c2.2-1.5 3.2-1.2 3.2-1.2.6 1.5.2 2.7.1 3 .8.8 1.2 1.8 1.2 3 0 4.2-2.7 5.2-5.3 5.5.4.4.8 1.1.8 2.2v3.2c0 .4.2.7.8.6A11.1 11.1 0 0 0 12 .9Z"/>',
    "id-badge": '<path fill="none" stroke="currentColor" stroke-width="2" d="M4 4h16v16H4V4Zm4 5a2 2 0 1 0 4 0 2 2 0 0 0-4 0ZM6.5 17c.4-1.8 2.3-3 5-3M14 8h4M14 11h4M14 14h3.5"/>',
    "profile": '<path fill="none" stroke="currentColor" stroke-width="2" d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm-6.5 8a6.5 6.5 0 0 1 13 0"/>',
    "library": '<path fill="none" stroke="currentColor" stroke-width="2" d="M4 5.5c2-1 5-1 7 .5v14c-2-1.5-5-1.5-7-.5V5.5Zm16 0c-2-1-5-1-7 .5v14c2-1.5 5-1.5 7-.5V5.5Z"/>',
    "search": '<path fill="none" stroke="currentColor" stroke-width="2" d="M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14Zm6.3 12.3L21 20"/>',
    "music": '<path fill="none" stroke="currentColor" stroke-width="2" d="M9 18V5l10-2v13M9 18a3 3 0 1 1-6 0 3 3 0 0 1 6 0Zm10-2a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"/>',
    "clipboard": '<path fill="none" stroke="currentColor" stroke-width="2" d="M9 4h6a1 1 0 0 1 1 1v1H8V5a1 1 0 0 1 1-1Zm-3 2h12v14a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V6Zm3 6h6M9 15h6"/>',
    "calendar": '<path fill="none" stroke="currentColor" stroke-width="2" d="M7 4v3M17 4v3M4 9h16M5 7h14a1 1 0 0 1 1 1v11a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V8a1 1 0 0 1 1-1Z"/>',
    "phone": '<path fill="none" stroke="currentColor" stroke-width="2" d="M6 4h3l2 5-2 1a11 11 0 0 0 5 5l1-2 5 2v3a1 1 0 0 1-1 1A15 15 0 0 1 5 5a1 1 0 0 1 1-1Z"/>',
    "email": '<path fill="none" stroke="currentColor" stroke-width="2" d="M4 5h16v14H4V5Zm0 0 8 7 8-7"/>',
    "document": '<path fill="none" stroke="currentColor" stroke-width="2" d="M6 3h9l3 3v15H6V3Zm9 0v3h3M9 11h6M9 15h6"/>',
    "book": '<path fill="none" stroke="currentColor" stroke-width="2" d="M6 4h9a3 3 0 0 1 3 3v13H9a3 3 0 0 0-3 3V4Zm3 4h6M9 11h6"/>',
    "magazine": '<path fill="none" stroke="currentColor" stroke-width="2" d="M3 5h13v13a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5Zm13 0h5v11a2 2 0 0 1-2 2h-3M7 8h5M7 11h5M7 14h3"/>',
    "link": '<path fill="none" stroke="currentColor" stroke-width="2" d="M9 15 15 9M10 6l1-1a4 4 0 1 1 6 6l-1 1M14 18l-1 1a4 4 0 1 1-6-6l1-1"/>',
}

CSS = """
:root {
  --bg: #f6f4ef;
  --paper: #fffdf8;
  --panel: #ffffff;
  --ink: #202124;
  --muted: #626866;
  --line: #d8d4ca;
  --accent: #1f6f78;
  --accent-dark: #164e55;
  --clay: #8b4a2f;
  --soft: #ece8df;
  --shadow: 0 18px 42px rgba(32, 33, 36, 0.08);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
main {
  width: min(720px, calc(100% - 32px));
  margin: 0 auto;
  padding: 48px 0 80px;
}
header.hero {
  text-align: center;
  margin-bottom: 40px;
}
header.hero .avatar {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid var(--paper);
  box-shadow: var(--shadow);
}
header.hero h1 {
  font-size: clamp(28px, 5vw, 40px);
  margin: 0 0 8px;
}
header.hero p {
  color: var(--muted);
  margin: 0;
  font-size: 16px;
}
section.category {
  margin-bottom: 32px;
}
section.category h2 {
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  margin: 0 0 12px;
}
ul.links {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
a.link-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 12px;
  box-shadow: var(--shadow);
  text-decoration: none;
  color: var(--ink);
  transition: border-color 0.15s ease, transform 0.15s ease;
}
a.link-card:hover {
  border-color: var(--accent);
  transform: translateY(-1px);
}
a.link-card svg {
  flex: none;
  width: 22px;
  height: 22px;
  color: var(--accent);
}
.link-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.link-text .name {
  font-weight: 600;
  font-size: 16px;
}
.link-text .desc {
  color: var(--muted);
  font-size: 14px;
  margin-top: 2px;
}

/* Tiled layout: a grid of cards, mirroring the year-card grid used on
   year-in-review's root page, instead of a single-column list. */
ul.links.tiled {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}
a.link-card.tiled {
  flex-direction: column;
  text-align: center;
  justify-content: center;
  gap: 10px;
  padding: 20px 14px;
  height: 100%;
}
a.link-card.tiled svg {
  width: 28px;
  height: 28px;
}
@media (max-width: 860px) {
  ul.links.tiled {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 600px) {
  ul.links.tiled {
    grid-template-columns: 1fr;
  }
}

.identity {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
button.qr {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  font: inherit;
  color: var(--muted);
}
button.qr svg {
  width: 90px;
  height: 90px;
  background: #fff;
  padding: 6px;
  border-radius: 8px;
  border: 1px solid var(--line);
  box-shadow: var(--shadow);
}
button.qr .qr-caption {
  font-size: 11px;
}
/* Fullscreen mode: fill the whole screen with a large, high-contrast
   QR code so it can be scanned from across a conference room. */
button.qr:fullscreen {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
}
button.qr:fullscreen svg {
  width: min(80vw, 80vh);
  height: min(80vw, 80vh);
  border: none;
  box-shadow: none;
}
button.qr:fullscreen .qr-caption {
  display: none;
}

footer {
  text-align: center;
  color: var(--muted);
  font-size: 13px;
  margin-top: 48px;
}
footer a { color: var(--accent); }
"""


def render_qr_svg(url: str) -> str:
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=2)
    buf = io.BytesIO()
    img.save(buf)
    svg = buf.getvalue().decode("utf-8")
    svg = svg.split("?>", 1)[1].lstrip()  # drop the <?xml ...?> declaration
    svg = re.sub(r'\s(width|height)="[^"]*"', "", svg)  # let CSS control size
    return svg


def render_link_card(link: dict, tiled: bool) -> str:
    icon_svg = ICONS.get(link.get("icon", ""), ICONS["link"])
    name = escape(link["name"])
    desc = escape(link.get("description", ""))
    url = escape(link["url"], quote=True)
    card_class = "link-card tiled" if tiled else "link-card"
    return f"""      <li>
        <a class="{card_class}" href="{url}">
          <svg viewBox="0 0 24 24" aria-hidden="true">{icon_svg}</svg>
          <span class="link-text">
            <span class="name">{name}</span>
            <span class="desc">{desc}</span>
          </span>
        </a>
      </li>"""


def build() -> None:
    data = yaml.safe_load(DATA_FILE.read_text(encoding="utf-8"))
    site = data["site"]
    categories = data["categories"]
    links = data["links"]

    tiled = site.get("layout", "list") == "tiled"
    links_class = "links tiled" if tiled else "links"

    sections = []
    for cat in categories:
        cat_links = [link for link in links if cat["key"] in link.get("tags", [])]
        if not cat_links:
            continue
        cards = "\n".join(render_link_card(link, tiled) for link in cat_links)
        sections.append(f"""    <section class="category">
      <h2>{escape(cat["label"])}</h2>
      <ul class="{links_class}">
{cards}
      </ul>
    </section>""")

    sections_html = "\n".join(sections)

    photo = site.get("photo")
    logo = site.get("logo")
    avatar_html = (
        f'<img class="avatar" src="{escape(photo, quote=True)}" alt="{escape(site["title"])}">'
        if photo
        else ""
    )
    favicon_html = (
        f'<link rel="icon" type="image/png" href="{escape(logo, quote=True)}">' if logo else ""
    )

    # Set by .github/workflows/deploy.yml at deploy time; absent for local
    # builds, since a local build isn't a deployment.
    last_updated = os.environ.get("LAST_UPDATED")
    last_updated_html = f"<p>Last updated on {escape(last_updated)}.</p>" if last_updated else ""

    site_url = site.get("url")
    qr_html = ""
    qr_script = ""
    if site_url:
        qr_svg = render_qr_svg(site_url)
        qr_html = f"""<button type="button" class="qr" id="qr-trigger" aria-label="Show QR code full screen for scanning">
          {qr_svg}
          <span class="qr-caption">Tap/click to enlarge</span>
        </button>"""
        qr_script = """<script>
    (() => {
      const btn = document.getElementById("qr-trigger");
      if (!btn || !btn.requestFullscreen) return;
      btn.addEventListener("click", () => { btn.requestFullscreen(); });
    })();
  </script>"""

    identity_html = f"""<div class="identity">
      {avatar_html}
      {qr_html}
      </div>""" if (avatar_html or qr_html) else ""

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(site["title"])}</title>
  {favicon_html}
  <style>{CSS}</style>
</head>
<body>
  <main>
    <header class="hero">
      {identity_html}
      <h1>{escape(site["title"])}</h1>
      <p>{escape(site["tagline"])}</p>
    </header>
{sections_html}
    <footer>
      <p>&copy; 2026&ndash;Present George K. Thiruvathukal.</p>
      <p>Built from <a href="https://github.com/gkthiruvathukal/keylinks">this repo</a>.</p>
      {last_updated_html}
    </footer>
  </main>
  {qr_script}
</body>
</html>
"""

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    (DIST_DIR / "index.html").write_text(html, encoding="utf-8")

    if ASSETS_DIR.exists():
        dist_assets = DIST_DIR / "assets"
        if dist_assets.exists():
            shutil.rmtree(dist_assets)
        shutil.copytree(ASSETS_DIR, dist_assets)

    if CNAME_FILE.exists():
        shutil.copy(CNAME_FILE, DIST_DIR / "CNAME")

    print(f"Wrote {DIST_DIR / 'index.html'}")


if __name__ == "__main__":
    build()
