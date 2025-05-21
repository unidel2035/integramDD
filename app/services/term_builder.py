"""Service function to transform flat SQL rows into structured term metadata."""

from typing import List, Dict
from collections import defaultdict
from app.models.term import TermMetadata, TermRequisite


def build_terms_from_rows(rows: List[Dict]) -> List[TermMetadata]:
    """Constructs a list of TermMetadata objects from raw SQL query rows.

    This function groups flat SQL results by term ID and builds
    structured TermMetadata objects with nested requisites.

    Args:
        rows: A list of dictionaries representing raw SQL rows.

    Returns:
        A list of TermMetadata objects with requisites grouped under each term.
    """
    terms_by_id: Dict[int, Dict] = {}
    reqs_by_term_id: Dict[int, List[TermRequisite]] = defaultdict(list)

    for row in rows:
        term_id = row["id"]

        # Initialize term metadata if not already stored
        if term_id not in terms_by_id:
            terms_by_id[term_id] = {
                "id": term_id,
                "up": row.get("up", 0),
                "type": row["base"],
                "val": row["obj"],
                "unique": 1 if row.get("uniq") else 0,
                "reqs": [], # Placeholder for requisites
                "mods": [
                    mod.encode("utf-8").decode("unicode_escape")
                    for mod in (row.get("obj_mods", []) or [])
                ],
            }

        # If a requisite is present in the row, build it and group by term ID
        if row.get("req_id"):
            req = TermRequisite(
                num=row.get("ord"),
                id=str(row["req_id"]),
                val=row.get("req_val"),
                type=str(row.get("req_t")),
                attrs=row.get("attrs"),
                ref_id=row.get("ref_id"),
                ref=row.get("ref_val"),
                default_val=row.get("default_val"),
                mods=row.get("mods"),
            )

            reqs_by_term_id[term_id].append(req.model_dump(exclude_none=True))

    # Combine base term info with its requisites
    return [
        TermMetadata(**{**term_data, "reqs": reqs_by_term_id[term_id]}).model_dump(
            exclude_none=True
        )
        for term_id, term_data in terms_by_id.items()
    ]
