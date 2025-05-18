export PGPASSWORD='postgres';
psql -h localhost -U postgres -d integram -f ./objs2.sql
psql -h localhost -U postgres -d integram -f ./terms6.sql