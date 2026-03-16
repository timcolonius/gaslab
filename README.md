# GasLab

GasLab is a browser-delivered compressible-flow teaching app built with Panel,
Pyodide, and the local `gaslab` Python package.

## GitHub Pages Layout

GitHub Pages serves this site from `docs/`.

- Landing page: `/`
- GasLab app: `/app/`

The deployment workflow builds the static Panel export into `docs/app/` and
generates a small landing page at `docs/index.html` that embeds the app in an
iframe.
