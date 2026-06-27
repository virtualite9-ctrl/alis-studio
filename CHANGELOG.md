# Changelog

All notable changes to Alis Studio are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project follows
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

The version lives in exactly one place — `studio/__version__` (in `studio/__init__.py`).
`pyproject.toml` reads it via `[tool.setuptools.dynamic]`, the server injects it into the
web UI, and the DMG build stamps it into the app bundle.

## [0.5.0] — 2026-06-27

### Added
- **Per-model prompt-language hint**: a one-line note under the prompt shows whether the active
  model understands non-English prompts natively (Krea 2 Turbo / Qwen-Image, via their Qwen text
  encoders) or works best in English (FLUX, via T5/CLIP) — so Korean users know Krea 2 Turbo and
  Qwen-Image take Korean directly, no translation needed.
- **Stop button**: while an image is generating, the Generate button becomes a Stop button.
  Clicking it cancels the run — the frontend aborts the request and `POST /api/cancel` flags the
  server, which halts at the next denoise step and reports `cancelled`. (Per-step backends like
  Krea 2 Turbo stop promptly; a fresh generation afterwards is unaffected.)
- App version is now shown in the UI — a small tag next to the brand in the top bar — and
  in the native window's title bar. New `GET /api/version` endpoint exposes it programmatically.
- **Self-contained `.dmg`**: `packaging/build_dmg.sh` builds an `Alis Studio.app` that bundles
  its own standalone Python interpreter **and every runtime dependency** (mlx, mflux, transformers,
  pywebview, the Krea 2 Turbo backend, …) under `Contents/Resources`. Double-click to run — no
  system Python, no `pip install`. The bundle is ad-hoc signed and wrapped in a drag-to-Applications
  disk image. `packaging/make_icon.py` renders the app's sparkle mark into `AppIcon.icns`.
  (Model **weights** are not bundled — they download from Hugging Face on the first generation.)

### Changed
- Single source of truth for the version: `pyproject.toml` no longer hard-codes it
  (`dynamic = ["version"]`), so the package version can never drift from `studio.__version__`.
- `pyproject.toml` uses the PEP 639 SPDX license expression (`license = "MIT"`) and requires
  `setuptools>=77`, replacing the deprecated `license = { text = "MIT" }` table form.

## [0.4.0] — 2026-06-27

### Added
- Native desktop app: runs in its own window via pywebview (WKWebView on macOS), no browser tab.

## [0.3.0] — 2026-06-27

### Added
- Multi-model support: Qwen-Image and FLUX (schnell/dev) backends alongside Krea 2 Turbo.
- Model names are shown in the UI; model picker reworked into a button + popover.

## [0.2.0] — 2026-06-27

### Added
- LM Studio-style detailed settings panel and an in-app model manager/downloader.

## [0.1.0] — 2026-06-27

### Added
- Initial release: a local, model-agnostic, standard-library image-generation studio for
  Apple silicon (MLX), with the pure-MLX Krea 2 Turbo backend.

[0.5.0]: https://github.com/avlp12/alis-studio/releases/tag/v0.5.0
[0.4.0]: https://github.com/avlp12/alis-studio/releases/tag/v0.4.0
[0.3.0]: https://github.com/avlp12/alis-studio/releases/tag/v0.3.0
[0.2.0]: https://github.com/avlp12/alis-studio/releases/tag/v0.2.0
[0.1.0]: https://github.com/avlp12/alis-studio/releases/tag/v0.1.0
