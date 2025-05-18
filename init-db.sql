-- Создаем новую базу данных перед вызовом этой процедуры
CREATE OR REPLACE PROCEDURE create_public_ru_table(dbname TEXT)
LANGUAGE plpgsql AS
$$
BEGIN

    EXECUTE format(
        'CREATE TABLE IF NOT EXISTS %I (
            id bigserial NOT NULL,
            up int8 NOT NULL,
            t int8 NOT NULL,
            val text NULL,
            CONSTRAINT %I_pk PRIMARY KEY (id)
        );', dbname, dbname
    );
    
    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS %I_upt_idx ON %I USING btree (up, t);', dbname, dbname
    );
    
    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS %I_tval_idx ON %I USING btree (t, lower(left(val, 127)));', dbname, dbname
    );
    
    EXECUTE format(
        'SELECT setval(''%I_id_seq'', 110);', dbname
    );
    
    EXECUTE format(
        'INSERT INTO %I (id, up, t, val) VALUES
            (1, 1, 1, ''ROOT''),
            (2, 0, 2, ''HTML''),
            (3, 0, 3, ''CHARS''),
            (4, 0, 4, ''DATETIME''),
            (5, 0, 5, ''TERM''),
            (6, 0, 6, ''PWD''),
            (7, 0, 7, ''BUTTON''),
            (8, 0, 8, ''MEDIA''),
            (9, 0, 9, ''DATE''),
            (10, 0, 10, ''FILE''),
            (11, 0, 11, ''BOOLEAN''),
            (12, 0, 12, ''MEMO''),
            (13, 0, 13, ''NUMBER''),
            (14, 0, 14, ''FLOAT''),
            (15, 0, 15, ''CALCULATABLE''),
            (16, 0, 16, ''UUID''),
            (17, 0, 17, ''PATH''),
            (30, 0, 0, ''NOT NULL''),
            (31, 0, 0, ''ALIAS''),
            (32, 0, 0, ''MULTIPLE''),
            (33, 0, 0, ''ORDER''),
            (34, 0, 0, ''UNIQUE''),
            (35, 0, 0, ''SIZE''),
            (36, 0, 0, ''VALIDATION''),
            (37, 0, 0, ''SHARD''),
            (64, 0, 3, ''Пользователь''),
            (65, 0, 3, ''Имя''),
            (66, 0, 3, ''email''),
            (67, 0, 3, ''Телефон''),
            (68, 0, 6, ''token''),
            (69, 0, 6, ''xsrf''),
            (70, 0, 4, ''Activity''),
            (71, 0, 3, ''Роль''),
            (72, 0, 5, ''Объект''),
            (73, 0, 3, ''Меню''),
            (74, 0, 3, ''Адрес''),
            (75, 0, 3, ''Доступ''),
            (76, 0, 11, ''EXPORT''),
            (77, 0, 11, ''DELETE''),
            (78, 0, 11, ''IMPORT''),
            (79, 0, 11, ''HREF''),
            (81, 0, 12, ''Примечание''),
            (82, 0, 3, ''Функция''),
            (83, 0, 8, ''Формат''),
            (84, 0, 3, ''Итог''),
            (85, 0, 12, ''Формула''),
            (86, 0, 3, ''Запрос''),
            (87, 0, 5, ''Колонка запроса''),
            (88, 0, 9, ''Дата''),
            (89, 0, 10, ''Фото''),
            (90, 0, 3, ''Secret''),
            (91, 0, 13, ''Limit''),
            (92, 0, 6, ''Пароль''),
            (93, 0, 12, ''Фильтр''),
            (94, 0, 3, ''SET''),
            (95, 0, 11, ''Скрыть''),
            (96, 0, 3, ''Маска''),
            (97, 0, 11, ''Интерактивный''),
            (98, 0, 3, ''URL''),
            (99, 0, 11, ''EXECUTE''),
            (100, 64, 65, ''1''),
            (101, 64, 66, ''2''),
            (102, 64, 67, ''3''),
            (103, 64, 68, ''4''),
            (104, 64, 70, ''5''),
            (105, 0, 12, ''Alias'');', dbname
    );
END
$$;

CALL create_public_ru_table('rep');