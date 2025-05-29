SELECT 
    CASE WHEN typs.up = 0 THEN 0 ELSE reqs.id END AS req_id,
    CASE WHEN typs.up = :type_id THEN reqs.val ELSE '' END AS req_val,
    CASE WHEN typs.up = :type_id OR typs.up = 0 THEN '' ELSE reqs.val END AS ref_t,
    typs.id AS t,
    SUM(CASE WHEN typs.up = 0 THEN 1 ELSE 0 END) AS arr_num,
    origs.t AS bt,
    typs.val AS ref_val
FROM {db} reqs
JOIN {db} typs ON typs.id = reqs.t
LEFT JOIN {db} origs ON origs.id = typs.t
WHERE reqs.up = :object_id
GROUP BY req_id, req_val, typs.id, origs.t, typs.val, ref_t
