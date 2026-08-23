# AGENTS.md

Guidance for AI coding agents working in this repository.

## What This Is

A serverless, git-backed link collection page for George K. Thiruvathukal. All
content lives in `links.yaml`; `scripts/build.py` renders it to a single
static `dist/index.html`. No login, no database, no framework. The only
client-side JavaScript is a ~5-line progressive-enhancement snippet for the
QR code's fullscreen button (see Architecture) — everything else is plain
HTML/CSS. Deployed to GitHub Pages at `keylinks.gkt.sh` via
`.github/workflows/deploy.yml` on every push to `main`. Sibling site:
`../year-in-review` (same visual language, same zero-dependency static-site
philosophy).

## Commands

```bash
uv run scripts/build.py                                   # build dist/
python3 -m http.server 8765 --directory dist --bind 127.0.0.1   # preview
```

`uv` resolves the script's dependencies (`pyyaml`, `qrcode`, declared via
PEP 723 inline metadata at the top of `scripts/build.py`) automatically — do
not add a `requirements.txt`, `pyproject.toml`, or venv for this. `qrcode`
is used with its SVG image factory (`qrcode.image.svg.SvgPathImage`), which
needs no Pillow — don't add `qrcode[pil]` or install Pillow, it's unused.

## Architecture

- `links.yaml` — the only content file. `site` (title/tagline/logo/photo/
  url/layout), `categories` (ordered `{key, label}` list), `links` (each
  with `name`, `url`, `description`, `icon`, `tags`). `site.url` is the
  page's own canonical URL — it drives the QR code and nothing else; it's
  optional and QR rendering is skipped entirely if absent.
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
     stale copy first), and copies the repo-root `CNAME` into `dist/CNAME`
     if present.
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
  to a forced 2-column cap at ≤860px and 1-column at ≤600px — deliberately
  wide breakpoints so a manually-resized desktop browser window reliably
  reaches single-column, not just actual phone viewports). Layout is chosen
  by `site.layout` in `links.yaml`, read once in `build()` — there is no
  client-side toggle.
- `assets/` — source images. `logo.png` (favicon) and `photo.jpg` (avatar)
  are referenced by path from `site.logo` / `site.photo` in `links.yaml`;
  paths are copied as-is, not renamed or optimized by the build.
- `render_qr_svg()` (in `scripts/build.py`) — generates a QR code for
  `site.url` via `qrcode`, strips the `<?xml ...?>` declaration and the
  `width`/`height` attributes qrcode hardcodes in mm (so CSS controls
  size via the preserved `viewBox`), and returns raw inline `<svg>`
  markup. Rendered inside a `<button id="qr-trigger">` (not an `<a>` —
  linking a QR code back to the page it's already on is a no-op), sitting
  next to the avatar in a `.identity` flex row in the header. A small
  inline `<script>` (only emitted when `site.url` is set) calls
  `btn.requestFullscreen()` on click so the code can be blown up
  full-screen for scanning from across a room — this is the one
  intentional exception to the no-JS posture, and it's pure progressive
  enhancement (the QR code renders and is scannable with JS entirely
  disabled; only the fullscreen-on-click convenience needs it).
- Footer (built inline in `build()`, not a separate function) — three
  lines: a hardcoded copyright (`© 2026–Present George K. Thiruvathukal`,
  not sourced from `links.yaml`), a "Built from this repo" link to
  `github.com/gkthiruvathukal/keylinks` (point this at wherever the repo
  actually lives if it's ever renamed/moved — it doesn't derive from git
  remote config), and the conditional "Last updated on ..." line (see the
  `.github/workflows/deploy.yml` bullet below for where `LAST_UPDATED`
  comes from).
- `CNAME` (repo root) — GitHub Pages custom domain (`keylinks.gkt.sh`).
  Copied into `dist/CNAME` by `build()` so it ships with every deployment;
  don't rely on the GitHub Pages UI setting instead, since Actions-based
  deploys can overwrite it.
- `.github/workflows/deploy.yml` — a `now` step computes the deploy date
  (`date -u '+%B %-d, %Y'`) and exposes it as the `LAST_UPDATED` env var
  for the build step, which `scripts/build.py` reads via `os.environ.get`
  to render the footer's "Last updated on ..." line (see the footer
  bullet above). Then `uv run scripts/build.py` runs, followed by
  `actions/upload-pages-artifact` + `actions/deploy-pages`, on push to
  `main`. This is the only deploy path; there is no manual publish step.
  `LAST_UPDATED` is intentionally absent for local builds — don't
  hardcode a fallback date in `build.py`, the missing line is correct.
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
- Keep `scripts/build.py`'s dependency list minimal and build-time only
  (currently `pyyaml`, `qrcode`). The zero-tooling posture (no Jinja, no
  bundler, no npm) is a deliberate match to `year-in-review`'s stack, not
  an oversight — don't introduce a template engine or JS build step
  without the user asking for it. A build-time Python dependency that
  outputs plain HTML/inline-SVG (no runtime dependency added) is fine on
  the same basis `qrcode` was added; a runtime dependency (CDN script,
  external API call from the page) is not.
- Do not fabricate URLs (profile pages, icons, identifiers) when adding
  content to `links.yaml`. Verify externally sourced links resolve (e.g.
  `curl -s -o /dev/null -w "%{http_code}"`) before adding them.
- `a.link-card.tiled { height: 100%; }` is load-bearing, not decorative.
  CSS Grid stretches each `<li>` grid cell to match the tallest item in
  its row automatically, but the `<a>` card inside doesn't inherit that
  stretched height on its own — without this rule, cards in the same row
  render at different heights whenever their name/description text wraps
  to different line counts. Removing it silently reintroduces uneven
  tiles; it won't show up as an error, just a visual regression.
- `.link-text { display: flex; flex-direction: column; }` is also
  load-bearing. `.name` and `.desc` are `<span>`s; without this, they're
  plain inline content and can end up sharing a line instead of stacking,
  depending on available width. Don't revert this to a bare `<div>` with
  no display rule.
