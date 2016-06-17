#!/usr/bin/env bash
export GALAXY_ENV=production-sdi

cd /opt/pygalaxy

python webapp.py 1> pygalaxy.log 2>&1 &
