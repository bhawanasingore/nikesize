import json, sys
from playwright.sync_api import sync_playwright

URL = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:3000/"
data = sorted(json.load(open(sys.argv[1])), key=lambda r: r["display_order"])
fmt = lambda v: str(int(v)) if float(v).is_integer() else str(v)
# Expected states come from the stock file itself, so the checks follow whatever snapshot is in data/.
SOLD = [fmt(r["size_us_men"]) for r in data if r["stock_status"] == "sold_out" or not r["in_stock"]]
SOLD_SKU = next(r["sku"] for r in data if r["stock_status"] == "sold_out")
PICK_SKU = [r["sku"] for r in data if r["stock_status"] == "in_stock"][len([r for r in data if r["stock_status"] == "in_stock"]) // 2]
LOW = [fmt(r["size_us_men"]) for r in data if r["stock_status"] == "low_stock" and r["in_stock"]]

problems = []
def check(cond, msg):
    if not cond:
        problems.append(msg)

def rect(page, sel):
    return page.eval_on_selector(sel, "e => { const r = e.getBoundingClientRect(); return {x:r.x, y:r.y, w:r.width, h:r.height, b:r.bottom, r:r.right}; }")

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")
    for height in (667, 812):
        ctx = browser.new_context(viewport={"width": 375, "height": height}, is_mobile=True, has_touch=True, device_scale_factor=2)
        page = ctx.new_page()
        page.goto(URL)
        page.wait_for_selector("[data-testid=size-grid]")
        tag = f"[375x{height}]"

        sw = page.evaluate("document.documentElement.scrollWidth")
        check(sw <= 375, f"{tag} horizontal overflow: scrollWidth={sw}")

        h, ph, g = rect(page, "[data-testid=product-header]"), rect(page, "[data-testid=main-photo]"), rect(page, "[data-testid=size-grid]")
        check(h["b"] <= ph["y"] <= ph["b"] <= g["y"], f"{tag} order wrong: header {h}, photo {ph}, grid {g}")
        check(height / 2 <= g["y"] < height, f"{tag} grid top {g['y']} not in lower half of first screen")
        print(f"{tag} grid starts at y={g['y']:.0f} of {height}; scrollWidth={sw}")

        body = page.inner_text("body")
        check(page.inner_text("[data-testid=product-name]") == data[0]["product_name"], "name mismatch")
        check(page.inner_text("[data-testid=price]") == "140.00", "price not 140.00")
        check(page.inner_text("[data-testid=product-colorway]") == data[0]["colorway"], "colorway mismatch")
        check(body.count("140.00") == 1 and body.count("Black/White-Volt") == 1, "price/colorway shown more than once")

        for system in ("men", "women"):
            page.click(f"[data-testid=size-toggle-{system}]")
            btns = page.query_selector_all("[data-testid^=size-button]")
            check(len(btns) == 26, f"{tag} {system}: {len(btns)} buttons")
            labels = [b.inner_text() for b in btns]
            expected = [fmt(r[f"size_us_{system}"]) for r in data]
            check(labels == expected, f"{tag} {system} labels/order wrong: {labels}")
            for b in btns:
                bb = b.bounding_box()
                check(b.is_visible() and abs(bb["width"] - 48) < 0.5 and abs(bb["height"] - 48) < 0.5,
                      f"{tag} {system} button {b.inner_text()} is {bb['width']}x{bb['height']}")
                check(bb["x"] >= 0 and bb["x"] + bb["width"] <= 375, f"{tag} button {b.inner_text()} off screen")

        page.click("[data-testid=size-toggle-men]")
        # Launch-check watched elements (web-platform-slow-4g-mobile profile, part 2)
        for tid in ("size-grid", "size-button", "size-button-sold-out", "main-photo", "price"):
            check(page.locator(f'[data-testid="{tid}"]').count() > 0, f"watched element {tid} missing")
        check(page.locator('[data-testid="size-button"]').count() == len(data) - len(SOLD), "wrong number of in-stock/low-stock buttons")
        check(page.locator('[data-testid="size-button"]:disabled').count() == 0, "a size-button is disabled")
        check(page.locator('[data-testid="size-button-sold-out"]:disabled').count() == len(SOLD), "sold-out buttons not all disabled")
        sold = page.eval_on_selector_all("[data-testid=size-button-sold-out]", """els => els.map(e => ({
            label: e.innerText, deco: getComputedStyle(e).textDecorationLine, bg: getComputedStyle(e).backgroundImage,
            w: e.getBoundingClientRect().width, h: e.getBoundingClientRect().height }))""")
        check([s["label"] for s in sold] == SOLD, f"sold out set wrong: {sold}")
        for s in sold:
            check("line-through" in s["deco"] and "gradient" in s["bg"], f"sold out {s['label']} lacks second cue")
            check(min(s["w"], s["h"]) >= 44 and s["w"] == 48 and s["h"] == 48, f"sold out {s['label']} not full size")
        before = page.eval_on_selector(f'[data-sku="{SOLD_SKU}"]', "e => e.getAttribute('aria-pressed')")
        page.click(f'[data-sku="{SOLD_SKU}"]', force=True)
        after = page.eval_on_selector(f'[data-sku="{SOLD_SKU}"]', "e => e.getAttribute('aria-pressed')")
        check(before == after, "sold out size became selectable")

        tags = page.eval_on_selector_all("[data-testid=low-stock-tag]", """els => els.map(e => {
            const r = e.getBoundingClientRect(); const btn = e.parentElement.querySelector('button');
            return {text: e.innerText, size: btn.innerText, x: r.x, r: r.right, y: r.y, b: r.bottom};})""")
        check([t["size"] for t in tags] == LOW, f"low stock set wrong: {tags}")
        check(all("🔥" in t["text"] for t in tags), "fire emoji missing")
        allbtn = page.eval_on_selector_all("[data-testid^=size-button]", "els => els.map(e => { const r = e.getBoundingClientRect(); return {x:r.x, r:r.right, y:r.y, b:r.bottom}; })")
        for t in tags:
            check(t["x"] >= 0 and t["r"] <= 375, f"tag under {t['size']} off screen")
            for bx in allbtn:
                if t["x"] < bx["r"] and bx["x"] < t["r"] and t["y"] < bx["b"] and bx["y"] < t["b"]:
                    problems.append(f"tag under {t['size']} overlaps a button")
        print(f"{tag} low-stock tags: " + ", ".join(f"{t['size']} [{t['r']-t['x']:.0f}px wide]" for t in tags))

        page.click(f'[data-sku="{PICK_SKU}"]')
        check(page.eval_on_selector(f'[data-sku="{PICK_SKU}"]', "e => e.getAttribute('aria-pressed')") == "true", "selection failed")
        page.click("[data-testid=size-toggle-men]")
        page.screenshot(path=f"first_screen_375x{height}.png")
        page.screenshot(path=f"full_375x{height}.png", full_page=True)
        ctx.close()
    browser.close()

print("PROBLEMS:" if problems else "ALL CHECKS PASSED")
for m in problems:
    print(" -", m)
