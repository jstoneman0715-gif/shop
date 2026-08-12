#!/usr/bin/env python3
"""Push shop URLs to search engines via IndexNow.

IndexNow is the one push-notification protocol still supported by major engines
(Bing, Yandex, Seznam, Naver) — Google retired its sitemap ping endpoint in 2023
and now discovers new URLs from robots.txt + Search Console instead, which the
build already wires up.

The key is public by design: it lives at <site>/<key>.txt so the engine can
verify that whoever submitted the URLs controls the site.

Run:  python3 tools/submit_indexnow.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENDPOINT = "https://api.indexnow.org/IndexNow"

with open(os.path.join(ROOT, "data", "config.json"), encoding="utf-8") as fh:
    BASE = json.load(fh)["store"]["base_url"].rstrip("/")

HOST = BASE.split("//", 1)[1].split("/", 1)[0]


def find_key() -> str | None:
    """The IndexNow key file is a bare <32-hex>.txt at the repository root."""
    for name in sorted(os.listdir(ROOT)):
        if re.fullmatch(r"[0-9a-f]{8,128}\.txt", name):
            with open(os.path.join(ROOT, name), encoding="utf-8") as fh:
                key = fh.read().strip()
            if key and name.startswith(key):
                return key
    return None


def sitemap_urls() -> list[str]:
    urls: list[str] = []
    for name in ("sitemap-shop.xml", "sitemap.xml"):
        path = os.path.join(ROOT, name)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            urls += re.findall(r"<loc>(.*?)</loc>", fh.read())
    # De-duplicate, keep order, cap at the protocol's per-request limit.
    seen, unique = set(), []
    for candidate in urls:
        if candidate not in seen:
            seen.add(candidate)
            unique.append(candidate)
    return unique[:10000]


def main() -> int:
    key = find_key()
    if not key:
        print("No IndexNow key file found at the repository root — skipping submission.")
        return 0

    urls = sitemap_urls()
    if not urls:
        print("No sitemap URLs to submit — skipping.")
        return 0

    payload = json.dumps(
        {
            "host": HOST,
            "key": key,
            "keyLocation": f"{BASE}/{key}.txt",
            "urlList": urls,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        ENDPOINT,
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            print(f"IndexNow accepted {len(urls)} URLs (HTTP {response.status}).")
    except urllib.error.HTTPError as exc:
        # 422 usually means the key file is not live yet — expected on a first run
        # before the branch is merged and published. Never fail the build for it.
        print(f"IndexNow returned HTTP {exc.code}: {exc.reason}", file=sys.stderr)
        print("This does not affect the published site. Check that "
              f"{BASE}/{key}.txt is reachable.", file=sys.stderr)
    except urllib.error.URLError as exc:
        print(f"IndexNow unreachable ({exc.reason}) — skipping.", file=sys.stderr)
    except Exception as exc:  # noqa: BLE001 - notifying engines is best effort
        print(f"IndexNow submission failed ({exc!r}) — skipping.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
