# Handoff: Heritage Lens — Web UI (replaces Streamlit)

## Overview
Heritage Lens is a multimodal RAG agent for cultural-heritage research (Mesoamerican / Olmec corpus). This handoff covers a **new web interface** that replaces the existing Streamlit UI (`ui/app.py`). The backend agent pipeline, Qdrant, and ingestion are **untouched**; a thin FastAPI layer wraps the existing Python modules, and a standalone React frontend talks to it.

The product's core differentiator is the **three-panel result layout** — Answer, Sources, and "What the System Doesn't Know" (epistemic transparency) — which must remain prominent and distinct.

## About the Design Files
The files in `reference/` are **design references created in HTML/CSS/JS** — a high-fidelity prototype showing the intended look and behavior. They are **not** production code to copy directly. The task is to **recreate this design in the target stack: React + Vite + Tailwind CSS 4**, using that ecosystem's idioms (function components, hooks, context). Treat the HTML/JS as the single source of visual + behavioral truth; reimplement, don't transplant.

- `reference/Heritage Lens Sidebar Classic.html` — the approved layout & markup
- `reference/app.js` — all interaction logic (state machine, reading comfort, dark mode, lightbox, history, share)
- `reference/Heritage Lens Wireframes.pdf` — the 5 explored directions; **"01 Sidebar Classic" is the chosen one**

## Fidelity
**High-fidelity.** Final colors, typography, spacing, and interactions are all specified below and present in the reference files. Recreate the UI faithfully. Placeholder media (striped `.ph` blocks) stand in for real corpus images/video frames — wire those to real data.

---

## Architecture (from product spec)

### Backend — FastAPI (`api/`, same venv as existing project)
Create a REST API that imports and calls existing modules (`agent/pipeline.py`, `agent/ingest.py`) — **do not reimplement the pipeline.**

| Method | Route | Purpose |
|---|---|---|
| POST | `/api/search` | Body `{ query: string }`. Calls pipeline (retrieve → generate → judge). Returns the full 3-layer result + image paths + video chunks. Stream the response (SSE) or return progress. |
| GET | `/api/status` | Corpus stats: text chunks, image count, video chunks, PDF count. |
| POST | `/api/ingest` | Triggers `initialize_vector_db()` (full rebuild). Stream progress via **SSE**. |
| GET | `/api/images/{path}` | Serves images from `data/cache/images/`. |

Files: `api/main.py`, `api/routes.py`, `api/models.py`. Update Dockerfile/docker-compose to add the FastAPI service (or run via uvicorn).

**Constraints (hard):** Never modify `agent/*`, `config/*`, or `data/`. Keep `ui/app.py` (Streamlit) intact. Put the new frontend in `ui/frontend/`.

### Response shape expected by the frontend
The search result should resolve to roughly:
```ts
interface SearchResult {
  query: string;
  answer: {
    // ordered blocks so the UI can render inline [BACKGROUND] tags + citations
    html?: string;                 // or structured blocks below
    blocks: Array<
      | { type: 'text'; text: string; citations?: number[] }
      | { type: 'background'; text: string }   // rendered as [BACKGROUND — not retrieved]
    >;
    grounded: boolean;
  };
  sources: Array<{
    n: number;
    title: string;
    subtitle: string;             // e.g. "Grove, D. C. · pp. 114–121"
    type: 'pdf' | 'img' | 'vid';
    meta: Record<string, string>; // expandable key/value detail
  }>;
  epistemic: {
    sourceBias: string;
    absences: string;
    interpretiveLimits: string;
    confidence: { level: 'low'|'moderate'|'high'; segments: 1|2|3|4; note: string };
  };
  videoChunks: Array<{ modality: 'audio_transcript'|'visual_caption'|'ocr_text'; timestamp: string; caption: string; videoUrl?: string }>;
  images: Array<{ path: string; caption: string; alt: string }>;
  meta: { sourceCount: number; videoCount: number; imageCount: number; elapsedSeconds: number };
}
```

---

## Frontend stack & conventions
- **React + Vite + Tailwind CSS 4**, TypeScript.
- `darkMode: 'class'` (toggle adds `.dark` to `<html>`/`<body>`).
- State via **React context/hooks only** (no Redux/external state libs).
- Fonts via **@fontsource** packages (no Google Fonts CDN): `@fontsource/inter`, `@fontsource/atkinson-hyperlegible`, plus OpenDyslexic (`@fontsource/opendyslexic` or bundled).
- CSS: Tailwind utilities + a minimal `globals.css` holding the **CSS custom properties** (design tokens + the live reading-comfort vars).

### Suggested component tree (`ui/frontend/src/`)
```
main.tsx
App.tsx
context/
  ThemeContext.tsx        // dark mode, persisted localStorage 'hl_dark', defaults to prefers-color-scheme
  ReadingContext.tsx      // reading-comfort vars, persisted 'hl_rc'
  SearchContext.tsx       // query, state machine (empty|loading|results), result, history
lib/
  api.ts                  // fetch wrappers + SSE client for /search and /ingest
components/
  Sidebar.tsx             // brand, nav, Answer Mode <select>, Show-all-layers switch, About, dark toggle
  TopBar.tsx              // sidebar-collapse btn, title, corpus status mini, dark btn, reading btn, rail-collapse btn
  SearchBar.tsx           // input, ⌘/Ctrl+Enter, search button
  EmptyState.tsx
  LoadingState.tsx        // pulse ring + 4-step progress (retrieve/interpret/attribute/evaluate)
  Results.tsx             // query recap + share/export + the panels grid + galleries
  AnswerPanel.tsx         // Panel 1 — reading-comfort-scoped doc, citations, [BACKGROUND] tags
  SourcesPanel.tsx        // Panel 2 — expand/collapse rows, metadata <dl>
  EpistemicPanel.tsx      // Panel 3 — 4 colored cards + confidence bar (lives in right rail)
  RightRail.tsx           // EpistemicPanel + collapsible Session Overview + Recent queries
  VideoGallery.tsx        // modality badges + seek links
  ImageGallery.tsx        // grid → Lightbox
  Lightbox.tsx
  ReadingComfortPanel.tsx // slide-out: font radios, spacing sliders, cream/ragged toggles
  Footer.tsx              // "How it works" flow + tagline
```

---

## Layout
Top-level is a **CSS grid**, three columns pinned so collapsing one leaves its slot empty (no reflow):

```
grid-template-columns: 248px 1fr 336px;   /* sidebar | main | right-rail */
grid-template-rows: 1fr auto;             /* content | footer (spans all cols) */
```
- Sidebar: `grid-column:1`, `grid-row:1 / span 2`, sticky, full-height, scrolls.
- Main: `grid-column:2`, flex column (TopBar sticky, then `.content`).
- Right rail: `grid-column:3`, sticky, full-height, scrolls.
- Footer: `grid-column:1 / -1`.

**Column collapse (full-screen reading):** body classes `nav-collapsed` → `grid-template-columns:0 1fr 336px` (hide sidebar); `rail-collapsed` → `248px 1fr 0` (hide rail); both → `0 1fr 0`. Toggle buttons live in the TopBar; state persisted (`hl_col_nav`, `hl_col_rail`).

**Content width / responsiveness:** `.searchwrap` and `.results` use `width:100%; max-width:min(1500px,100%); margin:0 auto` so they **expand to fill available width up to 1500px** (don't hard-cap narrow). The Answer reading column is separately capped (see reading-comfort `--rc-width`, default 68ch) so prose stays readable no matter how wide the panel grows.

**Breakpoints:**
- `≤1180px`: drop to `248px 1fr`; right rail moves below content (becomes a horizontal wrap row).
- `≤900px`: `.panels` becomes 1 column (Answer/Sources stack).
- `≤820px`: single column; sidebar hidden; `epi-grid` 1col; `vid-grid` 2col; `img-grid` 3col; `.content` padding 18px.

---

## Screens / Views

### 1. Empty state
- **Purpose:** landing before a query.
- **Layout:** centered, `max-width:760px`, `text-align:center`, `padding-top:30px`.
- **Components:** `h2` (24px, −.02em tracking) with copy: *"Heritage Lens combines multiple sources and perspectives to give you transparent, research-ready answers."* Sub `p` (15px, `--text-soft`, max-width 520px centered): *"Ask about the Mesoamerican corpus. Every answer cites its sources and tells you what it can't know."* (No suggestion buttons — removed per review.)

### 2. Loading state
- **Purpose:** shown while the query runs.
- **Components:** pulse ring (54px; three expanding ring spans, `pr` keyframe 1.8s, delays .6s/1.2s; solid core inset 18px). Stage text (14.5px, `--text-soft`) cycling through the four step strings. Four step chips (`Retrieve`, `Interpret`, `Attribute`, `Evaluate`): default faint; `.active` = answer color + tinted bg; `.done` = green border.
- **Timing in prototype:** ~480ms per step (4 steps) then resolve. Replace with real progress from the API (SSE) — keep the same visual stages.

### 3. Results
- **Query recap row:** query text (18px/600), meta line (12.5px faint: `"5 sources · 3 video chunks · 5 images · 1.4s"`), and right-aligned **Share query** + **Export** ghost buttons.
- **Panels grid:** `grid-template-columns:1.5fr 1fr` (Answer wider, Sources narrower); `align-items:start`; gap 16px; collapses to 1col ≤900px. **The epistemic panel is NOT in this grid — it lives in the right rail** (see below; moved there per review).
- Then **Video Evidence** gallery, then **Visual Evidence** gallery.

#### Panel 1 — The Answer
- Card: white surface, 1px border, radius 14px, soft shadow, **3px left border in answer-blue** (`--answer #2f6fdb`).
- Head: 30px rounded icon tile (answer-bg fill), `h2` "The Answer" (15px), right `ptag` "Grounded" (11px uppercase, answer-bg pill).
- Body holds `.answer-doc` whose typography is driven by reading-comfort CSS vars (`--rc-font`, `--rc-ls`, `--rc-lh`, `--rc-width`, `--rc-align`, `--rc-bg`, `--rc-pad`). Base size 15.5px.
  - **Citations:** superscript `.cite` spans (answer color, 600). Clicking one expands + flashes the matching source in Panel 2 (`box-shadow` pulse for ~900ms).
  - **Background tag:** inline `[ BACKGROUND — not retrieved ]` pill — warn color (`--warn #c2820f`), tinted bg, 1px tinted border, radius 6px. Used to mark non-retrieved general knowledge.
  - Footer: dashed top border, a `[BACKGROUND…]` pill + note "= general knowledge, clearly separated from corpus-grounded claims."

#### Panel 2 — Sources
- Card: **3px left border in purple** (`--sources #7c5cd6`); head icon + "Sources" + `ptag` "N cited".
- Each source = expandable row (`<button class=src-head>` + collapsible `.src-detail`):
  - `align-items:flex-start` (badges align to first line of multi-line titles).
  - 22px numbered square; `.src-title` (13.5px/600, **wraps** — `text-wrap:pretty`, no ellipsis); `.src-sub` block (12px faint) on its own line; type badge (`PDF` red / `IMG` purple / `VID` blue); chevron (rotates 180° when open).
  - Expanded: `<dl>` 2-col grid of metadata (Author, Work, Type, Location, Publisher, Institution, etc.). Animate via max-height.

#### Panel 3 — What the System Doesn't Know (epistemic) — **in the right rail**
- This is the differentiator. Card uses a 1.5px teal-tinted border (`--epi #0d9488`) and a subtle teal glow shadow; head icon teal, `ptag` "Epistemic".
- **Four cards** (`.epi-grid`; 2col in main, **1col in rail**), each a FILLED tinted card (not just a border):
  | Card | Header color | Background tint | Content (sample copy) |
  |---|---|---|---|
  | **Source Bias** | red `--bad #cf5a52` | `bad 9% over surface` | "Corpus skews toward English-language, mid-20th-century archaeology. Indigenous-authored and Spanish-language interpretations are underrepresented." |
  | **Absences** | amber `--warn #c2820f` | `warn 11% over surface` | "No settlement-survey tables, burial inventories, or epigraphic data for Chalcatzingo are present in the indexed material." |
  | **Interpretive Limits** | blue `--info #2f6fdb` | `info 9% over surface` | "Iconographic readings (e.g. 'ruler,' 'cave') are scholarly interpretations, not settled fact. Alternate readings exist and are contested." |
  | **Confidence** | green `--good #1f9d63` | `good 9% over surface` | full-width; **confidence bar** of 4 segments (l1 red / l2 amber / l3 #caa93f / l4 green; lit count = level), label ("Moderate") + note. |
- **All four cards must always be visible.** In the rail the panel is sticky-pinned to the top so it stays in view while the rest of the rail scrolls.

### Right rail (below the epistemic panel)
- **Session Overview** — label has a clock icon and a **mask/collapse chevron button** (`#btnMaskSession`): collapses the body to give the epistemic panel priority; state persisted (`hl_session_masked`). Rows: Started `14 Jun 2026, 13:20`, Mode `Strict Corpus-Only`, Sources Indexed `255`, Exchanges `2`; then full-width **Export Session** ghost button.
- **Recent queries** — last ≤8 queries from localStorage (`hl_hist`), click to re-run. Each row a clock icon + truncated query.

### Sidebar (left)
- Brand: gradient logo tile (answer→sources), "Heritage Lens" / "Multimodal RAG".
- **Explore** nav: Ask (active), Sources (count 255), Uploads, Sessions. Active item = answer-bg + answer text + tinted border.
- **Answer Settings:** "Answer Mode" `<select>` (Strict Corpus-Only / Corpus + Background / Exploratory); "Show all layers" switch (on); helper note.
- **About** paragraph.
- Bottom: "Dark mode" switch row.

### TopBar
Sidebar-collapse button · "Ask" title · spacer · corpus status mini (green dot + "Corpus ready · 255 sources") · dark-mode icon button (sun/moon swap) · reading-comfort icon button (`abc`) · divider · rail-collapse button. Sticky, blurred translucent bg, 1px bottom border.

### Reading Comfort panel (slide-out, korben.info style)
Triggered by the `abc` button. Right-anchored drawer (360px, max-width 90vw) + scrim; slides in via transform; `role="dialog"`, ESC closes. **Applies to the answer text only** (scoped CSS vars on `.answer-doc`). Sections:
- **Typeface** (radio): Inter (Default) · Atkinson Hyperlegible (badge "Sci ✓") · OpenDyslexic (badge "Pref ⓘ"). Selected = answer border + bg.
- **Spacing** (sliders): Letter spacing 0–0.15em step 0.01 · Line height 1.2–2.0 step 0.1 · Column width 50–100ch step 2 (default 68ch). Live numeric readout each.
- **Presentation** (switches): Cream background (Solarized base3 `#FDF6E3`; also sets a dark ink + padding) · Ragged-right (toggles `text-align` justify↔left).
- **Reset to defaults** footer button.
All settings → CSS custom properties on the answer doc, persisted to localStorage `hl_rc`.

### Footer
"How it works" label + a flow of chips: ① You ask → ② Retrieve → ③ Interpret → ④ Attribute → ⑤ Evaluate → ✓ Answers you can trust (last chip teal). Tagline below: *"Heritage Lens Multimodal Agent — Accountable AI for Specialised Research."*

---

## Interactions & Behavior
- **Submit:** Enter or **⌘/Ctrl+Enter** in the search field; clicking Search. `/` focuses the search field. Drives state machine empty → loading → results.
- **Share query:** copies `location.origin + pathname + '#q=' + encodeURIComponent(query)` to clipboard; toast "Share link copied". On load, a `#q=…` hash auto-runs that query.
- **Export:** per-result Markdown / JSON (prototype toasts; implement real download).
- **History:** unshift query, dedupe, cap 8, persist `hl_hist`.
- **Citations:** click `.cite` → open + flash the referenced source row.
- **Sources:** click row → expand/collapse metadata (`aria-expanded`).
- **Lightbox:** click image thumb → overlay with large image + caption; click backdrop / close / ESC to dismiss.
- **Video seek:** "Seek to mm:ss" — if `videoUrl` is http(s), seek/open the video at that timestamp.
- **Dark mode:** toggle adds `.dark`; persist `hl_dark`; **default to `prefers-color-scheme`** on first load.
- **Column collapse & session mask:** see Layout / Right rail; both persisted.
- **Reduced motion:** `@media (prefers-reduced-motion: reduce)` disables transitions/animations.

## State Management
- `theme`: 'light'|'dark' (ThemeContext) — persisted, defaults to system.
- `reading`: { font, letterSpacing, lineHeight, columnWidth, cream, ragged } (ReadingContext) — persisted.
- `searchState`: 'empty'|'loading'|'results'; `query`; `result: SearchResult|null`; `history: string[]` (SearchContext).
- UI-local: `navCollapsed`, `railCollapsed`, `sessionMasked`, `readingPanelOpen`, `lightbox: {open, image}`, per-source `open`.
- Data fetching: `POST /api/search` (prefer SSE for progressive stages); `GET /api/status` on mount for corpus counts; `POST /api/ingest` (SSE) for the Uploads/ingest flow.

## Design Tokens

### Colors — Light (`:root`)
```
--bg:#f6f7f9; --surface:#ffffff; --surface-2:#f1f3f6; --surface-3:#e9edf2;
--border:#e2e6ec; --border-strong:#d2d8e0;
--text:#1a1e24; --text-soft:#5a626d; --text-faint:#8b929c;
--answer:#2f6fdb; --answer-bg:#eef4fe;
--sources:#7c5cd6; --sources-bg:#f3effc;
--epi:#0d9488; --epi-bg:#f0faf8;
--good:#1f9d63; --warn:#c2820f; --bad:#cf5a52; --info:#2f6fdb;
```
### Colors — Dark (`body.dark`)
```
--bg:#0e1217; --surface:#161b21; --surface-2:#1c222a; --surface-3:#232a33;
--border:#2a313b; --border-strong:#36404b;
--text:#e7eaee; --text-soft:#99a2ac; --text-faint:#6b7480;
--answer:#6ea2f5; --answer-bg:#16243a;
--sources:#b39bf0; --sources-bg:#221c38;
--epi:#3fd0c0; --epi-bg:#10211f;
--good:#46c98a; --warn:#e0ad4e; --bad:#ec7b73; --info:#6ea2f5;
```
### Typography
- Family: Inter (UI + default body). Atkinson Hyperlegible & OpenDyslexic selectable for the answer via reading comfort.
- Base 15px / line-height 1.5. h-weights 600, tracking ≈ −.01em. Panel `h2` 15px. Section labels 11px/700, uppercase, .08em tracking, `--text-faint`. Answer body 15.5px.
### Radii
`--r:14px` (cards), `--r-sm:9px` (controls), 10px (inner cards), 6px (badges), pills 20px, circular avatars/dots.
### Shadows
```
--shadow: 0 1px 2px rgba(20,24,31,.04), 0 4px 16px rgba(20,24,31,.05);
--shadow-lg: 0 8px 40px rgba(20,24,31,.16);
```
Epistemic panel adds a teal-tinted glow. Dark mode uses stronger black-based shadows.
### Spacing
Content padding 26px 30px 36px (18px on mobile). Card padding 15–20px. Gaps: panels 16px, rail sections 20px, grids 12–14px.
### Tinted card backgrounds (epistemic)
`color-mix(in oklab, <accent> 9–11%, var(--surface))` with border `color-mix(in oklab, <accent> 24–26%, transparent)`.

## Assets
- **Icons:** inline SVG (stroke 2, round caps/joins) — equivalent to Lucide. Use `lucide-react` in the build.
- **Media placeholders:** striped `.ph` blocks (45° repeating-linear-gradient) labeled "video frame" / thumbnail names — replace with real images from `GET /api/images/{path}` and video frames/thumbnails. Every image needs real `alt` text.
- **Fonts:** Inter, Atkinson Hyperlegible, OpenDyslexic via @fontsource.
- No raster brand assets; the logo is a CSS gradient tile + search-glyph SVG.

## Files (in this bundle)
- `reference/Heritage Lens Sidebar Classic.html` — markup + all CSS (tokens, layout, components, responsive, reading-comfort, lightbox).
- `reference/app.js` — interaction logic (sample data `SOURCES`/`VIDEOS`/`IMAGES`, state machine, reading comfort, dark mode, lightbox, history, share, collapse/mask).
- `reference/Heritage Lens Wireframes.pdf` — the 5 explored directions (chosen: 01 Sidebar Classic).

## Implementation order (suggested)
1. FastAPI `api/` wrapping the pipeline; verify `/status` + `/search` return the shape above.
2. Vite + Tailwind 4 + @fontsource scaffold in `ui/frontend/`; port tokens into `globals.css`.
3. `api.ts` client (incl. SSE); ThemeContext + ReadingContext + SearchContext.
4. Layout shell: grid, Sidebar, TopBar, Footer, column-collapse.
5. SearchBar + the three states (empty/loading/results) with the state machine.
6. The three panels (Answer w/ citations & background tags, Sources expand, Epistemic in rail).
7. Galleries + Lightbox + video seek.
8. Reading Comfort panel + dark mode + session mask + history/share/export + keyboard shortcuts.
9. Wire to the live backend; test against the real corpus; update Dockerfile/compose.
