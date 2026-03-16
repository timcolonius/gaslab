#!/usr/bin/env python3
"""
Prepare a Panel Pyodide export to use the local gaslab wheel and bundled assets.
"""

from pathlib import Path
import subprocess
import shutil
import sys


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DIST = ROOT / "dist"
ASSETS = ROOT / "assets"


def newest_wheel() -> Path:
    wheels = sorted(DIST.glob("gaslab-*.whl"))
    if not wheels:
        build_local_wheel()
        wheels = sorted(DIST.glob("gaslab-*.whl"))
    if not wheels:
        raise FileNotFoundError("No gaslab wheel found in dist/ after attempting a local wheel build.")
    return wheels[-1]


def build_local_wheel() -> None:
    DIST.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, "-m", "pip", "wheel", ".", "-w", str(DIST), "--no-deps"],
        cwd=ROOT,
        check=True,
    )


def patch_worker_js(worker_path: Path, wheel_name: str) -> None:
    text = worker_path.read_text()
    if "'gaslab'" not in text:
        raise RuntimeError("Could not find bare 'gaslab' dependency in docs/app.js")
    worker_path.write_text(text.replace("'gaslab'", f"'./{wheel_name}'", 1))


def copy_assets() -> None:
    target_assets = DOCS / "assets"
    target_assets.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ASSETS / "gaslab_banner.png", target_assets / "gaslab_banner.png")


def write_pages_markers() -> None:
    (DOCS / ".nojekyll").write_text("")


def main() -> None:
    worker_js = DOCS / "app.js"
    if not worker_js.exists():
        raise FileNotFoundError("docs/app.js not found. Run `panel convert app.py --to pyodide-worker --out docs` first.")

    wheel = newest_wheel()
    target_wheel = DOCS / wheel.name
    shutil.copy2(wheel, target_wheel)
    patch_worker_js(worker_js, wheel.name)
    copy_assets()
    write_pages_markers()

    print(f"Copied wheel: {target_wheel}")
    print(f"Patched worker: {worker_js}")
    print(f"Copied assets to: {DOCS / 'assets'}")
    print(f"Wrote Pages marker: {DOCS / '.nojekyll'}")


if __name__ == "__main__":
    main()
