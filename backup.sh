#!/bin/sh
mkdir -p db_bak 
cp db.sqlite3 db_bak/`date "+%Y-%m-%d"`.sqlite3
