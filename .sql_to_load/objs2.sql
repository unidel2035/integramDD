-- Validations: Object uinquity and non-empty value
-- Parametes validated and formatted in the backend
-- Attrs set and their types: base type, reference, array
-- Parent: 1 for independent or the existing object as parent that have such term as requisite
SELECT array_agg(distinct mod_def.val) filter (where mod_def.val is not null) modifiers
  FROM rep obj
  	LEFT JOIN rep req ON obj.t=req.up AND req.t=48 /* тип реквизита {id} */
  	LEFT JOIN (rep mods CROSS JOIN rep mod_def) ON mods.up=req.id
AND mod_def.id=mods.t
  WHERE obj.id=254 /* id объекта {up} */ and req.up is not NULL;

-- Value is not empty - rechecked in the function, too
CREATE OR REPLACE FUNCTION public.post_objects(db text, up int8, type int8, attrs json, OUT newid int8, OUT res TEXT)
AS $$
DECLARE i record;
		reqs json;
		val text;
BEGIN
	val := COALESCE(replace(attrs->>('t'||type), '''', ''''''), ''); -- Object value
	IF val='' THEN
		res := 'err_empty_val';
		RETURN;
	END IF;
	-- Validate the type and get its modifiers
	EXECUTE format('SELECT obj.t, obj.up, json_object_agg(COALESCE(def.val, ''''), mods.val) mods'
				||' FROM %s base, %s obj LEFT JOIN (%s mods CROSS JOIN %s def) ON mods.up=obj.id AND def.id=mods.t AND def.up=0 AND def.t=0'
				||' WHERE obj.id=%s AND obj.up=0 AND base.id=obj.t AND base.t=base.id GROUP BY 1, 2', db, db, db, db, type) into i;
	-- Check if the value must be unique
	IF i IS NULL THEN
		res := 'err_type_not_found';
		RETURN;
	ELSIF i.mods->'UNIQUE' IS NOT NULL THEN
		EXECUTE format('SELECT id FROM %s WHERE t=%s AND val=''%s'' AND up=%s LIMIT 1', db, type, val, up) into newid;
		IF newid IS NOT NULL THEN
			res := 'err_non_unique_val';
			RETURN;
		END IF;
	END IF;
	EXECUTE format('INSERT INTO %s (up, t, val) VALUES (%s, %s, ''%s'') RETURNING id', db, up, type, val) into newid;
	-- Get the requisites
	EXECUTE format('SELECT json_object_agg(req.id, (''{"ord":"''||req.val||''","t":''||req.t||'',"base":''||base.t
							||'',"ref":''||CASE WHEN base.id=base.t THEN 0 ELSE typ.t END||''}'')::json)
					FROM %s req JOIN %s typ ON typ.id=req.t JOIN %s base ON base.id=typ.t
					WHERE req.up=%s', db, db, db, type) INTO reqs;
	-- Create the requisites
	FOR i IN (SELECT * FROM json_each(reqs)) LOOP
		-- raise notice '%(%) %', i.key, reqs->i.key->'base', reqs->i.key->'ref';
		val := COALESCE(replace(attrs->>('t'||i.key), '''', ''''''), '');
		IF val='' THEN -- Empty val, skip it
			CONTINUE;
		ELSIF (reqs->i.key->>'ref')::int=0 THEN -- it's not a Ref
			EXECUTE format('INSERT INTO %s (up, t, val) VALUES (%s, %s, ''%s'')', db, newid, i.key, val);
		ELSE -- This is a ref - check if the referenced id is valid
			EXECUTE format('SELECT id FROM %s WHERE t=%s AND id=%s', db, reqs->i.key->'ref', val) into val;
			IF val IS NULL THEN
				res := 'err_invalid_ref '||val;
				RETURN;
			END IF;
			-- Reference value is stored as Typ, while Type goes to Value
			EXECUTE format('INSERT INTO %s (up, t, val) VALUES (%s, %s, ''%s'')', db, newid, val, i.key);
		END IF;
	END LOOP;
	res := '1';
END;
$$ LANGUAGE plpgsql;

SELECT post_objects('dup', 1, 101, '{"t101":"Ellipse","t110":"19990820","t110":"Мира, 1","t112":114}');

-- Validations: Object uinquity and non-empty value
-- Attrs types are validated and formatted in the backend
CREATE OR REPLACE FUNCTION public.patch_object(db text, id int8, attrs json, OUT res TEXT)
AS $$
DECLARE i record;
		reqs json;
		typ text;
		val text;
		new_val text;
BEGIN
	-- Get the object type along with its modifiers
	EXECUTE format('SELECT obj.t, obj.up, obj.val, json_object_agg(COALESCE(def.val, ''''), mods.val) mods'
				||' FROM %s obj LEFT JOIN (%s mods CROSS JOIN %s def) ON mods.up=obj.t AND def.id=mods.t AND def.up=0 AND def.t=0'
				||' WHERE obj.id=%s GROUP BY 1, 2, 3', db, db, db, id) into i;
	typ := i.t;
	val := COALESCE(replace(i.val, '''', ''''''), ''); -- Current object value
	new_val := COALESCE(replace(attrs->>('t'||i.t), '''', ''''''), '');
	IF new_val='' THEN
		res := 'err_empty_val';
		RETURN;
	END IF;
	-- Check if the value must be unique in case it's going to change
	IF new_val!=val AND i.mods->'UNIQUE' IS NOT NULL THEN
		EXECUTE format('SELECT id FROM %s WHERE t=%s AND val=''%s'' AND up=%s AND id!=%s', db, typ, new_val, i.up, id) into i;
		IF i.id IS NOT NULL THEN
			res := 'err_non_unique_val '||id||' -> '||i.id;
			RETURN;
		END IF;
	END IF;
	-- Update the object value
	IF new_val!=val THEN
		EXECUTE format('UPDATE %s SET val=''%s'' WHERE id=%s', db, new_val, id);
	END IF;
	-- Get the requisites
	EXECUTE format('SELECT json_object_agg(req.id, (''{"ord":"''||req.val||''","id":''||COALESCE(vals.id, 0)||'',"t":''||req.t||'',"base":''||base.t
						||'',"ref":''||CASE WHEN base.id=base.t THEN 0 ELSE typ.t END||'',"ref_id":''||COALESCE(vals.t, 0)
						||'',"val":"''||trim(''"'' FROM COALESCE(vals.val, ''''))||''"''||''}'')::json)'
					||' FROM %s req JOIN %s typ ON typ.id=req.t JOIN %s base ON base.id=typ.t'
						||' LEFT JOIN %s vals ON vals.up=%s AND CASE WHEN base.id=base.t THEN vals.t=req.id ELSE vals.val=req.id::text END'
					||' WHERE req.up=%s', db, db, db, db, id, typ) INTO reqs;
	FOR i IN (SELECT * FROM json_each(reqs)) LOOP
		-- raise notice '%(%) val=% t=% ref=%', i.key, reqs->i.key->'base', reqs->i.key->'val', reqs->i.key->'ref', reqs->i.key->'ref_id';
		IF attrs->>('t'||i.key) IS NULL THEN
			CONTINUE; -- No value for this req
		END IF;
		-- Update the requisite if exists, otherwise - create one
		new_val := replace(attrs->>('t'||i.key), '''', '''''');
		IF new_val='' THEN -- Drop the requisite value
			IF reqs->i.key->'id' IS NOT NULL THEN -- if any
				EXECUTE format('DELETE FROM %s WHERE id=%s', db, reqs->i.key->'id');
			END IF;
		ELSIF (reqs->i.key->>'ref')::int=0 THEN -- it's not a Ref
			IF reqs->i.key->>'val'='' THEN -- no requisite yet - create
				EXECUTE format('INSERT INTO %s (up, t, val) VALUES (%s, %s, ''%s'')', db, id, i.key, new_val);
			ELSIF reqs->i.key->>'val'!=new_val THEN -- update the requisite
				EXECUTE format('UPDATE %s SET val=''%s'' WHERE id=%s', db, new_val, reqs->i.key->'id');
			END IF;
		ELSE -- This is a ref - check if the referenced id is valid
			EXECUTE format('SELECT id FROM %s WHERE t=%s AND id=%s', db, reqs->i.key->'ref', new_val) into val;
			IF val IS NULL THEN
				res := 'err_invalid_ref '||new_val;
				RETURN;
			END IF;
			-- Reference value is stored as Typ, while Type goes to Value
			IF reqs->i.key->>'val'='' THEN -- Create a Ref requisite
				EXECUTE format('INSERT INTO %s (up, t, val) VALUES (%s, %s, ''%s'')', db, id, new_val, i.key);
			ELSIF reqs->i.key->>'t'!=new_val THEN
				EXECUTE format('UPDATE %s SET t=%s, val=''%s'' WHERE id=%s', db, new_val, i.key, reqs->i.key->>'id');
			END IF;
		END IF;
	END LOOP;
	res := '1';
END;
$$ LANGUAGE plpgsql;

BEGIN;
SELECT patch_object('dup', 112, '{"t101":"H&H","t111":"77","t108":"770007777","t109":"20120823","t110":"Ленина, 22"}');
COMMIT;

CREATE OR REPLACE FUNCTION public.delete_object_rec(db text, ids text) RETURNS void
AS $$
DECLARE i record;
BEGIN
	EXECUTE format('SELECT string_agg(id::text, '','') ids FROM %s WHERE up IN(%s)', db, ids) into i;
	IF i.ids IS NOT NULL THEN
		PERFORM delete_object_rec(db, i.ids);
	END IF;
	EXECUTE format('DELETE FROM %s WHERE id IN(%s)', db, ids);
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION public.delete_object(db text, id int8, OUT res TEXT)
AS $$
DECLARE i record;
BEGIN
	-- Check the dependencies
	EXECUTE format('SELECT obj.up up, par.up pup, count(r.id) cnt'
					||' FROM %s obj LEFT JOIN %s r ON r.t=obj.id JOIN %s par ON par.id=obj.up'
					||' WHERE obj.id=%s group by 1, 2', db, db, db, id) into i;
	IF i IS NULL THEN
		res := 'err_obj_not_found';
	ELSIF i.pup = 0 OR i.up = 0 THEN
		res := 'err_is_metadata';
	ELSIF i.cnt > 0 THEN
		res := 'err_is_referenced '||i.cnt;
	ELSE
		PERFORM delete_object_rec(db, id::text);
		EXECUTE format('DELETE FROM %s WHERE id=%s', db, id);
		res := '1';
	END IF;
END;
$$ LANGUAGE plpgsql;

SELECT delete_object_rec('dup', '131');
SELECT delete_object('dup', 125);

SELECT string_agg(id::text, ',') ids FROM dup WHERE up IN(101);

