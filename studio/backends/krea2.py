"""Krea 2 Turbo backend — wraps the `krea2-alis-mlx` package (the pure-MLX port).

Weights are pulled from Hugging Face on first use (cached under ~/.cache/krea2_alis_mlx);
drop a transformer_*.safetensors in the working directory to use a local copy instead.
"""

from __future__ import annotations

import os

from .base import Backend


class Krea2Backend(Backend):
    id = "krea2-turbo"
    label = "Krea 2 Turbo"
    variants = [
        {"id": "8bit", "label": "8-bit · best quality"},
        {"id": "mixed-4-8", "label": "mixed-4/8 · smaller"},
    ]
    sizes = [512, 768, 1024]
    default_size = 1024
    default_steps = 8
    max_images = 4

    @classmethod
    def is_available(cls) -> bool:
        try:
            import krea2.pipeline  # noqa: F401
            return True
        except Exception:
            return False

    def __init__(self):
        self._pipe = None
        self._variant = None

    def _get(self, variant: str):
        import gc
        import mlx.core as mx
        from krea2.pipeline import Krea2Pipeline, resolve_weights

        if self._pipe is None or self._variant != variant:
            prec, path = resolve_weights(os.getcwd(), precision=variant, download=True)
            # free the previous build before loading another — two 12.9B transformers won't fit
            self._pipe, self._variant = None, None
            gc.collect()
            mx.clear_cache()
            self._pipe = Krea2Pipeline(path, precision=prec, base_dir=os.environ.get("KREA2_BASE_DIR"))
            self._variant = prec
        return self._pipe

    def generate(self, *, prompt, variant, width, height, steps, seed, num_images, step_callback):
        pipe = self._get(variant)
        return pipe.generate(prompt, width=width, height=height, steps=steps, seed=seed,
                             num_images=num_images, step_callback=step_callback)
