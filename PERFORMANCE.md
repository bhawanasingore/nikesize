# Pegasus 43 page — Slow 4G trace findings and fixes

The size grid moves **0px** while the page loads on a Slow 4G phone. That's true on a normal load, and also when the
price or its font arrives late. Lighthouse scores the page 99–100 under the launch profile's settings, so the values
in [`speed-budget.json`](speed-budget.json) all pass.

All numbers below come from the GitHub Pages build of this repo, served locally without compression. The live page
should load a little faster. Measured 23 November 2026.

## Settings used

These match the `web-platform-slow-4g-mobile` profile (owner: Diego Salazar, Web Platform Engineering).

| Setting | Lighthouse (simulated) | Trace (real browser, DevTools throttling) |
| --- | --- | --- |
| Screen | 375 × 812 CSS px, 3x pixel density, mobile on | Same |
| Network | Slow 4G: 150 ms round trip, 1638.4 Kbps | 562.5 ms per request (150 × 3.75), 1474.56 Kbps down, 675 Kbps up |
| CPU | 4x slowdown | 4x slowdown |
| Cache | Off | Off |

## speed-budget.json

| Key | Value set | Profile requires | Measured |
| --- | --- | --- | --- |
| `performance_score_min` | 90 | ≥ 90 (90–100) | 99, 100, 100 in 3 Lighthouse runs |
| `size_grid_shift_px_max` | 0 | 0 only | 0px in every trace |
| `size_button_min_px` | 48 | ≥ 44 | Every size button is 48 × 48px, sold-out ones included |

48 is stricter than the required 44, which the profile allows. It matches the 48 × 48 buttons the page was built with.

Lighthouse detail (3 runs): first contentful paint 1.1 s, largest contentful paint 1.1 s, total blocking time
70–100 ms, cumulative layout shift 0, speed index 1.1 s.

## Trace findings

**No element moves the size grid.** Each trace records the grid's top edge on every frame, from first paint until 3 s
after the page has loaded, and logs Chrome's layout-shift entries.

| Trace | Grid first drawn | Page loaded | Grid top | Grid movement | Layout shifts |
| --- | --- | --- | --- | --- | --- |
| Before the price fix, run 1 | 1,470 ms | 3,991 ms | 457px | 0px | 0 |
| Before the price fix, run 2 | 1,266 ms | 3,816 ms | 457px | 0px | 0 |
| Before the price fix, run 3 | 1,254 ms | 3,822 ms | 457px | 0px | 0 |
| After the price fix, run 1 | 1,287 ms | 3,843 ms | 454px | 0px | 0 |
| After the price fix, run 2 | 1,290 ms | 3,970 ms | 454px | 0px | 0 |
| After the price fix, run 3 | 1,305 ms | 3,864 ms | 454px | 0px | 0 |

The profile names the elements that could push the grid:

| Element | Could move the grid because | Result |
| --- | --- | --- |
| `main-photo` | A photo arriving late into a box with no reserved height | 0px. The box has a fixed 280px height (fix 1) |
| `price` | Price text or its font arriving late and growing the row | 0px. Fixed 24px price box (fix 2); was 3px in the late-arrival test before the fix |
| Product name and colourway | Late text or font | 0px. In the first HTML, using the phone's own fonts (no web fonts) |
| `size-grid` | Added or rebuilt by JavaScript after first paint | 0px. Drawn in the first HTML; JavaScript (done at about 3.8 s) doesn't change it |
| `low-stock-tag` | Tags pushing rows apart | 0px. Each tag sits in the gap under its button, positioned so it takes no space |

## Fixes

### 1. Fixed photo box

`main-photo` is a fixed 280px-tall box (`app/page.module.css`, `.photo`). Its space is reserved before anything loads
into it, so the photo can never push the grid down. The fixed height also keeps the grid starting on the lower part of
the first screen.

### 2. Fixed price height

- **Price box:** `.price` is `display: inline-block` with `height: 24px`, `line-height: 24px` and `min-width: 64px`
  (enough for "140.00").
- **Row alignment:** the name/price row uses `align-items: center` instead of `baseline`. With baseline alignment, an
  empty price box sits lower and makes the row taller.

The late-arrival test (`perf/late_price_test.py`) measured the change:

| Test | Before the fix | After the fix |
| --- | --- | --- |
| HTML arrives with no price; React fills it in when its JavaScript loads | Grid moved 3px down at about 3.5 s | 0px |
| Price switches to a different font 2 s into the load | Grid moved 3px down at about 2.6 s | 0px |

In the late-font test, the colourway moves sideways because the test font is wider than 64px. The grid doesn't move.

### 3. Test IDs match the launch check

`product-price` was renamed to `price`. Sold-out buttons now use `size-button-sold-out`, and `size-button` covers
in-stock and low-stock buttons only. All five watched elements are on the page: `size-grid`, `size-button`,
`size-button-sold-out`, `main-photo` and `price`.

## Open items

- **Largest element on screen:** Lighthouse reports the product name, not `main-photo`, because the photo box is
  still empty. When real photos arrive, use an `<img>` with `width`/`height` set, filling the 280px box, so the box
  keeps its size and the photo becomes the largest element.
- **Not Chrome DevTools MCP:** that tool wasn't connected, so the traces were recorded in Chrome directly through the
  same DevTools controls (Chrome DevTools Protocol, via Playwright).
- **Re-run on the live page:** do this once GitHub Pages is turned on.

## Prompts used

Trace prompt:

> Use Chrome DevTools MCP to record a performance trace of the Pegasus 43 page with a 375 x 812 viewport at 3x pixel density, mobile on, Slow 4G (150 ms round trip, 1638.4 Kbps) and a 4x CPU slowdown. After the trace, list each element that moves the size grid: what it is, what is causing it, how many px it moves the grid, and when it happens while loading.

Price fix prompt:

> Give the price a fixed height so it keeps its space even if it or its font loads late. Keep the grid at 0 px of shift, then re-run the Slow 4G trace and add this fix to the notes.

## Re-run the checks

Needs Python with Playwright and Chrome installed.

```bash
PAGES_BASE_PATH=/nikesize npm run build
mkdir -p site && cp -r out site/nikesize && (cd site && python3 -m http.server 3100 &)

python3 perf/trace_page.py http://localhost:3100/nikesize/ 3          # Slow 4G trace, grid movement, trace files
python3 perf/late_price_test.py <before-url> http://localhost:3100/nikesize/   # late price / late font test
python3 perf/check_page.py data/nike_pegasus_size_stock.json http://localhost:3100/nikesize/  # layout checks
npx lighthouse http://localhost:3100/nikesize/ --config-path=perf/lh-config.cjs --only-categories=performance
```

Each trace file (`pegasus43_trace_run*.json`) opens in Chrome DevTools: Performance panel → **Load profile**.
