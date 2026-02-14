#!/bin/bash

if command -v gkg &> /dev/null; then
    echo "Starting GKG web UI on port 27495..."
    gkg server start --port 27495 &
    GKG_PID=$!
    echo "GKG web UI started (PID: $GKG_PID)"

    sleep 1
    echo "Starting socat proxy on 0.0.0.0:27496 -> localhost:27495..."
    socat TCP-LISTEN:27496,fork,reuseaddr,bind=0.0.0.0 TCP:localhost:27495 &
    echo "Socat proxy started"
fi

echo "Starting GKG API service on port 8003..."
exec uvicorn main:app --host 0.0.0.0 --port 8003
