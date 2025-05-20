#!/bin/bash

while getopts u:p:d: flag; do
  case "${flag}" in
    u) DB_USER=${OPTARG} ;;
    p) DB_PASS=${OPTARG} ;;
    d) DB_NAME=${OPTARG} ;;
  esac
done

if [[ -z "$DB_USER" || -z "$DB_PASS" || -z "$DB_NAME" ]]; then
  echo "Usage: $0 -u <user> -p <password> -d <database>"
  exit 1
fi

export PGPASSWORD="$DB_PASS"

psql -h localhost -U "$DB_USER" -d "$DB_NAME" -f ./objs2.sql
psql -h localhost -U "$DB_USER" -d "$DB_NAME" -f ./terms6.sql
