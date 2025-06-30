from typing import Dict, Optional, Tuple, Literal, List, Any
from app.models.objects import (
    HeaderField,
)  # Предполагается, что HeaderField определён в models.objects
import logging

logger = logging.getLogger(__name__)


class SingleFilter:
    def __init__(self, value: str, field_id: int, db_name: str, mode: Literal["a", "b", "c"]):
        self.value = value.strip().lower()
        self.field_id = field_id
        self.mode = mode
        self.db_name = db_name

    def build(self) -> Tuple[Optional[str], str]:
        col = "val"

        if self.mode == "a":
            prefix = "vals"
        elif self.mode == "b":
            prefix = f"f{self.field_id}"
        elif self.mode == "c":
            prefix = f"repval_{self.field_id}"
        else:
            raise ValueError(f"Unknown filter mode: {self.mode}")

        # Определим, какой тип LIKE нужно применить
        self.like_type = None
        raw = self.value
        if raw.startswith("%") and raw.endswith("%"):
            self.like_type = "contains"
        elif raw.startswith("%"):
            self.like_type = "endswith"
        elif raw.endswith("%"):
            self.like_type = "startswith"

        if self.like_type:
            where = f"AND lower({prefix}.{col}) LIKE :filter_{self.field_id}"
        else:
            where = f"AND lower(left({prefix}.{col}, 127)) = :filter_{self.field_id}"

        from_ = None
        if self.mode == "b":
            from_ = f"LEFT JOIN {self.db_name} {prefix} ON {prefix}.up=vals.id AND {prefix}.t={self.field_id}"

        return from_, where

    def get_params(self) -> Dict[str, str]:
        key = f"filter_{self.field_id}"
        val = self.value

        if self.like_type == "contains":
            return {key: f"%{val.strip('%')}" + "%"}
        elif self.like_type == "startswith":
            return {key: f"{val.strip('%')}" + "%"}
        elif self.like_type == "endswith":
            return {key: "%" + f"{val.strip('%')}"}
        else:
            return {key: val}


class FilterBuilder:
    def __init__(
        self,
        filters: Dict[str, str],
        term_id: int,
        term_name: str,
        header: List[HeaderField],
        db_name: str,
        context_mode: Literal["default", "report"] = "default",
    ):
        self.filters = filters
        self.term_id = term_id
        self.term_name = term_name
        self.header = header
        self.context_mode = context_mode
        self.db_name = db_name

    def build(self) -> Tuple[str, str, Dict[str, str]]:
        from_clauses = []
        where_clauses = []
        params = {}

        for key, value in self.filters.items():
            if key in {"up", "limit", "offset"}:
                continue

            filt = self._resolve_filter(key, value)
            if not filt:
                logger.warning(f"Unknown filter field: {key}, skipping")
                continue

            from_sql, where_sql = filt.build()
            if from_sql:
                from_clauses.append(from_sql)
            where_clauses.append(where_sql)
            params.update(filt.get_params())

        return "\n".join(from_clauses), " ".join(where_clauses), params

    def _resolve_filter(self, key: str, value: str) -> Optional[SingleFilter]:
        key_lower = key.lower()
        value = value.strip()

        if key.startswith("f") and key[1:].isdigit():
            field_id = int(key[1:])
            mode = "a" if field_id == self.term_id else "b"
            return SingleFilter(value, field_id, self.db_name, mode)

        if key_lower == self.term_name.lower():
            return SingleFilter(value, self.term_id, self.db_name, "a")

        for field in self.header:
            if field.name.lower() == key_lower:
                return SingleFilter(value, field.id, self.db_name, "b")

        if self.context_mode == "report":
            try:
                field_id = int(key)
                return SingleFilter(value, field_id, self.db_name, "c")
            except ValueError:
                pass

        return None
