#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

cd "$ROOT_DIR/span_picker/frontend"

nohup npm run dev > frontend.log 2>&1 &

cd "$ROOT_DIR"

export SPAN_PICKER_DEV=1
nohup streamlit run app.py > streamlit.log 2>&1 &
