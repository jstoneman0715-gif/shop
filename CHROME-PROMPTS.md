# Prompts for Claude in Chrome

Copy one block at a time into Claude in Chrome. Each is self-contained — that
Claude knows nothing about this shop, so every prompt restates what it needs.

Do them in order. Prompt 1 is the whole of Route A.

**One rule to carry through all of them:** Claude in Chrome can search, read and
record. It cannot judge whether a product is any good. Look at what it brings
back before you commit to anything.

---

## Prompt 1 — source the 16 no-paperwork products

Paste this into Claude in Chrome with cjdropshipping.com open and signed in.

```
I run a small US online shop and I'm sourcing products on CJdropshipping.
I'll give you a list of products with a maximum landed cost for each.

For every product on the list:
1. Search CJdropshipping for it
2. Filter or prefer listings that ship from a US warehouse — this is a hard
   requirement, my site promises dispatch in 1-2 days, so skip any listing that
   only ships from China
3. Pick the listing that best matches the description, favouring higher review
   counts and a US warehouse over the lowest price
4. Record: product name, CJ product ID or SKU, product cost, shipping cost to
   Ohio, total landed cost, the product page URL, and the main image URL

Give me the results as a markdown table with one row per product. If nothing
matches from a US warehouse, write "NO US STOCK" in that row rather than
substituting a China-warehouse listing. If the landed cost is above my maximum,
still record it but flag it "OVER".

Here is the list, as "product — description — max landed cost":

1. Everyday Canvas Tote — structured 16oz canvas tote, reinforced base, interior zip pocket — $13.05
2. Travel Jewelry Case — zip case with chain slots and ring rolls, carry-on sized — $9.45
3. Weighted Jump Rope — steel cable, weighted handles, adjustable length — $7.65
4. Resistance Band Set — five fabric (not latex) booty bands with door anchor — $9.45
5. Aroma Stone Diffuser — passive ceramic stone diffuser, no power or water — $10.80
6. Cloud Slippers — thick EVA recovery slippers, sizes S-XL — $10.35
7. Sunset Projection Lamp — rotating sunset halo lamp, dimmable, USB-C — $9.45
8. Fridge Organiser Set — six clear stackable BPA-free fridge bins — $12.15
9. Olive Oil Mister — glass oil sprayer, fine mist, anti-clog — $7.20
10. Reusable Pet Hair Remover — self-cleaning roller, no adhesive refills — $6.75
11. Slow Feeder Bowl — maze-bottom dog bowl, non-slip base — $8.55
12. Folding MagSafe Stand — aluminium folding magnetic phone stand — $9.90
13. Braided Charge Cable 3-Pack — braided USB-C cables, 0.3m/1m/2m — $8.10
14. Magnesium Sleep Mist — magnesium chloride pillow and body mist with lavender — $9.90
15. Cryo Recovery Roller — stainless freezer-stored ice roller for face and body — $8.10
16. Acupressure Mat — spiked acupressure mat with neck pillow and bag — $15.30
```

---

## Prompt 2 — check the image rights

Same CJ session, after Prompt 1.

```
Open CJdropshipping's support or contact page and help me send this message:

"I'm setting up a store using your products. Can I use the product images from
your listings on my own website, and under what terms? Please confirm in
writing."

Then tell me where their policy on seller use of product images is documented,
and quote the relevant section back to me.
```

---

## Prompt 3 — compare against Faire

Open faire.com. Faire is worth checking because it offers net-60 terms — you get
the stock and pay 60 days later.

```
I'm a US retailer looking at Faire for wholesale. Search Faire for these
categories and tell me what you find:

- fridge and pantry organisers
- passive/stone reed diffusers
- ice rollers and facial recovery tools
- slow feeder pet bowls

For each, list up to three brands with: brand name, the product, wholesale unit
price, the retail price they suggest, and the brand's minimum opening order.

Also confirm for me: what is Faire's minimum order for a first-time retailer,
and does net-60 payment terms apply to new retail accounts?
```

---

## Prompt 4 — jewelry wholesale (needs paperwork first)

Only run this once you have an Ohio vendor's license number and a completed
STEC B form.

```
Open jb-jewelry.com and find their wholesale or dropshipping application.

Tell me exactly what the application asks for, field by field, and what
documents it wants uploaded, before I start filling it in.

Then search their catalogue for these three and record product name, SKU,
wholesale price, and whether it is gold-filled or plated (I need gold-filled,
not plated):

1. Set of three stacking rings, sizes 5-9
2. 4mm flat herringbone chain, 16 and 18 inch
3. Small hinged huggie hoops, around 12mm

Also ask them, or find in their terms: can I use their product photography on my
own store?
```

---

## Prompt 5 — beauty private label (needs paperwork first)

```
Open blanka.com and selfnamed.com. I'm a US shop looking at private-label
beauty with no minimum order quantity.

For each of the two sites tell me:
- what it costs to start, including any monthly platform fee
- the per-unit cost of a face serum, a lip balm or mask, and a mineral SPF
- whether they ship from a US warehouse and typical dispatch time
- whether product photography is provided and whether I may use it on my store
- what documents the signup requires

Then give me a straight recommendation of which of the two suits a shop selling
a niacinamide serum at $28, a lip mask at $16 and an SPF 50 at $26 retail.
```

---

## What to bring back here

For each product you actually decide on, five values:

```
slug          fridge-organiser-set
supplier      cjdropshipping
supplier_sku  <their ID>
landed_cost   9.40
image_url     <their photo URL>
```

The slugs are in SOURCING.md. Paste the table Claude in Chrome gives you
straight into this chat — I can read it and wire it in from there.
