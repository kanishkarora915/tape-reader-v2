#!/bin/bash
echo "=== Building React frontend ==="
npm install
npm run build
echo "=== Installing Python dependencies ==="
pip install -r backend/requirements.txt
echo "=== Build complete ==="
