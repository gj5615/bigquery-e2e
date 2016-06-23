#!/usr/bin/env bash
ymd=$(date +%Y%m%d)
seperator=$(echo -en '\x01')
bq load --nosync --field_delimiter=${seperator} --encoding=UTF-8 scratch.cmdhist_$ymd history.txt "cmd"

