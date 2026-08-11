#!/usr/bin/env python3
"""Tests for the merchandising bot's scoring. Run: python3 tools/test_catalogue.py"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from update_catalogue import (BAND_HIGH, BAND_LOW, WEIGHTS, apply, contribution,
                              margin, price_fit, score_all, season_score)

fails = []
def check(label, got, want):
    if got != want: fails.append(f"{label}: got {got!r}, want {want!r}")
def near(label, got, want, tol=1e-6):
    if abs(got - want) > tol: fails.append(f"{label}: got {got!r}, want ~{want!r}")

check("weights sum to 1", round(sum(WEIGHTS.values()), 6), 1.0)

# --- margin and contribution ---
near("margin", margin({"price": 20, "unit_cost": 5}), 0.75)
check("margin of a free item is 0", margin({"price": 0, "unit_cost": 0}), 0.0)
near("contribution", contribution({"price": 20, "unit_cost": 5}), 15.0)

# --- seasonality ---
peak = {"peak_months": [11, 12]}
check("peak month", season_score(peak, 12), 1.0)
check("month before a peak", season_score(peak, 10), 0.6)
check("month after a peak", season_score(peak, 1), 0.6)   # December wraps to January
check("off season", season_score(peak, 6), 0.2)
check("no stated season is neutral", season_score({"peak_months": []}, 6), 0.5)
check("january peak wraps back to december", season_score({"peak_months": [1]}, 12), 0.6)

# --- price band ---
check("inside band low edge", price_fit({"price": BAND_LOW}), 1.0)
check("inside band high edge", price_fit({"price": BAND_HIGH}), 1.0)
check("mid band", price_fit({"price": 22}), 1.0)
near("just above band", price_fit({"price": 45}), 0.5)
near("just below band", price_fit({"price": 5}), 1 - 10 / 30)
check("far outside band floors at 0", price_fit({"price": 500}), 0.0)

# --- ranking ---
products = [
    {"slug": "a", "name": "A", "price": 20, "unit_cost": 5, "demand_weight": 0.9, "peak_months": [6]},
    {"slug": "b", "name": "B", "price": 20, "unit_cost": 5, "demand_weight": 0.2, "peak_months": [6]},
    {"slug": "c", "name": "C", "price": 20, "unit_cost": 5, "demand_weight": 0.9, "peak_months": [1]},
]
june = score_all(products, 6)
check("higher demand ranks first", [p["slug"] for _, p, _ in june], ["a", "c", "b"])
january = score_all(products, 1)
check("season reorders by month", january[0][1]["slug"], "c")
check("scores are bounded", all(0 <= s <= 1 for s, _, _ in june), True)

# --- applying results ---
doc = {"products": [dict(p) for p in products]}
scored = score_all(doc["products"], 6)
changes = apply(doc, scored, 6)
check("catalogue reordered in place", [p["slug"] for p in doc["products"]], ["a", "c", "b"])
check("something was reported", len(changes) > 0, True)
check("seasonal badge set once",
      sum(1 for p in doc["products"] if p.get("badge") == "Peak season"), 1)

# A human-written badge must survive a bot run.
doc2 = {"products": [dict(p) for p in products]}
doc2["products"][0]["badge"] = "New drop"
apply(doc2, score_all(doc2["products"], 6), 6)
check("human badge preserved",
      next(p for p in doc2["products"] if p["slug"] == "a")["badge"], "New drop")

# Running twice must not keep changing things.
doc3 = {"products": [dict(p) for p in products]}
apply(doc3, score_all(doc3["products"], 6), 6)
second = apply(doc3, score_all(doc3["products"], 6), 6)
check("second run is a no-op", second, [])

# The bot must never touch trust-signal fields.
doc4 = {"products": [dict(p, stock=None, reviews=[]) for p in products]}
apply(doc4, score_all(doc4["products"], 6), 6)
check("stock untouched", all(p["stock"] is None for p in doc4["products"]), True)
check("reviews untouched", all(p["reviews"] == [] for p in doc4["products"]), True)

if fails:
    print(f"{len(fails)} test(s) failed:", file=sys.stderr)
    for f in fails: print("  - " + f, file=sys.stderr)
    raise SystemExit(1)
print("All merchandising bot tests passed.")
