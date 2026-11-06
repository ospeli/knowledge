# Card-extraction playbook (for Claude sessions and volunteers)

You are turning `inbox/*.jsonl` candidates into knowledge cards for Ospeli, a healthcare operations platform. Follow docs/CARDS.md exactly.

1. Pick the newest inbox file. Work only on records not already carded (search `cards/` for the DOI).
2. Prioritise:
   - tier A records (open abstract stored)
   - domains A2, A3, A4, B1, B2, B4 and C1 first
   - LMIC settings
   - higher designs (reviews, trials, controlled time series)
3. Make a card only when the record reports an operational intervention or a measured operational relationship with a KPI. Skip commentary, protocols with no results, and clinical treatment studies.
4. **Tier A/B:** copy the exact sentence holding each number into `evidence.quote`. Never round, never infer a confidence interval, never invent a number.
5. **Tier C (no stored abstract):** read the abstract at the DOI link. Write the finding in your own words, with no quotes. Leave `checked_by` empty, because a human reviewer fills it.
6. Set `status: candidate`. Never set `approved`; only a named human approves.
7. Run `python scripts/verify_cards.py` until it passes. Then open a pull request titled `Cards YYYY-MM-DD (N)` with the label `cards`. List the cards and anything uncertain.
8. **Hard rules:**
   - Operations only, no clinical advice.
   - No patient or staff identifiers.
   - Never ingest tier D sources (NICE, Cochrane full text, IHI, Model Hospital).
   - Aim for about 10–25 good cards a session. Quality over volume.
