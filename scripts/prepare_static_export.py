#!/usr/bin/env python3
"""
Prepare a Panel Pyodide export for GitHub Pages.

Resulting layout:

- docs/index.html      -> landing page
- docs/.nojekyll       -> Pages marker
- docs/app/            -> static GasLab app
"""

from pathlib import Path
import shutil
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
APP_DOCS = DOCS / "app"
DIST = ROOT / "dist"
ASSETS = ROOT / "assets"

LANDING_PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>GasLab — Compressible Flow Explorer</title>
    <style>
      :root {
        color-scheme: light;
        --bg: #f8fafc;
        --panel: #ffffff;
        --text: #111827;
        --muted: #6b7280;
        --border: #d1d5db;
      }

      * { box-sizing: border-box; }

      body {
        margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: var(--bg);
        color: var(--text);
      }

      main {
        max-width: 1400px;
        margin: 0 auto;
        padding: 24px 20px 32px;
      }

      h1 {
        margin: 0 0 6px;
        font-size: clamp(1.8rem, 2.4vw, 2.5rem);
        font-weight: 650;
        letter-spacing: -0.02em;
      }

      p.meta {
        margin: 0 0 18px;
        color: var(--muted);
        font-size: 0.98rem;
      }

      p.linkline {
        margin: 0 0 12px;
        font-size: 0.95rem;
      }

      a {
        color: inherit;
      }

      .frame-wrap {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 12px;
        overflow: hidden;
      }

      iframe {
        display: block;
        width: 100%;
        height: 92vh;
        min-height: 820px;
        border: 0;
        background: white;
      }
    </style>
  </head>
  <body>
    <main>
      <h1>GasLab — Compressible Flow Explorer</h1>
      <p class="meta">Tim Colonius • Caltech</p>
      <p class="linkline"><a href="app/index.html" target="_blank" rel="noopener">Open GasLab in a new window</a></p>
      <div class="frame-wrap">
        <iframe src="app/index.html" title="GasLab"></iframe>
      </div>
    </main>
  </body>
</html>
"""


def build_local_wheel() -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, "-m", "pip", "wheel", ".", "-w", str(DIST), "--no-deps"],
        cwd=ROOT,
        check=True,
    )


def newest_wheel() -> Path:
    wheels = sorted(DIST.glob("gaslab-*.whl"))
    if not wheels:
        build_local_wheel()
        wheels = sorted(DIST.glob("gaslab-*.whl"))
    if not wheels:
        raise FileNotFoundError("No gaslab wheel found in dist/ after attempting a local wheel build.")
    return wheels[-1]


def patch_worker_js(worker_path: Path, wheel_name: str) -> None:
    text = worker_path.read_text()
    if "'gaslab'" not in text:
        raise RuntimeError(f"Could not find bare 'gaslab' dependency in {worker_path}")
    worker_path.write_text(text.replace("'gaslab'", f"'./{wheel_name}'", 1))


def copy_assets() -> None:
    target_assets = APP_DOCS / "assets"
    target_assets.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ASSETS / "gaslab_banner.png", target_assets / "gaslab_banner.png")


def write_pages_markers() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / ".nojekyll").write_text("")


def ensure_app_index() -> None:
    app_html = APP_DOCS / "app.html"
    index_html = APP_DOCS / "index.html"
    if not app_html.exists():
        raise FileNotFoundError("docs/app/app.html not found after Panel export.")
    shutil.copy2(app_html, index_html)


def write_landing_page() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "index.html").write_text(LANDING_PAGE)


def main() -> None:
    worker_js = APP_DOCS / "app.js"
    if not worker_js.exists():
        raise FileNotFoundError(
            "docs/app/app.js not found. Run `panel convert app.py --to pyodide-worker --out docs/app` first."
        )

    wheel = newest_wheel()
    target_wheel = APP_DOCS / wheel.name
    APP_DOCS.mkdir(parents=True, exist_ok=True)
    shutil.copy2(wheel, target_wheel)
    patch_worker_js(worker_js, wheel.name)
    copy_assets()
    write_pages_markers()
    ensure_app_index()
    write_landing_page()

    print(f"Copied wheel: {target_wheel}")
    print(f"Patched worker: {worker_js}")
    print(f"Copied assets to: {APP_DOCS / 'assets'}")
    print(f"Wrote Pages marker: {DOCS / '.nojekyll'}")
    print(f"Wrote app entrypoint: {APP_DOCS / 'index.html'}")
    print(f"Wrote landing page: {DOCS / 'index.html'}")


if __name__ == "__main__":
    main()
