import json, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
FX = ROOT / "tests" / "fixtures"

from harvest import europepmc, openalex  # noqa: E402
from harvest.common import classify, licence_tier  # noqa: E402
import scripts.harvest as H  # noqa: E402
import scripts.verify_cards as V  # noqa: E402
import scripts.build_kb as B  # noqa: E402


def recs():
    e = [europepmc.parse(r) for r in json.loads((FX / "europepmc.json").read_text())["resultList"]["result"]]
    o = [openalex.parse(w) for w in json.loads((FX / "openalex.json").read_text())["results"]]
    return e + o


def test_parse_and_classify():
    r = recs()
    flow = r[0]
    assert flow.doi == "10.9999/test.flow.1" and flow.licence == "cc-by" and "hospital" in flow.title
    assert "A3_inpatient_flow" in classify(flow)
    assert classify(r[1]) == []          # lab science excluded
    assert licence_tier(flow) == "A"
    assert r[2].is_preprint


def test_run_dedupes_gates_and_strips(tmp_path, monkeypatch):
    monkeypatch.setattr(H, "INBOX", tmp_path / "inbox")
    monkeypatch.setattr(H, "SEEN", tmp_path / "seen.txt")
    monkeypatch.setattr(H, "STATE", tmp_path / "state.json")
    res = H.run("2026-11-01", "2026-11-05", [], records_in=recs())
    lines = [json.loads(l) for l in (tmp_path / "inbox" / "2026-11-05.jsonl").read_text().splitlines()]
    dois = [l["doi"] for l in lines]
    assert dois.count("10.9999/test.flow.1") == 1                 # merged across sources
    flow = next(l for l in lines if l["doi"] == "10.9999/test.flow.1")
    assert flow["tier"] == "A" and flow["abstract"]                # open: abstract kept
    supply = next(l for l in lines if l["doi"] == "10.9999/test.supply.3")
    assert supply["tier"] == "C" and supply["abstract"] is None    # paywalled: no publisher text stored
    assert all(l["domains"] for l in lines)
    again = H.run("2026-11-01", "2026-11-05", [], records_in=recs())
    assert again["kept"] == 0                                      # seen list prevents repeats


CARD = """id: kc-test-0001
version: 1
status: approved
title: Criteria-led discharge shortened length of stay
summary: Nurse-led discharge against agreed criteria cut medical length of stay by half a day.
intervention: Criteria-led discharge
comparator: Consultant-led discharge
source: {doi: 10.9999/test.flow.1, tier: A, licence: cc-by}
domains: [A3_inpatient_flow]
design: its_uncontrolled
evidence_level: OE3
setting: {income: HIC, facility: acute_hospital, beds: 400}
kpis:
  - name: length_of_stay_days
    effect: {value: -0.5, unit: days, ci: [-0.8, -0.2]}
    evidence: {quote: "reduced mean length of stay from 6.1 to 5.6 days (difference -0.5 days, 95% CI -0.8 to -0.2)"}
review_by: 2031-11-05
approval: {by: test-reviewer, date: 2026-11-05}
"""


def test_verify_and_build(tmp_path, monkeypatch):
    abstracts = {"10.9999/test.flow.1": json.loads((FX / "europepmc.json").read_text())["resultList"]["result"][0]["abstractText"]}
    p = tmp_path / "kc-test-0001.yaml"
    p.write_text(CARD)
    assert V.check(p, abstracts) == []
    bad = tmp_path / "kc-test-0002.yaml"
    bad.write_text(CARD.replace("kc-test-0001", "kc-test-0002").replace("-0.5, unit", "-0.9, unit"))
    assert any("not found in evidence quote" in e for e in V.check(bad, abstracts))
    paywalled = tmp_path / "kc-test-0003.yaml"
    paywalled.write_text(CARD.replace("kc-test-0001", "kc-test-0003").replace("tier: A", "tier: C"))
    assert any("must not quote publisher text" in e for e in V.check(paywalled, abstracts))
    cards = tmp_path / "cards"; cards.mkdir(); (cards / "kc-test-0001.yaml").write_text(CARD)
    monkeypatch.setattr(B, "ROOT", tmp_path)
    out = tmp_path / "kb.sqlite"
    assert B.build(out) == 1
    db = sqlite3.connect(out)
    hit = db.execute("SELECT id FROM cards_fts WHERE cards_fts MATCH 'discharge'").fetchall()
    assert hit == [("kc-test-0001",)]


def test_ai_approval_rules(tmp_path):
    abstracts = {"10.9999/test.flow.1": json.loads((FX / "europepmc.json").read_text())["resultList"]["result"][0]["abstractText"]}
    ok = tmp_path / "kc-test-0004.yaml"
    ok.write_text(CARD.replace("kc-test-0001", "kc-test-0004").replace(
        "approval: {by: test-reviewer, date: 2026-11-05}",
        "approval: {by: ospeli-review-bot, kind: ai, date: 2026-11-06, notes: numbers and design checked against abstract}"))
    assert V.check(ok, abstracts) == []
    bad = tmp_path / "kc-test-0005.yaml"
    bad.write_text(CARD.replace("kc-test-0001", "kc-test-0005").replace(
        "approval: {by: test-reviewer, date: 2026-11-05}", "approval: {by: someone, kind: ai, date: 2026-11-06}"))
    errs = V.check(bad, abstracts)
    assert any("ospeli-review-bot" in e for e in errs) and any("notes" in e for e in errs)
