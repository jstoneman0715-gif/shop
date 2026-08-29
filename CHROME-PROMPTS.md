# Prompts for Claude in Chrome

Copy one block at a time. Each is self-contained — Claude in Chrome knows nothing
about this shop, so every prompt restates what it needs.

**Start at Prompt 0 even if you think you have an account.** The earlier version
of this file assumed you were already signed in, which is why it failed.

### What Claude in Chrome can and cannot do

It can navigate, read pages, fill visible form fields, compare listings and
record what it finds. It **cannot** receive your verification email, solve a
CAPTCHA, or know your password. Those moments are marked **YOU DO THIS** in the
prompts, and Claude is told to stop and wait rather than guess.

Never paste a password, card number, SSN or EIN into a prompt. If a page asks
for one, type it yourself.

---

## Prompt 0 — create the CJdropshipping account

Open a browser tab on any page and paste this.

```
I want to create a free account on CJdropshipping to source products for a small
US online shop. Please walk me through it one step at a time.

1. Navigate to cjdropshipping.com and find the Sign Up / Register link
2. Tell me exactly what fields the signup form asks for before I fill anything in
3. I will type my own email and password — do not invent or enter credentials
4. If there is a CAPTCHA or an email verification code, stop and tell me what to
   do, then wait for me to say I have done it
5. After I confirm the account exists, help me find the account settings and tell
   me whether I need to set a shipping destination country (I am in Ohio, USA)

Do not skip ahead. After each step, tell me what you did and what you see on
screen, then wait for me before continuing.
```

---

## Prompt 1 — source ONE product as a test

Do not run the full batch until this works. Paste with CJ open and signed in.

```
I'm sourcing products on CJdropshipping for a US shop. Let's do one product as a
test so I can check your method before you do the rest.

Product: Fridge Organiser Set — six clear stackable BPA-free fridge bins,
mixed sizes, fits standard refrigerator shelves.
My maximum landed cost: $12.15 (product cost + shipping to Ohio, USA).

Steps:
1. Search CJdropshipping for it
2. Filter or sort so you can see which listings ship from a US warehouse. Tell me
   how you did this, because I want to know the filter works
3. Open the two or three best matching listings
4. For each one, tell me: product name, CJ product ID/SKU, product cost, shipping
   cost to Ohio, total landed cost, warehouse location, number of reviews or
   sales if shown, and the listing URL
5. Then recommend one, and say why

Rules:
- US warehouse is a hard requirement. My site promises dispatch in 1-2 days, so a
  China-only listing makes that promise false. If none ship from the US, say
  "NO US STOCK" rather than suggesting a China warehouse
- Prefer more reviews and a US warehouse over the lowest price
- Before you give me your final answer, re-open the listing you recommend and
  confirm the price and warehouse are what you reported. Tell me you did this

If anything blocks you — a login wall, a region selector, a CAPTCHA — stop and
tell me instead of working around it.
```

---

## Prompt 2 — the remaining 15 products

Only after Prompt 1 produced a sensible result.

```
Using the same method as before, source these 15 products on CJdropshipping.
Same rules: US warehouse is a hard requirement, prefer reviews over lowest price,
report "NO US STOCK" rather than substituting a China warehouse, and record cost
plus shipping to Ohio as the landed cost.

Work through them one at a time. After every 5 products, give me a progress
update and wait for me to say continue — I would rather check as we go than get
15 wrong answers at the end.

Before your final table, re-open each recommended listing and confirm the price
and warehouse still match what you recorded. Flag anything that changed.

Format the result as a markdown table with these columns:
product | CJ SKU | product cost | shipping to Ohio | landed cost | warehouse |
listing URL | main image URL | OVER? (yes if landed cost exceeds my maximum)

The list, as "product — description — max landed cost":

1. Everyday Canvas Tote — structured 16oz canvas tote, reinforced base, interior zip pocket — $13.05
2. Travel Jewelry Case — zip case with chain slots and ring rolls, carry-on sized — $9.45
3. Weighted Jump Rope — steel cable, weighted handles, adjustable length — $7.65
4. Resistance Band Set — five fabric (not latex) resistance bands with door anchor — $9.45
5. Aroma Stone Diffuser — passive ceramic stone diffuser, no power or water — $10.80
6. Cloud Slippers — thick EVA recovery slippers, sizes S to XL — $10.35
7. Sunset Projection Lamp — rotating sunset halo lamp, dimmable, USB-C — $9.45
8. Olive Oil Mister — glass oil sprayer, fine mist, anti-clog — $7.20
9. Reusable Pet Hair Remover — self-cleaning roller, no adhesive refills — $6.75
10. Slow Feeder Bowl — maze-bottom dog bowl, non-slip base — $8.55
11. Folding MagSafe Stand — aluminium folding magnetic phone stand — $9.90
12. Braided Charge Cable 3-Pack — braided USB-C cables, 0.3m/1m/2m — $8.10
13. Magnesium Sleep Mist — magnesium chloride pillow and body mist with lavender — $9.90
14. Cryo Recovery Roller — stainless freezer-stored ice roller for face and body — $8.10
15. Acupressure Mat — spiked acupressure mat with neck pillow and carry bag — $15.30
```

---

## Prompt 3 — image rights, in writing

```
On CJdropshipping, find their official policy on whether sellers may use supplier
product images on their own websites.

1. Search their help centre, policy pages and terms of service
2. Quote the exact wording back to me and give me the URL
3. Then help me send a support message asking them to confirm it in writing for
   the specific listings I am using

The message I want to send:

"I am setting up an online store using products sourced through CJdropshipping.
Please confirm in writing that I may use the product images from the listings I
order from on my own website, and tell me any conditions that apply."

Tell me where their support form or live chat is and walk me through sending it.
Do not send anything without showing me the text first.
```

---

## Prompt 4 — Faire, including signing up

Faire is worth it for net-60 terms: stock arrives, you pay 60 days later.

```
I run a small US online retail shop and want to open a retailer account on Faire
to buy wholesale.

Part 1 — the account:
1. Go to faire.com and find the sign-up for RETAILERS, not for brands. Be careful
   here, the two are different and I want the buying side
2. Tell me exactly what the application asks for before I fill anything in,
   including whether it wants a business name, EIN, resale certificate or a
   website
3. I will enter my own details. Stop and wait at anything requiring my email
   verification or a password
4. Tell me clearly: does Faire require a resale certificate or tax ID to approve
   a retailer account, and if so is it required immediately or only at checkout?

Part 2 — once I can browse, search for:
- fridge and pantry organisers
- passive stone or reed diffusers
- ice rollers and facial recovery tools
- slow feeder pet bowls

For each, list up to three brands with: brand name, product, wholesale unit
price, suggested retail price, and the brand's minimum opening order.

Part 3 — confirm for me from Faire's own pages, not from memory:
- the minimum order for a first-time retailer
- whether net-60 payment terms apply to new retail accounts
- what Faire charges a retailer, if anything

Quote the pages you got these from.
```

---

## Prompt 5 — jewelry wholesale

Run only once you have an Ohio vendor's license number and a completed STEC B.

```
I run a US retail shop and want to open a wholesale account with JB Jewelry BLVD.

Part 1:
1. Go to jb-jewelry.com and find the wholesale or dropshipping application
2. List every field and every document the application asks for, before I start
3. Tell me whether they require a resale certificate, and whether they accept an
   Ohio STEC B blanket exemption certificate
4. Do not submit anything — I will fill in my own business details

Part 2 — search their catalogue for these and record product name, SKU, wholesale
price, and critically whether each is GOLD-FILLED or gold-PLATED. I need
gold-filled; plated is not acceptable and I need you to check, not assume:

1. Set of three stacking rings, sizes 5 to 9
2. 4mm flat herringbone chain, 16 inch and 18 inch
3. Small hinged huggie hoop earrings, around 12mm

Part 3: find their policy on sellers using their product photography, quote it,
and give me the URL.
```

---

## Prompt 6 — beauty private label

```
I run a small US online shop selling a niacinamide serum at $28 retail, a lip
mask at $16 and a mineral SPF 50 at $26. I want private-label beauty with no
minimum order quantity.

Compare blanka.com and selfnamed.com. For each, from their own pages:

1. What it costs to start, including any monthly platform or subscription fee
2. Per-unit cost of: a face serum, a lip balm or mask, a mineral SPF
3. Whether they ship from a US warehouse, and typical dispatch time
4. Whether product photography is included and whether I may use it on my store
5. What the signup requires — is it open registration, or an application?

Walk me through creating a free account on whichever you recommend. Stop at
anything needing my email verification or password.

Then give me a straight recommendation with the reason, and tell me the gross
margin I would make at my retail prices using their per-unit costs.
```

---

## What to bring back here

For each product you decide on:

```
slug          fridge-organiser-set
supplier      cjdropshipping
supplier_sku  <their ID>
landed_cost   9.40
image_url     <their photo URL>
```

Slugs are in SOURCING.md. Paste the whole table from Claude in Chrome straight
into the chat — it can be read from there and wired in.

**One thing Claude in Chrome cannot do:** judge whether a product is any good.
Look at the listings it picks before committing money.
