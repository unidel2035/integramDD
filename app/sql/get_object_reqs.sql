SELECT reqs.val req_val, typs.id req_t, typs.val refr, '' arr_num
  FROM {db} reqs JOIN {db} typs ON typs.id=reqs.t
  WHERE reqs.up={term_id};