#!/usr/bin/env bash
source .venv/bin/activate
uvicorn backend.app:app --host 0.0.0.0 --port 8001 --reload
