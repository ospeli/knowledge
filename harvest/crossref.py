"""Crossref REST harvester. Uses the polite pool when OSPELI_CONTACT is set. Also used for retraction checks."""
import os
from .common import Record, get_json, norm_doi, norm_licence, strip_tags

API = "https://api.crossref.org/works"


def fetch(query: str, since: str, until: str, max_pages: int = 2):
    params = {"query.bibliographic": query, "filter": f"from-pub-date:{since},until-pub-date:{until},type:journal-article",
              "rows": 100, "cursor": "*", "select": "DOI,title,issued,container-title,author,abstract,license,URL,type"}
    mail = os.environ.get("OSPELI_CONTACT")
    if mail:
        params["mailto"] = mail
    for _ in range(max_pages):
        data = get_json(API, params, pause=0.5)
        msg = data.get("message", {})
        for it in msg.get("items", []):
            yield parse(it)
        nxt = msg.get("next-cursor")
        if not nxt or not msg.get("items"):
            break
        params["cursor"] = nxt


def parse(it: dict) -> Record:
    parts = ((it.get("issued") or {}).get("date-parts") or [[None]])[0]
    lic = (it.get("license") or [{}])[0].get("URL")
    return Record(
        source="crossref",
        title=strip_tags((it.get("title") or [""])[0]) or "",
        year=parts[0] if parts else None,
        doi=norm_doi(it.get("DOI")),
        journal=(it.get("container-title") or [None])[0],
        authors=[f"{a.get('given', '')} {a.get('family', '')}".strip() for a in (it.get("author") or [])][:12],
        abstract=strip_tags(it.get("abstract")),
        url=it.get("URL"),
        licence=norm_licence(lic),
    )


def is_retracted(doi: str) -> bool:
    """True if Crossref lists a retraction notice that updates this DOI."""
    data = get_json(API, {"filter": f"updates:{doi},update-type:retraction", "rows": 1})
    return data.get("message", {}).get("total-results", 0) > 0
