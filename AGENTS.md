# AGENTS.md

Guidance for AI coding agents working in this repository.

## What This Is

A serverless, git-backed linktree page for George K. Thiruvathukal. All
content lives in `links.yaml`; `scripts/build.py` renders it to a single
static `dist/index.html`. No login, no database, no client-side JavaScript,
no framework. Deployment target is GitHub Pages (not yet wired up — see
`README.md` Status section). Sibling site: `../year-in-review` (same visual
language, same zero-dependency static-site philosophy).

## Commands

```bash
uv run scripts/build.py                                   # build dist/
python3 -m http.server 8765 --directory dist --bind 127.0.0.1   # preview
```

`uv` resolves the script's only dependency (`pyyaml`, declared via PEP 723
inline metadata at the top of `scripts/build.py`) automatically — do not add
a `requirements.txt`, `pyproject.toml`, or venv for this.

## Architecture

- `links.yaml` — the only content file. `site` (title/tagline/logo/photo/
  layout), `categories` (ordered `{key, label}` list), `links` (each with
  `name`, `url`, `description`, `icon`, `tags`).
- `scripts/build.py` — the entire build, in one function (`build()`):
  1. Parses `links.yaml`.
  2. For each category, filters `links` to those whose `tags` list contains
     that category's `key`. This is the whole mechanism behind a link
     appearing in multiple sections — a link with `tags: [app, music]`
     simply satisfies the filter twice, once per category loop iteration.
     There is no dedup step and none is needed.
  3. Renders each surviving link to an `<li>` via `render_link_card()`,
     escaping all fields with `html.escape`.
  4. String-concatenates everything (cards → section `<ul>`s → full page)
     into one f-string and writes `dist/index.html`.
  5. Copies `assets/` into `dist/assets/` (`shutil.copytree`, wiping any
     stale copy first).
- `ICONS` dict (top of `scripts/build.py`) — icon key → inline SVG `<path>`.
  24x24 viewBox convention; brand marks (`linkedin`, `github`) use
  `fill="currentColor"`, everything else is `stroke="currentColor"
  stroke-width="2"` with `fill="none"`. Several icons (`website`,
  `institution`, `lab`, `linkedin`, `scholar`, `github`) are copied verbatim
  from `../year-in-review/index.html`'s profile-link strip — keep them
  byte-identical if touched, for visual continuity across `gkt.sh`
  properties.
- `CSS` string (also in `scripts/build.py`) — design tokens (colors,
  shadow) match `../year-in-review/DESIGN.md`. Two layouts share the same
  card markup: `list` (flex column) and `tiled` (CSS grid, `auto-fit` down
  to a forced 2-column cap at ≤600px and 1-column at ≤480px). Layout is
  chosen by `site.layout` in `links.yaml`, read once in `build()` — there is
  no client-side toggle.
- `assets/` — source images. `logo.png` (favicon) and `photo.jpg` (avatar)
  are referenced by path from `site.logo` / `site.photo` in `links.yaml`;
  paths are copied as-is, not renamed or optimized by the build.
- `dist/` — generated output. Never hand-edit; it's overwritten on every
  build.

## Conventions / Gotchas

- An `icon:` value with no matching key in `ICONS` does not error — it
  silently falls back to the generic `link` chain-icon. If a new entry's
  icon looks wrong, check for a typo before assuming a bug in `build.py`.
- Categories with zero matching links are skipped entirely (no empty
  section renders) — this is intentional, not a bug to fix.
- `tags` is a list, not a single value, specifically so one link can belong
  to more than one category (e.g. music apps tagged `[app, music]`). When
  adding new categories, prefer this over duplicating link entries.
- Keep `scripts/build.py` dependency-free beyond `pyyaml`. The zero-tooling
  posture (no Jinja, no bundler, no npm) is a deliberate match to
  `year-in-review`'s stack, not an oversight — don't introduce a template
  engine or JS build step without the user asking for it.
- Do not fabricate URLs (profile pages, icons, identifiers) when adding
  content to `links.yaml`. Verify externally sourced links resolve (e.g.
  `curl -s -o /dev/null -w "%{http_code}"`) before adding them.
