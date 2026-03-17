# GasLab

GasLab is a browser-delivered compressible-flow teaching app built with Panel,
Pyodide, and the local `gaslab` Python package.

## GitHub Pages Layout

GitHub Pages serves this site from `docs/`.

- Landing page: `/`
- GasLab app: `/app/`

The deployment workflow builds the static Panel export into `docs/app/` and
keeps `docs/index.html` as a normal hand-edited landing page.

## Static Build

The optimized static export uses Panel's `pyodide-worker` target with compiled
Pyodide, PWA generation, prerendered content, and an explicit minimal
requirements list:

```bash
panel convert app.py \
  --to pyodide-worker \
  --compiled \
  --pwa \
  --disable-http-patch \
  --requirements scripts/pyodide_requirements.txt \
  --out docs/app
python scripts/prepare_static_export.py
```

For normal updates, use:

```bash
scripts/publish.sh "Describe the update"
```
