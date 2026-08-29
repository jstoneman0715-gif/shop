# Sourcing worksheet

Every product in the shop, what it sells for, and the most you can pay for it
and still hold a 55% margin. **27 products, $658 of listed value.**

The "max landed cost" column is product cost **plus shipping to Ohio**. If a
supplier listing comes in above it, either the price on the site goes up or the
product comes off — do not quietly accept a thin margin, because shipping and
returns eat the rest.

The `unit_cost` values currently in the catalogue are **estimates I made up when
building it**. Every one of them needs replacing with a real number.

---

## Route A — no paperwork, source today (16 products)

CJdropshipping or Faire. Free account, no resale certificate needed for CJ.

| # | Product | Category | Sells for | Max landed cost | Variants |
| --- | --- | --- | --- | --- | --- |
| 1 | **Everyday Canvas Tote** | bags | $29 | **$13.05** | — |
| 2 | **Travel Jewelry Case** | bags | $21 | **$9.45** | — |
| 3 | **Weighted Jump Rope** | fitness | $17 | **$7.65** | — |
| 4 | **Resistance Band Set** | fitness | $21 | **$9.45** | — |
| 5 | **Aroma Stone Diffuser** | home | $24 | **$10.80** | — |
| 6 | **Cloud Slippers** | home | $23 | **$10.35** | S, M, L, XL |
| 7 | **Sunset Projection Lamp** | home | $21 | **$9.45** | — |
| 8 | **Fridge Organiser Set** | kitchen | $27 | **$12.15** | — |
| 9 | **Olive Oil Mister** | kitchen | $16 | **$7.20** | — |
| 10 | **Reusable Pet Hair Remover** | pet | $15 | **$6.75** | — |
| 11 | **Slow Feeder Bowl** | pet | $19 | **$8.55** | — |
| 12 | **Braided Charge Cable 3-Pack** | tech | $18 | **$8.10** | — |
| 13 | **Folding MagSafe Stand** | tech | $22 | **$9.90** | — |
| 14 | **Acupressure Mat & Pillow** | wellness | $34 | **$15.30** | — |
| 15 | **Magnesium Sleep Mist** | wellness | $22 | **$9.90** | — |
| 16 | **Cryo Recovery Roller** | wellness | $18 | **$8.10** | — |

## Route B — needs the Ohio paperwork (11 products)

JB Jewelry BLVD for jewelry; Blanka or SelfNamed for beauty, skincare and hair.
Bundles are made from products in the other rows, so they get sourced last.

| # | Product | Category | Sells for | Max landed cost | Variants |
| --- | --- | --- | --- | --- | --- |
| 1 | **Lip Glaze Trio** | beauty | $24 | **$10.80** | — |
| 2 | **The Everyday Stack** | bundles | $49 | **$22.05** | Ring size 5, Ring size 6, Ring size 7, Ring size 8, Ring size 9 |
| 3 | **The Glow Starter** | bundles | $59 | **$26.55** | — |
| 4 | **Heatless Curl Set** | hair | $19 | **$8.55** | — |
| 5 | **Scalp Detox Massager** | hair | $14 | **$6.30** | — |
| 6 | **Herringbone Chain** | jewelry | $32 | **$14.40** | 16 inch, 18 inch |
| 7 | **Huggie Hoops** | jewelry | $18 | **$8.10** | — |
| 8 | **Everyday Stack Rings** | jewelry | $26 | **$11.70** | 5, 6, 7, 8, 9 |
| 9 | **Glass Skin Serum** | skincare | $28 | **$12.60** | — |
| 10 | **Mineral SPF 50 Fluid** | skincare | $26 | **$11.70** | — |
| 11 | **Overnight Peptide Lip Mask** | skincare | $16 | **$7.20** | — |

---

## What to record for each

```
slug          <from the list above>
supplier      cjdropshipping | faire | jb-jewelry-blvd | blanka | selfnamed
supplier_sku  <their product ID>
landed_cost   <product cost + shipping to Ohio>
image_url     <their product photo>
```

Anything at or under the max landed cost is fine. Anything above it needs a
decision before it goes live.
