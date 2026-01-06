#!/usr/bin/env bash
set -e

# ===== 项目根目录 =====
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "==> Enter frontend"
cd "$ROOT_DIR/span_picker/frontend"

echo "==> npm install"
npm install

echo "==> build frontend"
npm run build

echo "==> back to root"
cd "$ROOT_DIR"

echo "==> export env"
export SPAN_PICKER_DEV=1

echo "==> install requirements"
pip install -r requirement.txt

