#!/usr/bin/env python3
"""Static storefront generator. The shop's name lives in data/config.json.

Reads data/config.json + data/products.json and writes every page of the site
as plain static HTML: storefront, one page per product, policy pages, the
post-purchase delivery page, product artwork, robots.txt and the sitemap. No
dependencies outside the standard library, no build server, and no third-party
platform holding the catalogue.

Run:  python3 tools/build_site.py
"""

from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.parse
from datetime import date, datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

# ---------------------------------------------------------------- data loading


def load() -> tuple[dict, dict]:
    with open(os.path.join(DATA, "config.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    with open(os.path.join(DATA, "products.json"), encoding="utf-8") as fh:
        cat = json.load(fh)
    return cfg, cat


CFG, CAT = load()
STORE = CFG["store"]
BRAND = CFG["brand"]
CONV = CFG["conversion"]
PREFIX = STORE["path_prefix"].rstrip("/")
BASE = STORE["base_url"].rstrip("/")
SYM = STORE["currency_symbol"]
# Site path the storefront lives at. "/" puts products at /<slug>/ rather than
# burying them under a /shop/ segment, which is shorter and ranks marginally
# better. Always leading- and trailing-slashed.
SR = STORE.get("store_root", "/")
SHORT = STORE.get("short_name", STORE["name"])
TODAY = date.today().isoformat()

PRODUCTS = [p for p in CAT["products"]]
BY_SLUG = {p["slug"]: p for p in PRODUCTS}
CATEGORIES = CAT["categories"]

e = html.escape


def url(path: str) -> str:
    """Site-root-relative URL, honouring the GitHub Pages project prefix."""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{PREFIX}{path}"


def abs_url(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{BASE}{path}"


def money(value: float) -> str:
    if float(value) == 0:
        return "Free"
    if float(value).is_integer():
        return f"{SYM}{int(value)}"
    return f"{SYM}{value:,.2f}"


def price_suffix(product: dict) -> str:
    return {"month": "/mo", "year": "/yr"}.get(product.get("billing", ""), "")


def write(rel_path: str, content: str) -> None:
    dest = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as fh:
        fh.write(content)
    print(f"  wrote {rel_path}")


def fp(rel: str) -> str:
    """File path for a page at site path SR + rel (rel ends in "/" or is "")."""
    return f"{(SR.strip('/') + '/' + rel).lstrip('/')}index.html"


def fa(rel: str) -> str:
    """File path for an asset under the store root."""
    return f"{(SR.strip('/') + '/' + rel).lstrip('/')}"


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


# ---------------------------------------------------------------------- styles

CSS = f"""
    *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}
    :root {{
      --accent: {BRAND['accent']};
      --accent-soft: {BRAND['accent_soft']};
      --bg: {BRAND['bg']};
      --bg-alt: {BRAND['bg_alt']};
      --text: {BRAND['text']};
      --muted: #a0a0a0;
      --line: rgba(255, 107, 53, 0.22);
      --card: linear-gradient(135deg, rgba(26,26,26,.85) 0%, rgba(42,42,42,.85) 100%);
    }}
    html {{ scroll-behavior: smooth; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: linear-gradient(180deg, var(--bg) 0%, var(--bg-alt) 100%);
      background-attachment: fixed;
      color: var(--text);
      line-height: 1.6;
      min-height: 100vh;
      -webkit-font-smoothing: antialiased;
    }}
    a {{ color: var(--accent); }}
    img {{ max-width: 100%; height: auto; }}
    .container {{ max-width: 1280px; margin: 0 auto; padding: 2rem 1rem 4rem; }}
    .skip {{ position: absolute; left: -9999px; }}
    .skip:focus {{ left: 1rem; top: 1rem; background: var(--accent); color: #000; padding: .6rem 1rem; border-radius: 6px; z-index: 99; }}

    .topbar {{
      background: rgba(255, 107, 53, 0.1);
      border-bottom: 1px solid var(--line);
      text-align: center; padding: .6rem 1rem; font-size: .9rem; color: #ffd9c7;
    }}
    .topbar a {{ color: var(--accent); font-weight: 700; text-decoration: none; }}
    .topbar a:hover {{ text-decoration: underline; }}

    header.site {{
      text-align: center; padding: 2.5rem 1rem 2rem;
      border-bottom: 3px solid var(--accent);
    }}
    header.site .brandmark {{
      font-size: clamp(1.9rem, 7vw, 3.4rem); color: var(--accent);
      text-transform: uppercase; letter-spacing: 3px; font-weight: 900; line-height: 1.1;
    }}
    header.site .tagline {{ color: var(--muted); letter-spacing: 1px; margin-top: .6rem; font-weight: 300; font-size: clamp(.95rem, 2.5vw, 1.2rem); }}

    nav.pillars {{ display: flex; flex-wrap: wrap; gap: .6rem; justify-content: center; margin: 1.4rem auto 0; max-width: 1000px; }}
    nav.pillars a {{
      background: rgba(255,255,255,.05); border: 1px solid var(--line); color: var(--text);
      padding: .5rem 1rem; border-radius: 999px; text-decoration: none; font-size: .88rem; font-weight: 600;
      transition: all .2s ease;
    }}
    nav.pillars a:hover {{ background: var(--accent); color: #000; }}
    nav.pillars a.active {{ background: var(--accent); color: #000; }}

    .breadcrumb {{ font-size: .85rem; color: var(--muted); margin-bottom: 1.5rem; }}
    .breadcrumb a {{ color: var(--muted); text-decoration: none; }}
    .breadcrumb a:hover {{ color: var(--accent); }}

    .hero {{
      display: grid; grid-template-columns: 1.15fr .85fr; gap: 2rem; align-items: center;
      background: var(--card); border: 1px solid var(--line); border-radius: 16px;
      padding: clamp(1.5rem, 4vw, 3rem); margin-bottom: 3rem;
      box-shadow: 0 12px 40px rgba(0,0,0,.35);
    }}
    .hero h2 {{ font-size: clamp(1.5rem, 4vw, 2.4rem); color: #fff; line-height: 1.2; margin-bottom: 1rem; }}
    .hero p {{ color: #ccc; margin-bottom: 1.4rem; }}
    .hero-art {{ width: 100%; border-radius: 12px; border: 1px solid var(--line); }}
    @media (max-width: 860px) {{ .hero {{ grid-template-columns: 1fr; }} }}

    .eyebrow {{ text-transform: uppercase; letter-spacing: 2px; font-size: .75rem; color: var(--accent); font-weight: 800; margin-bottom: .8rem; }}

    .btn {{
      display: inline-block; background: linear-gradient(135deg, var(--accent) 0%, var(--accent-soft) 100%);
      color: #000; font-weight: 800; padding: .95rem 1.8rem; border-radius: 8px; text-decoration: none;
      border: 2px solid transparent; cursor: pointer; font-size: 1rem; font-family: inherit;
      transition: transform .2s cubic-bezier(.34,1.56,.64,1), box-shadow .2s ease;
      box-shadow: 0 4px 15px rgba(255,107,53,.25);
    }}
    .btn:hover {{ transform: translateY(-3px); box-shadow: 0 12px 28px rgba(255,107,53,.4); }}
    .btn.secondary {{ background: transparent; color: var(--accent); border-color: var(--accent); box-shadow: none; }}
    .btn.secondary:hover {{ background: rgba(255,107,53,.12); }}
    .btn.block {{ display: block; width: 100%; text-align: center; }}

    h2.section {{ font-size: clamp(1.3rem, 3vw, 1.9rem); color: var(--accent); text-transform: uppercase; letter-spacing: 2px; margin: 3rem 0 .4rem; }}
    .section-blurb {{ color: var(--muted); margin-bottom: 1.6rem; max-width: 70ch; }}

    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 1.4rem; }}

    .card {{
      background: var(--card); border: 1px solid rgba(255,255,255,.07); border-radius: 14px;
      overflow: hidden; display: flex; flex-direction: column;
      transition: transform .25s ease, border-color .25s ease, box-shadow .25s ease;
    }}
    .card:hover {{ transform: translateY(-5px); border-color: var(--line); box-shadow: 0 16px 34px rgba(0,0,0,.4); }}
    .card img {{ width: 100%; display: block; aspect-ratio: 1200 / 630; object-fit: cover; background: #111; }}
    .card-body {{ padding: 1.2rem; display: flex; flex-direction: column; gap: .6rem; flex: 1; }}
    .card h3 {{ font-size: 1.12rem; line-height: 1.3; }}
    .card h3 a {{ color: #fff; text-decoration: none; }}
    .card h3 a:hover {{ color: var(--accent); }}
    .card p {{ color: #b5b5b5; font-size: .92rem; flex: 1; }}
    .card-foot {{ display: flex; align-items: center; justify-content: space-between; gap: .8rem; margin-top: .4rem; }}

    .price {{ font-size: 1.35rem; font-weight: 900; color: #fff; white-space: nowrap; }}
    .price .suffix {{ font-size: .85rem; font-weight: 600; color: var(--muted); }}
    .price s {{ color: var(--muted); font-size: .95rem; font-weight: 500; margin-right: .4rem; }}

    .badge {{
      display: inline-block; background: rgba(255,107,53,.15); color: var(--accent);
      border: 1px solid var(--line); border-radius: 999px; padding: .18rem .7rem;
      font-size: .72rem; font-weight: 800; text-transform: uppercase; letter-spacing: 1px;
    }}
    .badge.free {{ background: rgba(80,200,120,.14); color: #6ee7a0; border-color: rgba(110,231,160,.3); }}

    .trust {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1rem; margin: 2.5rem 0; }}
    .trust div {{ background: rgba(255,255,255,.035); border: 1px solid rgba(255,255,255,.07); border-radius: 10px; padding: 1rem 1.2rem; }}
    .trust strong {{ display: block; color: var(--accent); font-size: .85rem; text-transform: uppercase; letter-spacing: 1px; margin-bottom: .25rem; }}
    .trust span {{ color: #b5b5b5; font-size: .9rem; }}

    .product {{ display: grid; grid-template-columns: 1fr 380px; gap: 2.5rem; align-items: start; }}
    @media (max-width: 900px) {{ .product {{ grid-template-columns: 1fr; }} }}
    .product h1 {{ font-size: clamp(1.6rem, 4.5vw, 2.6rem); color: #fff; line-height: 1.15; margin: .6rem 0 .8rem; }}
    .lede {{ font-size: 1.1rem; color: #ccc; margin-bottom: 1.6rem; }}
    .prose p {{ margin-bottom: 1rem; color: #c8c8c8; }}
    .prose h2 {{ color: var(--accent); font-size: 1.25rem; margin: 2rem 0 .8rem; }}
    .prose h3 {{ color: #fff; font-size: 1.05rem; margin: 1.5rem 0 .6rem; }}
    .prose ul {{ margin: 0 0 1.2rem 1.2rem; color: #c8c8c8; }}
    .prose li {{ margin-bottom: .5rem; }}
    .feature-list {{ list-style: none; margin-left: 0 !important; }}
    .feature-list li {{ padding-left: 1.7rem; position: relative; }}
    .feature-list li::before {{ content: "▸"; color: var(--accent); position: absolute; left: .3rem; font-weight: 900; }}

    .buybox {{
      background: var(--card); border: 1px solid var(--line); border-radius: 14px;
      padding: 1.5rem; position: sticky; top: 1rem; box-shadow: 0 12px 34px rgba(0,0,0,.4);
    }}
    .buybox .price {{ font-size: 2.2rem; display: block; margin-bottom: .2rem; }}
    .buybox .delivery {{ color: var(--muted); font-size: .88rem; margin: .8rem 0 1.2rem; }}
    .buybox .fineprint {{ color: var(--muted); font-size: .78rem; margin-top: 1rem; text-align: center; }}
    .buybox img {{ width: 100%; border-radius: 10px; margin-bottom: 1.2rem; border: 1px solid rgba(255,255,255,.08); }}
    select {{
      width: 100%; padding: .7rem .8rem; border-radius: 8px; background: #141414; color: var(--text);
      border: 1px solid rgba(255,255,255,.15); font-family: inherit; font-size: .95rem; margin-bottom: 1rem;
    }}

    details.faq {{ background: rgba(255,255,255,.035); border: 1px solid rgba(255,255,255,.07); border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: .8rem; }}
    details.faq summary {{ cursor: pointer; font-weight: 700; color: #fff; }}
    details.faq summary::marker {{ color: var(--accent); }}
    details.faq p {{ margin-top: .7rem; color: #b8b8b8; }}

    .capture {{
      background: var(--card); border: 1px solid var(--line); border-radius: 14px;
      padding: clamp(1.4rem, 4vw, 2.4rem); margin: 3rem 0; text-align: center;
    }}
    .capture h2 {{ color: var(--accent); font-size: clamp(1.2rem, 3vw, 1.7rem); margin-bottom: .6rem; }}
    .capture p {{ color: #c0c0c0; max-width: 60ch; margin: 0 auto 1.4rem; }}
    .capture form {{ display: flex; gap: .7rem; max-width: 520px; margin: 0 auto; flex-wrap: wrap; }}
    .capture input {{
      flex: 1 1 240px; padding: .9rem 1rem; border-radius: 8px; background: #141414; color: var(--text);
      border: 1px solid rgba(255,255,255,.15); font-family: inherit; font-size: 1rem;
    }}
    .capture .note {{ color: var(--muted); font-size: .8rem; margin-top: .9rem; }}

    .notice {{ background: rgba(255,107,53,.08); border: 1px solid var(--line); border-radius: 10px; padding: 1rem 1.2rem; color: #d8d8d8; font-size: .92rem; margin: 1rem 0; }}

    table.compare {{ width: 100%; border-collapse: collapse; margin: 1.5rem 0; font-size: .93rem; }}
    table.compare th, table.compare td {{ border-bottom: 1px solid rgba(255,255,255,.09); padding: .75rem .6rem; text-align: left; }}
    table.compare th {{ color: var(--accent); text-transform: uppercase; font-size: .75rem; letter-spacing: 1px; }}
    .table-wrap {{ overflow-x: auto; }}

    .filterbar {{
      display: flex; flex-wrap: wrap; gap: .6rem; align-items: center;
      background: var(--card); border: 1px solid rgba(255,255,255,.08);
      border-radius: 12px; padding: 1rem; margin: 0 0 1.6rem;
      position: sticky; top: 0; z-index: 20; backdrop-filter: blur(8px);
    }}
    .filterbar input[type="search"] {{
      flex: 1 1 240px; padding: .7rem .9rem; border-radius: 8px; background: #0b1119;
      color: var(--text); border: 1px solid rgba(255,255,255,.15); font-family: inherit; font-size: .95rem;
    }}
    .chip {{
      background: rgba(255,255,255,.05); border: 1px solid rgba(255,255,255,.12); color: var(--text);
      padding: .5rem .9rem; border-radius: 999px; font-size: .85rem; font-weight: 600;
      cursor: pointer; font-family: inherit; transition: all .2s ease; white-space: nowrap;
    }}
    .chip:hover {{ border-color: var(--accent); }}
    .chip[aria-pressed="true"] {{ background: var(--accent); color: #04120c; border-color: var(--accent); }}
    .filter-count {{ color: var(--muted); font-size: .85rem; margin-left: auto; }}
    .no-results {{ color: var(--muted); padding: 2rem 0; }}

    .stickybuy {{ display: none; }}
    @media (max-width: 900px) {{
      .stickybuy {{
        display: flex; position: fixed; left: 0; right: 0; bottom: 0; z-index: 40;
        align-items: center; justify-content: space-between; gap: 1rem;
        background: rgba(7,11,18,.96); border-top: 1px solid var(--line);
        padding: .7rem 1rem; backdrop-filter: blur(10px);
      }}
      .stickybuy .price {{ font-size: 1.3rem; }}
      .stickybuy .btn {{ padding: .8rem 1.2rem; font-size: .92rem; white-space: nowrap; }}
      .stickybuy .fineprint {{ display: none; }}
      body {{ padding-bottom: 4.5rem; }}
      .buybox {{ position: static; }}
    }}

    table.sources {{ width: 100%; border-collapse: collapse; margin: 1.2rem 0; font-size: .92rem; }}
    table.sources th, table.sources td {{ border-bottom: 1px solid rgba(255,255,255,.09); padding: .7rem .6rem; text-align: left; vertical-align: top; }}
    table.sources th {{ color: var(--accent); text-transform: uppercase; font-size: .72rem; letter-spacing: 1px; }}

    footer.site {{ border-top: 1px solid rgba(255,255,255,.09); margin-top: 3rem; padding: 2.5rem 1rem; text-align: center; color: var(--muted); font-size: .88rem; }}
    footer.site nav {{ display: flex; flex-wrap: wrap; gap: 1rem; justify-content: center; margin-bottom: 1.2rem; }}
    footer.site a {{ color: #b5b5b5; text-decoration: none; }}
    footer.site a:hover {{ color: var(--accent); }}
    footer.site .legal {{ max-width: 75ch; margin: 1rem auto 0; font-size: .8rem; line-height: 1.7; }}
"""

# ------------------------------------------------------------------- artwork

ART_THEMES = {
    "memberships": ("#17e6a1", "#04352a"),
    "data-packs": ("#5ef0c0", "#06251f"),
    "tools": ("#8af7d6", "#0b1620"),
    "apparel": ("#17e6a1", "#0d1119"),
}


def artwork_svg(product: dict) -> str:
    """Deterministic brand artwork for a product — no external image assets."""
    accent, deep = ART_THEMES.get(product["category"], (BRAND["accent"], BRAND["bg_alt"]))
    name = e(product["name"])
    cat = e(next(c["name"] for c in CATEGORIES if c["slug"] == product["category"]).upper())
    words = product["name"].split()
    lines, current = [], ""
    for word in words:
        if len(current + " " + word) > 18 and current:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}".strip()
    lines.append(current)
    lines = lines[:3]
    text_els = "".join(
        f'<text x="60" y="{300 + i * 62}" font-family="Segoe UI,Helvetica,Arial,sans-serif" '
        f'font-size="52" font-weight="800" fill="#ffffff">{e(line)}</text>'
        for i, line in enumerate(lines)
    )
    bars = "".join(
        f'<rect x="{700 + i * 34}" y="{460 - h}" width="20" height="{h}" rx="4" fill="{accent}" opacity="{0.25 + i * 0.12}"/>'
        for i, h in enumerate([70, 120, 95, 165, 130, 205])
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630" role="img" aria-label="{name}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{BRAND['bg']}"/><stop offset="100%" stop-color="{deep}"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)"/>
  <rect x="0" y="0" width="1200" height="8" fill="{accent}"/>
  {bars}
  <text x="60" y="150" font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="26" font-weight="800" letter-spacing="6" fill="{accent}">{e(SHORT.upper())}</text>
  <text x="60" y="205" font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="22" font-weight="600" letter-spacing="3" fill="#9a9a9a">{cat}</text>
  {text_els}
  <text x="60" y="560" font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="28" font-weight="700" fill="{accent}">{e(money(product['price']) + price_suffix(product))}</text>
</svg>
"""


def store_og_svg() -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630" role="img" aria-label="{e(STORE['name'])}">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="{BRAND['bg']}"/><stop offset="100%" stop-color="#04352a"/></linearGradient></defs>
  <rect width="1200" height="630" fill="url(#g)"/>
  <rect x="0" y="0" width="1200" height="10" fill="{BRAND['accent']}"/>
  <text x="60" y="270" font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="82" font-weight="900" letter-spacing="3" fill="{BRAND['accent']}">{e(SHORT.upper())}</text>
  <text x="62" y="345" font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="40" font-weight="700" fill="#ffffff">{e(STORE['tagline'].upper())}</text>
  <text x="62" y="420" font-family="Segoe UI,Helvetica,Arial,sans-serif" font-size="30" font-weight="500" fill="#c9c9c9">{e(STORE['tagline'])}</text>
</svg>
"""


# --------------------------------------------------------------- page chrome


def head(
    *,
    title: str,
    description: str,
    canonical_path: str,
    og_image: str,
    keywords: str = "",
    jsonld: list[dict] | None = None,
    robots: str = "index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1",
) -> str:
    verif = ""
    for key, tag in (
        ("google_site_verification", "google-site-verification"),
        ("bing_site_verification", "msvalidate.01"),
        ("yandex_verification", "yandex-verification"),
        ("pinterest_verification", "p:domain_verify"),
    ):
        value = CFG["seo"].get(key)
        if value:
            verif += f'\n    <meta name="{tag}" content="{e(value)}" />'
    blocks = "".join(
        f'\n    <script type="application/ld+json">{json.dumps(b, ensure_ascii=False)}</script>'
        for b in (jsonld or [])
    )
    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{e(title)}</title>
    <meta name="description" content="{e(description)}" />
    <meta name="keywords" content="{e(keywords)}" />
    <meta name="author" content="{e(STORE['owner'])}" />
    <meta name="robots" content="{e(robots)}" />
    <link rel="canonical" href="{e(abs_url(canonical_path))}" />
    <link rel="shortcut icon" href="{url('/favicon.svg')}" type="image/svg+xml" />{verif}

    <meta property="og:type" content="website" />
    <meta property="og:site_name" content="{e(STORE['name'])}" />
    <meta property="og:url" content="{e(abs_url(canonical_path))}" />
    <meta property="og:title" content="{e(title)}" />
    <meta property="og:description" content="{e(description)}" />
    <meta property="og:image" content="{e(abs_url(og_image))}" />

    <meta name="twitter:card" content="summary_large_image" />
    <meta name="twitter:title" content="{e(title)}" />
    <meta name="twitter:description" content="{e(description)}" />
    <meta name="twitter:image" content="{e(abs_url(og_image))}" />
    <style>{CSS}</style>{blocks}
  </head>
  <body>
    <a class="skip" href="#main">Skip to content</a>
"""


def site_header(active: str = "", *, brand_is_h1: bool = False) -> str:
    links = [("Store", url(SR))] + [
        (item["label"], url(f"{SR}{item['path'].lstrip('/')}")) for item in CFG.get("nav", [])
    ]
    nav = "".join(
        '<a href="%s"%s>%s</a>' % (href, ' class="active"' if label == active else "", e(label))
        for label, href in links
    )
    free = BY_SLUG.get(CONV.get("free_lead_magnet", ""))
    bar = ""
    if free:
        bar = (
            f'<div class="topbar">Free: a real slice of the data — '
            f'<a href="{url(SR + free["slug"] + "/")}">get the sample</a></div>'
        )
    tag = "h1" if brand_is_h1 else "p"
    return f"""{bar}
    <header class="site">
      <{tag} class="brandmark"><a href="{url(SR)}" style="color:inherit;text-decoration:none">{e(STORE['name'])}</a></{tag}>
      <p class="tagline">{e(STORE['tagline'])}</p>
      <nav class="pillars">{nav}</nav>
    </header>
"""


def site_footer() -> str:
    year = datetime.now(timezone.utc).year
    links = [
        ("Store", url(SR)),
        ("Delivery & Shipping", url(f"{SR}policies/shipping/")),
        ("Refunds", url(f"{SR}policies/refunds/")),
        ("Terms", url(f"{SR}policies/terms/")),
        ("Privacy", url(f"{SR}policies/privacy/")),
        ("Contact", f"mailto:{STORE['support_email']}"),
    ]
    nav = "".join(f'<a href="{href}">{e(label)}</a>' for label, href in links)
    return f"""
    <footer class="site">
      <nav>{nav}</nav>
      <p>&copy; {year} {e(STORE['legal_entity'])}. All rights reserved.</p>
      <p class="legal">
        {e(SHORT)} sells beauty, jewelry, wellness and home goods. Nothing here is a medical
        or cosmetic claim beyond what the product page states, and results vary between people.
        Ingredients and materials are listed on every product page — check them against your own
        sensitivities before buying. Prices in USD.
      </p>
    </footer>
  </body>
</html>
"""


# ----------------------------------------------------------------- components


def checkout_block(product: dict, *, block: bool = True, note: bool = True) -> str:
    """Buy button when a payment link exists; honest waitlist capture when not."""
    cls = "btn block" if block else "btn"
    if product["type"] == "lead_magnet":
        return f'<a class="{cls}" href="#get-free-report">Send me the free report</a>'
    link = (product.get("checkout_url") or "").strip()
    if link:
        label = "Start membership" if product["category"] == "memberships" else "Buy now"
        return (
            f'<a class="{cls}" href="{e(link)}" rel="nofollow noopener" '
            f'data-product="{e(product["slug"])}">{label} — {e(money(product["price"]) + price_suffix(product))}</a>'
        )
    fineprint = (
        '<p class="fineprint">Checkout opens as soon as payments are switched on. '
        "The launch list is notified first.</p>"
        if note
        else ""
    )
    return (
        f'<a class="{cls}" href="#get-free-report" data-product="{e(product["slug"])}">'
        f"Join the launch list</a>{fineprint}"
    )


def product_card(product: dict) -> str:
    href = url(f"{SR}{product['slug']}/")
    badge = ""
    if product.get("badge"):
        cls = "badge free" if product["price"] == 0 else "badge"
        badge = f'<span class="{cls}">{e(product["badge"])}</span>'
    compare = f"<s>{e(money(product['compare_at']))}</s>" if product.get("compare_at") else ""
    haystack = " ".join(
        [product["name"], product["short"], product["category"]] + product.get("keywords", [])
    ).lower()
    return f"""      <article class="card" data-category="{e(product['category'])}" data-type="{e(product['type'])}" data-search="{e(haystack)}" data-price="{product['price']}">
        <a href="{href}" aria-label="{e(product['name'])}"><img src="{url(product.get('image') or SR + 'assets/' + product['slug'] + '.svg')}" alt="{e(product['name'])}" loading="lazy" width="1200" height="630" /></a>
        <div class="card-body">
          {badge}
          <h3><a href="{href}">{e(product['name'])}</a></h3>
          <p>{e(product['short'])}</p>
          <div class="card-foot">
            <span class="price">{compare}{e(money(product['price']))}<span class="suffix">{e(price_suffix(product))}</span></span>
            <a class="btn secondary" href="{href}">Details</a>
          </div>
        </div>
      </article>
"""


def capture_form(heading: str, body: str) -> str:
    endpoint = CFG["capture"].get("endpoint", "").strip()
    if endpoint:
        form = f"""<form id="capture-form" action="{e(endpoint)}" method="{e(CFG['capture'].get('method', 'POST'))}">
          <input type="email" name="email" required placeholder="you@example.com" aria-label="Email address" />
          <input type="hidden" name="source" value="edge-store" />
          <button class="btn" type="submit">Send it</button>
        </form>"""
    else:
        # No endpoint configured yet. A mailto <form> is not reliably supported by
        # browsers, so fall back to a prefilled mailto link, which always opens.
        subject = urllib.parse.quote(f"Send me the free sample pack")
        body = urllib.parse.quote(
            "Add me to the drop list.\n\n(Sent from the site.)"
        )
        form = (
            f'<a class="btn" href="mailto:{e(STORE["support_email"])}'
            f'?subject={subject}&body={body}">Email me the sample pack</a>'
        )
    return f"""
      <section class="capture" id="get-free-report">
        <h2>{e(heading)}</h2>
        <p>{e(body)}</p>
        {form}
        <p class="note">Your address is used to send the sample pack and release notes. It is never sold or shared, and every email unsubscribes in one click.</p>
      </section>
"""


def trust_row() -> str:
    days = CONV.get("show_money_back_days", 7)
    return f"""
      <div class="trust">
        <div><strong>Instant delivery</strong><span>Digital products download the moment payment clears.</span></div>
        <div><strong>{days}-day guarantee</strong><span>If a digital product is not what was described, email for a refund.</span></div>
        <div><strong>Secure checkout</strong><span>Card details go straight to Stripe. This site never sees them.</span></div>
        <div><strong>Openly licensed</strong><span>Public-domain sources, compiled and documented — provenance named for every field.</span></div>
      </div>
"""


# --------------------------------------------------------------- JSON-LD


def org_jsonld() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "OnlineStore",
        "@id": abs_url(f"{SR}#store"),
        "name": STORE["name"],
        "url": abs_url(SR),
        "description": STORE["description"],
        "email": STORE["support_email"],
        "image": abs_url(CFG["seo"]["default_og_image"]),
        "logo": abs_url(CFG["seo"]["default_og_image"]),
        "founder": {"@type": "Person", "name": STORE["owner"]},
        "foundingDate": STORE["founded"],
        "currenciesAccepted": STORE["currency"],
        "paymentAccepted": "Credit Card, Debit Card",
        "areaServed": "Worldwide",

    }


def website_jsonld() -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "@id": abs_url(f"{SR}#website"),
        "url": abs_url(SR),
        "name": STORE["name"],
        "description": STORE["description"],
        "inLanguage": "en",
        "publisher": {"@id": abs_url(f"{SR}#store")},
    }


def breadcrumb_jsonld(trail: list[tuple[str, str]]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": name, "item": abs_url(path)}
            for i, (name, path) in enumerate(trail)
        ],
    }


def product_jsonld(product: dict) -> dict:
    offer = {
        "@type": "Offer",
        "url": abs_url(f"{SR}{product['slug']}/"),
        "price": f"{product['price']:.2f}",
        "priceCurrency": STORE["currency"],
        "availability": "https://schema.org/InStock",
        "priceValidUntil": f"{date.today().year + 1}-12-31",
        "seller": {"@type": "Organization", "name": STORE["name"]},
        "itemCondition": "https://schema.org/NewCondition",
    }
    if product["type"] == "digital":
        offer["hasMerchantReturnPolicy"] = {
            "@type": "MerchantReturnPolicy",
            "applicableCountry": STORE["country"],
            "returnPolicyCategory": "https://schema.org/MerchantReturnFiniteReturnWindow",
            "merchantReturnDays": CONV.get("show_money_back_days", 7),
            "returnMethod": "https://schema.org/ReturnByMail",
            "returnFees": "https://schema.org/FreeReturn",
        }
    data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product["name"],
        "sku": product["sku"],
        "description": product["description"],
        "image": [abs_url(product.get('image') or f"{SR}assets/{product['slug']}.svg")],
        "brand": {"@type": "Brand", "name": SHORT},
        "category": next(c["name"] for c in CATEGORIES if c["slug"] == product["category"]),
        "offers": offer,
    }
    if product.get("variants"):
        data["additionalProperty"] = [
            {"@type": "PropertyValue", "name": "Available options", "value": ", ".join(product["variants"])}
        ]
    return data


def faq_jsonld(pairs: list[dict]) -> dict:
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": pair["q"],
                "acceptedAnswer": {"@type": "Answer", "text": pair["a"]},
            }
            for pair in pairs
        ],
    }


# ------------------------------------------------------------------ pages

FILTER_BAR = """
      <form class="filterbar" role="search" id="filters" onsubmit="return false">
        <label for="q" class="skip">Search products</label>
        <input type="search" id="q" placeholder="Search products — data, CSV, membership, hoodie…" autocomplete="off" />
        <button type="button" class="chip" data-filter="all" aria-pressed="true">All</button>
        {chips}
        <button type="button" class="chip" id="clear-filters" hidden>✕ Clear</button>
        <span class="filter-count" id="filter-count" role="status"></span>
      </form>
      <p class="no-results" id="no-results" hidden>Nothing matches that — clear the filters to see the full catalogue.</p>
"""

STORE_FAQ = [
    {
        "q": "How fast does it ship?",
        "a": "Orders placed before 2pm ship the same working day, otherwise the next one. Delivery is typically 2-5 working days in the US.",
    },
    {
        "q": "What does shipping cost?",
        "a": "Free over $35. Under that it is a flat $4.95, shown before you pay.",
    },
    {
        "q": "Can I return something?",
        "a": f"Yes — {CONV.get('show_money_back_days', 30)} days on unopened items, and anything faulty or wrong is replaced or refunded regardless of how long it has been.",
    },
    {
        "q": "How does subscribe and save work?",
        "a": "Tick it on any refillable item and it repeats at your chosen interval with 15% off every order. Skip, pause or cancel any time from the link in your confirmation email.",
    },
    {
        "q": "How can I pay?",
        "a": "Card (Visa, Mastercard, Amex), Apple Pay and Google Pay through our payment provider, plus PayPal and Cash App. Card details never touch this site.",
    },
    {
        "q": "Why are there no star ratings on this site?",
        "a": "Because we would have had to invent them. Reviews go up when real customers leave them, and not before.",
    },
]


def build_storefront() -> None:
    featured = [p for p in PRODUCTS if p.get("featured")]
    hero = BY_SLUG.get(CONV.get("hero_product")) or (featured[0] if featured else PRODUCTS[0])
    sellable = [p for p in PRODUCTS if p["type"] != "lead_magnet"]

    item_list = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"{STORE['name']} products",
        "numberOfItems": len(sellable),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "url": abs_url(f"{SR}{p['slug']}/"),
                "name": p["name"],
            }
            for i, p in enumerate(sellable)
        ],
    }

    chips = "".join(
        f'<button type="button" class="chip" data-filter="{c["slug"]}" aria-pressed="false">{e(c["name"])}</button>'
        for c in CATEGORIES
    )
    filter_bar = FILTER_BAR.replace("{chips}", chips)

    sections = []
    for cat in CATEGORIES:
        members = [p for p in PRODUCTS if p["category"] == cat["slug"]]
        if not members:
            continue
        cards = "".join(product_card(p) for p in members)
        sections.append(
            f"""
      <h2 class="section" id="{cat['slug']}">{e(cat['name'])}</h2>
      <p class="section-blurb">{e(cat['blurb'])}</p>
      <div class="grid">
{cards}      </div>
"""
        )

    compare_rows = "".join(
        f"<tr><td>{e(p['name'])}</td><td>{e(next(c['name'] for c in CATEGORIES if c['slug'] == p['category']))}</td>"
        f"<td>{e(p['delivery'])}</td><td>{e(money(p['price']) + price_suffix(p))}</td></tr>"
        for p in sellable
    )

    faqs = "".join(
        f'<details class="faq"><summary>{e(f["q"])}</summary><p>{e(f["a"])}</p></details>'
        for f in STORE_FAQ
    )

    title = f"{STORE['name']} — Analysis-Ready Public Data"
    desc = (
        f"Shop {SHORT}: beauty, skincare, jewelry, wellness, home and kitchen edits in the "
        "$14-34 range. Free shipping over $35, 30-day returns, ships in 1-2 days."
    )

    body = f"""{head(
        title=title,
        description=desc,
        canonical_path=SR,
        og_image=CFG["seo"]["default_og_image"],
        keywords="lip gloss set, glass skin serum, gold fill jewelry, stacking rings, sunset lamp, fridge organiser, heatless curls, affordable beauty shop",
        jsonld=[
            org_jsonld(),
            website_jsonld(),
            breadcrumb_jsonld([(STORE["name"], SR)]),
            item_list,
            faq_jsonld(STORE_FAQ),
        ],
    )}{site_header(active="Store", brand_is_h1=True)}
    <main id="main" class="container">

      <section class="hero">
        <div>
          <p class="eyebrow">Start here</p>
          <h2>{e(hero['name'])}</h2>
          <p>{e(hero['short'])}</p>
          <p>{e(hero['description'][:240].rsplit(' ', 1)[0])}…</p>
          <p style="margin-bottom:1rem"><span class="price">{e(money(hero['price']))}<span class="suffix">{e(price_suffix(hero))}</span></span></p>
          <span style="display:inline-flex;flex-wrap:wrap;gap:.6rem">
            {checkout_block(hero, block=False, note=False)}
            <a class="btn secondary" href="{url(SR + hero['slug'] + '/')}">What's inside</a>
          </span>
        </div>
        <img class="hero-art" src="{url(hero.get('image') or SR + 'assets/' + hero['slug'] + '.svg')}" alt="{e(hero['name'])}" width="1200" height="630" />
      </section>

      {trust_row()}

      {filter_bar}

      <h2 class="section" id="featured" data-featured>Featured</h2>
      <p class="section-blurb">The products that do the most for a reader who wants to stop guessing and start measuring.</p>
      <div class="grid" id="featured-grid" data-featured>
{''.join(product_card(p) for p in featured)}      </div>
{''.join(sections)}
      <h2 class="section" id="compare">Everything in the store</h2>
      <div class="table-wrap">
        <table class="compare">
          <thead><tr><th>Product</th><th>Category</th><th>Delivery</th><th>Price</th></tr></thead>
          <tbody>{compare_rows}</tbody>
        </table>
      </div>

{capture_form(
        "Get a real sample of the data, free",
        "First look at every drop, plus the restock alerts. No more than one email a week.",
    )}

      <h2 class="section" id="faq">Store FAQ</h2>
      {faqs}

      <h2 class="section" id="data-sources">How things get picked</h2>
      <p class="section-blurb">Everything here has to clear the same bar before it goes on the shelf:
      it has to solve something visible, survive normal use, and cost little enough that trying it is
      not a decision. What is on this page is what cleared it.</p>
      <div class="table-wrap">
        <table class="sources">
          <thead><tr><th>Test</th><th>What it means</th></tr></thead>
          <tbody>
            <tr><td>Does one job</td><td>If it needs explaining twice, it does not go on.</td></tr>
            <tr><td>Survives real use</td><td>Water, sweat, dishwashers, being slept in — whichever applies.</td></tr>
            <tr><td>Honest price</td><td>Priced from what it costs us, not from what the category charges.</td></tr>
            <tr><td>Restockable</td><td>We only list what we can get again, so a favourite does not vanish.</td></tr>
            <tr><td>No invented proof</td><td>No star ratings, sold counts or countdowns anywhere on this site.</td></tr>
          </tbody>
        </table>
      </div>
      <p class="section-blurb">Something not right? Write to
      <a href="mailto:{e(STORE['support_email'])}">{e(STORE['support_email'])}</a> are fixed and pushed to
      everyone entitled to updates.</p>

    </main>
    <script>
      (function () {{
        var form = document.getElementById('filters');
        if (!form) return;
        var query = document.getElementById('q');
        var chips = form.querySelectorAll('.chip[data-filter]');
        var count = document.getElementById('filter-count');
        var empty = document.getElementById('no-results');
        var clear = document.getElementById('clear-filters');
        var active = 'all';

        function apply() {{
          var term = query.value.trim().toLowerCase();
          var shown = 0;
          document.querySelectorAll('.grid:not([data-featured]) .card').forEach(function (card) {{
            var okCat = active === 'all' || card.dataset.category === active;
            var okTerm = !term || (card.dataset.search || '').indexOf(term) !== -1;
            var show = okCat && okTerm;
            card.style.display = show ? '' : 'none';
            if (show) shown++;
          }});
          // Hide a section heading whose grid has nothing left in it.
          document.querySelectorAll('.grid:not([data-featured])').forEach(function (grid) {{
            var any = [].slice.call(grid.children).some(function (c) {{ return c.style.display !== 'none'; }});
            var prev = grid.previousElementSibling;
            grid.hidden = !any;
            while (prev && (prev.classList.contains('section-blurb') || prev.classList.contains('section'))) {{
              prev.hidden = !any;
              prev = prev.previousElementSibling;
            }}
          }});
          var filtering = Boolean(term) || active !== 'all';
          // The featured row repeats products shown below, so hide it while a
          // filter is active rather than double-counting them.
          document.querySelectorAll('[data-featured]').forEach(function (el) {{
            el.hidden = filtering;
          }});
          count.textContent = filtering ? shown + (shown === 1 ? ' match' : ' matches') : '';
          clear.hidden = !filtering;
          empty.hidden = shown !== 0;
        }}

        query.addEventListener('input', apply);
        chips.forEach(function (chip) {{
          chip.addEventListener('click', function () {{
            active = chip.dataset.filter;
            chips.forEach(function (c) {{ c.setAttribute('aria-pressed', String(c === chip)); }});
            apply();
          }});
        }});
        clear.addEventListener('click', function () {{
          query.value = '';
          active = 'all';
          chips.forEach(function (c) {{ c.setAttribute('aria-pressed', String(c.dataset.filter === 'all')); }});
          apply();
        }});
      }})();
    </script>
{site_footer()}"""
    write(fp(""), body)


def build_product(product: dict) -> None:
    cat = next(c for c in CATEGORIES if c["slug"] == product["category"])
    related = [p for p in PRODUCTS if p["slug"] != product["slug"] and p["type"] != "lead_magnet"]
    related = [p for p in related if p["category"] == product["category"]] + [
        p for p in related if p["category"] != product["category"]
    ]
    related = related[:3]

    features = "".join(f"<li>{e(f)}</li>" for f in product.get("features", []))
    faq_pairs = product.get("faq", [])
    faqs = "".join(
        f'<details class="faq"><summary>{e(f["q"])}</summary><p>{e(f["a"])}</p></details>'
        for f in faq_pairs
    )
    variants = ""
    if product.get("variants"):
        opts = "".join(f"<option>{e(v)}</option>" for v in product["variants"])
        label = "Size" if product["category"] == "apparel" else "Option"
        variants = f'<label for="variant" style="display:block;font-size:.85rem;color:#a0a0a0;margin-bottom:.35rem">{label}</label><select id="variant" name="variant">{opts}</select>'

    compare = f"<s>{e(money(product['compare_at']))}</s>" if product.get("compare_at") else ""
    bump = BY_SLUG.get(CONV.get("order_bump", ""))
    bump_html = ""
    if bump and bump["slug"] != product["slug"] and product["type"] not in ("lead_magnet",):
        bump_html = f"""
        <div class="notice" style="margin-top:1.2rem">
          <strong style="color:#fff">Pairs with this:</strong> {e(bump['name'])} — {e(bump['short'])}
          <a href="{url(SR + bump['slug'] + '/')}">Add it for {e(money(bump['price']))} →</a>
        </div>"""

    jsonld = [
        breadcrumb_jsonld(
            [
                (STORE["name"], SR),
                (cat["name"], f"{SR}#{cat['slug']}"),
                (product["name"], f"{SR}{product['slug']}/"),
            ]
        ),
        product_jsonld(product),
    ]
    if faq_pairs:
        jsonld.append(faq_jsonld(faq_pairs))

    title = f"{product['name']} | {SHORT}"
    desc = product["short"][:157]

    body = f"""{head(
        title=title,
        description=desc,
        canonical_path=f"{SR}{product['slug']}/",
        og_image=product.get('image') or f"{SR}assets/{product['slug']}.svg",
        keywords=", ".join(product.get("keywords", [])),
        jsonld=jsonld,
    )}{site_header()}
    <main id="main" class="container">
      <p class="breadcrumb">
        <a href="{url(SR)}">Store</a> ›
        <a href="{url(SR + '#' + cat['slug'])}">{e(cat['name'])}</a> ›
        <span>{e(product['name'])}</span>
      </p>

      <div class="product">
        <div class="prose">
          {'<span class="badge' + (' free' if product['price'] == 0 else '') + '">' + e(product['badge']) + '</span>' if product.get('badge') else ''}
          <h1>{e(product['name'])}</h1>
          <p class="lede">{e(product['short'])}</p>
          <p>{e(product['description'])}</p>

          <h2>What you get</h2>
          <ul class="feature-list">{features}</ul>

          <h2>How it reaches you</h2>
          <p>{e(product['delivery'])}</p>
          {bump_html}

          {'<h2>Questions</h2>' + faqs if faqs else ''}

          <h2>Related products</h2>
          <div class="grid">
{''.join(product_card(p) for p in related)}          </div>
        </div>

        <aside class="buybox">
          <img src="{url(product.get('image') or SR + 'assets/' + product['slug'] + '.svg')}" alt="{e(product['name'])}" width="1200" height="630" />
          <span class="price">{compare}{e(money(product['price']))}<span class="suffix">{e(price_suffix(product))}</span></span>
          <p class="delivery">{e(product['delivery'])}</p>
          {variants}
          {checkout_block(product)}
          <p class="fineprint">Secure checkout by Stripe · {e(str(CONV.get('show_money_back_days', 7)))}-day guarantee on digital products</p>
        </aside>
      </div>

{capture_form(
        "Not ready to buy?",
        "Take a real slice of the data for free and check the joins against your own standards.",
    )}
    </main>

    <div class="stickybuy">
      <span class="price">{compare}{e(money(product['price']))}<span class="suffix">{e(price_suffix(product))}</span></span>
      {checkout_block(product, block=False, note=False)}
    </div>
{site_footer()}"""
    write(fp(f"{product['slug']}/"), body)


def build_thank_you() -> None:
    downloads = "".join(
        f'<li data-slug="{e(p["slug"])}"><strong>{e(p["name"])}</strong> — {e(p["delivery"])}</li>'
        for p in PRODUCTS
        if p["type"] in ("digital", "lead_magnet")
    )
    body = f"""{head(
        title=f"Thank you — your order | {SHORT}",
        description=f"Order confirmation and download access for {STORE['name']} purchases.",
        canonical_path=f"{SR}thank-you/",
        og_image=CFG["seo"]["default_og_image"],
        robots="noindex, follow",
    )}{site_header()}
    <main id="main" class="container">
      <div class="prose" style="max-width:70ch;margin:0 auto">
        <p class="eyebrow">Payment received</p>
        <h1 style="color:#fff;font-size:clamp(1.7rem,4vw,2.6rem);margin-bottom:1rem">Thanks — you're in.</h1>
        <p id="order-ref" class="notice" hidden></p>
        <p>Your receipt is on its way from Stripe, and your delivery email is on its way from {e(SHORT)}.
           Digital files are attached or linked in that email; made-to-order items go into production straight away.</p>

        <h2>What happens next</h2>
        <ul class="feature-list">
          <li><strong>Digital products</strong> — delivery email arrives within a couple of minutes.</li>
          <li><strong>Subscriptions</strong> — skip, pause or cancel any time from the link in your confirmation email.</li>
          <li><strong>Merch</strong> — printed on order, usually shipped within 2–5 business days, with tracking emailed on dispatch.</li>
        </ul>

        <h2>Nothing arrived?</h2>
        <p>Check the spam folder first, then email <a href="mailto:{e(STORE['support_email'])}">{e(STORE['support_email'])}</a>
           with your order reference below and it will be sent again by hand.</p>

        <h2>In the catalogue</h2>
        <ul class="feature-list">{downloads}</ul>

        <p style="margin-top:2rem"><a class="btn" href="{url(SR)}">Back to the store</a></p>
      </div>
    </main>
    <script>
      (function () {{
        var params = new URLSearchParams(window.location.search);
        var ref = params.get('session_id') || params.get('s') || '';
        if (ref) {{
          var el = document.getElementById('order-ref');
          el.textContent = 'Order reference: ' + ref;
          el.hidden = false;
        }}
      }})();
    </script>
{site_footer()}"""
    write(fp("thank-you/"), body)


POLICIES = {
    "refunds": (
        "Refund Policy",
        "How refunds work on digital downloads, memberships and made-to-order apparel.",
        """
        <h2>Digital products</h2>
        <p>Unopened items can be returned within {days} days of delivery for a full refund. Opened
        cosmetics can be returned within the same window if they caused a reaction — tell us what
        happened and we will refund it, no photograph of your face required.</p>

        <h2>Memberships</h2>
        <p>Cancel any time from the customer portal linked in your Stripe receipt. Cancellation stops the
        next renewal and you keep access until the end of the period you already paid for. If a renewal
        charge catches you by surprise and you have not downloaded that period's drop, email within 14 days
        and it is refunded.</p>

        <h2>Apparel and prints</h2>
        <p>Apparel and wall prints are made to order, so they are not stocked and cannot be resold. They are
        replaced or refunded free of charge if they arrive damaged, misprinted, or materially different from
        what was ordered — send a photo within 30 days of delivery. Change-of-mind returns on made-to-order
        items are not accepted, so please check the size guide before ordering.</p>

        <h2>How to claim</h2>
        <p>Email {email} with your order reference and what went wrong. Approved refunds are issued to the
        original payment method through Stripe and usually appear within 5–10 business days.</p>
        """,
    ),
    "shipping": (
        "Delivery & Shipping",
        "Delivery times for digital downloads and made-to-order apparel and prints.",
        """
        <h2>Digital delivery</h2>
        <p>Orders placed before 2pm ship the same working day, otherwise the next one. Free US shipping
        over $35; under that it is a flat $4.95, shown before you pay. Tracking is emailed on dispatch.</p>

        <h2>Memberships</h2>
        <p>Access starts immediately. Refreshes and new packs are announced by email as they ship.</p>

        <h2>Physical items</h2>
        <p>Apparel and prints are produced by a print-on-demand partner after you order. Production usually
        takes 2–5 business days, then transit time depends on destination: typically 3–7 business days
        within the United States and 7–20 business days internationally. Tracking is emailed on dispatch.</p>

        <h2>Customs and duties</h2>
        <p>International orders may attract import duties or taxes set by the destination country. Those
        charges are the customer's responsibility and are not collected at checkout.</p>

        <h2>Wrong address</h2>
        <p>Email {email} straight away if you mistyped an address. Before production starts it can be fixed
        free; after dispatch a replacement has to be reordered.</p>
        """,
    ),
    "privacy": (
        "Privacy Policy",
        "What data this store collects, who processes it, and how to have it deleted.",
        """
        <h2>Who runs this store</h2>
        <p>{legal}. Contact: {email}.</p>

        <h2>What is collected</h2>
        <p>If you buy something, Stripe collects the name, email, payment details and billing address needed
        to take the payment; this store receives only the order details and your email, never your card
        number. If you join the email list, your email address is stored so drops can be sent to you. If you
        order a physical item, your shipping address is passed to the print partner solely to fulfil that
        order.</p>

        <h2>What is not done</h2>
        <p>Your data is never sold, rented or traded. There are no advertising trackers, no ad-network
        pixels and no third-party profiling scripts on these pages.</p>

        <h2>Processors</h2>
        <p>Payments are processed by Stripe under its own privacy policy. Static pages are hosted by GitHub
        Pages, whose servers log standard request data such as IP address. Physical orders are fulfilled by
        a print partner who receives only the shipping details for that order.</p>

        <h2>Your rights</h2>
        <p>You can ask what is held about you, ask for it to be corrected, or ask for it to be deleted, at
        any time, by emailing {email}. Marketing emails unsubscribe in one click and the address is removed
        on unsubscribe. Records tied to a completed sale are kept as long as tax law requires.</p>

        <h2>Cookies</h2>
        <p>These pages set no tracking cookies. Stripe's hosted checkout sets its own cookies necessary for
        payment and fraud prevention.</p>
        """,
    ),
    "terms": (
        "Terms of Sale",
        "The terms that apply to purchases from this store.",
        """
        <h2>Agreement</h2>
        <p>Buying from this store means you accept these terms. The seller is {legal}, contactable at
        {email}.</p>

        <h2>Licence for digital products</h2>
        <p>Digital products are licensed, not sold. You get a personal, non-exclusive, non-transferable
        licence to use the files for your own analysis, including internal use within a business you own.
        You may not resell, redistribute, republish, sublicense or bundle the files or the data in them into
        a product offered to others without written permission. Reasonable citation of findings with a
        credit and a link back is welcome.</p>

        <h2>No guarantee of results</h2>
        <p>Everything sold here is compiled reference data and analysis tooling. It is not financial,
        investment, legal, medical or policy advice, and no decision you make from it is guaranteed to
        work out. Figures are supplied for analysis, not as a statement of fact about the world, and
        upstream sources revise their own numbers regularly. Check anything consequential against the
        primary source before you rely on it.</p>

        <h2>Accuracy</h2>
        <p>Data is compiled carefully from public sources and checked, but it is provided "as is" without
        warranty of completeness or fitness for a particular purpose. Errors reported to {email} are
        corrected and the fix goes out to everyone entitled to updates.</p>

        <h2>Memberships</h2>
        <p>{store} Pass renews automatically at the interval you chose until cancelled. Cancel any time from
        the customer portal; cancellation applies to the next renewal. Prices for existing members are held
        at the rate they signed up on unless notified 30 days in advance.</p>

        <h2>Independence</h2>
        <p>{store} is independent and is not affiliated with, endorsed by, or connected to any of the
        brands whose products it may resell, and no trademark of theirs is claimed here.</p>

        <h2>Liability</h2>
        <p>To the maximum extent permitted by law, liability for any claim connected to a product is limited
        to the amount you paid for that product.</p>

        <h2>Governing law</h2>
        <p>These terms are governed by the laws of the United States and the seller's state of residence.</p>
        """,
    ),
}


def build_policies() -> None:
    index_links = "".join(
        f'<li><a href="{url(SR + "policies/" + slug + "/")}">{e(title)}</a> — {e(desc)}</li>'
        for slug, (title, desc, _) in POLICIES.items()
    )
    body = f"""{head(
        title=f"Store Policies | {SHORT}",
        description=f"Refunds, delivery, privacy and terms of sale for {STORE['name']}.",
        canonical_path=f"{SR}policies/",
        og_image=CFG["seo"]["default_og_image"],
        jsonld=[breadcrumb_jsonld([(STORE["name"], SR), ("Policies", f"{SR}policies/")])],
    )}{site_header()}
    <main id="main" class="container">
      <div class="prose" style="max-width:75ch;margin:0 auto">
        <h1 style="color:#fff;font-size:2rem;margin-bottom:1rem">Store policies</h1>
        <p>The rules that apply when you buy from this store, in plain language.</p>
        <ul class="feature-list">{index_links}</ul>
      </div>
    </main>
{site_footer()}"""
    write(fp("policies/"), body)

    for slug, (title, desc, raw) in POLICIES.items():
        content = raw.format(
            days=CONV.get("show_money_back_days", 7),
            email=STORE["support_email"],
            legal=STORE["legal_entity"],
            store=STORE["name"],
        )
        page = f"""{head(
            title=f"{title} | {SHORT}",
            description=desc,
            canonical_path=f"{SR}policies/{slug}/",
            og_image=CFG["seo"]["default_og_image"],
            jsonld=[
                breadcrumb_jsonld(
                    [
                        (STORE["name"], SR),
                        ("Policies", f"{SR}policies/"),
                        (title, f"{SR}policies/{slug}/"),
                    ]
                )
            ],
        )}{site_header()}
    <main id="main" class="container">
      <p class="breadcrumb"><a href="{url(SR)}">Store</a> › <a href="{url(SR + 'policies/')}">Policies</a> › <span>{e(title)}</span></p>
      <div class="prose" style="max-width:75ch">
        <h1 style="color:#fff;font-size:clamp(1.6rem,4vw,2.2rem);margin-bottom:.6rem">{e(title)}</h1>
        <p style="color:#8f8f8f;font-size:.85rem">Last updated {e(TODAY)}</p>
        {content}
        <p style="margin-top:2rem"><a class="btn secondary" href="{url(SR)}">Back to the store</a></p>
      </div>
    </main>
{site_footer()}"""
        write(fp(f"policies/{slug}/"), page)


def build_assets() -> None:
    write(fa("assets/og-store.svg"), store_og_svg())
    for product in PRODUCTS:
        write(fa(f"assets/{product['slug']}.svg"), artwork_svg(product))


def build_seo() -> None:
    """Shop sitemap, sitemap index entry and robots.txt."""
    paths = [SR, f"{SR}policies/"]
    paths += [f"{SR}{p['slug']}/" for p in PRODUCTS]
    paths += [f"{SR}policies/{slug}/" for slug in POLICIES]

    def priority(path: str) -> str:
        if path == SR:
            return "1.0"
        if path.startswith(f"{SR}policies"):
            return "0.3"
        return "0.85"

    entries = "\n".join(
        f"""  <url>
    <loc>{abs_url(path)}</loc>
    <lastmod>{TODAY}</lastmod>
    <changefreq>{'daily' if path == SR else 'weekly'}</changefreq>
    <priority>{priority(path)}</priority>
  </url>"""
        for path in paths
    )
    write(
        "sitemap.xml",
        f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
</urlset>
""",
    )

    # Sitemap index that names every sitemap in the repo.
    existing = [
        name
        for name in ("sitemap.xml",)
        if os.path.exists(os.path.join(ROOT, name))
    ]
    maps = "".join(
        f"<sitemap><loc>{abs_url('/' + name)}</loc><lastmod>{TODAY}</lastmod></sitemap>"
        for name in existing
    )
    write(
        "sitemap-index.xml",
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{maps}</sitemapindex>\n',
    )

    write(
        "robots.txt",
        f"""# {STORE['name']}
# NOTE: on a GitHub Pages *project* site this file lives under a path prefix and
# crawlers only honour robots.txt at the domain root. It becomes effective the
# moment the site moves to its own domain. Until then, indexing control comes
# from each page's meta robots tag, and sitemaps are submitted in each engine's
# webmaster console.
User-agent: *
Allow: /
Disallow: {url(f"{SR}thank-you/")}

# Named explicitly: some crawlers respect a specific block more reliably than a
# wildcard, and a few ignore Crawl-delay entirely.
User-agent: Googlebot
Allow: /

User-agent: Googlebot-Image
Allow: /

User-agent: Bingbot
Allow: /

User-agent: Slurp
Allow: /

User-agent: DuckDuckBot
Allow: /

User-agent: YandexBot
Allow: /

User-agent: Baiduspider
Allow: /

User-agent: Applebot
Allow: /

User-agent: PetalBot
Allow: /

Sitemap: {abs_url('/sitemap.xml')}
Sitemap: {abs_url('/sitemap-index.xml')}
""",
    )


def validate() -> list[str]:
    """Catch catalogue mistakes before they reach a live page."""
    problems: list[str] = []
    seen: set[str] = set()
    cat_slugs = {c["slug"] for c in CATEGORIES}
    required = {"slug", "name", "category", "type", "price", "short", "description", "delivery", "sku"}
    for product in PRODUCTS:
        missing = required - product.keys()
        if missing:
            problems.append(f"{product.get('slug', '?')}: missing fields {sorted(missing)}")
        if product.get("slug") in seen:
            problems.append(f"duplicate slug: {product['slug']}")
        seen.add(product.get("slug", ""))
        if product.get("slug") != slugify(product.get("slug", "")):
            problems.append(f"{product['slug']}: slug is not URL-safe")
        if product.get("category") not in cat_slugs:
            problems.append(f"{product['slug']}: unknown category {product.get('category')}")
        if product.get("compare_at") and product["compare_at"] <= product["price"]:
            problems.append(f"{product['slug']}: compare_at must be higher than price")
        if product.get("price", 0) < 0:
            problems.append(f"{product['slug']}: negative price")
        link = (product.get("checkout_url") or "").strip()
        if link and not link.startswith("https://"):
            problems.append(f"{product['slug']}: checkout_url must be https")
    for key in ("hero_product", "order_bump", "free_lead_magnet"):
        ref = CONV.get(key)
        if ref and ref not in BY_SLUG:
            problems.append(f"config.conversion.{key} points at unknown product '{ref}'")
    return problems


def margin_report() -> None:
    print("\n  Margin snapshot (price - unit cost):")
    for product in sorted(PRODUCTS, key=lambda p: -p["price"]):
        if product["price"] == 0:
            continue
        cost = product.get("unit_cost", 0)
        margin = (product["price"] - cost) / product["price"] * 100
        recurring = " (recurring)" if product.get("billing") in ("month", "year") else ""
        print(f"    {product['slug']:<30} {money(product['price']):>8}  margin {margin:5.1f}%{recurring}")


def main() -> int:
    problems = validate()
    if problems:
        print("Catalogue validation failed:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    print(f"Building {STORE['name']} → {BASE}{SR}")
    build_assets()
    build_storefront()
    for product in PRODUCTS:
        build_product(product)
    build_thank_you()
    build_policies()
    build_seo()
    live = sum(1 for p in PRODUCTS if (p.get("checkout_url") or "").strip())
    print(f"\n  {len(PRODUCTS)} products, {live} with live checkout links.")
    margin_report()
    print("\nDone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
