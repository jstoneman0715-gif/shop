# SOFTLAUNCH — setup and operations

Everything that can be automated already is. What is left needs accounts only you
can open. In order of revenue impact.

---

## 1. Take payments (this is the only step between the shop and money)

Three ways in, easiest first. Whichever you fill in is what the checkout sheet
offers; anything left blank is hidden rather than shown broken.

### PayPal — 2 minutes, no developer setup

1. Get your PayPal.me handle at <https://paypal.me>.
2. Put it in `data/config.json` → `payments.paypal.me_handle` (just the handle,
   no URL).
3. Push. The cart now opens `paypal.me/<handle>/<total>` with the amount filled in.

### Cash App — 2 minutes, no developer setup

1. Find your `$Cashtag` in the Cash App profile screen.
2. Put it in `data/config.json` → `payments.cashapp.cashtag`.
3. Push. The cart opens `cash.app/$<cashtag>/<total>`.

**Test both with a $1 order before you announce anything.**

### Card — Visa, Mastercard, Amex, Apple Pay, Google Pay

1. Create a Stripe account at <https://dashboard.stripe.com/register>. Funds
   settle directly to your bank; nothing sits with an intermediary.
2. For a whole-cart button: create one Payment Link with "customer chooses
   price" and put it in `payments.card.cart_link`.
3. For per-product buy buttons: create a Price per product, set its metadata
   `slug` to the product's slug, create a Payment Link, and paste it into that
   product's `checkout_url` in `data/products.json`.
4. Set the Payment Link confirmation page to redirect to your `/thank-you/` page.

Stripe also gives you Cash App Pay, Link and Klarna/Afterpay inside the same
hosted checkout — turn them on in the Stripe dashboard, no code change here.

---

## 2. Get the shop online

The repository already carries a workflow that builds, validates and publishes to
GitHub Pages, enabling Pages on its first run. Push to `main` and it goes live at
`https://<you>.github.io/shop/`.

For a real domain: buy one, add a `CNAME` file at the repo root containing it,
point DNS at GitHub Pages, then set `store.base_url` to the domain and
`store.path_prefix` to `""` in `data/config.json`. Every canonical, sitemap entry
and internal link follows automatically.

---

## 3. Source the products

The catalogue describes real, orderable product types — sourcing is yours to
arrange. Two routes:

- **Print-on-demand / dropship** (Printify, Printful, Zendrop, CJ): no stock, no
  cash up front, thinner margin. Best for testing which items move.
- **Small wholesale buys** (Faire, Alibaba, local distributors): better margin,
  requires cash and storage. Worth it once an item proves itself.

Whatever you use, replace the placeholder `unit_cost` values in
`data/products.json` with real landed costs — the margin report is only as
honest as those numbers.

---

## 4. The merchandising bot

`tools/update_catalogue.py` re-ranks the shop for what should sell this month and
runs weekly in CI.

```bash
python3 tools/update_catalogue.py --dry-run            # see the ranking
python3 tools/update_catalogue.py --dry-run --month 12 # plan for December
python3 tools/update_catalogue.py                      # apply
python3 tools/test_catalogue.py                        # tests for the scoring
```

It scores demand, seasonality, unit profit and price-band fit, then reorders the
shop, sets `featured` flags and one seasonal badge. It writes
`data/merchandising-report.md` so you can see why the shop changed. It commits
only when the ranking actually moves.

It will never write ratings, review counts, sold counts or stock numbers. Those
come from real fulfilment and real customers.

---

## 5. Day to day

```bash
python3 tools/build_site.py      # regenerate every page, sitemap, robots.txt
python3 tools/check_site.py      # fails on broken links, bad JSON-LD, missing SEO tags
python3 tools/build_onepage.py   # the single-file storefront
```

Add a product by appending an object to `products` in `data/products.json` with
`slug`, `name`, `category`, `price`, `unit_cost`, `short`, `description`,
`features`, `demand_weight` and `peak_months`. Everything else generates.

---

## 6. Get found

Already handled: canonical URLs, meta descriptions, OG/Twitter tags, JSON-LD
(`OnlineStore`, `Product` + `Offer`, `BreadcrumbList`, `FAQPage`, `ItemList`),
`sitemap.xml`, `robots.txt`, an IndexNow key, and `noindex` on the post-purchase
page.

Needs your Google account: add the site to
[Search Console](https://search.google.com/search-console), verify it, submit
`sitemap.xml`. Google retired its sitemap ping in 2023, so this is the only route
for Google. Bing, Yandex and Seznam are notified automatically after each build.

---

## First-week checklist

- [ ] PayPal handle and Cashtag into `config.json` — checkout works the same day
- [ ] Stripe account, then card checkout
- [ ] Real `unit_cost` values from your actual supplier
- [ ] Push to `main` so Pages publishes
- [ ] Buy a domain and switch `base_url`
- [ ] Verify in Search Console, submit the sitemap
- [ ] Place a $1 test order through every payment method you enabled
