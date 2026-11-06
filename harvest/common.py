"""Shared harvesting helpers: HTTP, normalisation, licence gate, classification."""
from __future__ import annotations
import json, re, time, urllib.parse, urllib.request
from dataclasses import dataclass, field, asdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
LICENCES = yaml.safe_load((ROOT / "licences.yaml").read_text())
TAXONOMY = yaml.safe_load((ROOT / "taxonomy.yaml").read_text())
USER_AGENT = "ospeli-knowledge-harvester/0.1 (+https://ospeli.com)"


def get_json(url: str, params: dict | None = None, tries: int = 4, pause: float = 0.4) -> dict:
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    for attempt in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as r:
                time.sleep(pause)  # stay well inside published rate limits
                return json.loads(r.read().decode("utf-8"))
        except Exception:
            if attempt == tries - 1:
                raise
            time.sleep(2 ** attempt)
    return {}


@dataclass
class Record:
    source: str
    title: str
    year: int | None = None
    doi: str | None = None
    pmid: str | None = None
    pmcid: str | None = None
    openalex: str | None = None
    journal: str | None = None
    authors: list[str] = field(default_factory=list)
    abstract: str | None = None
    url: str | None = None
    licence: str = "unknown"
    is_oa: bool = False
    is_preprint: bool = False
    tier: str = "C"
    domains: list[str] = field(default_factory=list)
    retrieved_at: str = ""

    def key(self) -> str:
        if self.doi:
            return "doi:" + self.doi.lower()
        if self.pmid:
            return "pmid:" + self.pmid
        if self.openalex:
            return "oa:" + self.openalex
        first = (self.authors[0] if self.authors else "").split()[-1:] or [""]
        return "t:" + re.sub(r"[^a-z0-9]", "", (self.title or "").lower())[:80] + f":{self.year}:{first[0].lower()}"

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)


def norm_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    doi = doi.strip().lower()
    for p in ("https://doi.org/", "http://doi.org/", "doi:"):
        if doi.startswith(p):
            doi = doi[len(p):]
    return doi or None


def norm_licence(raw: str | None) -> str:
    if not raw:
        return "unknown"
    s = raw.lower().replace("_", "-").replace(" ", "-")
    for k in ("cc-by-nc-nd", "cc-by-nc-sa", "cc-by-nc", "cc-by-nd", "cc-by-sa", "cc-by", "cc0", "ogl"):
        if k in s:
            return k
    if "public-domain" in s or s == "pd":
        return "pd"
    return "publisher" if s not in ("", "unknown", "none") else "unknown"


def licence_tier(record: Record) -> str:
    """Apply licences.yaml. Full text is only ever kept for tier A/B; C is metadata only; D is dropped."""
    src = LICENCES["sources"].get(record.source, {})
    if src.get("default_tier") == "D":
        return "D"
    return LICENCES["licence_tiers"].get(record.licence, "C")


_TERMS = {d: [t.lower() for t in terms] for d, terms in TAXONOMY["domains"].items()}
_CONTEXT = [t.lower() for t in TAXONOMY["context_terms"]]
_EXCLUDE = [t.lower() for t in TAXONOMY["exclude_terms"]]


def classify(record: Record) -> list[str]:
    """First-pass rule classifier. Returns operations domains, or [] if not an operations record."""
    text = f"{record.title or ''} {record.abstract or ''}".lower()
    if any(x in text for x in _EXCLUDE):
        return []
    if not any(c in text for c in _CONTEXT):
        return []
    hits = []
    for dom, terms in _TERMS.items():
        score = sum(1 for t in terms if t in text)
        if score:
            hits.append((score, dom))
    hits.sort(reverse=True)
    return [d for _, d in hits[:3]]


def strip_tags(s: str | None) -> str | None:
    if not s:
        return s
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)).strip()
