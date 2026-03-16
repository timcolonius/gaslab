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
      body {
        margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
          Roboto, Helvetica, Arial, sans-serif;
        background: #f9fafb;
        color: #374151;
      }

      .header {
        background: #f3f4f6;
        border-bottom: 1px solid #e5e7eb;
        text-align: center;
      }

      .banner {
        width: 100%;
        max-height: 150px;
        object-fit: contain;
      }

      .container {
        max-width: 1100px;
        margin: auto;
        padding: 30px 20px 10px 20px;
      }

      .title {
        font-size: 30px;
        margin-bottom: 5px;
      }

      .subtitle {
        color: #6b7280;
        margin-bottom: 20px;
      }

      .buttons {
        margin-bottom: 25px;
      }

      .button {
        display: inline-block;
        padding: 10px 18px;
        margin-right: 10px;
        background: #374151;
        color: white;
        text-decoration: none;
        border-radius: 6px;
        font-size: 15px;
      }

      .button.secondary {
        background: #6b7280;
      }

      .description {
        max-width: 700px;
        margin-bottom: 30px;
        line-height: 1.5;
      }

      .footer {
        text-align: center;
        margin-top: 25px;
        padding: 20px;
        font-size: 13px;
        color: #9ca3af;
      }
    </style>
  </head>
  <body>
    <div class="header">
      <img src="assets/gaslab_banner.png" class="banner" alt="GasLab banner" />
    </div>

    <div class="container">
      <div class="title">GasLab</div>
      <div class="subtitle">Interactive Compressible Flow Explorer</div>

      <div class="buttons">
        <a class="button" href="app/" target="_blank" rel="noopener">Launch App</a>
        <a class="button secondary" href="https://github.com/timcolonius/gaslab" target="_blank" rel="noopener">View Source on GitHub</a>
      </div>

      <div class="description">
        GasLab is a browser-based interactive tool for exploring compressible flow processes,
        including shocks, Prandtl-Meyer expansions, quasi-one-dimensional area change,
        Fanno flow, and Rayleigh flow.
        <br /><br />
        Build flow processes graphically, inspect the resulting states, and export the
        equivalent Python commands for further analysis.
      </div>

      <div class="footer">
        Tim Colonius • California Institute of Technology
      </div>
    </div>
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
    root_assets = DOCS / "assets"
    root_assets.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ASSETS / "gaslab_banner.png", root_assets / "gaslab_banner.png")
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
    print(f"Copied assets to: {DOCS / 'assets'} and {APP_DOCS / 'assets'}")
    print(f"Wrote Pages marker: {DOCS / '.nojekyll'}")
    print(f"Wrote app entrypoint: {APP_DOCS / 'index.html'}")
    print(f"Wrote landing page: {DOCS / 'index.html'}")


if __name__ == "__main__":
    main()
