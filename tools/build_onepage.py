#!/usr/bin/env python3
"""Build the shop as one self-contained, mobile-first page.

Design brief: short-form marketplace. Thumb-reachable, one tap to add, one sheet
to pay, no page ever reloads. Desktop gets a grid; phones get a two-column feed
with a sticky checkout bar at the thumb.

Transaction path is deliberately short — add, open cart, pick how to pay:
    Card        Stripe hosted checkout (Visa/Mastercard/Amex, wallets, Cash App Pay)
    PayPal      paypal.me/<handle>/<total>
    Cash App    cash.app/$<cashtag>/<total>
Whichever of those is configured shows up. If none is, the cart still produces a
complete itemised order by email, so no button is ever dead.

Run:  python3 tools/build_onepage.py   ->  dist/onepage.html
"""

from __future__ import annotations

import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
e = html.escape

with open(os.path.join(ROOT, "data", "config.json"), encoding="utf-8") as fh:
    CFG = json.load(fh)
with open(os.path.join(ROOT, "data", "products.json"), encoding="utf-8") as fh:
    CAT = json.load(fh)

STORE = CFG["store"]
BRAND = CFG["brand"]
PAY = CFG["payments"]
SHIP = CFG.get("shipping", {})
MECH = CAT.get("_mechanics", {})
PRODUCTS = CAT["products"]
CATEGORIES = CAT["categories"]
EMAIL = STORE["support_email"]
SHARE_URL = CFG.get("share_url", "")
FREE_OVER = float(SHIP.get("free_over") or MECH.get("free_shipping_threshold") or 0)
FLAT_RATE = float(SHIP.get("flat_rate") or 0)
SUB_PCT = int(MECH.get("subscribe_discount_pct") or 0)
GUARANTEE = int(CFG["conversion"].get("show_money_back_days", 30))


def brandmark() -> str:
    """Store name with its last word accented — derived, never hardcoded."""
    parts = STORE["name"].split()
    if len(parts) == 1:
        return e(parts[0])
    return f'{e(" ".join(parts[:-1]))} <em>{e(parts[-1])}</em>'


def money(value: float) -> str:
    return f"${int(value)}" if float(value).is_integer() else f"${value:,.2f}"


def discount_pct(product: dict) -> int:
    was, now = product.get("compare_at"), product["price"]
    return round((1 - now / was) * 100) if was and was > now else 0


def art(product: dict, index: int) -> str:
    """Inline gradient plate per category — self-contained, no external images."""
    palettes = {
        "beauty": ("#ff2e63", "#ff9ec4"),
        "skincare": ("#ff5c8a", "#ffd0dd"),
        "hair": ("#c2417f", "#ffb3d1"),
        "jewelry": ("#c9922f", "#ffe6a7"),
        "wellness": ("#5b6cff", "#b9c2ff"),
        "fitness": ("#00b3a4", "#8ff0e6"),
        "home": ("#ff7a3d", "#ffc9a8"),
        "kitchen": ("#7a5cff", "#cfc2ff"),
        "pet": ("#ff9f1c", "#ffdda6"),
        "tech": ("#3d8bff", "#b6d4ff"),
        "bags": ("#8c6a4f", "#e3cbb4"),
        "bundles": ("#ff2e63", "#ffd166"),
    }
    a, b = palettes.get(product["category"], (BRAND["accent"], BRAND["accent_soft"]))
    initials = "".join(word[0] for word in product["name"].split()[:2]).upper()
    blobs = "".join(
        f'<circle cx="{40 + i * 55}" cy="{60 + (i % 2) * 40}" r="{34 - i * 4}" fill="{b}" opacity="{0.30 + i * 0.08}"/>'
        for i in range(3 + index % 2)
    )
    return (
        f'<svg class="plate" viewBox="0 0 220 150" preserveAspectRatio="xMidYMid slice" '
        f'role="img" aria-label="{e(product["name"])}">'
        f'<defs><linearGradient id="g{index}" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0%" stop-color="{a}"/><stop offset="100%" stop-color="{b}"/>'
        f"</linearGradient></defs>"
        f'<rect width="220" height="150" fill="url(#g{index})"/>{blobs}'
        f'<text x="110" y="90" text-anchor="middle" font-family="system-ui,sans-serif" '
        f'font-size="46" font-weight="800" fill="#ffffff" opacity=".9">{e(initials)}</text></svg>'
    )


def media(product: dict, index: int) -> str:
    """Photo when the catalogue has one, generated plate when it does not.

    The plate stays in the DOM underneath as a real fallback: this page is also
    published to hosts whose content policy blocks off-site images, and a broken
    image icon on every card is worse than an abstract plate.
    """
    plate = art(product, index)
    photo = (product.get("image") or "").strip()
    if not photo:
        return plate
    return (
        f'{plate}<img class="photo" src="{e(photo)}" alt="{e(product["name"])}" '
        f'loading="lazy" decoding="async" '
        f'onerror="this.remove()" />'
    )


def card(product: dict, index: int) -> str:
    pct = discount_pct(product)
    off = f'<span class="off">−{pct}%</span>' if pct else ""
    was = f'<s>{e(money(product["compare_at"]))}</s>' if product.get("compare_at") else ""
    badge = f'<span class="badge">{e(product["badge"])}</span>' if product.get("badge") else ""

    variants = ""
    if product.get("variants"):
        options = "".join(f"<option>{e(v)}</option>" for v in product["variants"])
        variants = (
            f'<select class="variant" data-slug="{e(product["slug"])}" '
            f'aria-label="Option for {e(product["name"])}">{options}</select>'
        )

    sub = ""
    if product.get("subscribe") and SUB_PCT:
        sub = (
            f'<label class="sub"><input type="checkbox" class="subtoggle" '
            f'data-slug="{e(product["slug"])}"> Subscribe &amp; save {SUB_PCT}%</label>'
        )

    # Stock and reviews render only when the data is real. Empty stays invisible.
    stock = ""
    if isinstance(product.get("stock"), int) and product["stock"] <= 10:
        stock = f'<span class="stock">Only {product["stock"]} left</span>'

    feats = "".join(f"<li>{e(f)}</li>" for f in (product.get("features") or [])[:3])

    return f"""      <article class="card" id="p-{e(product['slug'])}" data-cat="{e(product['category'])}">
        <div class="media">{media(product, index)}{off}{badge}</div>
        <div class="body">
          <h3>{e(product['name'])}</h3>
          <p class="blurb">{e(product['short'])}</p>
          <ul class="feat">{feats}</ul>
          <div class="pricerow">
            <span class="price">{was}<strong>{e(money(product['price']))}</strong></span>
            {stock}
          </div>
          {sub}
          <div class="buyrow">
            {variants}
            <button class="add" data-slug="{e(product['slug'])}">Add</button>
            <button class="share-item" data-slug="{e(product['slug'])}" aria-label="Share {e(product['name'])}">↗</button>
          </div>
        </div>
      </article>"""


def sections() -> str:
    out, index = [], 0
    for category in CATEGORIES:
        members = [p for p in PRODUCTS if p["category"] == category["slug"]]
        if not members:
            continue
        cards = []
        for product in members:
            cards.append(card(product, index))
            index += 1
        out.append(
            f"""    <section class="cat" id="{e(category['slug'])}">
      <div class="sechead"><h2>{e(category['name'])}</h2><p>{e(category['blurb'])}</p></div>
      <div class="grid">
{chr(10).join(cards)}
      </div>
    </section>"""
        )
    return "\n".join(out)


def chips() -> str:
    items = "".join(
        f'<a class="chip" href="#{e(c["slug"])}">{e(c["name"])}</a>'
        for c in CATEGORIES
        if any(p["category"] == c["slug"] for p in PRODUCTS)
    )
    return f'<nav class="chips" aria-label="Categories"><a class="chip on" href="#top">All</a>{items}</nav>'


def catalogue_js() -> str:
    return json.dumps(
        {
            p["slug"]: {
                "name": p["name"],
                "price": p["price"],
                "sku": p["sku"],
                "url": (p.get("checkout_url") or "").strip(),
                "sub": bool(p.get("subscribe")) and bool(SUB_PCT),
            }
            for p in PRODUCTS
        },
        ensure_ascii=False,
    )


def build() -> str:
    featured = [p for p in PRODUCTS if p.get("featured")][:6]
    hero = featured[0] if featured else PRODUCTS[0]
    pay_js = json.dumps(
        {
            "card": bool(PAY["card"].get("enabled")) and bool(PAY["card"].get("cart_link")),
            "cardLink": PAY["card"].get("cart_link", ""),
            "paypal": PAY["paypal"].get("me_handle", "") if PAY["paypal"].get("enabled") else "",
            "cashapp": PAY["cashapp"].get("cashtag", "") if PAY["cashapp"].get("enabled") else "",
        }
    )

    return f"""<title>{e(STORE['name'])} — {e(STORE['tagline'])}</title>
<style>
  :root {{
    --bg:#faf7f8; --surface:#ffffff; --raised:#f3eef0;
    --ink:#120f13; --soft:#6b6270; --line:#e7dfe3;
    --accent:{BRAND['accent']}; --accent2:{BRAND['accent_soft']}; --on-accent:#ffffff;
    --good:#12805c; --shadow:0 1px 2px rgba(18,15,19,.06),0 10px 30px rgba(18,15,19,.07);
    color-scheme:light;
  }}
  @media (prefers-color-scheme:dark) {{
    :root:not([data-theme="light"]) {{
      --bg:{BRAND['bg']}; --surface:{BRAND['bg_alt']}; --raised:#1e1e28;
      --ink:{BRAND['text']}; --soft:#a09aa8; --line:#2a2a36;
      --good:#4fd6a8; --shadow:0 1px 2px rgba(0,0,0,.6),0 10px 30px rgba(0,0,0,.45);
      color-scheme:dark;
    }}
  }}
  :root[data-theme="dark"] {{
    --bg:{BRAND['bg']}; --surface:{BRAND['bg_alt']}; --raised:#1e1e28;
    --ink:{BRAND['text']}; --soft:#a09aa8; --line:#2a2a36;
    --good:#4fd6a8; --shadow:0 1px 2px rgba(0,0,0,.6),0 10px 30px rgba(0,0,0,.45);
    color-scheme:dark;
  }}

  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--ink);
    font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;line-height:1.55;
    -webkit-font-smoothing:antialiased;padding-bottom:76px}}
  button{{font:inherit;cursor:pointer}}
  a{{color:var(--accent)}}
  :focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
  .wrap{{max-width:1180px;margin:0 auto;padding:0 14px}}
  .sr{{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}}

  header.top{{position:sticky;top:0;z-index:30;background:var(--surface);border-bottom:1px solid var(--line)}}
  .bar{{display:flex;align-items:center;gap:10px;padding:10px 0}}
  .brand{{font-weight:900;letter-spacing:-.04em;font-size:20px}}
  .brand em{{font-style:normal;color:var(--accent)}}
  .brand{{white-space:nowrap}}
  .grow{{flex:1}}
  .iconbtn{{background:var(--raised);border:1px solid var(--line);color:var(--ink);
    border-radius:999px;padding:0 15px;min-height:44px;font-size:14px;font-weight:600}}
  .chips{{display:flex;gap:8px;overflow-x:auto;padding:0 0 10px;scrollbar-width:none}}
  .chips::-webkit-scrollbar{{display:none}}
  .chip{{flex:0 0 auto;background:var(--raised);border:1px solid var(--line);color:var(--ink);
    text-decoration:none;padding:0 16px;border-radius:999px;font-size:13.5px;font-weight:650;white-space:nowrap;
    min-height:44px;display:inline-flex;align-items:center}}
  .chip.on{{background:var(--accent);color:var(--on-accent);border-color:var(--accent)}}

  .hero{{display:grid;grid-template-columns:1.05fr .95fr;gap:26px;align-items:center;padding:26px 0 14px}}
  @media (max-width:820px){{.hero{{grid-template-columns:1fr;gap:16px;padding:18px 0 8px}}}}
  h1{{font-size:clamp(28px,7vw,46px);line-height:1.03;letter-spacing:-.04em;margin:0 0 10px;text-wrap:balance}}
  .lede{{color:var(--soft);font-size:16px;margin:0 0 16px;max-width:46ch}}
  .herobtns{{display:flex;gap:10px;flex-wrap:wrap}}
  .btn{{background:var(--accent);color:var(--on-accent);border:1px solid transparent;text-decoration:none;
    border-radius:12px;padding:13px 20px;font-weight:750;font-size:15px;display:inline-block}}
  .btn.ghost{{background:transparent;color:var(--ink);border-color:var(--line)}}
  .heroart{{position:relative;border-radius:18px;overflow:hidden;box-shadow:var(--shadow);aspect-ratio:5/4}}
  .heroart svg{{width:100%;height:100%;display:block}}
  .heroart .photo{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
  .perks{{display:flex;gap:14px;flex-wrap:wrap;color:var(--soft);font-size:13px;margin-top:14px}}
  .perks span::before{{content:"✓";color:var(--good);font-weight:800;margin-right:5px}}

  section.cat{{padding:22px 0 6px}}
  .sechead h2{{margin:0;font-size:20px;letter-spacing:-.02em}}
  .sechead p{{margin:2px 0 14px;color:var(--soft);font-size:14px;max-width:70ch}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(232px,1fr));gap:14px}}
  @media (max-width:560px){{.grid{{grid-template-columns:1fr 1fr;gap:10px}}}}

  .card{{background:var(--surface);border:1px solid var(--line);border-radius:16px;overflow:hidden;
    display:flex;flex-direction:column;box-shadow:var(--shadow)}}
  .media{{position:relative;aspect-ratio:4/3;background:var(--raised)}}
  .plate{{width:100%;height:100%;display:block}}
  .media .photo{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;display:block}}
  .off{{position:absolute;left:8px;top:8px;background:var(--accent);color:var(--on-accent);
    font-size:12px;font-weight:800;padding:3px 8px;border-radius:8px}}
  .badge{{position:absolute;right:8px;top:8px;background:rgba(0,0,0,.62);color:#fff;
    font-size:10.5px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;padding:3px 8px;border-radius:8px}}
  .body{{padding:11px 12px 12px;display:flex;flex-direction:column;gap:6px;flex:1}}
  .card h3{{margin:0;font-size:15px;line-height:1.25;letter-spacing:-.01em}}
  .blurb{{margin:0;color:var(--soft);font-size:12.8px}}
  ul.feat{{margin:0;padding-left:15px;color:var(--soft);font-size:12px;flex:1}}
  @media (max-width:560px){{ul.feat{{display:none}} .blurb{{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}}}
  .pricerow{{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}}
  .price strong{{font-size:20px;letter-spacing:-.02em}}
  .price s{{color:var(--soft);font-size:13px;margin-right:5px}}
  .stock{{color:var(--accent);font-size:12px;font-weight:700}}
  .sub{{display:flex;align-items:center;gap:6px;font-size:12.5px;color:var(--soft)}}
  .buyrow{{display:flex;align-items:center;gap:6px;margin-top:2px}}
  select.variant{{flex:1;min-width:0;font:inherit;font-size:13px;padding:0 8px;min-height:44px;
    border-radius:10px;border:1px solid var(--line);background:var(--raised);color:var(--ink)}}
  .add{{flex:1;background:var(--accent);color:var(--on-accent);border:0;border-radius:10px;
    padding:0 12px;min-height:44px;font-weight:750;font-size:14px}}
  .add.done{{background:var(--good)}}
  .share-item{{background:var(--raised);border:1px solid var(--line);color:var(--ink);
    border-radius:10px;padding:0 13px;min-height:44px;min-width:44px;font-size:15px;line-height:1}}

  /* sticky thumb bar — the whole transaction lives here on a phone */
  .thumb{{position:fixed;left:0;right:0;bottom:0;z-index:35;background:var(--surface);
    border-top:1px solid var(--line);padding:9px 14px calc(9px + env(safe-area-inset-bottom));
    display:flex;align-items:center;gap:10px}}
  .thumb .tot{{font-weight:800;font-size:17px}}
  .thumb .sub2{{color:var(--soft);font-size:12px}}
  .thumb .go{{margin-left:auto;background:var(--accent);color:var(--on-accent);border:0;
    border-radius:12px;padding:12px 20px;font-weight:800;font-size:15px}}
  .thumb .go[disabled]{{opacity:.45}}

  .ship{{margin-top:8px}}
  .shipbar{{height:6px;background:var(--raised);border-radius:999px;overflow:hidden}}
  .shipbar i{{display:block;height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2));width:0}}
  .shiptxt{{font-size:12px;color:var(--soft);margin:5px 0 0}}
  .shiptxt.done{{color:var(--good);font-weight:650}}

  .scrim{{position:fixed;inset:0;background:rgba(6,4,8,.5);z-index:40;opacity:0;pointer-events:none;transition:opacity .18s}}
  .scrim.open{{opacity:1;pointer-events:auto}}
  aside.cart{{position:fixed;z-index:50;background:var(--surface);display:flex;flex-direction:column;
    transition:transform .22s ease}}
  @media (min-width:721px){{
    aside.cart{{top:0;right:0;bottom:0;width:420px;border-left:1px solid var(--line);transform:translateX(105%)}}
    aside.cart.open{{transform:none}}
  }}
  @media (max-width:720px){{
    aside.cart{{left:0;right:0;bottom:0;max-height:88vh;border-radius:20px 20px 0 0;
      border-top:1px solid var(--line);transform:translateY(102%)}}
    aside.cart.open{{transform:none}}
  }}
  .ch{{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;border-bottom:1px solid var(--line)}}
  .ch h2{{margin:0;font-size:16px}}
  .x{{background:transparent;border:0;color:var(--soft);font-size:26px;line-height:1;
    min-height:44px;min-width:44px}}
  .items{{flex:1;overflow-y:auto;padding:4px 16px}}
  .empty{{color:var(--soft);text-align:center;padding:30px 0;font-size:14px}}
  .line{{display:grid;grid-template-columns:1fr auto;gap:4px 10px;padding:12px 0;border-bottom:1px solid var(--line)}}
  .ln{{font-weight:650;font-size:14.5px}}
  .lv{{color:var(--soft);font-size:12px}}
  .lp{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
  .qty{{display:inline-flex;align-items:center;border:1px solid var(--line);border-radius:8px;overflow:hidden;margin-top:4px}}
  .qty button{{background:var(--raised);border:0;color:var(--ink);width:44px;height:44px;font-size:17px}}
  .qty span{{min-width:30px;text-align:center;font-size:13.5px}}
  .cf{{border-top:1px solid var(--line);padding:14px 16px calc(14px + env(safe-area-inset-bottom));display:flex;flex-direction:column;gap:10px}}
  .tot2{{display:flex;justify-content:space-between;align-items:baseline}}
  .tot2 strong{{font-size:22px;font-variant-numeric:tabular-nums}}
  .pays{{display:grid;gap:8px}}
  .pay{{border:1px solid var(--line);background:var(--raised);color:var(--ink);border-radius:12px;
    padding:13px;font-weight:750;font-size:15px;display:flex;align-items:center;justify-content:center;gap:8px}}
  .pay.primary{{background:var(--accent);color:var(--on-accent);border-color:var(--accent)}}
  .pay[disabled]{{opacity:.45}}
  .paynote{{font-size:11.5px;color:var(--soft);margin:0;text-align:center}}
  .cards{{display:flex;gap:6px;justify-content:center;margin-top:2px}}
  .cards span{{border:1px solid var(--line);border-radius:5px;padding:2px 7px;font-size:10px;
    font-weight:800;letter-spacing:.03em;color:var(--soft)}}

  footer{{border-top:1px solid var(--line);margin-top:26px;padding:22px 0 30px;color:var(--soft);font-size:13px}}
  footer p{{max-width:78ch}}
  .toast{{position:fixed;left:50%;bottom:88px;transform:translateX(-50%) translateY(14px);z-index:60;
    background:var(--ink);color:var(--bg);padding:10px 16px;border-radius:999px;font-size:14px;font-weight:650;
    opacity:0;pointer-events:none;transition:opacity .2s,transform .2s}}
  .toast.on{{opacity:1;transform:translateX(-50%) translateY(0)}}
  @media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
</style>

<header class="top" id="top">
  <div class="wrap">
    <div class="bar">
      <span class="brand">{brandmark()}</span>
      <span class="grow"></span>
      <button class="iconbtn" id="share-store">Share</button>
      <button class="iconbtn" id="open-cart">Cart <span id="cart-count">0</span></button>
    </div>
    {chips()}
  </div>
</header>

<main class="wrap">
  <div class="hero">
    <div>
      <h1>{e(STORE['tagline'])}</h1>
      <p class="lede">{e(STORE['description'])}</p>
      <div class="herobtns">
        <a class="btn" href="#beauty">Shop the drop</a>
        <a class="btn ghost" href="#bundles">See bundles</a>
      </div>
      <div class="perks">
        <span>Free shipping over {e(money(FREE_OVER))}</span>
        <span>{GUARANTEE}-day returns</span>
        <span>Ships in 1–2 days</span>
      </div>
    </div>
    <div class="heroart">{media(hero, 99)}</div>
  </div>

{sections()}
</main>

<footer>
  <div class="wrap">
    <p><strong>{e(STORE['legal_entity'])}</strong> · <a href="mailto:{e(EMAIL)}">{e(EMAIL)}</a></p>
    <p>Free US shipping over {e(money(FREE_OVER))}, otherwise {e(money(FLAT_RATE))} flat.
      {GUARANTEE}-day returns on unopened items; anything faulty is replaced or refunded.
      Prices in USD.</p>
    <p>No ratings, sold counts or countdowns appear anywhere on this site, because we would
      have had to invent them. Reviews go up when there are real ones.</p>
  </div>
</footer>

<div class="thumb">
  <div>
    <div class="tot" id="thumb-total">$0</div>
    <div class="sub2" id="thumb-sub">Cart empty</div>
  </div>
  <button class="go" id="thumb-go" disabled>Checkout</button>
</div>

<div class="scrim" id="scrim"></div>
<aside class="cart" id="cart" role="dialog" aria-label="Cart" aria-modal="false">
  <div class="ch"><h2>Your bag</h2><button class="x" id="close-cart" aria-label="Close">×</button></div>
  <div class="items" id="items"></div>
  <div class="cf">
    <div class="ship">
      <div class="shipbar"><i id="shipfill"></i></div>
      <p class="shiptxt" id="shiptxt"></p>
    </div>
    <div class="tot2"><span>Total</span><strong id="total">$0</strong></div>
    <div class="pays" id="pays"></div>
    <p class="paynote" id="paynote"></p>
    <div class="cards"><span>VISA</span><span>MASTERCARD</span><span>AMEX</span><span>APPLE PAY</span></div>
  </div>
</aside>
<div class="toast" id="toast"></div>

<script>
(function () {{
  "use strict";
  var C = {catalogue_js()};
  var PAY = {pay_js};
  var EMAIL = {json.dumps(EMAIL)};
  var SHARE_URL = {json.dumps(SHARE_URL)};
  var STORE = {json.dumps(STORE["name"])};
  var FREE_OVER = {FREE_OVER};
  var SUB_PCT = {SUB_PCT};
  var KEY = "shop.bag.v1";

  var bag = read();
  function read() {{
    try {{
      var raw = JSON.parse(localStorage.getItem(KEY) || "[]");
      return Array.isArray(raw) ? raw.filter(function (l) {{ return C[l.slug]; }}) : [];
    }} catch (err) {{ return []; }}
  }}
  function save() {{ try {{ localStorage.setItem(KEY, JSON.stringify(bag)); }} catch (err) {{}} }}

  function money(v) {{ return "$" + (Number.isInteger(v) ? v : v.toFixed(2)); }}
  function unit(line) {{
    var price = C[line.slug].price;
    return line.sub ? price * (1 - SUB_PCT / 100) : price;
  }}
  function total() {{
    return bag.reduce(function (sum, l) {{ return sum + unit(l) * l.qty; }}, 0);
  }}
  function count() {{ return bag.reduce(function (n, l) {{ return n + l.qty; }}, 0); }}

  function toast(message) {{
    // The bag sheet already shows the change, and a toast would sit on top of
    // the pay button. Stay quiet while it is open.
    if (document.getElementById("cart").classList.contains("open")) return;
    var el = document.getElementById("toast");
    el.textContent = message;
    el.classList.add("on");
    clearTimeout(el._t);
    el._t = setTimeout(function () {{ el.classList.remove("on"); }}, 1600);
  }}

  function add(slug, variant, sub) {{
    var existing = bag.filter(function (l) {{
      return l.slug === slug && l.variant === variant && l.sub === sub;
    }})[0];
    if (existing) {{ existing.qty += 1; }}
    else {{ bag.push({{ slug: slug, variant: variant, sub: sub, qty: 1 }}); }}
    save(); render();
  }}

  function bump(index, delta) {{
    bag[index].qty += delta;
    if (bag[index].qty < 1) bag.splice(index, 1);
    save(); render();
  }}

  function payOptions() {{
    var box = document.getElementById("pays");
    var note = document.getElementById("paynote");
    box.innerHTML = "";
    var sum = total();
    var made = [];

    if (PAY.cardLink) made.push(["Pay by card", "primary", function () {{ go(PAY.cardLink); }}]);
    if (PAY.paypal) {{
      made.push(["PayPal", made.length ? "" : "primary", function () {{
        go("https://paypal.me/" + PAY.paypal + "/" + sum.toFixed(2));
      }}]);
    }}
    if (PAY.cashapp) {{
      made.push(["Cash App", made.length ? "" : "primary", function () {{
        go("https://cash.app/$" + PAY.cashapp.replace(/^\\$/, "") + "/" + sum.toFixed(2));
      }}]);
    }}
    if (!made.length) made.push(["Place order", "primary", orderByEmail]);

    made.forEach(function (spec) {{
      var button = document.createElement("button");
      button.className = "pay " + spec[1];
      button.textContent = spec[0] + (spec[1] === "primary" ? " · " + money(sum) : "");
      button.disabled = bag.length === 0;
      button.addEventListener("click", spec[2]);
      box.appendChild(button);
    }});

    note.textContent = PAY.cardLink || PAY.paypal || PAY.cashapp
      ? "Checkout is handled by the payment provider. This site never sees your card details."
      : "Card checkout is switching on. Placing an order sends an itemised request and a payment link comes back, usually same day.";
  }}

  function go(url) {{ window.open(url, "_blank", "noopener"); }}

  function orderByEmail() {{
    var lines = bag.map(function (l) {{
      var item = C[l.slug];
      return "- " + item.name + (l.variant ? " (" + l.variant + ")" : "")
        + (l.sub ? " [subscribe]" : "") + " x" + l.qty + "  " + money(unit(l) * l.qty)
        + "  [" + item.sku + "]";
    }});
    window.location.href = "mailto:" + EMAIL
      + "?subject=" + encodeURIComponent("Order — " + STORE)
      + "&body=" + encodeURIComponent("Order from " + STORE + ":\\n\\n" + lines.join("\\n")
        + "\\n\\nTotal: " + money(total()) + "\\n\\nShipping address:\\n");
  }}

  function render() {{
    var n = count(), sum = total();
    document.getElementById("cart-count").textContent = String(n);
    document.getElementById("thumb-total").textContent = money(sum);
    document.getElementById("thumb-sub").textContent =
      n === 0 ? "Cart empty" : n + (n === 1 ? " item" : " items");
    document.getElementById("thumb-go").disabled = n === 0;
    document.getElementById("total").textContent = money(sum);

    var box = document.getElementById("items");
    box.innerHTML = "";
    if (!bag.length) {{
      var empty = document.createElement("p");
      empty.className = "empty";
      empty.textContent = "Your bag is empty.";
      box.appendChild(empty);
    }}

    bag.forEach(function (line, index) {{
      var item = C[line.slug];
      var row = document.createElement("div");
      row.className = "line";

      var left = document.createElement("div");
      var name = document.createElement("div");
      name.className = "ln"; name.textContent = item.name; left.appendChild(name);

      var meta = [];
      if (line.variant) meta.push(line.variant);
      if (line.sub) meta.push("Subscribe · " + SUB_PCT + "% off");
      if (meta.length) {{
        var subline = document.createElement("div");
        subline.className = "lv"; subline.textContent = meta.join(" · "); left.appendChild(subline);
      }}

      var qty = document.createElement("div");
      qty.className = "qty";
      var minus = document.createElement("button");
      minus.type = "button"; minus.textContent = "−";
      minus.setAttribute("aria-label", "Remove one " + item.name);
      minus.addEventListener("click", function () {{ bump(index, -1); }});
      var num = document.createElement("span");
      num.textContent = String(line.qty);
      var plus = document.createElement("button");
      plus.type = "button"; plus.textContent = "+";
      plus.setAttribute("aria-label", "Add one " + item.name);
      plus.addEventListener("click", function () {{ bump(index, 1); }});
      qty.appendChild(minus); qty.appendChild(num); qty.appendChild(plus);
      left.appendChild(qty);

      var price = document.createElement("div");
      price.className = "lp";
      price.textContent = money(unit(line) * line.qty);

      row.appendChild(left); row.appendChild(price);
      box.appendChild(row);
    }});

    var remaining = Math.max(0, FREE_OVER - sum);
    var fill = document.getElementById("shipfill");
    var text = document.getElementById("shiptxt");
    fill.style.width = Math.min(100, FREE_OVER ? (sum / FREE_OVER) * 100 : 0) + "%";
    if (!bag.length) {{ text.textContent = ""; text.className = "shiptxt"; }}
    else if (remaining > 0) {{
      text.textContent = "Add " + money(remaining) + " for free shipping";
      text.className = "shiptxt";
    }} else {{
      text.textContent = "Free shipping unlocked";
      text.className = "shiptxt done";
    }}

    payOptions();
  }}

  function openCart(open) {{
    document.getElementById("cart").classList.toggle("open", open);
    document.getElementById("scrim").classList.toggle("open", open);
    document.getElementById("cart").setAttribute("aria-modal", String(open));
    if (open) document.getElementById("close-cart").focus();
  }}

  function share(title, text) {{
    var url = SHARE_URL || location.href;
    if (navigator.share) {{
      navigator.share({{ title: title, text: text, url: url }}).catch(function () {{}});
      return;
    }}
    if (navigator.clipboard) {{
      navigator.clipboard.writeText(url).then(function () {{ toast("Link copied"); }},
        function () {{ toast(url); }});
      return;
    }}
    toast(url);
  }}

  document.querySelectorAll(".add").forEach(function (button) {{
    button.addEventListener("click", function () {{
      var slug = button.dataset.slug;
      var variant = document.querySelector('.variant[data-slug="' + slug + '"]');
      var sub = document.querySelector('.subtoggle[data-slug="' + slug + '"]');
      add(slug, variant ? variant.value : "", Boolean(sub && sub.checked));
      var was = button.textContent;
      button.textContent = "Added";
      button.classList.add("done");
      setTimeout(function () {{ button.textContent = was; button.classList.remove("done"); }}, 1100);
      toast(C[slug].name + " added");
    }});
  }});

  document.querySelectorAll(".share-item").forEach(function (button) {{
    button.addEventListener("click", function () {{
      var item = C[button.dataset.slug];
      share(item.name + " · " + STORE, item.name + " — " + money(item.price));
    }});
  }});

  document.getElementById("share-store").addEventListener("click", function () {{
    share(STORE, {json.dumps(STORE['tagline'])});
  }});
  document.getElementById("open-cart").addEventListener("click", function () {{ openCart(true); }});
  document.getElementById("thumb-go").addEventListener("click", function () {{ openCart(true); }});
  document.getElementById("close-cart").addEventListener("click", function () {{ openCart(false); }});
  document.getElementById("scrim").addEventListener("click", function () {{ openCart(false); }});
  document.addEventListener("keydown", function (event) {{
    if (event.key === "Escape") openCart(false);
  }});

  document.querySelectorAll(".chip").forEach(function (chip) {{
    chip.addEventListener("click", function () {{
      document.querySelectorAll(".chip").forEach(function (c) {{ c.classList.remove("on"); }});
      chip.classList.add("on");
    }});
  }});

  render();
}})();
</script>
"""


def main() -> int:
    out = os.path.join(ROOT, "dist", "onepage.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    page = build()
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(page)
    print(f"wrote dist/onepage.html ({len(page):,} bytes, {len(PRODUCTS)} products)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
