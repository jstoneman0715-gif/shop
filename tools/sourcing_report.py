#!/usr/bin/env python3
"""Report what is actually sourced, and what is still a guess.

A shop can look finished long before it can ship anything. Two things are easy
to forget once the site looks right:

  * unit_cost is an estimate until a real supplier quotes a landed cost, so
    every margin figure on the build is a guess
  * the photograph on a product card is a stock image of something similar,
    not the item a customer receives

Both are fine while building and both are a problem the moment money changes
hands, so this prints the gap and can fail a build that claims to be ready.

    python3 tools/sourcing_report.py            # print the gap
    python3 tools/sourcing_report.py --strict   # non-zero exit if anything is sellable but unsourced

A product counts as sellable when it has a checkout URL, because that is the
point at which a stranger can pay for it.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(name: str) -> dict:
    with open(os.path.join(ROOT, "data", name), encoding="utf-8") as fh:
        return json.load(fh)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    catalogue = load("products.json")
    suppliers = load("suppliers.json")
    known = {s["id"] for s in suppliers["suppliers"]}
    products = catalogue["products"]

    sourced, unsourced, placeholder, sellable_unsourced, bad_ref = [], [], [], [], []

    for product in products:
        s = product.get("sourcing") or {}
        supplier = (s.get("supplier") or "").strip()
        sellable = bool((product.get("checkout_url") or "").strip())

        if supplier:
            sourced.append(product)
            if supplier not in known:
                bad_ref.append((product["slug"], supplier))
        else:
            unsourced.append(product)
            if sellable:
                sellable_unsourced.append(product)

        if s.get("image_source") in ("stock-placeholder", "none"):
            placeholder.append(product)

    total = len(products)
    print(f"Catalogue: {total} products")
    print(f"  sourced from a named supplier : {len(sourced)}")
    print(f"  not yet sourced               : {len(unsourced)}")
    print(f"  showing a placeholder image   : {len(placeholder)}")
    print(f"  real landed cost recorded     : {sum(1 for p in products if (p.get('sourcing') or {}).get('landed_cost'))}")

    if unsourced:
        print("\nSuggested supplier per unsourced product:")
        for product in unsourced[:40]:
            candidates = (product.get("sourcing") or {}).get("candidates") or []
            first = candidates[0] if candidates else "— none mapped for this category"
            print(f"  {product['slug']:<26} {product['category']:<10} -> {first}")

    if placeholder:
        print(f"\n{len(placeholder)} products show a photograph of something that is not the product.")
        print("That is fine while building and a refund request once someone pays for it.")

    problems = False
    for slug, supplier in bad_ref:
        print(f"\nERROR {slug}: sourcing.supplier '{supplier}' is not in suppliers.json", file=sys.stderr)
        problems = True
    for product in sellable_unsourced:
        print(f"\nERROR {product['slug']}: has a checkout URL but no supplier — it can be bought "
              f"and not fulfilled.", file=sys.stderr)
        problems = True

    if args.strict and problems:
        return 1
    if not problems:
        print("\nNothing is sellable-but-unfulfillable, and every supplier reference resolves.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
