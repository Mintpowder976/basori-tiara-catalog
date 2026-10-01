#!/usr/bin/env python3
"""Validate catalog invariants without third-party dependencies."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "data" / "catalog.json"
REQUIRED = {
    "id",
    "name_ja",
    "name_zh",
    "category",
    "campaign",
    "campaign_year",
    "manufacturer",
    "variant",
    "sale_format",
    "spec",
    "release_date",
    "list_price_yen",
    "official_status",
    "verification",
    "images",
    "sales",
    "sources",
    "tags",
    "notes",
}
SALE_FORMATS = {"single", "random", "set"}
VERIFICATION = {"confirmed_text", "confirmed_image", "seller_claim", "unverified"}
IMAGE_SIGNATURES = (b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"RIFF")


def valid_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def main() -> int:
    data = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    errors: list[str] = []
    ids: set[str] = set()
    thumbnail_count = 0

    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    for index, item in enumerate(data.get("items", []), start=1):
        prefix = f"items[{index}]"
        missing = REQUIRED - item.keys()
        if missing:
            errors.append(f"{prefix}: missing {', '.join(sorted(missing))}")
        item_id = item.get("id")
        if item_id in ids:
            errors.append(f"{prefix}: duplicate id {item_id}")
        ids.add(item_id)

        sale_type = item.get("sale_format", {}).get("type")
        if sale_type not in SALE_FORMATS:
            errors.append(f"{prefix}: unsupported sale format {sale_type}")
        if item.get("verification") not in VERIFICATION:
            errors.append(f"{prefix}: unsupported verification value")
        price = item.get("list_price_yen")
        if price is not None and (not isinstance(price, int) or price < 0):
            errors.append(f"{prefix}: list_price_yen must be a non-negative integer or null")

        for image in item.get("images", []):
            image_path = ROOT / image.get("path", "")
            if not image_path.is_file():
                errors.append(f"{prefix}: image not found: {image_path.relative_to(ROOT)}")
            elif image_path.stat().st_size < 1024 or not image_path.read_bytes()[:12].startswith(IMAGE_SIGNATURES):
                errors.append(f"{prefix}: invalid local image: {image_path.relative_to(ROOT)}")
            if not valid_url(image.get("source_url")):
                errors.append(f"{prefix}: invalid image source URL")

            thumbnail_path = ROOT / image.get("thumbnail_path", "")
            if not image.get("thumbnail_path") or not thumbnail_path.is_file():
                errors.append(f"{prefix}: thumbnail not found")
            elif thumbnail_path.stat().st_size < 512 or not thumbnail_path.read_bytes()[:12].startswith(b"RIFF"):
                errors.append(f"{prefix}: invalid WebP thumbnail: {thumbnail_path.relative_to(ROOT)}")
            else:
                thumbnail_count += 1

        for source in item.get("sources", []):
            if not valid_url(source.get("url")):
                errors.append(f"{prefix}: invalid source URL")

    if errors:
        print("Catalog validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    with_images = sum(bool(item["images"]) for item in data["items"])
    print(
        f"OK: {len(ids)} items, {with_images} with local images, "
        f"{thumbnail_count} thumbnails, all IDs unique"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
