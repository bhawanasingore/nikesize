"""Record a phone performance trace and log every movement of the size grid.

Settings match the Web Platform Slow 4G mobile profile (DevTools / real-browser values):
375 x 812 CSS px, 3x DPR, mobile on, latency 562.5 ms (= 150 ms RTT x 3.75),
download 1474.56 Kbps, upload 675 Kbps, CPU slowdown 4x, cache off.
"""
import json, sys
from playwright.sync_api import sync_playwright

URL = sys.argv[1]
RUNS = int(sys.argv[2]) if len(sys.argv) > 2 else 3
KBPS = 1024 / 8  # Kbps -> bytes/s (same conversion Lighthouse uses)

INIT = r"""
(() => {
  const label = (n) => {
    if (!n) return null;
    if (n.nodeType !== 1) return n.nodeName;
    return n.getAttribute('data-testid') || (n.tagName.toLowerCase() + (n.className ? '.' + String(n.className).split(' ')[0] : ''));
  };
  window.__shifts = []; window.__grid = []; window.__lcp = []; window.__paint = [];
  new PerformanceObserver((list) => {
    for (const e of list.getEntries()) {
      window.__shifts.push({ t: e.startTime, value: e.value, input: e.hadRecentInput,
        sources: (e.sources || []).map((s) => ({ node: label(s.node),
          prevY: s.previousRect.y, curY: s.currentRect.y, prevH: s.previousRect.height, curH: s.currentRect.height })) });
    }
  }).observe({ type: 'layout-shift', buffered: true });
  new PerformanceObserver((list) => {
    for (const e of list.getEntries()) window.__lcp.push({ t: e.startTime, el: label(e.element), size: e.size });
  }).observe({ type: 'largest-contentful-paint', buffered: true });
  new PerformanceObserver((list) => {
    for (const e of list.getEntries()) window.__paint.push({ name: e.name, t: e.startTime });
  }).observe({ type: 'paint', buffered: true });
  const tick = () => {
    const g = document.querySelector('[data-testid="size-grid"]');
    if (g) {
      const top = g.getBoundingClientRect().top + window.scrollY;
      const last = window.__grid[window.__grid.length - 1];
      if (!last || Math.abs(last.top - top) > 0.01) window.__grid.push({ t: performance.now(), top });
    }
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
})();
"""

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")
    results = []
    for run in range(1, RUNS + 1):
        ctx = browser.new_context(viewport={"width": 375, "height": 812}, device_scale_factor=3,
                                  is_mobile=True, has_touch=True)
        page = ctx.new_page()
        page.add_init_script(INIT)
        cdp = ctx.new_cdp_session(page)
        cdp.send("Network.enable")
        cdp.send("Network.setCacheDisabled", {"cacheDisabled": True})
        cdp.send("Network.emulateNetworkConditions", {
            "offline": False, "latency": 562.5,
            "downloadThroughput": 1474.56 * KBPS, "uploadThroughput": 675 * KBPS})
        cdp.send("Emulation.setCPUThrottlingRate", {"rate": 4})

        trace_path = f"pegasus43_trace_run{run}.json"
        browser.start_tracing(page=page, path=trace_path, screenshots=True)
        page.goto(URL, wait_until="load", timeout=120000)
        page.wait_for_timeout(3000)  # keep watching after load for late shifts
        nav = page.evaluate("(() => { const n = performance.getEntriesByType('navigation')[0]; return {dcl: n.domContentLoadedEventEnd, load: n.loadEventEnd}; })()")
        data = page.evaluate("({shifts: window.__shifts, grid: window.__grid, lcp: window.__lcp, paint: window.__paint})")
        browser.stop_tracing()
        ctx.close()
        data["nav"] = nav
        data["run"] = run
        results.append(data)

        grid = data["grid"]
        moves = [(b["t"], b["top"] - a["top"]) for a, b in zip(grid, grid[1:])]
        fcp = next((x["t"] for x in data["paint"] if x["name"] == "first-contentful-paint"), None)
        print(f"--- run {run} ---")
        print(f"FCP {fcp:.0f} ms | DOMContentLoaded {nav['dcl']:.0f} ms | load {nav['load']:.0f} ms")
        print("LCP:", ", ".join(f"{x['el']} at {x['t']:.0f} ms ({x['size']} px²)" for x in data["lcp"]))
        print(f"grid top first seen at {grid[0]['t']:.0f} ms, y={grid[0]['top']:.1f}px" if grid else "grid never seen")
        print(f"grid movements after first paint: {len(moves)}; total {sum(abs(d) for _, d in moves):.1f}px")
        for t, d in moves:
            print(f"   {t:.0f} ms: moved {d:+.1f}px")
        print(f"layout-shift entries: {len(data['shifts'])}; CLS sum {sum(s['value'] for s in data['shifts'] if not s['input']):.4f}")
        for s in data["shifts"]:
            print(f"   {s['t']:.0f} ms value {s['value']:.4f}: " + "; ".join(
                f"{x['node']} y {x['prevY']:.0f}->{x['curY']:.0f}" for x in s["sources"]))
    json.dump(results, open("pegasus43_trace_summary.json", "w"), indent=2)
    browser.close()
