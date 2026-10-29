"""ImportYeti US import records -> CSV + a supplier sourcing shortlist.

pip install -r requirements.txt
APIFY_TOKEN=<YOUR_APIFY_TOKEN> python example.py
"""
import csv
import os
import sys

from apify_client import ApifyClient

TOKEN = os.environ.get("APIFY_TOKEN", "<YOUR_APIFY_TOKEN>")
ACTOR = "rel8ble/importyeti-scraper"

run_input = {
    "queries": ["yoga mats", "door mats"],
    "entityType": "all",          # "company" = US importers, "supplier" = overseas suppliers
    "includeDetails": True,       # top suppliers / customers, HS codes, lanes, carriers
    "minShipments": 0,
    "maxItemsPerQuery": 50,
    "maxItems": 200,
}

FIELDS = ["type", "name", "countryCode", "city", "region", "website",
          "totalShipments", "shipments12m", "firstShipment", "lastShipment",
          "partnerCount", "topProduct", "topPartner", "topPartnerShipments",
          "mainLane", "sourceQuery", "url"]


def partners(row):
    """Top suppliers for a US importer, top US customers for a supplier."""
    key = "topCustomers" if row.get("type") == "supplier" else "topSuppliers"
    return [p for p in (row.get(key) or [])
            if p.get("name") and "missing in source" not in p["name"].lower()]


def flatten(row):
    top = partners(row)
    lanes = row.get("tradeLanes") or []
    products = row.get("topProducts") or []
    return {
        **row,
        "topProduct": products[0]["description"] if products else "",
        "topPartner": top[0]["name"] if top else "",
        "topPartnerShipments": top[0].get("shipments") if top else "",
        "mainLane": (f"{lanes[0].get('loadingPort')} -> {lanes[0].get('unloadingPort')}"
                     if lanes else ""),
    }


def summarize(rows):
    with open("importyeti_records.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, extrasaction="ignore")
        w.writeheader()
        w.writerows(flatten(r) for r in rows)

    importers = [r for r in rows if r.get("type") == "company"]
    suppliers = [r for r in rows if r.get("type") == "supplier"]
    print(f"{len(rows)} records -> importyeti_records.csv "
          f"({len(importers)} US importers, {len(suppliers)} overseas suppliers)")

    countries = {}
    for r in suppliers:
        countries[r.get("countryCode") or "?"] = countries.get(r.get("countryCode") or "?", 0) + 1
    print("suppliers by country:",
          ", ".join(f"{k} {v}" for k, v in sorted(countries.items(), key=lambda kv: -kv[1])))

    # Sourcing shortlist: suppliers that shipped to the US in the last 12 months,
    # busiest first, with their biggest US customer as a reference.
    active = sorted((r for r in suppliers if (r.get("shipments12m") or 0) > 0),
                    key=lambda r: -(r.get("shipments12m") or 0))
    print(f"\nactive suppliers (shipped to the US in the last 12 months): {len(active)}")
    for r in active[:15]:
        top = partners(r)
        ref = f"{top[0]['name']} ({top[0].get('shipments')})" if top else "-"
        print(f"  {r['name']:<32} {r.get('countryCode') or '':<3} "
              f"{r.get('shipments12m'):>4} in 12m  last {r.get('lastShipment')}  top US customer: {ref}")

    # Lead list: US importers still importing, with who they buy from.
    live = sorted((r for r in importers if (r.get("shipments12m") or 0) > 0),
                  key=lambda r: -(r.get("shipments12m") or 0))
    print(f"\nUS importers with shipments in the last 12 months: {len(live)}")
    for r in live[:15]:
        top = partners(r)
        src = f"{top[0]['name']} ({top[0].get('countryCode')})" if top else "-"
        print(f"  {r['name']:<32} {r.get('shipments12m'):>4} in 12m  main supplier: {src}")


def main():
    if TOKEN.startswith("<"):
        sys.exit("Set APIFY_TOKEN first (console.apify.com/settings/integrations).")
    client = ApifyClient(TOKEN)
    run = client.actor(ACTOR).call(run_input=run_input)
    summarize(list(client.dataset(run["defaultDatasetId"]).iterate_items()))


if __name__ == "__main__":
    main()
