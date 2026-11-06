"""OpenAlex harvester. Metadata is CC0. Set OPENALEX_API_KEY for the larger free budget."""
import os
from .common import Record, get_json, norm_doi, norm_licence

API = "https://api.openalex.org/works"


def _abstract(inv: dict | None) -> str | None:
    if not inv:
        return None
    pos = {}
    for word, idxs in inv.items():
        for i in idxs:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))


def fetch(query: str, since: str, until: str, max_pages: int = 3):
    params = {"search": query, "filter": f"from_publication_date:{since},to_publication_date:{until}",
              "per-page": 100, "cursor": "*"}
    key = os.environ.get("OPENALEX_API_KEY")
    if key:
        params["api_key"] = key
    mail = os.environ.get("OSPELI_CONTACT")
    if mail:
        params["mailto"] = mail
    for _ in range(max_pages):
        data = get_json(API, params)
        for w in data.get("results", []):
            yield parse(w)
        nxt = (data.get("meta") or {}).get("next_cursor")
        if not nxt:
            break
        params["cursor"] = nxt


def parse(w: dict) -> Record:
    ids = w.get("ids") or {}
    loc = w.get("best_oa_location") or w.get("primary_location") or {}
    src = (w.get("primary_location") or {}).get("source") or {}
    return Record(
        source="openalex",
        title=w.get("title") or w.get("display_name") or "",
        year=w.get("publication_year"),
        doi=norm_doi(w.get("doi")),
        pmid=(ids.get("pmid") or "").rsplit("/", 1)[-1] or None,
        pmcid=(ids.get("pmcid") or "").rsplit("/", 1)[-1] or None,
        openalex=(w.get("id") or "").rsplit("/", 1)[-1] or None,
        journal=src.get("display_name"),
        authors=[(a.get("author") or {}).get("display_name", "") for a in (w.get("authorships") or [])][:12],
        abstract=_abstract(w.get("abstract_inverted_index")),
        url=w.get("doi") or w.get("id"),
        licence=norm_licence(loc.get("license")),
        is_oa=bool((w.get("open_access") or {}).get("is_oa")),
        is_preprint=w.get("type") == "preprint",
    )
