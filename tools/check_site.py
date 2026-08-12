#!/usr/bin/env python3
"""Post-build checks for the storefront.

Runs in CI after tools/build_site.py so a broken page can never reach the live
site: every JSON-LD block must parse, every internal link must resolve to a file
that exists, every page needs the SEO tags Google looks for, and the sitemap must
list only URLs that are actually published.

Run:  python3 tools/check_site.py
"""

from __future__ import annotations

import json
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, "data", "config.json"), encoding="utf-8") as fh:
    CFG = json.load(fh)

PREFIX = CFG["store"]["path_prefix"].rstrip("/")
SR = CFG["store"].get("store_root", "/")
BASE = CFG["store"]["base_url"].rstrip("/")

failures: list[str] = []
checked_pages = 0


def fail(msg: str) -> None:
    failures.append(msg)


class Extractor(HTMLParser):
    """Pulls the bits of a page the checks care about."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.imgs: list[str] = []
        self.canonical = ""
        self.description = ""
        self.robots = ""
        self.title_open = False
        self.title = ""
        self.jsonld: list[str] = []
        self._in_ld = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "img" and a.get("src"):
            self.imgs.append(a["src"])
            if not a.get("alt"):
                fail("image without alt text: " + a["src"])
        elif tag == "link" and a.get("rel") == "canonical":
            self.canonical = a.get("href", "")
        elif tag == "meta":
            if a.get("name") == "description":
                self.description = a.get("content", "")
            elif a.get("name") == "robots":
                self.robots = a.get("content", "")
        elif tag == "title":
            self.title_open = True
        elif tag == "script" and a.get("type") == "application/ld+json":
            self._in_ld = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.title_open = False
        elif tag == "script":
            self._in_ld = False

    def handle_data(self, data):
        if self.title_open:
            self.title += data
        elif self._in_ld:
            self.jsonld.append(data)


def local_path_for(href: str) -> str | None:
    """Map a site URL onto the file that should serve it, or None if external."""
    if href.startswith(("http://", "https://")):
        if not href.startswith(BASE):
            return None
        href = href[len(BASE) :] or "/"
    elif href.startswith(("mailto:", "tel:", "#", "javascript:")):
        return None
    href = href.split("#")[0].split("?")[0]
    if not href:
        return None
    if PREFIX and href.startswith(PREFIX):
        href = href[len(PREFIX) :] or "/"
    rel = href.lstrip("/")
    candidate = os.path.join(ROOT, rel)
    if href.endswith("/") or not os.path.splitext(rel)[1]:
        candidate = os.path.join(ROOT, rel, "index.html")
    return candidate


def check_page(path: str) -> None:
    global checked_pages
    checked_pages += 1
    rel = os.path.relpath(path, ROOT)
    with open(path, encoding="utf-8") as fh:
        raw = fh.read()

    parser = Extractor()
    parser.feed(raw)

    if not parser.title.strip():
        fail(f"{rel}: no <title>")
    elif len(parser.title) > 70:
        fail(f"{rel}: title is {len(parser.title)} chars (keep under ~70 for search results)")
    if not parser.description.strip():
        fail(f"{rel}: no meta description")
    elif len(parser.description) > 320:
        fail(f"{rel}: meta description is {len(parser.description)} chars (too long)")
    if not parser.canonical.startswith(BASE):
        fail(f"{rel}: canonical does not point at the live host ({parser.canonical!r})")

    if raw.count("<h1") > 1:
        fail(f"{rel}: more than one <h1>")

    for block in parser.jsonld:
        try:
            data = json.loads(block)
        except json.JSONDecodeError as exc:
            fail(f"{rel}: invalid JSON-LD ({exc})")
            continue
        if "@context" not in data or "@type" not in data:
            fail(f"{rel}: JSON-LD block missing @context/@type")

    for href in parser.links + parser.imgs:
        target = local_path_for(href)
        if target and not os.path.exists(target):
            fail(f"{rel}: broken internal link → {href}")


def check_svg_assets() -> None:
    """Artwork must be well-formed XML or browsers silently show a broken image."""
    import xml.etree.ElementTree as ET

    assets = os.path.join(ROOT, SR.strip("/"), "assets") if SR.strip("/") else os.path.join(ROOT, "assets")
    if not os.path.isdir(assets):
        fail("assets directory is missing")
        return
    for name in sorted(os.listdir(assets)):
        if not name.endswith(".svg"):
            continue
        try:
            ET.parse(os.path.join(assets, name))
        except ET.ParseError as exc:
            fail(f"assets/{name}: malformed SVG ({exc})")


def check_sitemap() -> None:
    sitemap = os.path.join(ROOT, "sitemap.xml")
    if not os.path.exists(sitemap):
        fail("sitemap.xml missing")
        return
    with open(sitemap, encoding="utf-8") as fh:
        body = fh.read()
    locs = re.findall(r"<loc>(.*?)</loc>", body)
    if not locs:
        fail("sitemap.xml lists no URLs")
    for loc in locs:
        target = local_path_for(loc)
        if target and not os.path.exists(target):
            fail(f"sitemap lists a URL with no page: {loc}")
        page = os.path.join(ROOT, SR.strip("/"), "thank-you", "index.html") if SR.strip("/") else os.path.join(ROOT, "thank-you", "index.html")
        if target == page:
            fail("sitemap must not list the noindex thank-you page")

    robots = os.path.join(ROOT, "robots.txt")
    if not os.path.exists(robots):
        fail("robots.txt missing")
    else:
        with open(robots, encoding="utf-8") as fh:
            text = fh.read()
        if "Sitemap:" not in text:
            fail("robots.txt does not reference a sitemap")


def main() -> int:
    skip = {".git", "tools", "data", "automation", ".github", "node_modules", "dist"}
    for dirpath, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in skip]
        for name in files:
            if name.endswith(".html"):
                check_page(os.path.join(dirpath, name))
    check_svg_assets()
    check_sitemap()

    print(f"Checked {checked_pages} pages.")
    if failures:
        print(f"\n{len(failures)} problem(s) found:", file=sys.stderr)
        for problem in failures:
            print(f"  - {problem}", file=sys.stderr)
        return 1
    print("All checks passed: links resolve, JSON-LD parses, SEO tags present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
