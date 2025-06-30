SELECT row_number() OVER() ord, vals.id, vals.t, vals.val, vals.up 
  FROM {db} vals
  {joins}
  WHERE vals.t={term_id} AND vals.up={parent_id}
    {where_clauses}
  ORDER BY vals.t, lower(left(vals.val, 127))
  LIMIT {limit} OFFSET {offset};