#!/usr/bin/env python3
"""Check every product image actually loads, and optionally pull them local.

Two problems this solves.

First, the catalogue points at images on someone else's server. When one of
those URLs dies the card silently falls back to a generated plate — the page
still looks fine, so nobody notices the shop lost its photography. This script
requests every image and reports the dead ones.

Second, hotlinking is a bad foundation for a shop: the host can rate-limit,
rewrite or remove an image at any time, and pages that embed off-site images
break under a strict content policy. `--download` fetches each image into
assets/photos/ and rewrites the catalogue to point at the local copy, so the
shop owns its own pictures.

    python3 tools/check_images.py              # report only
    python3 tools/check_images.py --download   # fetch local copies and rewrite

Run it where the network is open — CI is fine, a locked-down sandbox is not.
A network failure is reported, never guessed at: an image this script could not
reach is listed as UNREACHABLE, not as broken.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOGUE = os.path.join(ROOT, "data", "products.json")
PHOTO_DIR = os.path.join(ROOT, "assets", "photos")
TIMEOUT = 25
AGENT = "all-the-rage-image-check/1.0"

CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/avif": ".avif",
    "image/gif": ".gif",
}


def load() -> dict:
    with open(CATALOGUE, encoding="utf-8") as fh:
        return json.load(fh)


def save(doc: dict) -> None:
    with open(CATALOGUE, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def fetch(url: str) -> tuple[bytes | None, str, str]:
    """Return (body, content_type, error). body is None when it could not load."""
    request = urllib.request.Request(url, headers={"User-Agent": AGENT})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.read(), response.headers.get("Content-Type", ""), ""
    except urllib.error.HTTPError as exc:
        return None, "", f"HTTP {exc.code}"
    except urllib.error.URLError as exc:
        return None, "", f"unreachable: {exc.reason}"
    except Exception as exc:  # noqa: BLE001 - report, never crash the build
        return None, "", f"error: {exc!r}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="save local copies and rewrite the catalogue")
    parser.add_argument("--strict", action="store_true", help="exit non-zero if any image is broken")
    args = parser.parse_args()

    doc = load()
    remote = [p for p in doc["products"] if (p.get("image") or "").startswith("http")]
    local = [p for p in doc["products"] if p.get("image") and not p["image"].startswith("http")]
    none = [p for p in doc["products"] if not p.get("image")]

    print(f"{len(doc['products'])} products: {len(remote)} remote images, "
          f"{len(local)} local, {len(none)} without one.")
    if not remote:
        print("Nothing to check.")
        return 0

    broken, unreachable, ok = [], [], []
    if args.download:
        os.makedirs(PHOTO_DIR, exist_ok=True)

    for product in remote:
        body, ctype, error = fetch(product["image"])
        if body is None:
            bucket = unreachable if error.startswith("unreachable") else broken
            bucket.append((product["slug"], error))
            print(f"  {'?' if bucket is unreachable else 'x'} {product['slug']}: {error}")
            continue

        base = ctype.split(";")[0].strip().lower()
        if not base.startswith("image/") or len(body) < 1024:
            broken.append((product["slug"], f"not an image ({base or 'no type'}, {len(body)} bytes)"))
            print(f"  x {product['slug']}: not an image ({base or 'no type'}, {len(body)} bytes)")
            continue

        ok.append(product["slug"])
        if args.download:
            name = product["slug"] + CONTENT_TYPES.get(base, ".jpg")
            with open(os.path.join(PHOTO_DIR, name), "wb") as fh:
                fh.write(body)
            product["image"] = f"/assets/photos/{name}"
            print(f"  saved {name} ({len(body) // 1024} KB)")
        else:
            print(f"  ok {product['slug']} ({len(body) // 1024} KB)")

    if args.download and ok:
        save(doc)
        print(f"\nCatalogue rewritten: {len(ok)} products now use local images.")
        print("The shop no longer depends on anyone else's server for its photography.")

    print(f"\n{len(ok)} ok, {len(broken)} broken, {len(unreachable)} unreachable.")
    for slug, why in broken:
        print(f"  BROKEN {slug}: {why}", file=sys.stderr)
    for slug, why in unreachable:
        print(f"  UNREACHABLE {slug}: {why} (network, not necessarily a bad URL)", file=sys.stderr)

    if broken:
        print("\nA broken image is invisible on the site — the card quietly falls back to its "
              "generated plate. Fix the URL or clear the field.", file=sys.stderr)
    return 1 if (broken and args.strict) else 0


if __name__ == "__main__":
    raise SystemExit(main())
