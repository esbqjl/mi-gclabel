#!/usr/bin/env bash
set -e
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# 先确保 dist 存在（可选）
cd "$ROOT_DIR/span_picker/frontend"
npm ci
npm run build

cd "$ROOT_DIR"
unset SPAN_PICKER_DEV
nohup streamlit run label_system.py --server.address 0.0.0.0 --server.port 8501 > streamlit.log 2>&1 &
