# Ospeli knowledge

The living knowledge base behind [Ospeli](https://ospeli.com), an open, offline-first healthcare operations platform.

It gathers new research on how hospitals and health systems are run: patient flow, theatres, diagnostics, supply chain, engineering, workforce, quality, finance and preparedness. It turns findings into small, cited, human-approved **knowledge cards**, and publishes them nightly as a single SQLite file that works offline on a hospital server.

## How it works
1. **Harvest (nightly, GitHub Actions).** New records from Europe PMC, OpenAlex and Crossref are deduplicated, checked against [licences.yaml](licences.yaml) and classified against [taxonomy.yaml](taxonomy.yaml) (28 operational domains). Results land in `inbox/`. Publisher text is never stored for paywalled work.
2. **Extract.** Candidates become knowledge cards (`cards/`). The format is in [docs/CARDS.md](docs/CARDS.md). Every number is tied to the sentence it came from.
3. **Review.** A named reviewer approves each card in a pull request. See [docs/REVIEWING.md](docs/REVIEWING.md). Merging is the approval, and git history is the audit trail.
4. **Build.** Approved cards are built into `ospeli-kb-core.sqlite` (open-licence) and `ospeli-kb-community.sqlite` (adds non-commercial material). They are published as the `kb-latest` release with checksums.

## Rules
- Operations knowledge only. No clinical decision content.
- No patient data, ever. This repo holds public literature only.
- Licences are respected (tiers A–D in `licences.yaml`). NICE, Cochrane full text, IHI and Model Hospital content is not ingested without permission.

## Run locally
```
pip install -r requirements.txt
python -m pytest -q tests
python scripts/harvest.py --since 2026-11-01   # needs internet
python scripts/verify_cards.py && python scripts/build_kb.py
python scripts/search.py "discharge before noon"
```
