SELECT a.id, a.val, a.t, a.up, typs.val AS typ_name, typs.t AS base_typ
FROM {db} a
JOIN {db} typs ON typs.id = a.t AND typs.up = 0
WHERE a.id = :object_id
