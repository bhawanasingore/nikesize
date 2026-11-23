"""Stress test: does the size grid move if the price, or the price's font, arrives late?

Same Slow 4G phone settings as trace_page.py. Scenarios:
  late_text: the page's HTML is served with an empty price; React fills it in when its JS loads.
  late_font: 2 s after load starts, the price switches to a different font (like a web font swapping in).
"""
import sys
from playwright.sync_api import sync_playwright

KBPS = 1024 / 8
INIT = open(__import__("pathlib").Path(__file__).with_name("trace_page.py")).read().split('INIT = r"""')[1].split('"""')[0]
FONT_SWAP = """
setTimeout(() => {
  const p = document.querySelector('[data-testid="price"]');
  if (p) { p.style.fontFamily = '"DejaVu Serif", Georgia, serif'; p.style.fontSize = '20px'; p.style.letterSpacing = '1px'; }
}, 2000);
"""

def run(url, scenario):
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        ctx = browser.new_context(viewport={"width": 375, "height": 812}, device_scale_factor=3,
                                  is_mobile=True, has_touch=True)
        page = ctx.new_page()
        page.add_init_script(INIT)
        if scenario == "late_font":
            page.add_init_script(FONT_SWAP)
        if scenario == "late_text":
            def blank_price(route):
                resp = route.fetch()
                html = resp.text()
                marker = 'data-testid="price">'
                i = html.index(marker) + len(marker)
                j = html.index("</span>", i)
                route.fulfill(response=resp, body=html[:i] + html[j:])
            page.route(url, blank_price)
        cdp = ctx.new_cdp_session(page)
        cdp.send("Network.enable")
        cdp.send("Network.setCacheDisabled", {"cacheDisabled": True})
        cdp.send("Network.emulateNetworkConditions", {"offline": False, "latency": 562.5,
            "downloadThroughput": 1474.56 * KBPS, "uploadThroughput": 675 * KBPS})
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})
        page.goto(url, wait_until="load", timeout=120000)
        page.wait_for_timeout(3500)
        d = page.evaluate("({grid: window.__grid, shifts: window.__shifts})")
        price = page.inner_text('[data-testid="price"]')
        browser.close()
    g = d["grid"]
    moves = [(b["t"], b["top"] - a["top"]) for a, b in zip(g, g[1:])]
    total = sum(abs(m) for _, m in moves)
    detail = "; ".join(f"{t:.0f} ms {m:+.1f}px" for t, m in moves) or "none"
    srcs = "; ".join(f"{s['t']:.0f} ms " + ", ".join(f"{x['node']} {x['prevY']:.0f}->{x['curY']:.0f}" for x in s["sources"]) for s in d["shifts"]) or "none"
    print(f"{scenario:9} | price at end '{price}' | grid start y={g[0]['top']:.0f} | moves: {detail} | total {total:.1f}px | shifts: {srcs}")

for label, url in (("BEFORE fix", sys.argv[1]), ("AFTER fix ", sys.argv[2])):
    print(f"== {label}: {url}")
    for scenario in ("late_text", "late_font"):
        run(url, scenario)
