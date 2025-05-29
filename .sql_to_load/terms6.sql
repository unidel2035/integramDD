-- OUT res='1' in case of success, otherwise - error or warning message
-- Create the term with the given base type
CREATE OR REPLACE FUNCTION public.post_terms(db text, value text, base int8, mods json default '{}', OUT newid int8, OUT res TEXT)
AS $$
DECLARE i record;
		m int8;
BEGIN
	EXECUTE format('SELECT obj.id FROM %s obj, %s base WHERE obj.val ILIKE ''%s'' AND obj.up=0 AND base.t=obj.t AND base.id=base.t', db, db, replace(value, '''', '''''')) into newid;
	IF newid IS NOT NULL THEN
		res := 'warn_term_exists';
	ELSE
		EXECUTE format('insert into %s (up, t, val) values (0, %s, ''%s'') RETURNING id', db, base, replace(value, '''', '''''')) into newid;
		res := '1';
		FOR i IN (SELECT * FROM json_each(mods)) LOOP
			EXECUTE format('SELECT id FROM %s WHERE t=0 AND up=0 AND val ILIKE ''%s'' LIMIT 1', db, i.key) INTO m;
			IF m IS NOT NULL THEN
				EXECUTE format('INSERT INTO %s (up, t, val) VALUES (%s, %s, ''%s'')', db, newid, m, trim('"' FROM i.value::text));
			END IF;
		END LOOP;
	END IF;
END;
$$ LANGUAGE plpgsql;

explain SELECT obj.id FROM rep obj, rep base WHERE obj.val ILIKE 'operatn' AND obj.up=0 AND base.t=obj.t AND base.id=base.t;
SELECT public.post_terms('rep', 'operat1''1ion143336', 3);
SELECT public.post_terms('rep', 'operatn143336', 3);
SELECT post_terms('dup', 'operations', 5);
SELECT post_terms('rep', 'operation112', 3);
SELECT post_terms('dup', 'ope''ration3467', 3, '{"UNIQUE":"", "ALIAS":"tnx"}'::json); -- Modifiers

-- Add a requisite to a term 
CREATE OR REPLACE FUNCTION public.post_requisites(db text, term_id int8, req_id int8, mods json default '{}', OUT newid int8, OUT res TEXT)
AS $$
DECLARE ord int8; i record; m int8;
BEGIN
	EXECUTE format('SELECT obj.id, newreq.id, max(concat(''0'', reqs.val)::NUMERIC), max(CASE WHEN reqs.t=newreq.id THEN reqs.id ELSE 0 END)
		FROM %s obj LEFT JOIN %s newreq ON newreq.id=%s AND newreq.up=obj.up AND newreq.t!=newreq.id
			LEFT JOIN (%s reqs CROSS JOIN %s defs) ON reqs.up=obj.id AND defs.id=reqs.t AND defs.t!=0
		WHERE obj.id=%s AND obj.up=0 AND obj.t!=obj.id
		GROUP BY 1, 2', db, db, req_id, db, db, term_id) into term_id, req_id, ord, newid;
	IF term_id IS NULL THEN res := 'err_term_not_found';
	ELSIF req_id IS NULL THEN res := 'err_req_not_found';
	ELSIF newid!=0 THEN res := 'warn_req_exists';
	ELSE
		EXECUTE format('INSERT INTO %s (up, t, val) VALUES (%s, %s, %s) RETURNING id', db, term_id, req_id, ord+1) into newid;
		FOR i IN (SELECT * FROM json_each(mods)) LOOP
			EXECUTE format('SELECT id FROM %s WHERE t=0 AND up=0 AND val ILIKE ''%s'' LIMIT 1', db, i.key) INTO m;
			IF m IS NOT NULL THEN
				EXECUTE format('INSERT INTO %s (up, t, val) VALUES (%s, %s, ''%s'')', db, newid, m, trim('"' FROM i.value::text));
			END IF;
		END LOOP;
		res := '1';
	END IF;
END;
$$ LANGUAGE plpgsql;

SELECT post_requisites('rep', 315, 45);

-- Create a reference to a term 
CREATE OR REPLACE FUNCTION public.post_references(db text, term_id int8, OUT newid int8, OUT res TEXT)
AS $$
declare i int;
BEGIN
	EXECUTE format('SELECT obj.id, ref.id FROM %s obj LEFT JOIN %s ref ON ref.up=0 AND ref.t=obj.id AND ref.val IS null
		WHERE obj.id=%s AND obj.id!=obj.t AND obj.up=0', db, db, term_id) into term_id, newid;
	IF term_id IS NULL THEN res := 'err_incorrect_term';
	ELSIF newid IS NOT NULL THEN res := 'warn_ref_exists';
	ELSE
		EXECUTE format('INSERT INTO %s (up, t, val) VALUES (0, %s, NULL) RETURNING id', db, term_id) into newid;
		res := '1';
	END IF;
END;
$$ LANGUAGE plpgsql;

SELECT post_references('rep', 43);

-- Change the term name or base type
CREATE OR REPLACE FUNCTION public.patch_terms(db text, term_id int8, value text, base int8, OUT exid int8, OUT res TEXT)
AS $$
BEGIN
	EXECUTE format('SELECT obj.id FROM %s obj, %s base WHERE obj.val ILIKE ''%s'' AND obj.up=0 AND base.t=obj.t AND base.id=base.t AND obj.id!=''%s'''
					, db, db, replace(value, '''', ''''''), term_id) into exid;
	IF exid IS NOT NULL THEN
		res := 'err_term_name_exists';
	ELSE
		EXECUTE format('UPDATE %s SET val=''%s'', t=%s WHERE id=%s', db, replace(value, '''', ''''''), base, term_id);
		res := '1';
	END IF;
END;
$$ LANGUAGE plpgsql;

SELECT patch_terms('rep', 315,'operation3', 3);
SELECT patch_terms('dup', 315,'operation3', 5);
SELECT patch_terms('rep', 316,'operation222', 3);

-- Delete the term, res
CREATE OR REPLACE FUNCTION public.delete_terms(db text, term_id int8, OUT res TEXT)
AS $$
DECLARE exid int8;
BEGIN
	EXECUTE format('SELECT id FROM %s WHERE t=%s LIMIT 1', db, term_id) into exid;
	IF exid IS NOT NULL THEN
		res := 'err_term_is_in_use';
	ELSE
		EXECUTE format('DELETE FROM %s WHERE id=%s RETURNING 1', db, term_id) into res;
		IF res IS NULL THEN
			res := 'err_term_not_found';
		END IF;
	END IF;
END;
$$ LANGUAGE plpgsql;

SELECT public.post_terms('rep', 'operatn143336', 3);
SELECT delete_terms('rep', 383662);
