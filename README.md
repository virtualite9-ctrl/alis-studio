# Alis Studio

A local, **model-agnostic** image-generation studio for **Apple silicon** — a clean, native-feeling
web UI that runs text-to-image models entirely on your Mac with [MLX](https://github.com/ml-explore/mlx).
No cloud, no accounts, your images never leave your machine.

The first model it ships with is **[Krea 2 Turbo](https://github.com/avlp12/krea2_alis_mlx)**
(a 12.9B text-to-image model, pure-MLX). Other models plug in as small backends — see
[Adding a model](#adding-a-model).

---

## Quickstart

**Requires an Apple-silicon Mac (M1+) with ≥ 24 GB unified memory.** On macOS use `python3`.

```bash
git clone https://github.com/avlp12/alis-studio.git
cd alis-studio
python3 -m pip install -r requirements.txt
python3 app.py            # opens http://localhost:7860 in your browser
```

Type a prompt, pick a model, click **Generate**. The first run downloads the model weights from
Hugging Face (a few minutes); after that it's instant to start. A 1024² image takes ~50 s on an
M3 Ultra (8-step Turbo; slower chips take longer).

- **Light + dark** follow your system appearance.
- **Live progress** — a per-step bar as the model denoises.
- **NSFW safety filter** runs by default (pure-MLX, no PyTorch); toggle it with the shield icon.
- Bind to your LAN with `KREA2_HOST=0.0.0.0 python3 app.py` (only on networks you trust); change
  the port with `ALIS_PORT=7861`.

---

## Models

The **model** dropdown is built from whatever backends are installed — the UI discovers them at
startup via `/api/models`, so adding a model needs no UI changes.

| Model | Backend | Notes |
|---|---|---|
| **Krea 2 Turbo** | `krea2-alis-mlx` | 8-bit (best quality) or mixed-4/8 (smaller). 8-step Turbo, no guidance. |

Switching models in the dropdown loads that build on first use (and frees the previous one).

---

## Adding a model

Drop a file in `studio/backends/`, subclass `Backend`, implement `generate(...)`, and register it.
That's the whole contract — the UI updates itself.

```python
# studio/backends/mymodel.py
from .base import Backend

class MyBackend(Backend):
    id = "my-model"
    label = "My Model"
    variants = [{"id": "default", "label": "default"}]
    sizes = [512, 1024]
    default_size = 1024
    default_steps = 20

    @classmethod
    def is_available(cls):
        try:
            import my_package  # noqa
            return True
        except Exception:
            return False

    def generate(self, *, prompt, variant, width, height, steps, seed, num_images, step_callback):
        # call step_callback(step, total) per denoising step for the live progress bar
        return [pil_image, ...]
```

Then add it to `studio/registry.py`:

```python
from .backends.mymodel import MyBackend
BACKENDS = [Krea2Backend, MyBackend]
```

Backends whose dependencies aren't installed are skipped automatically, so the app always runs
with whatever you have.

---

## How it works

- `app.py` → `studio/server.py` — a Python **standard-library** HTTP server (zero web dependencies).
  It serves `web/index.html`, lists models at `/api/models`, and streams generation as NDJSON from
  `/api/generate` (one line per denoising step, then the finished images as base64 PNGs).
- `studio/registry.py` — the list of available models.
- `studio/backends/` — one file per model; each wraps a model behind the small `Backend` interface.

Generation is serialized (one GPU, one job at a time). The NSFW filter is applied at the app level
to every backend's output, reusing Krea 2's pure-MLX classifier.

---

## Privacy & license

Everything runs **locally** — prompts and images never leave your Mac.

This application is **MIT** licensed ([`LICENSE`](LICENSE)). **Each model carries its own license:**
the Krea 2 Turbo backend uses weights under the
[Krea 2 Community License](https://krea.ai/krea-2-licensing) (commercial use requires annual revenue
under $1M; content filtering required for deployments — the built-in filter is on by default). You're
responsible for complying with the license of any model you load.

*Part of the **Alis** MLX line — see also [krea2_alis_mlx](https://github.com/avlp12/krea2_alis_mlx).*
