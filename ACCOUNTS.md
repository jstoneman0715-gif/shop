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

## Ohio specifics

Reviewed for Ohio, August 2026. Fees and forms change — confirm each at the
source before paying anything. Not legal or tax advice.

### What is different here

Ohio calls the sales tax registration a **vendor's license**, and it has **no
standalone resale certificate**. Those two facts change the order of operations,
because suppliers ask for a resale certificate and in Ohio you cannot produce a
valid one until the vendor's license exists.

### Step A — Register the trade name (Form 534A, $39)

"ALL THE RAGE" is not your legal name, so Ohio requires it to be registered as a
trade name before you trade under it.

- **Ohio Secretary of State** → Name Registration, **Form 534A**
- **$39**, valid **five years**, renewable in the six months before it expires
- Governed by Ohio Revised Code Chapter 1329

Do this before opening the PayPal Business account, because that application
asks for the business name and it should match what the state has on file.

### Step B — OHID, then the vendor's license

1. Create an **OHID** account — you cannot register online without one
2. **Ohio Business Gateway** or Ohio TAX eServices → apply for a **regular
   vendor's license** (Form **ST-1** if you would rather post it or take it to
   your county auditor)
3. Fee reported as **$25**, and as **$50 since 9 April 2025** — sources
   disagree, so budget $50 and check the figure on the application screen
4. You need the business name, structure (sole proprietorship) and your EIN

A **regular** vendor's license is the one for a fixed place of business in an
Ohio county, which includes running the shop from home.

The $100,000 / 200-transaction economic nexus threshold you will read about is
for **out-of-state** sellers. It does not apply to you. As an Ohio seller you
need the licence from the first taxable sale, not after a threshold.

### Step C — STEC B, for the suppliers

Ohio issues no separate resale certificate. You claim resale on the
**Sales and Use Tax Blanket Exemption Certificate, form STEC B**, which you fill
in yourself and hand to each supplier.

- Download **STEC B** from tax.ohio.gov
- Reason for exemption: **resale**
- It asks for your **vendor's license number** — hence Step B first
- No expiry, but it is only valid while your vendor's license is active
- Use the blanket version, not STEC U, since you will buy repeatedly

Send a completed STEC B to JB Jewelry BLVD and to Blanka or SelfNamed when you
open those accounts. It is what stops them charging you sales tax on stock you
are going to resell.

### Revised Ohio order

1. **EIN** — irs.gov, free, 10 minutes
2. **Trade name** — Ohio SoS Form 534A, $39
3. **PayPal Business** + paypal.me handle → into config → **shop takes money**
4. **Cash App Business** → $Cashtag into config
5. **OHID** → **Ohio Business Gateway** → **vendor's license** (~$25–50)
6. **STEC B** filled in, ready to send to suppliers
7. **Stripe** → payment links → cards and wallets
8. **JB Jewelry BLVD** + **Blanka or SelfNamed**, STEC B attached
9. **Order one of everything to yourself**

Steps 1–4 are an afternoon and end with the shop able to take money. Steps 5–6
are what let a supplier open a wholesale account for you.

### The sales tax gap in the shop as it stands

Worth saying plainly: **the checkout does not calculate or collect sales tax.**
PayPal.me and Cash App just move an amount — they do not know what was bought or
where it is going. So on an Ohio order today, the tax comes out of your margin
and you still owe it.

Three ways out, cheapest first:

- **Absorb it at first.** At a handful of orders a month, treat the listed price
  as tax-inclusive for Ohio buyers and remit from the proceeds. Simplest, and it
  quietly costs you a few points of margin on in-state sales only.
- **Turn on tax in Stripe.** Stripe Tax calculates and collects per destination
  at checkout. This is the real fix and the reason to prioritise Stripe over
  staying on PayPal links.
- **Register, file, remit** on the schedule the vendor's license assigns you,
  whichever of the above you pick. The licence is what creates the filing
  obligation, not the volume.

Ohio sourcing rules decide which rate applies to an in-state order. Confirm the
current rule with the Department of Taxation rather than guessing — the rate
differs by county.


---

## Opening a supplier account, step by step

There are two routes and they need completely different things. Route A needs no
paperwork and covers most of the shop. Start there.

### Route A — CJdropshipping, today, no documents (16 of 27 products)

CJ is a free account with no application and no resale certificate, because you
are not buying wholesale — you pay per order at their price. That makes it the
only supplier you can open before the Ohio paperwork clears.

Covers home, kitchen, pet, tech, bags, wellness and fitness: **16 products,
$347 of listed value**, well over half the catalogue.

1. **cjdropshipping.com** → Sign Up. Email and password. No business documents.
2. Search for the first product — start with **Fridge Organiser Set**. Use their
   image search if a text search is noisy.
3. **Filter to a US warehouse.** This is not optional: the site promises dispatch
   in 1–2 days, and a China-warehouse listing makes that promise false.
4. On the listing, write down three things:
   - their **product ID / SKU**
   - the **product cost**
   - the **shipping cost to Ohio** — cost plus shipping is your landed cost
5. Save their **product photos**. These show the actual item, unlike the stock
   images currently on the site.
6. Repeat for the other 15. Budget an hour.

**Ask CJ support one question in writing before you list anything:**

> "Can I use your product images on my own store, and under what terms?"

Their policy allows supplier images in connection with selling that supplier's
products, subject to the individual supplier's terms — get it confirmed for the
specific listings you use, and save the reply.

### Route B — wholesale, needs the Ohio paperwork (9 products)

JB Jewelry BLVD (3 jewelry products) and Blanka or SelfNamed (6 beauty and hair)
are real wholesale accounts. They sell at wholesale prices, which is why they
ask you to prove you are a business.

**Have these four things ready before you apply — an application without them
gets rejected or stalls:**

| Document | Where | Note |
| --- | --- | --- |
| EIN | irs.gov, free, 10 min | Not a licence on its own; proves the business is real |
| Trade name registration | Ohio SoS Form 534A, $39 | "ALL THE RAGE" is not your legal name |
| Ohio vendor's license | Ohio Business Gateway, ~$25–50 | Ohio's version of a seller's permit |
| STEC B, completed | tax.ohio.gov, free | Needs the vendor's license number on it |

Then:

1. **jb-jewelry.com** → wholesale / dropshipping application
2. Fill in business name, EIN, and vendor's license number
3. Attach the completed **STEC B** — this is what stops them charging you sales
   tax on stock you intend to resell
4. Same again at **blanka.com** or **selfnamed.com**
5. Ask each the image-rights question in writing, and keep the answer

Approval is usually a day or two, not instant, because a human reviews it.

### What to send back here

For each product sourced, four values:

```
slug             stack-rings-set
supplier         jb-jewelry-blvd
supplier_sku     THEIR-SKU-HERE
landed_cost      7.40          (product + shipping to Ohio)
```

Plus the image URLs or the files. That is everything needed to replace the
estimated costs with real ones and the placeholder photographs with pictures of
the actual product.

### Order of play

Route A today gets 16 products real costs and real photos with no waiting.
Route B runs in parallel while the Ohio paperwork clears, and picks up the
highest-margin nine.

---

## The order, one line each

1. **EIN** — irs.gov, free, 10 min
2. **PayPal Business** + claim paypal.me handle → into config → **shop takes money**
3. **Cash App Business** → $Cashtag into config
4. **Stripe** → payment links → cards, Apple Pay, Google Pay
5. **State sales tax permit** → resale certificate
6. **JB Jewelry BLVD** + **Blanka or SelfNamed** → ask about image rights in writing
7. **Order one of everything to yourself** before selling any of it
