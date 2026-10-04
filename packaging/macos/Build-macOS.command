#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-build.txt
.venv/bin/python packaging/build_native.py
open release
read -r -p '按回车关闭…' _

