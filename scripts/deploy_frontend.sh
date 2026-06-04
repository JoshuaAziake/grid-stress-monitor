#!/bin/bash
set -e

REPO_FRONTEND="/home/joshua/grid-stress-monitor/frontend"
SERVE_FRONTEND="/srv/grid-stress-monitor/frontend"

sudo cp "$REPO_FRONTEND/index.html" "$SERVE_FRONTEND/index.html"
echo "Deployed frontend to $SERVE_FRONTEND"
