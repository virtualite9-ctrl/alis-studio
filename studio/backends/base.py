"""Backend interface — a pluggable image-generation model.

To add a model to Alis Studio, drop a `studio/backends/<name>.py` that subclasses Backend,
implements `generate(...)`, and register it in `studio/registry.py`. The web UI discovers
registered backends via `/api/models` and builds its model dropdown automatically — no UI
changes needed.
"""

from __future__ import annotations


class Backend:
    id = ""                     # stable id, e.g. "krea2-turbo"
    label = ""                  # display name, e.g. "Krea 2 Turbo"
    variants: list[dict] = []   # selectable builds: [{"id": "8bit", "label": "8-bit · best quality"}]
    sizes: list[int] = [512, 768, 1024]
    default_size = 1024
    default_steps = 8
    max_steps = 50
    max_images = 4

    @classmethod
    def is_available(cls) -> bool:
        """True if this backend's dependencies are importable. Unavailable backends are
        skipped at registration so the app still runs with whatever is installed."""
        return True

    def meta(self) -> dict:
        return {
            "id": self.id, "label": self.label, "variants": self.variants,
            "sizes": self.sizes, "default_size": self.default_size,
            "default_steps": self.default_steps, "max_steps": self.max_steps,
            "max_images": self.max_images,
        }

    def generate(self, *, prompt, variant, width, height, steps, seed, num_images, step_callback):
        """Return a list of PIL.Image. Call step_callback(step, total) per denoising step
        so the UI can show live progress."""
        raise NotImplementedError
