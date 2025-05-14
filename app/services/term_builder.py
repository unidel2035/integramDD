from typing import List, Dict
from collections import defaultdict
from app.models.term import TermMetadata, TermRequisite


def build_terms_from_rows(rows: List[Dict]) -> List[TermMetadata]:
    terms_by_id: Dict[int, Dict] = {}
    reqs_by_term_id: Dict[int, List[TermRequisite]] = defaultdict(list)

    for row in rows:
        term_id = row["id"]

        if term_id not in terms_by_id:
            terms_by_id[term_id] = {
                "id": term_id,
                "up": row.get("up", 0),
                "type": row["base"],
                "val": row["obj"],
                "unique": row.get("uniq", 1),
                "reqs": []
            }

        if row.get("req_id"):
            req = TermRequisite(
                num=row.get("ord"),
                id=row["req_id"],
                val=row.get("req_val"),
                type=row.get("req_t"),
                attrs=row.get("attrs"),
                ref_id=row.get("ref_id"),
                ref=row.get("ref_val"),
                default_val=row.get("default_val"),
                mods=row.get("mods"),
            )
            reqs_by_term_id[term_id].append(req)

    return [
        TermMetadata(**{**term_data, "reqs": reqs_by_term_id[term_id]})
        for term_id, term_data in terms_by_id.items()
    ]
