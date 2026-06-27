"""Optional local prompt enhancer — translate a non-English prompt to English and lightly enrich
it into a vivid image caption, using a small on-device MLX LLM.

OPTIONAL by design: mlx-lm is lazy-imported, so the dependency-light server runs fine without it.
Enable with `pip install "alis-studio[rewrite]"` (or `pip install mlx-lm`). Everything is on-device —
no prompt ever leaves the machine. The first call downloads the model (~2.3 GB) from Hugging Face.
"""

from __future__ import annotations

import importlib.util
import threading

# Newest light, multilingual instruct model with explicit translation strength (2025-07 refresh);
# same Qwen lineage as the image text-encoders, ~2.3 GB at 4-bit.
MODEL = "mlx-community/Qwen3-4B-Instruct-2507-4bit"

_SYSTEM = (
    "You rewrite text-to-image prompts. Given the user's prompt in any language:\n"
    "- If it is not English, translate it into natural English.\n"
    "- Lightly enrich it into a vivid, concrete image caption (subject, setting, lighting, mood, "
    "style) without inventing unrelated content or changing the user's intent.\n"
    "- Reply with ONLY the rewritten English prompt — no quotes, no preface, no explanation."
)

_LOCK = threading.Lock()       # serialize model load + generation (shared one GPU)
_STATE: dict = {"model": None, "tok": None}
_CACHE: dict[str, str] = {}    # prompt -> rewritten; greedy + cached == deterministic & reproducible


def is_available() -> bool:
    """True if mlx-lm is importable (the optional `rewrite` extra is installed)."""
    return importlib.util.find_spec("mlx_lm") is not None


def _ensure_loaded():
    if _STATE["model"] is None:
        from mlx_lm import load
        _STATE["model"], _STATE["tok"] = load(MODEL)
    return _STATE["model"], _STATE["tok"]


def enhance(prompt: str) -> str:
    """Translate-to-English + lightly enrich `prompt`. Deterministic (greedy) and cached, so the
    same input always yields the same English — preserving seed reproducibility. Raises
    RuntimeError with an actionable message if mlx-lm isn't installed."""
    prompt = (prompt or "").strip()
    if not prompt:
        return prompt
    if prompt in _CACHE:
        return _CACHE[prompt]
    if not is_available():
        raise RuntimeError('Prompt enhancer needs mlx-lm — install with: pip install "alis-studio[rewrite]"')
    with _LOCK:
        if prompt in _CACHE:        # another request filled it while we waited on the lock
            return _CACHE[prompt]
        from mlx_lm import generate
        from mlx_lm.sample_utils import make_sampler
        model, tok = _ensure_loaded()
        text = tok.apply_chat_template(
            [{"role": "system", "content": _SYSTEM}, {"role": "user", "content": prompt}],
            add_generation_prompt=True,
        )
        out = generate(model, tok, text, max_tokens=256, sampler=make_sampler(temp=0.0), verbose=False)
        out = (out or "").strip()
        if "</think>" in out:        # defensive: strip any reasoning block (the Instruct-2507 model shouldn't emit one)
            out = out.rsplit("</think>", 1)[-1].strip()
        out = out.strip('"').strip()
        _CACHE[prompt] = out or prompt
        return _CACHE[prompt]
