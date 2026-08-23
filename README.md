# link collection

A serverless, git-backed link-in-bio page. All content lives in `links.yaml`;
a small Python script renders it to a single static `dist/index.html`. No
login, no database, no JavaScript framework — updates happen by editing YAML
and committing.

## Requirements

- [`uv`](https://docs.astral.sh/uv/) (manages the Python + dependency for the
  build script automatically — nothing to `pip install` by hand)

## Update and build

1. Edit `links.yaml` (see schema below).
2. Build the site:

   ```bash
   uv run scripts/build.py
   ```

   This regenerates `dist/index.html` and copies `assets/` into `dist/assets/`.

3. Preview locally:

   ```bash
   python3 -m http.server 8765 --directory dist --bind 127.0.0.1
   ```

   Then open <http://127.0.0.1:8765/>. Leave the server running — rerunning
   the build in step 2 updates `dist/index.html` in place, so a browser
   refresh picks up changes without restarting the server.

## `links.yaml` schema

```yaml
site:
  title: "..."          # page title / H1
  tagline: "..."        # subtitle under the title
  logo: "assets/logo.png"    # optional, used as the favicon
  photo: "assets/photo.jpg"  # optional, used as the circular avatar
  url: "https://keylinks.gkt.sh/"  # optional, canonical URL; generates
                                    # the QR code next to the avatar if set
  layout: "tiled"        # "list" (one link per row) or "tiled" (card grid)

categories:
  - key: home            # short identifier, matched against link tags
    label: "Home"        # human-readable section heading

links:
  - name: "..."          # link title
    url: "..."           # href (supports tel:, mailto:, https://, etc.)
    description: "..."   # one line shown under the name
    icon: website         # key into the ICONS dict in scripts/build.py
    tags: [home]          # one or more category keys — a link with
                           # multiple tags appears in every matching section
```

- **Adding a link**: append an entry under `links:` with at least one tag
  matching an existing category `key`.
- **Adding a category**: append `{key, label}` under `categories:`. Order in
  the list controls the order sections appear on the page. A category with
  no matching links is simply skipped.
- **Multi-category links**: give a link more than one tag (e.g.
  `tags: [app, music]`) to have it appear in both sections. Nothing else
  needs to change — the build script filters links per category by tag
  membership, so the same entry naturally shows up wherever it's tagged.
- **Icons**: `icon` must match a key in the `ICONS` dict at the top of
  `scripts/build.py`. An unrecognized or missing key silently falls back to
  a generic chain-link icon — check `scripts/build.py` if a new link's icon
  isn't showing what you expect. To add a new icon, add an inline SVG
  `<path>` entry to `ICONS` (24x24 viewBox, `stroke="currentColor"
  stroke-width="2"` for line icons, `fill="currentColor"` for brand marks).
- **Layout**: `site.layout: tiled` gives a responsive card grid (capped at 2
  columns at ≤860px, 1 column at ≤600px for phones/small tablets); `list`
  gives a single-column list of rows. Toggle it in `links.yaml` — no code
  changes needed.
- **QR code**: set `site.url` to the page's own canonical URL and a QR
  code encoding it renders next to the avatar. It's a real `<button>`, not
  a link — clicking it calls the browser's Fullscreen API so the code
  fills the whole screen at high contrast, handy for projecting at a
  conference so people can scan it from across the room. Omit `site.url`
  to skip rendering it. Generated at build time with the `qrcode` package
  (pure Python, no Pillow needed) as inline SVG — no runtime dependency,
  no external QR-generation service called.

## Project structure

```
links.yaml                    content: site config, categories, links
scripts/build.py               the entire build — reads links.yaml, writes dist/
assets/                         source images (logo, photo) copied into dist/ on build
CNAME                           custom domain for GitHub Pages, copied into dist/ on build
.github/workflows/deploy.yml    builds and deploys dist/ to GitHub Pages on push to main
dist/                           generated output (not source of truth — rebuild, don't hand-edit)
```

## Design

Visual language (colors, spacing, typography tokens) and several icons are
carried over from the [`year-in-review`](../year-in-review) repo's
`DESIGN.md` for continuity across `gkt.sh` properties.

## Deployment

Deployed via GitHub Pages at `keylinks.gkt.sh`. `.github/workflows/deploy.yml`
runs `uv run scripts/build.py` on every push to `main` and publishes `dist/`
(which includes the copied `CNAME`) using `actions/deploy-pages`. No manual
deploy step — pushing to `main` is the deploy.

The footer shows a copyright line, a "Built from this repo" link, and a
"Last updated on <date>" line. That date comes from a `LAST_UPDATED`
environment variable the workflow computes at deploy time (`date -u` in a
`now` step) and passes to the build — a plain local `uv run scripts/build.py`
has no `LAST_UPDATED` set, so the "Last updated" line simply doesn't render
locally (a local build isn't a deployment, so it shouldn't claim to be one).

DNS: a `CNAME` record for `keylinks.gkt.sh` must point at
`gkthiruvathukal.github.io` in whatever DNS provider hosts `gkt.sh`. This is
managed outside this repo.

## Status

- Git repo, GitHub Actions deploy, and custom domain (`CNAME`) are wired up.
- Not yet done: analytics; Cloudflare (planned for a v2, out of scope for now).
