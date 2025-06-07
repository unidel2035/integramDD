SELECT reqs.t AS req_t, obj.id AS object_id, COUNT(*) AS count
FROM {db} obj
JOIN {db} arr ON arr.up = obj.id
JOIN {db} reqs ON reqs.up = obj.t AND reqs.t = arr.t
WHERE obj.t = {term_id} AND obj.up = {parent_id}
GROUP BY reqs.t, obj.id;