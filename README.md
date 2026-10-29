# ImportYeti scraper in Python: US import records, bills of lading, importers and their suppliers

Get US customs import data (bills of lading) from ImportYeti as JSON or CSV with a few lines of Python: find **US importers** of a product and the **overseas suppliers** that ship it, with total sea shipments, shipments in the last 12 months, first and last shipment, top suppliers or top US customers, HS codes, origin countries, ocean carriers and trade lanes (ports). Useful for B2B lead lists, supplier sourcing and competitor supply-chain research.

> Disclosure: I built this actor; it's a paid tool on Apify ([rel8ble/importyeti-scraper](https://apify.com/rel8ble/importyeti-scraper)), **$0.75 per 1,000 results, no start fee**. Apify's free plan credit covers small runs.

## Quick start

```bash
pip install -r requirements.txt
export APIFY_TOKEN=<YOUR_APIFY_TOKEN>   # console.apify.com/settings/integrations
python example.py
```

`example.py` searches 2 products, writes `importyeti_records.csv` (one row per importer or supplier, with its top product, biggest trade partner and main port lane), counts suppliers by country, and prints two lists: overseas suppliers that shipped to the US in the last 12 months (with their biggest US customer as a reference), and US importers still importing (with their main supplier).

### Minimal call

```python
from apify_client import ApifyClient

client = ApifyClient("<YOUR_APIFY_TOKEN>")
run = client.actor("rel8ble/importyeti-scraper").call(run_input={
    "queries": ["solar panels"],
    "entityType": "company",      # US importers only
    "minShipments": 10,
    "maxItems": 100,
})
for row in client.dataset(run["defaultDatasetId"]).iterate_items():
    top = (row.get("topSuppliers") or [{}])[0]
    print(row["name"], row["shipments12m"], row["lastShipment"], top.get("name"))
```

Already have a company in mind? Pass its ImportYeti page instead of a search:

```python
run = client.actor("rel8ble/importyeti-scraper").call(run_input={
    "startUrls": ["https://www.importyeti.com/company/lululemon-usa"],
})
```

### Node.js

```js
import { ApifyClient } from 'apify-client';
const client = new ApifyClient({ token: '<YOUR_APIFY_TOKEN>' });
const run = await client.actor('rel8ble/importyeti-scraper').call({
  queries: ['lithium batteries'], entityType: 'supplier', countries: ['CN', 'VN'],
});
const { items } = await client.dataset(run.defaultDatasetId).listItems();
console.log(items.length, items[0]);
```

## Input

| Field | Example | Notes |
|---|---|---|
| `queries` | `["yoga mats", "costco wholesale"]` | products, company names or brands; one search per line |
| `startUrls` | `["https://www.importyeti.com/company/lululemon-usa"]` | company or supplier pages; one full row each, no search |
| `entityType` | `"company"` | `all` (default), `company` = US importers, `supplier` = overseas suppliers |
| `includeDetails` | `true` | default; adds top suppliers/customers, HS codes, lanes, carriers, shipments per month. `false` = search rows only, about 10x faster |
| `minShipments` | `10` | drop one-off importers |
| `activeSinceYear` | `"2025"` | keep only companies with a shipment in that year or later |
| `countries` | `["IN", "VN"]` | 2-letter country codes |
| `maxItemsPerQuery` / `maxItems` | `50` / `1000` | caps |

## Real output (20-result sample run for "yoga mats", 21 Oct 2026, ImportYeti data updated 19 Oct 2026)

One supplier row, trimmed to the main fields (lists cut to the first entries):

```json
{
  "name": "Mats N More",
  "type": "supplier",
  "url": "https://www.importyeti.com/supplier/mats-n-more",
  "country": "India",
  "website": "matsnmore.in",
  "totalShipments": 428,
  "shipments12m": 91,
  "firstShipment": "2015-10-05",
  "lastShipment": "2026-10-10",
  "partnerCount": 26,
  "topProducts": [
    { "hsChapter": "57", "description": "Carpets", "shipments": 259 }
  ],
  "topCustomers": [
    { "name": "Home & More", "countryCode": "US", "shipments": 161,
      "hsCodes": ["5703.90", "5305.00"],
      "url": "https://www.importyeti.com/company/home-more" },
    { "name": "Logo Brands", "countryCode": "US", "shipments": 62,
      "hsCodes": ["5305.00", "5703.90"],
      "url": "https://www.importyeti.com/company/logo-brands" }
  ],
  "originCountries": [
    { "country": "India", "shipments": 362 },
    { "country": "Sri Lanka", "shipments": 35 }
  ],
  "tradeLanes": [
    { "loadingPort": "Colombo Harbor", "unloadingPort": "Savannah, Ga.", "shipments": 132 }
  ],
  "carriers": [ { "name": "Expeditors International", "shipments": 90 } ],
  "databaseUpdated": "2026-10-19"
}
```

US importer rows carry the same fields with `topSuppliers` instead of `topCustomers`. The full record also has HS code breakdowns, other addresses and names, bill and container types, and shipments per year and month.

That sample had 18 overseas suppliers (8 in India) and 2 US importers. `example.py`'s active-supplier list on it kept 10 suppliers with US shipments in the last 12 months; the top 5:

| supplier | country | shipments, last 12 months | last shipment | biggest US customer (shipments) |
|---|---|---|---|---|
| Travancore Mats And Matting | IN | 206 | 2026-10-15 | Ikea Supply (1,110) |
| Mats N More | IN | 91 | 2026-10-10 | Home & More (161) |
| Chandra Mats | IN | 53 | 2026-04-08 | Wal Mart (90) |
| Ara Mats International | IN | 16 | 2026-10-12 | Rubber Cal (153) |
| Mats Four | IN | 13 | 2026-09-21 | Direct Home Textiles Group (21) |

## Pricing and limits

- $0.75 per 1,000 results, no start fee and no charge per search; failed requests are not charged.
- Sea freight only: ImportYeti indexes US ocean bills of lading. Air freight, trucking and non-US trade are not in the data.
- The search is ImportYeti's own and matches company names and product descriptions: the "yoga mats" sample also returned "Yoga Electronics" and "Yangjiang Yoga Kitchenware". Use precise product words, several synonyms and `minShipments` to clean lists.
- No contact details: phone numbers, e-mails and people's names are never collected.
- ImportYeti rate-limits per IP; a run of 1,000 full records takes roughly 10-15 minutes at the default settings.

## Related

- [alibaba-product-scraper-python](https://github.com/Rel8ble/alibaba-product-scraper-python): Alibaba products, prices, MOQ and suppliers
- [global-sources-scraper-python](https://github.com/Rel8ble/global-sources-scraper-python): Global Sources products and verified factories
- [website-contact-scraper-python](https://github.com/Rel8ble/website-contact-scraper-python): emails and socials from the importer websites you collect

MIT licensed.
