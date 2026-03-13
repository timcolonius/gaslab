# Static Export Assessment

This Panel app is a candidate for browser-only deployment through Panel's
Pyodide export path, because all application logic is implemented in Python
callbacks and the app does not rely on:

- filesystem writes at runtime
- database access
- network calls
- subprocesses
- server session state outside the current document

## Features that still require Python execution

The app is not a plain HTML/JavaScript static site. It still requires a Python
runtime, but that runtime can potentially be provided in the browser via
Pyodide instead of a live server.

Current app features that require Python execution:

- all `param.watch(...)` callbacks in `app.py`
- all process application methods in `GasLabApp`
- gas-dynamics computations in `src/gaslab/state.py`
- root solves via `scipy.optimize.root_scalar` in `src/gaslab/relations.py`
- plot generation in `src/gaslab/plotting.py`

Features that are already browser-native:

- clipboard copy button for the Python expression
- HTML table rendering
- local banner image rendering

## Likely blockers or risks for Pyodide deployment

The main risks are package support and payload size, not app architecture.

Expected browser/Pyodide dependencies:

- `numpy`
- `scipy`
- `matplotlib`
- `panel`
- `bokeh`

Potential issues:

- `scipy` is heavy and increases startup time substantially
- `matplotlib` in the browser can be slower than on CPython
- Pyodide support depends on the installed Panel/Bokeh version used for export
- local package discovery for `gaslab` must be included in the exported app

## Why the first local test failed

The generated `docs/app.js` asks Pyodide to install:

- Panel and Bokeh from CDN wheels
- `pyodide-http`
- `gaslab`

The `gaslab` entry is the immediate problem. In a browser export, that is
treated as an external package name, but this repository's package is only
available locally unless you build and bundle a wheel.

There is also a second packaging issue:

- `assets/gaslab_banner.png` is not automatically copied into `docs/assets/`

So the failure you saw does not imply that a live Python server is required.
It means the exported browser bundle is incomplete.

## Minimal local test

If Panel is installed in the environment, try:

```bash
panel convert app.py --to pyodide-worker --out docs
python scripts/prepare_static_export.py
python -m http.server 8000 -d docs
```

Then open:

```text
http://localhost:8000/app.html
```

If the export succeeds and the app loads, the app is a viable browser-only
candidate. If it fails, the failure is most likely due to package support in
the chosen Panel/Pyodide toolchain rather than the current app structure.

The helper script added here:

- builds a local `gaslab` wheel with `pip wheel` if `dist/` is empty
- copies the local `gaslab` wheel from `dist/` into `docs/`
- patches `docs/app.js` so Pyodide installs that local wheel instead of trying
  to fetch `gaslab` as a remote package
- copies the banner asset into `docs/assets/`
