#!/bin/bash
source "$(pwd)/myenv/bin/activate"
echo "starting server"
uvicorn server:app --port 5500 --host 0.0.0.0 --reload
