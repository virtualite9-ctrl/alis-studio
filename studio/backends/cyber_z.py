"""CyberRealistic Z — a Civitai community finetune of Z-Image-Turbo, adopted as a built-in model.

CyberRealistic Z-Image Turbo (creator Cyberdelia, https://civitai.com/models/2218365) is the
photorealism-focused finetune of Tongyi's Z-Image-Turbo: same ~6B DiT / ~9-step / no-CFG /
multilingual recipe, tuned for natural skin, lighting, and film-like texture. v4.0 was taken from
the creator's own HF mirror (cyberdelia/cyberrealistic_zimage), converted from the ComfyUI
single-file layout to mflux's layout (fused qkv split, prefix strip — with a both-ways key
completeness check, since mflux silently skips unmapped keys), and re-hosted pre-quantized at
avlp12/CyberRealistic-Z-Image-Turbo-v4-mflux-{4bit,8bit} under CreativeML OpenRAIL-M.

Everything else (params, loading, img2img, VAE-tiling memory policy) is inherited from the
Z-Image backend — this is a BUILDS + metadata override.
"""

from __future__ import annotations

from .z_image import ZImageTurboBackend


class CyberRealisticZBackend(ZImageTurboBackend):
    id = "cyberrealistic-z"
    label = "CyberRealistic Z"
    min_ram_gib = 16   # same footprint as Z-Image Turbo: 4-bit pipeline ~6 GB resident
    prompt_note = "Photorealism finetune of Z-Image Turbo — best for people/scenes. Korean prompts OK (Qwen3 encoder)."
    info = "CreativeML OpenRAIL-M · Civitai photorealism finetune by Cyberdelia · downloads on first use"
    BUILDS = {
        "4bit": ("avlp12/CyberRealistic-Z-Image-Turbo-v4-mflux-4bit", None),
        "8bit": ("avlp12/CyberRealistic-Z-Image-Turbo-v4-mflux-8bit", None),
    }
    variants = [
        {"id": "4bit", "label": "4-bit · ~5.5 GB · 16 GB-Mac friendly"},
        {"id": "8bit", "label": "8-bit · ~10 GB · wants ≥ 24 GB RAM", "min_ram": 24},
    ]
