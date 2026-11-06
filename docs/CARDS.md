# Knowledge card format

One finding per card, written as `cards/<domain>/<id>.yaml`. IDs are `kc-YYYY-NNNN`.

```yaml
id: kc-2026-0001
version: 1
status: candidate          # candidate → approved → superseded | deprecated | retracted
title: Criteria-led discharge shortened length of stay       # plain English, under 90 characters
summary: One or two sentences a ward manager would understand.
intervention: Criteria-led discharge
comparator: Consultant-led discharge
source: {doi: 10.xxxx/..., tier: A, licence: cc-by, url: https://doi.org/...}
domains: [A3_inpatient_flow]                                 # from taxonomy.yaml
design: its_uncontrolled                                     # from taxonomy.yaml methods
evidence_level: OE3                                          # OE1–OE5 or G (official guidance)
setting: {country: GB, income: HIC, facility: acute_hospital, beds: 400}
kpis:
  - name: length_of_stay_days
    definition: Mean inpatient days per discharge, medical wards
    effect: {value: -0.5, unit: days, ci: [-0.8, -0.2]}
    evidence: {quote: "exact sentence from the open abstract or text"}
implementation_needs: [discharge criteria agreed, nurse training]
lmic_applicability: uncertain          # yes | partial | uncertain | no, with a reason in notes
notes: Single site; no control group.
review_by: 2031-11-05                   # 5 years; 2 years for guidance
approval: {by: reviewer-github-handle, date: 2026-11-06}     # added at approval
```

## Rules the checker enforces (`scripts/verify_cards.py`)
- **Tier A/B (open) sources:** every number in an effect must appear inside `evidence.quote`, and the quote must appear verbatim in the stored abstract.
- **Tier C (paywalled) sources:** no quotes at all. Numbers need `evidence.checked_by`, the reviewer who read the source.
- **Approved cards** need `approval.by` and `approval.date`.
- **Domains, designs and evidence levels** must come from `taxonomy.yaml`.

## Evidence levels
| Level | Meaning |
|---|---|
| OE1 | Systematic review, meta-analysis, or multi-site RCT |
| OE2 | RCT, controlled interrupted time series, or stepped-wedge trial |
| OE3 | Uncontrolled ITS or controlled before–after study |
| OE4 | Simple before–after study, case study, or validated simulation |
| OE5 | Expert opinion, unvalidated model, or preprint |
| G | Official guidance |

Downgrade one level for high risk of bias, a single site with no comparison, or no confidence interval. Say so in `notes`.
