SELECT CASE WHEN typs.up=0 THEN '' ELSE reqs.val END req_val
, typs.id req_t, typs.val refr
, sum(CASE WHEN typs.up=0 THEN 1 END) arr_num
  FROM {db} reqs JOIN {db} typs ON typs.id=reqs.t and typs.id in({array_ids})
  WHERE reqs.up={obj_id}
  GROUP BY req_val, req_t, refr;