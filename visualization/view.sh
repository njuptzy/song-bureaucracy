#!/usr/bin/env bash
# 便捷启动审查可视化：只给版本标签（= records 下的桶名），自动找桶里的结果库接入。
#
# 用法:
#   ./visualization/view.sh                      # 列出所有可用版本
#   ./visualization/view.sh <版本标签> [端口]    # 接入该版本并启动（端口默认 8642）
# 例:
#   ./visualization/view.sh v0613-v4-flash
#   ./visualization/view.sh v0614-v4-flash 8643
set -euo pipefail

# 切到仓库根（脚本在 visualization/ 下）
cd "$(dirname "$0")/.."
RECORDS="agent-v0612/records"

list_versions() {
  echo "可用版本（$RECORDS/ 下含 .db 的桶）："
  for d in "$RECORDS"/*/; do
    [ -d "$d" ] || continue
    tag=$(basename "$d")
    db=$(ls "$d"*.db 2>/dev/null | head -1)
    [ -n "$db" ] && printf "  %-20s → %s\n" "$tag" "$(basename "$db")"
  done
}

# 无参：列出可选版本
if [ $# -eq 0 ]; then
  echo "用法: ./visualization/view.sh <版本标签> [端口]"
  echo
  list_versions
  exit 0
fi

TAG="$1"
PORT="${2:-8642}"
DIR="$RECORDS/$TAG"

if [ ! -d "$DIR" ]; then
  echo "✗ 没有这个版本桶: $DIR"
  echo
  list_versions
  exit 1
fi

# 找桶里的 .db（桶内库文件名不统一，靠 glob 而非拼名字）
DBS=("$DIR"/*.db)
if [ ! -e "${DBS[0]}" ]; then
  echo "✗ 桶里没有 .db 文件: $DIR"
  exit 1
fi
if [ "${#DBS[@]}" -gt 1 ]; then
  echo "✗ 桶里有多个 .db，请改用 server.py --entry-db 明确指定其中一个："
  printf "  %s\n" "${DBS[@]}"
  exit 1
fi
DB="${DBS[0]}"

# 端口占用提示（不擅自杀进程）
if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "⚠️  端口 $PORT 已被占用。换个端口：./visualization/view.sh $TAG 8643"
  echo "    或先停掉占用进程：lsof -nP -iTCP:$PORT -sTCP:LISTEN"
  exit 1
fi

echo "版本: $TAG"
echo "接入: $DB"
echo "地址: http://127.0.0.1:$PORT"
exec python3 visualization/server.py --entry-db "$DB" --port "$PORT"
