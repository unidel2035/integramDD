from typing import List, Dict, Set, Optional
from app.models.queries import QueryColumn, JoinType, JoinInfo
from app.logger import setup_logger

logger = setup_logger(__name__)

class QueryBuilder:
    def __init__(self):
        self.added_tables: Set[int] = set()
        self.joins: List[JoinInfo] = []
        self.table_aliases: Dict[int, str] = {}
        self.subqueries: Dict[int, str] = {}

    def build_query(self, columns: List[QueryColumn], db_name: str) -> str:
        """Строит SQL запрос на основе колонок"""
        logger.info(f"Building query for {len(columns)} columns")
        
        # Очищаем состояние
        self.added_tables = set()
        self.joins = []
        self.table_aliases = {}
        self.subqueries = {}
        
        # Сортируем колонки по порядку
        sorted_columns = sorted(columns, key=lambda x: x.ord)
        logger.info(f"Column order: {[f'{col.ord}:{col.obj}({col.obj_name})' for col in sorted_columns]}")

        # Добавляем первую колонку как мастер-таблицу
        master_column = sorted_columns[0]
        master_alias = f"a{master_column.obj}"
        self.table_aliases[master_column.obj] = master_alias
        self.added_tables.add(master_column.obj)
        logger.info(f"Master table: {master_column.obj_name} (alias: {master_alias})")

        # Обрабатываем остальные колонки итеративно
        remaining_columns = sorted_columns[1:]
        max_iterations = len(remaining_columns) * 3  # Максимальное количество итераций
        iteration = 0
        
        while remaining_columns and iteration < max_iterations:
            logger.info(f"Iteration {iteration + 1}, remaining: {len(remaining_columns)} columns")
            added_in_iteration = []
            
            for column in remaining_columns[:]:
                if self._try_add_column(column, sorted_columns, db_name):
                    added_in_iteration.append(column)
                    remaining_columns.remove(column)
                    logger.info(f"Added column: {column.obj_name} ({column.obj})")
            
            if not added_in_iteration:
                logger.warning(f"No columns added in iteration {iteration + 1}")
                # На последней итерации добавляем оставшиеся как отдельные таблицы
                if iteration == max_iterations - 1:
                    for column in remaining_columns[:]:
                        logger.warning(f"Force adding as separate table: {column.obj_name}")
                        self.table_aliases[column.obj] = f"a{column.obj}"
                        self.added_tables.add(column.obj)
                        added_in_iteration.append(column)
                        remaining_columns.remove(column)
                else:
                    break
                
            iteration += 1

        if remaining_columns:
            logger.warning(f"Failed to add {len(remaining_columns)} columns: {[col.obj_name for col in remaining_columns]}")

        return self._generate_sql(sorted_columns, master_column, master_alias, db_name)

    def _try_add_column(self, column: QueryColumn, all_columns: List[QueryColumn], db_name: str) -> bool:
        """Пытается добавить колонку в запрос"""
        if column.obj in self.added_tables:
            return True

        # Если это подчиненная колонка (up != 0), сначала добавляем родительскую
        if column.up != 0 and column.up not in self.added_tables:
            parent_column = next((c for c in all_columns if c.obj == column.up), None)
            if parent_column and not self._try_add_column(parent_column, all_columns, db_name):
                return False

        # Если у колонки есть ref связь, пытаемся добавить целевую таблицу для ссылки
        if hasattr(column, 'ref') and column.ref and column.ref not in self.added_tables:
            # Ищем колонку с нужным obj
            ref_column = next((c for c in all_columns if c.obj == column.ref), None)
            if ref_column and not self._try_add_column(ref_column, all_columns, db_name):
                # Если не можем добавить через ссылку, добавляем как базовую таблицу
                logger.warning(f"Cannot add ref target {column.ref} for column {column.obj_name}, will add ref table manually")
                self.table_aliases[column.ref] = f"a{column.ref}"
                self.added_tables.add(column.ref)

        # Ищем связь с уже добавленными таблицами
        connection = self._find_connection(column, all_columns)
        if connection:
            self._create_join(column, connection, db_name)
            self.added_tables.add(column.obj)
            return True
        
        # Если связь не найдена, но это не первая колонка, логируем предупреждение
        if len(self.added_tables) > 0:
            logger.warning(f"No connection found for column {column.obj_name}, adding as separate master table")
            
        # Добавляем как отдельную таблицу (для случаев когда нет связей)
        self.table_aliases[column.obj] = f"a{column.obj}"
        self.added_tables.add(column.obj)
        return True

    def _find_connection(self, column: QueryColumn, all_columns: List[QueryColumn]) -> Optional[Dict]:
        """Находит связь между колонкой и уже добавленными таблицами"""
        
        for added_obj in self.added_tables:
            added_column = next((c for c in all_columns if c.obj == added_obj), None)
            if not added_column:
                continue

            # 1. Ссылочная связь: добавленная колонка ссылается на нашу (ref)
            if hasattr(added_column, 'ref') and added_column.ref and added_column.ref == column.obj:
                logger.info(f"Found reference connection: {added_column.obj_name} -> {column.obj_name} (ref={added_column.ref})")
                return {
                    "type": "reference",
                    "parent_obj": added_obj,
                    "parent_column": added_column,
                    "target_obj": column.obj,
                    "ref_id": added_column.ref
                }

            # 2. Подчиненная связь: наша колонка подчинена добавленной (arr)
            if hasattr(added_column, 'arr') and added_column.arr and added_column.arr == column.obj:
                logger.info(f"Found dependent connection: {column.obj_name} -> {added_column.obj_name} (arr={added_column.arr})")
                return {
                    "type": "dependent", 
                    "parent_obj": added_obj,
                    "parent_column": added_column,
                    "target_obj": column.obj
                }

            # 3. Обратная ссылочная связь: наша колонка ссылается на добавленную
            if hasattr(column, 'ref') and column.ref and column.ref == added_obj:
                logger.info(f"Found reverse reference: {column.obj_name} -> {added_column.obj_name} (reverse ref={column.ref})")
                return {
                    "type": "reference",
                    "parent_obj": added_obj,
                    "parent_column": added_column,
                    "target_obj": column.obj,
                    "ref_id": column.ref,
                    "reverse": True
                }

            # 4. Подчиненная колонка: up указывает на родителя
            if hasattr(column, 'up') and column.up and column.up == added_obj:
                logger.info(f"Found parent-child connection: {column.obj_name} -> {added_column.obj_name} (up={column.up})")
                return {
                    "type": "child",
                    "parent_obj": added_obj,
                    "parent_column": added_column,
                    "target_obj": column.obj
                }

            # 4a. Специальная обработка ссылочных колонок (is_ref=1) с up-связью
            if hasattr(column, 'is_ref') and column.is_ref and hasattr(column, 'up') and column.up and column.up == added_obj:
                logger.info(f"Found reference-up connection: {column.obj_name} -> {added_column.obj_name} (is_ref=1, up={column.up})")
                return {
                    "type": "reference_up",
                    "parent_obj": added_obj,
                    "parent_column": added_column,
                    "target_obj": column.obj
                }

            # 5. Связь через base с req_id
            if hasattr(column, 'base') and hasattr(column, 'req_id') and column.base == added_obj and column.req_id:
                logger.info(f"Found base connection: {column.obj_name} -> {added_column.obj_name} (base={column.base}, req_id={column.req_id})")
                return {
                    "type": "base_reference",
                    "parent_obj": added_obj,
                    "parent_column": added_column,
                    "target_obj": column.obj,
                    "req_id": column.req_id
                }

            # 6. Обратная связь через base
            if hasattr(added_column, 'base') and hasattr(added_column, 'req_id') and added_column.base == column.obj and added_column.req_id:
                logger.info(f"Found reverse base connection: {added_column.obj_name} -> {column.obj_name} (reverse base={added_column.base})")
                return {
                    "type": "base_reference",
                    "parent_obj": added_obj, 
                    "parent_column": added_column,
                    "target_obj": column.obj,
                    "req_id": added_column.req_id,
                    "reverse": True
                }

        return None

    def _create_join(self, column: QueryColumn, connection: Dict, db_name: str):
        """Создает JOIN для колонки"""
        alias = f"a{column.obj}"
        self.table_aliases[column.obj] = alias
        parent_alias = self.table_aliases[connection["parent_obj"]]
        master_obj = min(self.table_aliases.keys())  # Первая добавленная таблица

        if connection["type"] == "reference":
            # Ссылочная связь: r{ref_id} -> a{target_obj}
            ref_id = connection["ref_id"]
            subquery = f"""(SELECT r{ref_id}.up, a{column.obj}.val a{column.obj}_val, a{column.obj}.id a{column.obj}_id
                FROM {db_name} r{ref_id}, {db_name} a{column.obj}
                WHERE a{column.obj}.id=r{ref_id}.t AND a{column.obj}.t={column.obj})"""
            # Для мастер колонки используем .id, для JOIN колонок используем .a{obj}_id
            if connection["parent_obj"] == master_obj:
                condition = f"{alias}.up={parent_alias}.id"
            else:
                condition = f"{alias}.up={parent_alias}.a{connection['parent_column'].obj}_id"

        elif connection["type"] == "dependent":
            # Подчиненная таблица: a{obj}.up = parent.id
            subquery = f"""(SELECT a{column.obj}.up, a{column.obj}.val a{column.obj}_val, a{column.obj}.id a{column.obj}_id
                FROM {db_name} a{column.obj}
                WHERE a{column.obj}.t={column.obj})"""
            # Для мастер колонки используем .id, для JOIN колонок используем .a{obj}_id
            if connection["parent_obj"] == master_obj:
                condition = f"{alias}.up={parent_alias}.id"
            else:
                condition = f"{alias}.up={parent_alias}.a{connection['parent_column'].obj}_id"

        elif connection["type"] == "child":
            # Дочерняя колонка: a{obj}.up = parent.id
            subquery = f"""(SELECT a{column.obj}.up, a{column.obj}.val a{column.obj}_val, a{column.obj}.id a{column.obj}_id
                FROM {db_name} a{column.obj}
                WHERE a{column.obj}.t={column.obj})"""
            # Для мастер колонки используем .id, для JOIN колонок используем .a{obj}_id
            if connection["parent_obj"] == master_obj:
                condition = f"{alias}.up={parent_alias}.id"
            else:
                condition = f"{alias}.up={parent_alias}.a{connection['parent_column'].obj}_id"

        elif connection["type"] == "reference_up":
            # Ссылочная колонка с up-связью (is_ref=1): a{obj}.up = parent.id
            subquery = f"""(SELECT a{column.obj}.up, a{column.obj}.val a{column.obj}_val, a{column.obj}.id a{column.obj}_id
                FROM {db_name} a{column.obj}
                WHERE a{column.obj}.t={column.obj})"""
            # Для мастер колонки используем .id, для JOIN колонок используем .a{obj}_id
            if connection["parent_obj"] == master_obj:
                condition = f"{alias}.up={parent_alias}.id"
            else:
                condition = f"{alias}.up={parent_alias}.a{connection['parent_column'].obj}_id"

        elif connection["type"] == "base_reference":
            # Связь через base с req_id
            req_id = connection["req_id"]
            subquery = f"""(SELECT r{req_id}.up, a{column.obj}.val a{column.obj}_val, a{column.obj}.id a{column.obj}_id
                FROM {db_name} r{req_id} CROSS JOIN {db_name} a{column.obj}
                WHERE a{column.obj}.id=r{req_id}.t AND a{column.obj}.t={column.obj} AND r{req_id}.val='{req_id}')"""
            # Для мастер колонки используем .id, для JOIN колонок используем .a{obj}_id
            if connection["parent_obj"] == master_obj:
                condition = f"{alias}.up={parent_alias}.id"
            else:
                condition = f"{alias}.up={parent_alias}.a{connection['parent_column'].obj}_id"

        # Определяем тип JOIN-а для модели
        if connection["type"] in ["reference", "base_reference"]:
            join_type = JoinType.REFERENCE
        elif connection["type"] in ["dependent", "child", "reference_up"]:
            join_type = JoinType.DEPENDENT
        else:
            join_type = JoinType.DEPENDENT

        # Сохраняем информацию о JOIN
        join_info = JoinInfo(
            table_alias=alias,
            join_type=join_type,
            parent_alias=parent_alias,
            condition=condition,
            subquery=subquery,
        )
        self.joins.append(join_info)

    def _generate_sql(self, columns: List[QueryColumn], master_column: QueryColumn, master_alias: str, db_name: str) -> str:
        """Генерирует финальный SQL запрос"""
        
        # Определяем какие таблицы участвуют в JOIN-ах
        joined_tables = set()
        for join in self.joins:
            # Извлекаем obj_id из table_alias (например, "a72" -> 72)
            if join.table_alias.startswith('a') and join.table_alias[1:].isdigit():
                joined_tables.add(int(join.table_alias[1:]))
        
        # SELECT clause
        select_fields = []
        for column in columns:
            alias = self.table_aliases.get(column.obj, master_alias)
            if column.obj == master_column.obj:
                select_fields.append(f"{alias}.val c{column.col_id}")
            elif column.obj in joined_tables:
                # Это колонка из JOIN
                select_fields.append(f"{alias}.a{column.obj}_val c{column.col_id}")
            else:
                # Это отдельная таблица без JOIN
                select_fields.append(f"{alias}.val c{column.col_id}")

        # FROM clause - если есть несколько отдельных таблиц, используем CROSS JOIN
        separate_tables = []
        for column in columns:
            if column.obj != master_column.obj and column.obj not in joined_tables:
                separate_tables.append(column.obj)
        
        if separate_tables:
            # Есть отдельные таблицы, используем CROSS JOIN
            from_parts = [f"{db_name} {master_alias}"]
            for obj_id in separate_tables:
                alias = self.table_aliases[obj_id]
                from_parts.append(f"CROSS JOIN {db_name} {alias}")
            from_clause = " ".join(from_parts)
        else:
            from_clause = f"{db_name} {master_alias}"
        
        # JOIN clauses с правильными условиями
        join_clauses = []
        for join in self.joins:
            # Получаем parent obj_id
            parent_obj_id = None
            for obj_id, alias in self.table_aliases.items():
                if alias == join.parent_alias:
                    parent_obj_id = obj_id
                    break
            
            # Корректируем условие JOIN в зависимости от типа родительской таблицы
            if parent_obj_id == master_column.obj:
                # Родитель - мастер таблица, используем .id
                corrected_condition = join.condition
            elif parent_obj_id in joined_tables:
                # Родитель - JOIN таблица, используем .a{obj}_id  
                corrected_condition = join.condition
            else:
                # Родитель - отдельная таблица, используем .id
                corrected_condition = join.condition.replace(f".a{parent_obj_id}_id", ".id")
            
            join_clauses.append(f"LEFT JOIN {join.subquery} {join.table_alias} ON {corrected_condition}")

        # WHERE clause
        where_conditions = [f"{master_alias}.t={master_column.obj} AND {master_alias}.up!=0"]
        
        # Добавляем условия для отдельных таблиц
        for obj_id in separate_tables:
            alias = self.table_aliases[obj_id]
            where_conditions.append(f"{alias}.t={obj_id}")
            
        where_clause = " AND ".join(where_conditions)

        # Собираем итоговый запрос
        sql_parts = [
            f"SELECT {', '.join(select_fields)}",
            f"FROM {from_clause}"
        ]
        
        if join_clauses:
            sql_parts.extend(join_clauses)
            
        sql_parts.append(f"WHERE {where_clause}")

        sql = "\n".join(sql_parts)
        logger.info(f"Generated SQL:\n{sql}")
        
        return sql

    def _build_nested_subquery(self, parent_obj: int, nested_joins: List, table_columns: Dict, db_name: str) -> Optional[str]:
        """Строит вложенный подзапрос для таблицы с дочерними JOIN-ами"""
        # Пока используем простую логику - вернем None, чтобы использовать обычные JOIN-ы
        return None
