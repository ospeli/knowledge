"""Check every knowledge card before it can be merged. Exit 1 on any problem.

Rules (docs/CARDS.md):
- required fields and allowed values
- every number in an effect must appear in its evidence quote (tier A/B), or the card must be tier C with a named reviewer
- quotes from tier A/B sources must appear verbatim in the stored abstract when we have it
- approved cards need a named approver and an approval date
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TAX = yaml.safe_load((ROOT / "taxonomy.yaml").read_text())
DOMAINS, METHODS, LEVELS = set(TAX["domains"]), set(TAX["methods"]), set(TAX["evidence_levels"])
STATUSES = {"candidate", "approved", "superseded", "deprecated", "retracted"}
REQUIRED = ["id", "version", "status", "title", "summary", "source", "domains", "design", "evidence_level", "setting", "review_by"]


def load_abstracts() -> dict:
    out = {}
    for f in (ROOT / "inbox").glob("*.jsonl"):
        for line in f.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if r.get("abstract") and r.get("doi"):
                out[r["doi"].lower()] = r["abstract"]
    return out


def numbers(x) -> list[str]:
    return re.findall(r"-?\d+(?:\.\d+)?", str(x))


def check(path: Path, abstracts: dict) -> list[str]:
    errs = []
    try:
        c = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"{path.name}: not valid YAML ({e})"]
    for f in REQUIRED:
        if c.get(f) in (None, "", []):
            errs.append(f"missing {f}")
    if c.get("id") and path.stem != c["id"]:
        errs.append("file name must equal id")
    if c.get("status") not in STATUSES:
        errs.append(f"status must be one of {sorted(STATUSES)}")
    bad = set(c.get("domains") or []) - DOMAINS
    if bad:
        errs.append(f"unknown domains {sorted(bad)}")
    if c.get("design") not in METHODS:
        errs.append(f"design must be one of taxonomy methods")
    if c.get("evidence_level") not in LEVELS:
        errs.append("evidence_level must be OE1-OE5 or G")
    src = c.get("source") or {}
    tier = src.get("tier")
    if tier not in ("A", "B", "C"):
        errs.append("source.tier must be A, B or C (D is never carded)")
    if not (src.get("doi") or src.get("url")):
        errs.append("source needs a doi or url")
    abstract = abstracts.get((src.get("doi") or "").lower())
    for k in c.get("kpis") or []:
        eff = k.get("effect") or {}
        nums = numbers(eff.get("value")) + [n for ci in (eff.get("ci") or []) for n in numbers(ci)]
        quote = (k.get("evidence") or {}).get("quote")
        if tier in ("A", "B"):
            if nums and not quote:
                errs.append(f"kpi {k.get('name')}: numbers need an evidence quote")
            for n in nums:
                if quote and n.lstrip("-") not in quote:
                    errs.append(f"kpi {k.get('name')}: {n} not found in evidence quote")
            if quote and abstract and quote not in abstract:
                errs.append(f"kpi {k.get('name')}: quote not found verbatim in source abstract")
        elif tier == "C":
            if quote:
                errs.append(f"kpi {k.get('name')}: tier C cards must not quote publisher text")
            if nums and c.get("status") == "approved" and not (k.get("evidence") or {}).get("checked_by"):
                errs.append(f"kpi {k.get('name')}: tier C numbers need evidence.checked_by (reviewer read the source)")
    if c.get("status") == "approved":
        ap = c.get("approval") or {}
        if not (ap.get("by") and ap.get("date")):
            errs.append("approved cards need approval.by and approval.date")
        kind = ap.get("kind", "human")
        if kind not in ("human", "ai"):
            errs.append("approval.kind must be human or ai")
        if kind == "ai":
            if ap.get("by") != "ospeli-review-bot":
                errs.append("ai approvals must be by ospeli-review-bot")
            if not ap.get("notes"):
                errs.append("ai approvals need approval.notes (what was checked against the source)")
    return [f"{path.name}: {e}" for e in errs]


def main() -> int:
    abstracts = load_abstracts()
    files = sorted((ROOT / "cards").rglob("*.yaml"))
    errs = [e for f in files for e in check(f, abstracts)]
    ids = [yaml.safe_load(f.read_text())["id"] for f in files if not errs]
    if len(ids) != len(set(ids)):
        errs.append("duplicate card ids")
    for e in errs:
        print("FAIL", e)
    print(f"Checked {len(files)} cards, {len(errs)} problems")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
