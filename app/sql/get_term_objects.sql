SELECT row_number() OVER() AS ord, vals.id, vals.t, vals.val, vals.up
FROM {db} vals
WHERE vals.t = {term_id} AND vals.up = {parent_id}
ORDER BY vals.val
LIMIT 20 OFFSET 0;
