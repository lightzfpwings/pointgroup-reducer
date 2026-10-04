#!/bin/bash
ROOT="$(cd "$(dirname "$0")" && pwd)"
# Use a writable, predictable export directory instead of a read-only app bundle.
EXPORTS="$HOME/Documents/PointGroupReducer"
mkdir -p "$EXPORTS" || exit 1
cd "$EXPORTS" || exit 1
export PYTHONUTF8=1
"$ROOT/CLI/PointGroupReducer-CLI" "$@"
status=$?
if [[ $status -ne 0 ]]; then
    echo "程序退出码：$status"
    read -r -p '按回车关闭此窗口…' _
fi
exit "$status"

