# linktree

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
- **Layout**: `site.layout: tiled` gives a responsive card grid (2 columns
  at ≤600px, 1 column at ≤480px for phones); `list` gives a single-column
  list of rows. Toggle it in `links.yaml` — no code changes needed.

## Project structure

```
links.yaml          content: site config, categories, links
scripts/build.py     the entire build — reads links.yaml, writes dist/
assets/               source images (logo, photo) copied into dist/ on build
dist/                 generated output (not source of truth — rebuild, don't hand-edit)
```

## Design

Visual language (colors, spacing, typography tokens) and several icons are
carried over from the [`year-in-review`](../year-in-review) repo's
`DESIGN.md` for continuity across `gkt.sh` properties.

## Status

Local build and preview only, so far. Not yet wired up:

- Git repository / version control
- GitHub Actions build + deploy to GitHub Pages
- Analytics
- Cloudflare (planned for a v2, out of scope for now)
