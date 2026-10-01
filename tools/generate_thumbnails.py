#!/usr/bin/env python3
"""Generate lightweight list thumbnails and record them in catalog.json."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageOps


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "catalog.json"
THUMBNAIL_DIR = ROOT / "images" / "thumbs"
MAX_SIZE = (640, 640)


def main() -> None:
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)

    generated = 0
    for item in catalog["items"]:
        for index, image in enumerate(item.get("images", [])):
            source = ROOT / image["path"]
            if not source.is_file():
                print(f"SKIP missing: {image['path']}")
                continue

            suffix = f"-{index + 1}" if index else ""
            target = THUMBNAIL_DIR / f"{item['id']}{suffix}.webp"
            with Image.open(source) as opened:
                converted = ImageOps.exif_transpose(opened).convert("RGB")
                converted.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)
                converted.save(target, "WEBP", quality=72, method=6)

            image["thumbnail_path"] = target.relative_to(ROOT).as_posix()
            generated += 1

    CATALOG_PATH.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Generated {generated} thumbnails in {THUMBNAIL_DIR.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
