SELECT obj.id, obj.val, obj.t base
FROM {db} obj WHERE obj.up=0 AND obj.id!=obj.t AND obj.val!='' AND obj.t!=0
AND NOT EXISTS (SELECT 1 FROM {db} oth LEFT JOIN {db} reqs ON reqs.up=oth.id AND reqs.t=obj.id AND oth.id!=obj.id WHERE oth.up=0 AND reqs.t=obj.id);