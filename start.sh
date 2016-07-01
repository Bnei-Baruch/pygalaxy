#!/usr/bin/env bash

export GALAXY_ENV=production-sdi
export GST_DEBUG="*:2"

cd /opt/pygalaxy
python webapp.py
