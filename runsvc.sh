#!/bin/bash
alias python=python3|true
python -m venv localvenv
source localvenv/bin/activate
python -m pip install .
uvicorn fastapppkg.restapi.rootsvc:app --host 0.0.0.0 --port 8001