SELECT obj.id,
       CASE WHEN refs.id IS NULL THEN obj.val ELSE CONCAT('-> ', refs.val) END AS obj,
       obj.t AS base,
       refs.id AS ref_id,
       refs.t AS ref_base,
       ARRAY_AGG(DISTINCT CONCAT(obj_mod_defs.val, ' ', obj_mods.val))
           FILTER (WHERE obj_mods.t IS NOT NULL) AS obj_mods,
       reqs.id AS req_id,
       reqs.val AS ord,
       reqs.t AS req_t,
       req_defs.val AS req_val,
       ref_reqs.val AS ref_val,
       req_defaults.val AS default_val,
       ARRAY_AGG(DISTINCT CONCAT(mod_defs.val, ' ', mods.val))
           FILTER (WHERE mods.t != 0) AS mods
FROM {db} obj
LEFT JOIN ({db} reqs CROSS JOIN {db} req_defs)
    ON reqs.up = obj.id AND req_defs.id = reqs.t AND req_defs.t != 0
LEFT JOIN {db} req_defaults
    ON req_defaults.up = reqs.id AND req_defaults.t = 0
LEFT JOIN {db} ref_reqs
    ON ref_reqs.id = req_defs.t AND ref_reqs.t != ref_reqs.id
LEFT JOIN {db} refs
    ON refs.id = obj.t AND refs.t != refs.id
LEFT JOIN ({db} obj_mods CROSS JOIN {db} obj_mod_defs)
    ON obj_mods.up = obj.id AND obj_mod_defs.id = obj_mods.t AND obj_mod_defs.t = 0
LEFT JOIN ({db} mods CROSS JOIN {db} mod_defs)
    ON mods.up = reqs.id AND mod_defs.id = mods.t AND obj_mod_defs.t = 0
WHERE obj.up = 0 AND obj.id != obj.t AND obj.id = {term_id} AND obj.t != 0
GROUP BY obj.id, obj, base, ref_id, req_id, req_t, ref_base, req_defs.val, ref_reqs.val, default_val
ORDER BY ord;