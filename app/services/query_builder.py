from typing import List, Dict, Set, Optional
from app.models.queries import QueryColumn, JoinType, JoinInfo
import logging


class QueryBuilder:
    def __init__(self):
        self.added_tables: Set[int] = set()
        self.joins: List[JoinInfo] = []
        self.table_aliases: Dict[int, str] = {}

    def build_query(self, columns: List[QueryColumn]) -> str:
        """Строит SQL запрос на основе колонок"""
        # Очищаем состояние
        self.added_tables = set()
        self.joins = []
        self.table_aliases = {}
        
        # Сортируем колонки по порядку
        sorted_columns = sorted(columns, key=lambda x: x.ord)

        # Добавляем первую колонку как мастер-таблицу
        master_column = sorted_columns[0]
        master_alias = f"a{master_column.obj}"
        self.table_aliases[master_column.obj] = master_alias
        self.added_tables.add(master_column.obj)

        # Обрабатываем остальные колонки в цикле до тех пор, пока все не будут добавлены
        remaining_columns = sorted_columns[1:]
        max_iterations = len(remaining_columns) * 2  # Защита от бесконечного цикла
        iteration = 0
        
        while remaining_columns and iteration < max_iterations:
            added_in_iteration = []
            
            for column in remaining_columns[:]:  # Копируем список для безопасной итерации
                if self._add_column_to_query(column, sorted_columns):
                    added_in_iteration.append(column)
                    remaining_columns.remove(column)
            
            if not added_in_iteration:
                # Если ничего не добавили в этой итерации, выходим
                break
                
            iteration += 1

        return self._generate_sql(sorted_columns, master_column, master_alias)

    def _add_column_to_query(self, column: QueryColumn, all_columns: List[QueryColumn]) -> bool:
        """Добавляет колонку в запрос, находя подходящие связи. Возвращает True если колонка была добавлена"""
        if column.obj in self.added_tables:
            return True

        # Сначала проверяем, нужно ли добавить родительскую колонку (если это не первая колонка таблицы)
        if column.up != 0 and column.up not in self.added_tables:
            parent_column = next((c for c in all_columns if c.obj == column.up), None)
            if parent_column:
                if not self._add_column_to_query(parent_column, all_columns):
                    return False  # Не удалось добавить родительскую колонку

        # Ищем связь с уже добавленными таблицами
        connection = self._find_connection(column, all_columns)
        if connection:
            self._create_join(column, connection)
            self.added_tables.add(column.obj)
            return True
            
        return False

    def _find_connection(
        self, column: QueryColumn, all_columns: List[QueryColumn]
    ) -> Optional[Dict]:
        """Находит связь между колонкой и уже добавленными таблицами"""
        for added_obj in self.added_tables:
            added_column = next((c for c in all_columns if c.obj == added_obj), None)
            if not added_column:
                continue

            # Проверяем ссылочную связь - добавленная колонка ссылается на нашу (ref)
            if added_column.ref == column.obj:
                return {
                    "type": JoinType.REFERENCE,
                    "parent_obj": added_obj,
                    "parent_column": added_column,
                    "ref_id": added_column.ref,
                    "target_obj": column.obj
                }

            # Проверяем подчиненную связь - наша колонка является подчиненной для добавленной (arr)
            if added_column.arr == column.obj:
                return {
                    "type": JoinType.DEPENDENT,
                    "parent_obj": added_obj,
                    "parent_column": added_column,
                    "arr_id": added_column.arr,
                    "target_obj": column.obj
                }

            # Обратная ссылочная связь - наша колонка ссылается на добавленную
            if column.ref == added_obj:
                return {
                    "type": JoinType.REFERENCE,
                    "parent_obj": added_obj,
                    "parent_column": added_column,
                    "ref_id": column.ref,
                    "target_obj": column.obj,
                    "reverse": True,
                }
                
            # Проверяем связь через base (как в примере с Доступом)
            if column.base == added_obj or added_column.base == column.obj:
                return {
                    "type": JoinType.REFERENCE,
                    "parent_obj": added_obj,
                    "parent_column": added_column,
                    "ref_id": getattr(column, 'req_id', None),
                    "target_obj": column.obj,
                    "base_connection": True
                }

        return None

    def _create_join(self, column: QueryColumn, connection: Dict):
        """Создает JOIN для колонки"""
        alias = f"a{column.obj}"
        self.table_aliases[column.obj] = alias
        parent_alias = self.table_aliases[connection["parent_obj"]]

        if connection["type"] == JoinType.REFERENCE:
            # Ссылочный джойн
            if connection.get("base_connection") and connection.get("ref_id"):
                # Специальный случай для связи через base с req_id (как Доступ)
                ref_id = connection["ref_id"]
                subquery = f"""(SELECT r{ref_id}.up, a{column.obj}.val a{column.obj}_val, a{column.obj}.id a{column.obj}_id
                    FROM ru r{ref_id} CROSS JOIN ru a{column.obj}
                    WHERE a{column.obj}.id=r{ref_id}.t AND a{column.obj}.t={column.obj} AND r{ref_id}.val='{connection["ref_id"]}')"""
                condition = f"r{ref_id}.up={parent_alias}.id"
            else:
                # Обычная ссылочная связь
                ref_id = connection.get("ref_id", column.obj)
                subquery = f"""(SELECT r{ref_id}.up, a{column.obj}.val a{column.obj}_val, a{column.obj}.id a{column.obj}_id
                    FROM ru r{ref_id}, ru a{column.obj}
                    WHERE a{column.obj}.id=r{ref_id}.t AND a{column.obj}.t={column.obj})"""
                condition = f"r{ref_id}.up={parent_alias}.id"

        else:  # DEPENDENT
            # Подчиненная таблица
            subquery = f"""(SELECT a{column.obj}.up, a{column.obj}.val a{column.obj}_val, a{column.obj}.id a{column.obj}_id
                FROM ru a{column.obj}
                WHERE a{column.obj}.t={column.obj})"""
            condition = f"a{column.obj}.up={parent_alias}.id"

        join_info = JoinInfo(
            table_alias=alias,
            join_type=connection["type"],
            parent_alias=parent_alias,
            condition=condition,
            subquery=subquery,
        )
        self.joins.append(join_info)

    def _generate_sql(
        self, columns: List[QueryColumn], master_column: QueryColumn, master_alias: str
    ) -> str:
        """Генерирует финальный SQL запрос"""
        # SELECT clause
        select_fields = []
        for column in columns:
            alias = self.table_aliases.get(column.obj, master_alias)
            if column.obj == master_column.obj:
                select_fields.append(f"{alias}.val c{column.col_id}")
            else:
                select_fields.append(f"{alias}.a{column.obj}_val c{column.col_id}")

        # FROM clause
        from_clause = f"ru {master_alias}"

        # JOIN clauses
        join_clauses = []
        for join in self.joins:
            join_clauses.append(
                f"LEFT JOIN {join.subquery} {join.table_alias} ON {join.condition}"
            )

        # WHERE clause
        where_clause = f"{master_alias}.t={master_column.obj} AND {master_alias}.up!=0"

        # Собираем запрос
        sql = f"""SELECT {', '.join(select_fields)}
FROM {from_clause}
{chr(10).join(join_clauses)}
WHERE {where_clause}"""

        return sql
