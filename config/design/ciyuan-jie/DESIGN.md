# 词元长街 · Token Street — Design System

A Chinese newspaper editorial aesthetic for an AI daily digest. Warm paper texture,
inky typography, vermillion accent — the feeling of a printed broadsheet, built for the web.

---

## §1 Brand & Voice

**Name**: 词元长街 / Token Street  
**Tagline**: 多源聚合 · 去重分类 · 每日更新  
**Subline**: A Daily Digest of Artificial Intelligence Research & Systems  
**Locale**: zh-CN primary; English used for category labels and display accents only  
**Tone**: Authoritative, calm, scholarly — like a well-edited print newspaper, not a blog  
**Est.**: MMXXVI (show the founding year in footer)

---

## §2 Color Palette

All colors use OKLCH for perceptual uniformity.

| Token          | Value                         | Usage                                     |
|----------------|-------------------------------|-------------------------------------------|
| `--paper`      | `oklch(0.965 0.012 85)`       | Page background — warm cream              |
| `--paper-2`    | `oklch(0.935 0.015 82)`       | Hover tint, secondary surfaces            |
| `--rule`       | `oklch(0.78 0.015 70)`        | Horizontal rules, borders, dividers       |
| `--ink`        | `oklch(0.20 0.010 60)`        | Primary text — near-black with warmth     |
| `--ink-soft`   | `oklch(0.38 0.012 60)`        | Secondary text, dek/summary copy          |
| `--ink-mute`   | `oklch(0.55 0.012 60)`        | Tertiary text, timestamps, metadata       |
| `--accent`     | `oklch(0.55 0.18 30)`         | 朱砂红 — highlights, eyebrows, hot badges |
| `--accent-ink` | `oklch(0.40 0.14 30)`         | Accent on light background (links, tags)  |

Body background uses a subtle dot texture:
```css
background-image:
  radial-gradient(oklch(0.88 0.02 75 / .18) 1px, transparent 1px),
  radial-gradient(oklch(0.88 0.02 75 / .12) 1px, transparent 1px);
background-size: 3px 3px, 7px 7px;
background-position: 0 0, 1px 2px;
```
A fixed vignette overlay (`::before` on `.paper`) gives depth without weight.

---

## §3 Typography

Three families — each with a distinct role. Never mix them arbitrarily.

| Variable    | Family                                         | Role                                    |
|-------------|------------------------------------------------|-----------------------------------------|
| `--serif`   | Noto Serif SC → Songti SC → SimSun → serif     | Body text, headings, article titles     |
| `--display` | Playfair Display → Noto Serif SC → serif       | Masthead, issue numbers, ornamental use |
| `--mono`    | JetBrains Mono → ui-monospace → monospace      | Metadata, dates, tags, labels, UI       |

**Scale**:
- Masthead title: `clamp(72px, 9vw, 140px)`, weight 900, Noto Serif SC
- Featured article title: `clamp(36px, 4vw, 56px)`, weight 700
- Section heads / cat heads: 22–24px, weight 900
- Article titles: 21px, weight 700, line-height 1.22
- Issue titles (list): 24px, weight 700
- Body / dek: 14–18px, line-height 1.55–1.65
- Mono labels: 10–12px, `letter-spacing: .08–.2em`, `text-transform: uppercase`

**Display font in italic** (`font-style: italic`) is the signature move — Playfair Display
italic at large sizes reads as distinctly editorial.

---

## §4 Spacing & Layout

Max content width: `1280px`, centered, `padding: 28px 56px 120px`.

**Homepage grid** (issue list row):
```
grid-template-columns: 110px 1.1fr 2.4fr 1fr
```
Four columns: issue number → date → body (title + summary + tags) → stats sidebar.

**Article grid** (within a daily issue):
```
grid-template-columns: 72px 1fr
```
Two columns: ordinal number → article content.

**Featured / highlights block**:
```
grid-template-columns: 1.4fr 1fr
```
Left: main story. Right: "IN NUMBERS" sidebar.

Rule rhythm: sections separated by `border-bottom: 1px solid var(--ink)` (thick rule)
or `border-bottom: 1px solid var(--rule)` (soft rule). Never use spacing alone without a rule.

The masthead bottom border is `3px double var(--ink)` — the signature double rule.

---

## §5 Components

### Masthead
- Top bar (`.topbar`): monospace, 11px, uppercase, live clock on right
- Title block (`.masthead`): centered, kicker → huge title → italic English subtitle → meta-strip
- Meta strip: 3-column grid (city names | issue count | date)
- Bottom border: `3px double var(--ink)`

### Category / Section Head (`.cat-head`, `.section-head`)
- Chinese name (Noto Serif SC, weight 900) + italic English in Playfair Display
- Count on the right in monospace
- Bottom border: `1px solid var(--ink)`

### Article Item (`.article`)
- Left: italic Playfair Display ordinal `font-size: 26px`
- Eyebrow: `──── CATEGORY` in monospace accent, with a 12px line before text
- Title: Noto Serif SC, 700, links hover to accent red
- Dek: 15px, ink-soft, max 64ch
- Meta bar: monospace 10px uppercase — source, date, source-count
- Multi-source articles get `border-left: 3px solid var(--accent)` — the red left rail

### Issue List Row (`.issue`)
- Issue number: italic Playfair Display `34px` + "№" label above
- Date: monospace, with day-of-week below in `10px uppercase`
- Body: eyebrow → issue title (24px serif) → summary → tags → "阅读全文 →"
- Sidebar: stats rows (items/sources/top stories) with left border

### Tags & Badges
- `.tag`: monospace 10px uppercase, `#` prefix in accent color, no border
- `.badge`: monospace 10px uppercase, `1px solid var(--rule)` border
- `.badge-hot`: filled accent background, paper text

### Search & Filters
- Search box: `1px solid var(--ink)` border, serif input placeholder in italic
- Filter chips (`.chip`): monospace uppercase, `.on` → filled ink background

### Footer
- `3px double var(--ink)` top border (mirrors masthead)
- 4-column grid: colophon → sections → sources → about
- Brand in italic Playfair Display, 22px

---

## §6 Motion & Interaction

Interactions are minimal — this is a newspaper, not an app.

- Issue row hover: `background: oklch(0.97 0.02 80)` + title color → accent red (`.15s ease`)
- Link hover: `color: var(--accent)` (`.15s`)
- No transforms, no scale effects, no bouncing
- The live clock in the top bar is the only animated element

---

## §7 Do's & Don'ts

**Do:**
- Use `double` border for masthead and footer top — it's the signature detail
- Display Playfair italic at large sizes for ordinal numbers and the masthead
- Keep metadata strictly in JetBrains Mono, `letter-spacing: .08–.2em`, uppercase
- Use the accent red sparingly: eyebrows, ordinal numbers, multi-source rail, hot badges
- Add `#` prefix in accent color to all category tags
- Keep article dek max-width at `64ch` — no rivers of text
- Use `clamp()` for headline sizes for responsive scaling without breakpoints

**Don't:**
- Don't use sans-serif for body text — this design is serif-first
- Don't use the accent red for body links or large fills — it's a point accent only
- Don't remove the dot texture from the body background
- Don't use color backgrounds for article cards — the paper bg IS the card
- Don't round corners anywhere — square edges only
- Don't add shadows — depth comes from rules and grid, not elevation
- Don't use emoji or icons beyond the SVG search icon
- Don't change the masthead layout: kicker → 巨型标题 → en subtitle → meta-strip, in that order

---

## §8 CSS & Template Implementation Notes

### Homepage — use the template verbatim, no generation needed

`designs/ciyuan-jie/standalone.html` **is** the homepage. It contains its own JavaScript
that reads `data/issues.json` and renders the issue list dynamically in the browser.

When this design is active:
1. **Copy `designs/ciyuan-jie/standalone.html` → `site/index.html`** directly. No edits needed.
2. **Do NOT run `build_index.py`** for the homepage — it's irrelevant for this design.
   The JS in the file does all the rendering at view time from `data/issues.json`.
3. The RSS autodiscovery `<link>` is already present in the template (`href="feed.xml"`).

The only thing that needs to be kept in sync is `site/data/issues.json` — as long as
the pipeline writes correct entries there, the homepage self-updates on every browser load.

### CSS — copy verbatim, do not regenerate

The complete, production-ready CSS lives in `designs/ciyuan-jie/style.css`.
Copy it to `site/assets/style.css` verbatim. **Do not regenerate from this DESIGN.md.**
This design is already implemented; the CSS file is the source of truth.

### Daily issue pages — use `editorial-longscroll` layout with these class names

- Section header: `.cat-head` with `.cat-name` + `.cat-en` + `.cat-count`
- Article list: `.articles` > `.article` (add `.multi-source` when `source_count > 1`)
- Article ordinal: `.art-num` > `.art-n` (italic Playfair Display number)
- Article eyebrow: `.art-eyebrow` (category slug, monospace, accent)
- Summary: `.art-dek`
- Meta bar: `.art-meta` with `.sep` dots between items
- Tags: `.art-tags` > `.badge` (or `.badge-hot` for `source_count >= 3`)
- "Read more" link: `.art-link`

Daily issue pages load `../assets/style.css` (relative path) and are self-contained HTML files.

### Known pitfalls (from first production run)

**1. `issues.json` must include `source_count` at the issue level.**
The homepage JS reads `it.source_count` in two places (`.iside` row and featured byline).
Missing this field renders as "来源 undefined 个". Always write:
```json
{ "date": "...", "item_count": 17, "source_count": 2, ... }
```

**2. Body wrapper: use `<body><main class="paper">` not `<body class="paper">`.**
The `.paper` class applies `max-width: 1280px`. Putting it on `<body>` clips the background
texture to the content width. Use `<main class="paper">` inside a plain `<body>` — matches
`standalone.html` structure.

**3. Topbar requires `.left` / `.right` child divs.**
```html
<!-- CORRECT -->
<div class="topbar">
  <div class="left"><span><span class="dot"></span>正在刊行</span></div>
  <div class="right"><span id="live-clock">— : —</span></div>
</div>
```
Bare `<span>` children inside `.topbar` break the flex layout.

**4. `.sep` in `.art-meta` must be an EMPTY element.**
The CSS renders `.sep` as a 3 px dot via `width`/`height`/`background`. Putting text
inside it (e.g. `<span class="sep">·</span>`) shows both the dot AND the character.
```html
<!-- CORRECT -->
<span class="sep"></span>
<!-- WRONG -->
<span class="sep">·</span>
```

**5. Lead/summary section: use `.highlights-block`, not custom classes.**
There is no `.lead-section`, `.lead-text`, or `.lead-meta` in the stylesheet.
The correct structure for the "今日要闻" block is:
```html
<div class="highlights-block">
  <div>
    <div class="hl-title">今日要闻 · TODAY'S HIGHLIGHTS</div>
    <h2>Issue headline</h2>
    <ol class="hl-list">
      <li><a href="#item-1">Top story title</a></li>
      ...
    </ol>
  </div>
  <aside class="stats-aside">
    <h4>今日数字 · IN NUMBERS</h4>
    <ul>
      <li><span class="n">17</span><span>今日条目</span><span class="v">ITEMS</span></li>
      ...
    </ul>
  </aside>
</div>
```

**6. Footer must be a `<footer>` element, not a `<div>`.**
The CSS selector is `footer.site-footer` — a `<div class="site-footer">` gets no styles.
No `.footer-inner` wrapper. Direct children: `.colophon`, plain `div(h5+ul)` × 3,
`div.bottom` (spans all 4 columns via `grid-column: 1 / -1`).

**7. Issue page masthead: date as `h1`, site name as kicker.**
Reusing the homepage's giant `clamp(72px,9vw,140px)` h1 on issue pages is wrong —
it dominates the page and repeats the homepage brand without adding value.
On issue pages:
- Site name → small kicker with link back to homepage
- Date → `h1` at `clamp(36px,4vw,52px)` (Chinese date format: `2026年04月19日`)
- Period / source count → `meta-strip`

**8. After running `build_index.py`, always re-copy `standalone.html`.**
`build_index.py` overwrites `site/index.html` with a script-generated version that
doesn't work for this design. For `ciyuan-jie`, always follow with:
```bash
cp designs/ciyuan-jie/standalone.html site/index.html
```

---

## §9 Sample Markup Skeleton

```html
<!-- Category section on a daily issue page -->
<div class="cat-head">
  <div>
    <span class="cat-name">重大发布</span>
    <span class="cat-en">Major Releases</span>
  </div>
  <span class="cat-count">4 条 · 4 ITEMS</span>
</div>

<ul class="articles">
  <li class="article multi-source">
    <div class="art-num">
      <span class="art-n">01</span>
      <span>重大发布</span>
    </div>
    <div>
      <div class="art-eyebrow">重大发布 · Major Release</div>
      <h3><a href="https://...">GPT-5 正式发布</a></h3>
      <p class="art-dek">OpenAI 今日正式推出 GPT-5，综合能力全面超越前代……</p>
      <div class="art-meta">
        <span>OpenAI Blog</span>
        <span class="sep"></span>
        <span>2026-04-19</span>
        <span class="sep"></span>
        <span class="src-count">3 个来源</span>
      </div>
      <div class="art-tags">
        <span class="badge badge-hot">热点</span>
        <span class="badge">major-release</span>
      </div>
      <a class="art-link" href="https://...">阅读原文 →</a>
    </div>
  </li>
</ul>
```
