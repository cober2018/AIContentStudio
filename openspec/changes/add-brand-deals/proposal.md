## Why

The user plans to take brand deals and asked for a module and advice on the workflow (2026-10-21). The agreed flow: enquiry → quote → brief → contract → platform registration → script review → production → final review → publish → results report → payment → review.

## What Changes

- **Rate card** on each account: prices by format, length and platform, plus add-ons (usage rights for ads, exclusivity, extra revision rounds).
- **Deals**: brand, contact, products, budget, deadlines, status along the pipeline; each deal links to one project and its works.
- **Quote** drafted from the rate card; versions kept.
- **Brief intake**: selling points, must-say and must-not-say, required visuals, references; becomes the project brief and the fact boundary (brand claims marked as brand-provided).
- **Contract terms record**: price, payment stages, revision rounds, exclusivity window, ad usage rights and duration; usage rights flow into the work's rights record.
- **Platform registration checklist**: 星图 / 蒲公英 / 花火 / 互选 order number per platform version; publishing without it shows a warning.
- **Brand review rounds**: script and final cut sent as frozen versions; brand feedback recorded per round; counts against contracted rounds.
- **Ad-law check**: deterministic check for banned absolute terms and required "广告/合作" labels before review.
- **Results report** generated from growth data for the agreed day (7 or 15).
- **Payment tracking**: stages, invoice, received.
- **Media kit** page per persona: best work and audience data from growth analysis, for brands.

## Capabilities

### New Capabilities

- `brand-deals`: rate cards, deal pipeline, brand review rounds, ad-law checks, reports and payment tracking.

## Impact

- New tables: rate card, deal, deal event, review round, payment; migration.
- Reuses projects, briefs, fact boundary, candidates, review and growth reports.
- Web: 商单 area in navigation once built; media kit page.
