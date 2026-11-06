"""Europe PMC REST harvester (no key). Covers PubMed, PMC and preprints."""
from .common import Record, get_json, norm_doi, norm_licence, strip_tags

API = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def fetch(query: str, since: str, until: str, max_pages: int = 4):
    cursor = "*"
    q = f'({query}) AND FIRST_PDATE:[{since} TO {until}]'
    for _ in range(max_pages):
        data = get_json(API, {"query": q, "format": "json", "resultType": "core", "pageSize": 100, "cursorMark": cursor})
        for r in data.get("resultList", {}).get("result", []):
            yield parse(r)
        nxt = data.get("nextCursorMark")
        if not nxt or nxt == cursor:
            break
        cursor = nxt


def parse(r: dict) -> Record:
    year = r.get("pubYear")
    return Record(
        source="europepmc",
        title=strip_tags(r.get("title")) or "",
        year=int(year) if year and str(year).isdigit() else None,
        doi=norm_doi(r.get("doi")),
        pmid=r.get("pmid"),
        pmcid=r.get("pmcid"),
        journal=(r.get("journalInfo") or {}).get("journal", {}).get("title"),
        authors=[a.strip() for a in (r.get("authorString") or "").rstrip(".").split(",") if a.strip()][:12],
        abstract=strip_tags(r.get("abstractText")),
        url=f"https://europepmc.org/article/{r.get('source', 'MED')}/{r.get('id')}",
        licence=norm_licence(r.get("license")),
        is_oa=r.get("isOpenAccess") == "Y",
        is_preprint=r.get("source") == "PPR",
    )
