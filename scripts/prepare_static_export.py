#!/usr/bin/env python3
"""
Prepare a Panel Pyodide export for GitHub Pages.

Resulting layout:

- docs/index.html      -> hand-edited landing page
- docs/.nojekyll       -> Pages marker
- docs/assets/         -> landing-page assets
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

    app_assets = APP_DOCS / "assets"
    app_assets.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ASSETS / "gaslab_banner.png", app_assets / "gaslab_banner.png")


def write_pages_markers() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / ".nojekyll").write_text("")


def ensure_app_index() -> None:
    app_html = APP_DOCS / "app.html"
    index_html = APP_DOCS / "index.html"
    if not app_html.exists():
        raise FileNotFoundError("docs/app/app.html not found after Panel export.")
    shutil.copy2(app_html, index_html)


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

    print(f"Copied wheel: {target_wheel}")
    print(f"Patched worker: {worker_js}")
    print(f"Copied assets to: {DOCS / 'assets'} and {APP_DOCS / 'assets'}")
    print(f"Wrote Pages marker: {DOCS / '.nojekyll'}")
    print(f"Wrote app entrypoint: {APP_DOCS / 'index.html'}")


if __name__ == "__main__":
    main()
