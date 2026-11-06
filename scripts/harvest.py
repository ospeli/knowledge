"""Nightly harvest: fetch new records, dedupe, licence-gate, classify, write the inbox.

Usage: python -m scripts.harvest [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--sources europepmc,openalex,crossref]
Raw candidates are not knowledge. Knowledge enters only as reviewed cards (see docs/CARDS.md).
"""
from __future__ import annotations
import argparse, datetime as dt, json, sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from harvest import crossref, europepmc, openalex  # noqa: E402
from harvest.common import classify, licence_tier  # noqa: E402

SOURCES = {"europepmc": europepmc, "openalex": openalex, "crossref": crossref}
STATE = ROOT / "state" / "state.json"
SEEN = ROOT / "state" / "seen.txt"
INBOX = ROOT / "inbox"


def merge(a, b):
    """Keep the richest fields across sources for the same work."""
    for f in ("doi", "pmid", "pmcid", "openalex", "journal", "url", "year"):
        if not getattr(a, f) and getattr(b, f):
            setattr(a, f, getattr(b, f))
    if (not a.abstract) and b.abstract:
        a.abstract = b.abstract
    if a.licence in ("unknown", "publisher") and b.licence not in ("unknown", "publisher"):
        a.licence = b.licence
    a.is_oa = a.is_oa or b.is_oa
    a.is_preprint = a.is_preprint or b.is_preprint
    return a


def run(since: str, until: str, sources: list[str], records_in=None) -> dict:
    queries = yaml.safe_load((ROOT / "harvest" / "queries.yaml").read_text())["queries"]
    seen = set(SEEN.read_text().split()) if SEEN.exists() else set()
    found, errors = {}, []
    stamp = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    stream = records_in if records_in is not None else (
        r for s in sources for q in queries for r in _safe(SOURCES[s].fetch, q, since, until, errors, s))
    for rec in stream:
        if not rec.title:
            continue
        k = rec.key()
        found[k] = merge(found[k], rec) if k in found else rec
    kept = []
    for k, rec in found.items():
        if k in seen:
            continue
        rec.domains = classify(rec)
        if not rec.domains:
            continue
        rec.tier = licence_tier(rec)
        if rec.tier == "D":
            continue
        if rec.tier == "C":
            rec.abstract = None  # never store publisher text; reviewers follow the link
        rec.retrieved_at = stamp
        kept.append(rec)
        seen.add(k)
    INBOX.mkdir(exist_ok=True)
    out = INBOX / f"{until}.jsonl"
    with out.open("a", encoding="utf-8") as f:
        for rec in kept:
            f.write(rec.to_json() + "\n")
    _summary(out.with_suffix(".md"), kept, since, until, len(found), errors)
    SEEN.parent.mkdir(exist_ok=True)
    SEEN.write_text("\n".join(sorted(seen)) + "\n")
    STATE.write_text(json.dumps({"last_until": until, "updated": stamp}, indent=2) + "\n")
    return {"fetched": len(found), "kept": len(kept), "errors": errors, "file": out.name}


def _safe(fn, q, since, until, errors, name):
    try:
        yield from fn(q, since, until)
    except Exception as e:  # one failing source must not stop the night
        errors.append(f"{name}: {q[:40]}: {e}")


def _summary(path: Path, kept, since, until, fetched, errors):
    by = {}
    for r in kept:
        for d in r.domains:
            by[d] = by.get(d, 0) + 1
    lines = [f"# Inbox {until}", "", f"Window {since} to {until}. Fetched {fetched} unique records; {len(kept)} new operations candidates.", "",
             "| Domain | New |", "|---|---|"] + [f"| {d} | {n} |" for d, n in sorted(by.items(), key=lambda x: -x[1])]
    lines += ["", "## Candidates (tier · domains · title)", ""]
    for r in sorted(kept, key=lambda r: (r.tier, r.domains[0]))[:300]:
        link = f"https://doi.org/{r.doi}" if r.doi else (r.url or "")
        lines.append(f"- **{r.tier}** · {', '.join(r.domains)} · [{r.title}]({link}){' · preprint' if r.is_preprint else ''}")
    if errors:
        lines += ["", "## Source errors", ""] + [f"- {e}" for e in errors[:50]]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    today = dt.date.today()
    last = json.loads(STATE.read_text())["last_until"] if STATE.exists() else (today - dt.timedelta(days=7)).isoformat()
    ap.add_argument("--since", default=last)
    ap.add_argument("--until", default=today.isoformat())
    ap.add_argument("--sources", default="europepmc,openalex,crossref")
    a = ap.parse_args()
    res = run(a.since, a.until, a.sources.split(","))
    print(json.dumps(res, indent=2))
