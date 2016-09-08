#!/bin/sh
export FLASK_APP=rfmembers.py
export FLASK_DEBUG=1
flask "$@"

