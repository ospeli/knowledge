"""Search the built knowledge base offline: python scripts/search.py "discharge before noon" """
import json, sqlite3, sys
from pathlib import Path

db = sqlite3.connect(Path(__file__).resolve().parent.parent / "dist" / "kb.sqlite")
q = " ".join(sys.argv[1:]) or "patient flow"
rows = db.execute("SELECT c.id, c.title, c.evidence_level, c.source FROM cards_fts f JOIN cards c ON c.id=f.id "
                  "WHERE cards_fts MATCH ? ORDER BY rank LIMIT 10", (q,)).fetchall()
for cid, title, lvl, src in rows:
    s = json.loads(src)
    print(f"[{cid}] {lvl} · {title} · {s.get('doi') or s.get('url')}")
print(f"{len(rows)} results · {dict(db.execute('SELECT key, value FROM meta'))['version']}")
