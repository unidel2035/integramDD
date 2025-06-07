SELECT obj.id AS object_id, vals.t AS req_t, vals.val AS value
FROM {db} obj
JOIN {db} vals ON vals.up = obj.id
WHERE obj.t = {term_id} AND obj.up = {parent_id};