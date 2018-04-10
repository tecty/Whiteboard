#!/bin/sh

# backup the database
mkdir -p db_bak 
cp db.sqlite3 db_bak/`date "+%Y-%m-%d"`.sqlite3

# update the programme 
git pull 
./manage.py migrate 

