#!/usr/bin/env python3
"""The merchandising bot: re-rank the shop for what is likely to sell now.

Runs on a schedule. For every product it computes a score from four signals and
rewrites the catalogue so the storefront leads with what should sell this month:

    demand      how much pull the product and its category have (0-1)
    season      whether this month is one of its peak months
    margin      contribution per unit, normalised across the catalogue
    price fit   proximity to the $15-30 band that converts best

Then it sets `featured` on the top items, promotes the best seasonal item into a
badge, and writes a dated report so a human can see why the shop changed.

It never invents social proof. Stock counts and reviews are only ever written by
real fulfilment and real customers — this bot does not touch those fields.

Usage:
    python3 tools/update_catalogue.py              # apply, for the current month
    python3 tools/update_catalogue.py --dry-run    # show the ranking, change nothing
    python3 tools/update_catalogue.py --month 12   # plan ahead for December
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOGUE = os.path.join(ROOT, "data", "products.json")
REPORT = os.path.join(ROOT, "data", "merchandising-report.md")

# How many products carry a "featured" flag on the storefront. Enough to fill a
# row on desktop without turning the whole shop into a highlight reel.
FEATURED_COUNT = 6

# Weights sum to 1. Demand dominates because category pull is the strongest
# single predictor; season is next because it decides *when* to surface a thing.
WEIGHTS = {"demand": 0.40, "season": 0.30, "margin": 0.20, "price_fit": 0.10}

# The converting band from the 2026 marketplace data.
BAND_LOW, BAND_HIGH = 15.0, 30.0

# Badges the bot is allowed to set. Anything else in the file is a human's
# decision and is left alone.
BOT_BADGES = {"Peak season", "Best margin", "Trending now", "Save"}


def load() -> dict:
    with open(CATALOGUE, encoding="utf-8") as fh:
        return json.load(fh)


def margin(product: dict) -> float:
    price = float(product.get("price") or 0)
    if price <= 0:
        return 0.0
    return (price - float(product.get("unit_cost") or 0)) / price


def contribution(product: dict) -> float:
    """Cash per unit, which is what actually pays the bills — not margin percent."""
    return float(product.get("price") or 0) - float(product.get("unit_cost") or 0)


def season_score(product: dict, month: int) -> float:
    """1.0 in a peak month, 0.5 in the month either side of one, else 0.2."""
    peaks = product.get("peak_months") or []
    if not peaks:
        return 0.5  # no stated seasonality: neither helped nor punished
    if month in peaks:
        return 1.0
    adjacent = {((m - 2) % 12) + 1 for m in peaks} | {(m % 12) + 1 for m in peaks}
    return 0.6 if month in adjacent else 0.2


def price_fit(product: dict) -> float:
    """1.0 inside the converting band, tapering off outside it."""
    price = float(product.get("price") or 0)
    if BAND_LOW <= price <= BAND_HIGH:
        return 1.0
    distance = BAND_LOW - price if price < BAND_LOW else price - BAND_HIGH
    return max(0.0, 1.0 - distance / 30.0)


def score_all(products: list[dict], month: int) -> list[tuple[float, dict, dict]]:
    contributions = [contribution(p) for p in products] or [0.0]
    top = max(contributions) or 1.0

    scored = []
    for product in products:
        parts = {
            "demand": float(product.get("demand_weight") or 0.5),
            "season": season_score(product, month),
            "margin": max(0.0, contribution(product) / top),
            "price_fit": price_fit(product),
        }
        total = sum(WEIGHTS[key] * value for key, value in parts.items())
        scored.append((round(total, 4), product, parts))

    scored.sort(key=lambda row: (-row[0], row[1]["slug"]))
    return scored


def apply(doc: dict, scored: list[tuple[float, dict, dict]], month: int) -> list[str]:
    """Reorder, set featured flags, refresh only bot-owned badges."""
    changes: list[str] = []
    ranked = [product for _, product, _ in scored]

    if [p["slug"] for p in doc["products"]] != [p["slug"] for p in ranked]:
        changes.append("reordered the catalogue by score")
    doc["products"] = ranked

    for index, product in enumerate(ranked):
        should_feature = index < FEATURED_COUNT
        if bool(product.get("featured")) != should_feature:
            changes.append(
                f"{'featured' if should_feature else 'unfeatured'} {product['slug']}"
            )
        product["featured"] = should_feature

    # One seasonal call-out, on the highest-scoring product that actually peaks
    # this month. Existing human-written badges are never overwritten.
    #
    # Compare against the badges as they were before this pass, so a run that
    # lands on the same product reports nothing. Without this the bot commits a
    # "change" on every scheduled run forever.
    before = {product["slug"]: product.get("badge") for product in ranked}

    for product in ranked:
        if product.get("badge") in BOT_BADGES:
            product["badge"] = None

    for product in ranked:
        if month in (product.get("peak_months") or []) and not product.get("badge"):
            product["badge"] = "Peak season"
            break

    for product in ranked:
        was, now = before[product["slug"]], product.get("badge")
        if was == now:
            continue
        if now:
            changes.append(f"badged {product['slug']} as {now.lower()}")
        else:
            changes.append(f"cleared the {was.lower()} badge on {product['slug']}")

    return changes


def write_report(scored: list[tuple[float, dict, dict]], month: int, changes: list[str]) -> None:
    month_name = dt.date(2000, month, 1).strftime("%B")
    lines = [
        f"# Merchandising report — {month_name}",
        "",
        f"Generated {dt.date.today().isoformat()} by `tools/update_catalogue.py`.",
        "",
        "Score = "
        + " + ".join(f"{weight:g}×{name}" for name, weight in WEIGHTS.items())
        + ".",
        "",
        "| # | Product | Score | Demand | Season | Margin | Price fit | Unit profit |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for index, (total, product, parts) in enumerate(scored, start=1):
        lines.append(
            f"| {index} | {product['name']} | {total:.3f} | {parts['demand']:.2f} | "
            f"{parts['season']:.2f} | {parts['margin']:.2f} | {parts['price_fit']:.2f} | "
            f"${contribution(product):.2f} |"
        )

    lines += ["", "## Changes applied", ""]
    lines += [f"- {change}" for change in changes] or ["- none; the shop was already optimal"]
    lines += [
        "",
        "## What this bot will not do",
        "",
        "- invent ratings, review counts, sold counts or viewer counts",
        "- write stock numbers it has not been given by real fulfilment",
        "- start a countdown that does not correspond to a real deadline",
        "",
        "Those lift conversion in the short term and cost the customer twice.",
        "",
    ]
    with open(REPORT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--month", type=int, default=dt.date.today().month, choices=range(1, 13))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    doc = load()
    scored = score_all(doc["products"], args.month)

    print(f"Ranking {len(scored)} products for month {args.month}:")
    for index, (total, product, parts) in enumerate(scored[:10], start=1):
        print(
            f"  {index:2}. {total:.3f}  {product['name'][:34]:<34} "
            f"season={parts['season']:.1f} profit=${contribution(product):.2f}"
        )

    if args.dry_run:
        print("\nDry run — nothing written.")
        return 0

    changes = apply(doc, scored, args.month)
    with open(CATALOGUE, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    write_report(scored, args.month, changes)

    print(f"\n{len(changes)} change(s) applied. Report: data/merchandising-report.md")
    for change in changes[:12]:
        print(f"  - {change}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
