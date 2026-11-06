"""Build dist/kb.sqlite from approved cards: one portable file with full-text search, usable offline.

Only status=approved cards are included. Tier B cards go only into the community bundle (--community).
"""
from __future__ import annotations
import argparse, datetime as dt, json, sqlite3, sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def build(out: Path, community: bool = False) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    db = sqlite3.connect(out)
    db.executescript("""
      CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
      CREATE TABLE cards(id TEXT PRIMARY KEY, version INT, title TEXT, summary TEXT, domains TEXT, design TEXT,
                         evidence_level TEXT, setting TEXT, source TEXT, kpis TEXT, review_by TEXT, approval_kind TEXT, json TEXT);
      CREATE VIRTUAL TABLE cards_fts USING fts5(id UNINDEXED, title, summary, intervention, kpi_names, domains);
    """)
    n = 0
    for f in sorted((ROOT / "cards").rglob("*.yaml")):
        c = yaml.safe_load(f.read_text(encoding="utf-8"))
        if c.get("status") != "approved":
            continue
        if (c.get("source") or {}).get("tier") == "B" and not community:
            continue
        kpis = c.get("kpis") or []
        db.execute("INSERT INTO cards VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (
            c["id"], c["version"], c["title"], c["summary"], ",".join(c["domains"]), c["design"], c["evidence_level"],
            json.dumps(c.get("setting")), json.dumps(c.get("source")), json.dumps(kpis), str(c["review_by"]), (c.get("approval") or {}).get("kind", "human"), json.dumps(c, default=str)))
        db.execute("INSERT INTO cards_fts VALUES (?,?,?,?,?,?)", (
            c["id"], c["title"], c["summary"], c.get("intervention") or "", " ".join(k.get("name", "") for k in kpis), " ".join(c["domains"])))
        n += 1
    version = "kb-" + dt.date.today().isoformat()
    db.executemany("INSERT INTO meta VALUES (?,?)", [("version", version), ("cards", str(n)),
                                                       ("bundle", "community" if community else "core"),
                                                       ("built_at", dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"))])
    db.commit()
    db.close()
    return n


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "dist" / "kb.sqlite"))
    ap.add_argument("--community", action="store_true")
    a = ap.parse_args()
    print(f"Built {a.out} with {build(Path(a.out), a.community)} approved cards")
