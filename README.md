# All The Rage

A mobile-first shop for beauty, jewelry, wellness and home goods. Static HTML, no
storefront platform, no revenue share — payments go straight to your own PayPal,
Cash App or Stripe account.

27 products across 12 categories, priced in the $14–34 band that converts best,
with bundles above it to lift order value.

## How it fits together

```
data/products.json ─┐
data/config.json ───┴─> tools/build_site.py     ─> every page, sitemap, robots.txt
                     └─> tools/build_onepage.py ─> dist/onepage.html (single file)
                                  │
                                  └─> tools/check_site.py  (fails the build on a broken page)

tools/update_catalogue.py ─> re-ranks the shop each month, writes a report
```

You edit JSON. CI regenerates, validates, publishes and re-ranks. No HTML is ever
edited by hand.

## Commands

```bash
python3 tools/sourcing_report.py             # what is sourced vs still a guess
python3 tools/check_images.py                # which product images actually load
python3 tools/build_site.py                  # regenerate the multi-page site
python3 tools/build_onepage.py               # regenerate the single-file storefront
python3 tools/check_site.py                  # links, JSON-LD, SEO tags, SVG validity
python3 tools/update_catalogue.py --dry-run  # what should sell this month
python3 tools/test_catalogue.py              # tests for the ranking logic
```

`build_site.py` prints the margin on every product, so a pricing change shows its
effect immediately.

## What the shop does for order value

- **Free-shipping progress bar** at $35 — the highest-return order-value lever a
  small store has, and the threshold sits above the natural basket so most people
  add one more thing.
- **Bundles** priced under the sum of their parts.
- **Subscribe and save** on refillables at 15% off, because repeat purchase, not
  acquisition, is what makes these shops profitable.
- **One-tap add, one sheet to pay.** Nothing reloads, the bag survives a refresh,
  and every tap target clears 44px.

## Getting started

New to this? [ACCOUNTS.md](ACCOUNTS.md) is the ordered checklist for every
account you need, shortest path first. Steps 0–2 are an afternoon and end with
the shop able to take money.

## Payments

Card (Visa/Mastercard/Amex plus Apple Pay and Google Pay) through Stripe, PayPal
via `paypal.me`, and Cash App via `cash.app`. PayPal and Cash App need only a
username — no API keys, no developer setup. Whatever is configured shows up in
the checkout sheet; anything blank is hidden rather than shown broken. See
[SETUP.md](SETUP.md).

## What is deliberately absent

No star ratings, review counts, sold counts, viewer counts, countdown timers or
stock numbers. Every one of those would have to be invented on a shop that has
not sold anything yet. Reviews go up when real customers leave them; stock counts
render only when real fulfilment supplies them. The merchandising bot is
explicitly forbidden from writing any of them, and there is a test that proves
it doesn't.

Electronics are also absent on purpose: highest revenue in the category data,
but the thinnest margin and the worst return rates.
