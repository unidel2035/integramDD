SELECT obj.id AS object_id, vals.t AS req_t, refs.id AS ref_id, refs.val AS ref_val
FROM {db} obj
JOIN {db} vals ON vals.up = obj.id AND vals.val ~ '^\d+$'
JOIN {db} refs ON refs.id = vals.val::bigint AND refs.t = refs.id
WHERE obj.t = {term_id} AND obj.up = {parent_id};