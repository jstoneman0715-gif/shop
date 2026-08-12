# Accounts — the shortest path to taking money

Ordered by what unlocks what. Steps 0–2 can be done in an afternoon and get the
shop taking payments. Steps 3–4 are what let you actually ship.

Not legal or tax advice — rules vary by state, so confirm anything money-related
with your own state's revenue department.

---

## Step 0 — Get an EIN first (10 minutes, free)

Do this before anything else. It is free, instant, and almost every other
account on this list goes smoother with it.

- Go to **irs.gov** and search "Apply for an EIN online"
- Sole proprietor is a valid answer — you do not need an LLC to get one
- You get the number on screen at the end. Save it.

**Why first:** business accounts at PayPal, Stripe and every wholesale supplier
ask for a tax ID. Using an EIN instead of your SSN keeps your social security
number off a dozen third-party systems, and it is the difference between a
business account and a personal one.

Only official IRS site. Anything charging you for an EIN is reselling a free
form.

---

## Step 1 — Payment accounts (same day, this is the revenue step)

### PayPal — easiest, do this one first

1. **paypal.com** → Sign Up → choose **Business Account**, not Personal
2. Business type: sole proprietorship. Enter the EIN from Step 0
3. Link your bank account
4. Go to **paypal.me** and claim your handle (e.g. `paypal.me/alltherage`)
5. Put just the handle — no URL — into `data/config.json`:
   `payments.paypal.me_handle`

### Cash App — also quick, but read the warning

1. In the Cash App app: profile → **switch to a Business account**
2. Your `$Cashtag` is your handle
3. Put it into `data/config.json` → `payments.cashapp.cashtag`

**The warning that matters:** taking sales through a *personal* PayPal or Cash
App account is against both platforms' terms and is a common way to get funds
frozen mid-launch. Business accounts charge a fee per transaction; that fee is
the price of not having your money held. Switch both before your first sale.

### Stripe — 30 minutes, needed for card payments

1. **dashboard.stripe.com/register**
2. Business details, EIN, bank account
3. Products → create a Payment Link per item, or one "customer chooses amount"
   link for the whole cart
4. Paste into `payments.card.cart_link`, or per product into `checkout_url`

Stripe gives you Visa, Mastercard, Amex, Apple Pay, Google Pay and Cash App Pay
on one hosted page. Activation can take a day or two if they ask for documents,
which is why PayPal goes first.

**After any of these:** push the config change, then place a **$1 test order
through every method you enabled** before telling anyone the shop is open.

---

## Step 2 — Sales tax registration (varies by state)

Search "*[your state]* sales tax permit" and register with your state's revenue
department. Usually free or low cost.

This produces your **resale certificate**, which does two jobs: it makes you
legal to collect sales tax, and it is what wholesale suppliers ask for before
they will open an account. Skipping it is the single most common thing that
stalls a supplier application.

---

## Step 3 — Supplier accounts (start with two)

Do not open eight accounts. Open the two that cover the highest-margin half of
the catalogue, prove they work, then expand.

### JB Jewelry BLVD — jewelry

- **jb-jewelry.com** → wholesale / dropshipping application
- Gold-filled and stainless, **no MOQ**, ships from Fort Lauderdale in 1–7 days
- Have ready: business name, EIN, resale certificate
- Covers: stack rings, herringbone chain, huggie hoops, the Everyday Stack bundle

### Blanka or SelfNamed — beauty and skincare

- **blanka.com** or **selfnamed.com** → sign up, free plan to browse
- Both zero MOQ; SelfNamed is EU-certified and FDA-compliant with a US warehouse
- Covers: lip glaze, lip mask, serum, SPF, and the Glow Starter bundle

### CJdropshipping — everything else, later

- **cjdropshipping.com** → free account, no application needed
- Use their image search to match the home, kitchen, pet, tech and bag items
- Filter to **US warehouse** or the 1–2 day dispatch promise on the site breaks

**At every supplier, ask one question in writing before you list anything:**

> "Can I use your product photography on my own store, and under what terms?"

Save the reply. Supplier images may only be used in connection with selling that
supplier's products and within their terms. Product photography you do not have
rights to carries US statutory damages from $750 to $150,000 per work.

---

## Step 4 — Wire it back into the shop

For each product you have sourced, fill in `data/products.json`:

```json
"sourcing": {
  "supplier": "jb-jewelry-blvd",
  "supplier_sku": "THEIR-SKU",
  "landed_cost": 7.40,
  "image_source": "supplier",
  "image_credit": "JB Jewelry BLVD, written permission 2026-08-12"
}
```

Set `unit_cost` to the real landed cost too — every margin figure the build
prints is an estimate until you do.

Then:

```bash
python3 tools/sourcing_report.py    # what is sourced, what is still a guess
python3 tools/check_images.py       # confirm every image loads
```

CI fails the build if a product has a checkout URL and no supplier, so it is not
possible to leave something buyable that nobody can ship.

---

## The order, one line each

1. **EIN** — irs.gov, free, 10 min
2. **PayPal Business** + claim paypal.me handle → into config → **shop takes money**
3. **Cash App Business** → $Cashtag into config
4. **Stripe** → payment links → cards, Apple Pay, Google Pay
5. **State sales tax permit** → resale certificate
6. **JB Jewelry BLVD** + **Blanka or SelfNamed** → ask about image rights in writing
7. **Order one of everything to yourself** before selling any of it
