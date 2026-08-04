#!/usr/bin/env bash
# Versioned runner for agent-v0612.
#
# 常用示例：
#   ./run.sh --tag v0613-test --model google/gemini-2.5-flash --limit 20
#   ./run.sh --tag v0613-test --model deepseek/deepseek-chat --start 20 --limit 80
#   ./run.sh --tag v0613-test --entries "河北兵马大元帅-482,都督府-483"
#   ./run.sh --tag v0613-test --out records/v0613-test --background --yes
#
# 兼容旧用法：
#   ./run.sh v0613-test deepseek/deepseek-chat

set -euo pipefail

CALLER_DIR="$(pwd)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

usage() {
  cat <<'EOF'
用法:
  ./run.sh --tag <版本标签> [选项]
  ./run.sh <版本标签> [模型ID]                 # 兼容旧用法

核心选项:
  -t, --tag TAG          版本标签，例如 v0613-v5-flash
  -p, --provider NAME    切换 .env 里的 LLM provider profile（deepseek/openrouter/volcengine/...）
  -m, --model MODEL      覆盖该 provider 的默认模型 ID
  -o, --out DIR          输出目录，默认 records/<TAG>
      --db PATH          结果 SQLite 路径，默认 <OUT>/song_bureaucracy_entries_<TAG>.db
      --log PATH         日志路径，默认 <OUT>/run.log

跑哪些词条:
      --start N          从辞典索引第 N 条开始，0-based，默认 0
      --limit N          跑 N 条，默认 25；传 all 表示从 start 跑到末尾
      --end N            跑到第 N 条之前，0-based exclusive；优先于 --limit
      --entries LIST     精确指定词条，逗号分隔，例如 "河北兵马大元帅-482,都督府-483"

运行方式:
      --background       后台 nohup 运行，输出 PID
      --fresh            若结果库已存在，先删除旧结果库和旧 records_*.json
  -y, --yes              结果库已存在时不交互，直接叠加继续
      --dry-run          只打印将要使用的配置，不启动
  -h, --help             显示帮助

输出目录中会包含:
  song_bureaucracy_entries_<TAG>.db
  records_*.json
  failed_entries.json
  run.log
EOF
}

cd "$SCRIPT_DIR"

TAG=""
MODEL=""
PROVIDER=""
OUT_DIR=""
DB_PATH=""
LOG_PATH=""
START="0"
LIMIT="25"
END=""
ENTRIES=""
BACKGROUND=0
FRESH=0
YES=0
DRY_RUN=0

# 兼容旧用法：./run.sh TAG [MODEL]
if [ "${1:-}" != "" ] && [ "${1#-}" = "$1" ]; then
  TAG="$1"
  shift
  if [ "${1:-}" != "" ] && [ "${1#-}" = "$1" ]; then
    MODEL="$1"
    shift
  fi
fi

while [ "$#" -gt 0 ]; do
  case "$1" in
    -t|--tag)
      TAG="${2:?--tag 需要参数}"
      shift 2
      ;;
    -m|--model)
      MODEL="${2:?--model 需要参数}"
      shift 2
      ;;
    -p|--provider)
      PROVIDER="${2:?--provider 需要参数}"
      shift 2
      ;;
    -o|--out|--output-dir)
      OUT_DIR="${2:?--out 需要参数}"
      shift 2
      ;;
    --db|--entry-db)
      DB_PATH="${2:?--db 需要参数}"
      shift 2
      ;;
    --log)
      LOG_PATH="${2:?--log 需要参数}"
      shift 2
      ;;
    --start)
      START="${2:?--start 需要参数}"
      shift 2
      ;;
    --limit)
      LIMIT="${2:?--limit 需要参数}"
      shift 2
      ;;
    --end)
      END="${2:?--end 需要参数}"
      shift 2
      ;;
    --entries)
      ENTRIES="${2:?--entries 需要参数}"
      shift 2
      ;;
    --background|--bg)
      BACKGROUND=1
      shift
      ;;
    --fresh)
      FRESH=1
      shift
      ;;
    -y|--yes)
      YES=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "未知参数: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -z "$TAG" ]; then
  echo "缺少版本标签。请使用 --tag <版本标签>。" >&2
  usage >&2
  exit 2
fi

resolve_path() {
  case "$1" in
    /*) printf '%s\n' "$1" ;;
    *) printf '%s\n' "$CALLER_DIR/$1" ;;
  esac
}

if [ -z "$OUT_DIR" ]; then
  OUT_DIR_ABS="$SCRIPT_DIR/records/$TAG"
else
  OUT_DIR_ABS="$(resolve_path "$OUT_DIR")"
fi
mkdir -p "$OUT_DIR_ABS"

DB_PATH="${DB_PATH:-$OUT_DIR_ABS/song_bureaucracy_entries_${TAG}.db}"
LOG_PATH="${LOG_PATH:-$OUT_DIR_ABS/run.log}"
DB_PATH="$(resolve_path "$DB_PATH")"
LOG_PATH="$(resolve_path "$LOG_PATH")"
mkdir -p "$(dirname "$DB_PATH")" "$(dirname "$LOG_PATH")"

export SONG_RUN_TAG="$TAG"
export SONG_OUTPUT_DIR="$OUT_DIR_ABS"
export SONG_ENTRY_DB_PATH="$DB_PATH"
export SONG_ENTRY_START="$START"
export SONG_ENTRY_LIMIT="$LIMIT"
# 固定每次批跑的上下文策略，避免继承上一轮 shell。完整实体/辞典索引保留，
# 已加载实体中的长引文与较早 CoT 默认压缩，减少重复 token。
export SONG_COMPACT_CONTEXT=0
export SONG_COMPACT_ENTITY_INDEX="${SONG_COMPACT_ENTITY_INDEX:-0}"
export SONG_COMPACT_ENTITY_DETAILS="${SONG_COMPACT_ENTITY_DETAILS:-1}"
export SONG_COMPACT_HISTORY="${SONG_COMPACT_HISTORY:-1}"
export SONG_COMPACT_DICT_INDEX="${SONG_COMPACT_DICT_INDEX:-0}"
[ -n "$END" ] && export SONG_ENTRY_END="$END" || unset SONG_ENTRY_END || true
[ -n "$ENTRIES" ] && export SONG_TODO_ENTRIES="$ENTRIES" || unset SONG_TODO_ENTRIES || true
# --provider 切换 .env 里的 LLM profile（agent.py / SimpleLLMClient 内部
# 通过 LLM_PROFILE 决定读哪一组 <PROFILE>_API_KEY/_BASE_URL/_MODEL/_MAX_TOKENS）。
[ -n "$PROVIDER" ] && export LLM_PROFILE="$PROVIDER"
# --model 临时覆盖当前 profile 的模型 ID（写到 <PROFILE>_MODEL）。
if [ -n "$MODEL" ]; then
  active_profile_upper=$(echo "${LLM_PROFILE:-$(grep -E '^LLM_PROFILE=' .env 2>/dev/null | cut -d= -f2-)}" | tr '[:lower:]' '[:upper:]')
  active_profile_upper="${active_profile_upper:-OPENROUTER}"
  export "${active_profile_upper}_MODEL=$MODEL"
fi
export PYTHONUNBUFFERED=1

active_profile_show="${LLM_PROFILE:-$(grep -E '^LLM_PROFILE=' .env 2>/dev/null | cut -d= -f2-)}"
active_profile_show="${active_profile_show:-deepseek}"
active_profile_upper_show=$(echo "$active_profile_show" | tr '[:lower:]' '[:upper:]')

echo "版本标签: $SONG_RUN_TAG"
if [ "${USE_KIMI_CLI:-}" = "1" ]; then
  echo "Provider: kimi-cli 子进程"
  echo "模型:     ${KIMI_CLI_MODEL:-kimi-cli 默认 = kimi-code/kimi-for-coding}"
else
  effective_model=$(eval echo "\${${active_profile_upper_show}_MODEL:-}")
  [ -z "$effective_model" ] && effective_model=$(grep -E "^${active_profile_upper_show}_MODEL=" .env 2>/dev/null | cut -d= -f2-)
  echo "Provider: $active_profile_show"
  echo "模型:     ${effective_model:-（.env 未配置 ${active_profile_upper_show}_MODEL）}"
fi
echo "输出目录: $SONG_OUTPUT_DIR"
echo "结果库:   $SONG_ENTRY_DB_PATH"
echo "日志:     $LOG_PATH"
echo "压缩:     selective (ENTITY_INDEX=$SONG_COMPACT_ENTITY_INDEX, ENTITY_DETAILS=$SONG_COMPACT_ENTITY_DETAILS, HISTORY=$SONG_COMPACT_HISTORY, DICT_INDEX=$SONG_COMPACT_DICT_INDEX)"
if [ -n "$ENTRIES" ]; then
  echo "词条:     $ENTRIES"
else
  if [ -n "$END" ]; then
    echo "范围:     [$START:$END]"
  else
    echo "范围:     start=$START limit=$LIMIT"
  fi
fi
echo "后台:     $BACKGROUND"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "dry-run: 不启动。"
  exit 0
fi

if [ "$FRESH" -eq 1 ]; then
  echo "fresh: 删除旧结果库和旧记录文件"
  rm -f "$SONG_ENTRY_DB_PATH"
  rm -f "$SONG_OUTPUT_DIR"/records_*.json "$SONG_OUTPUT_DIR"/failed_entries.json
fi

if [ -f "$SONG_ENTRY_DB_PATH" ] && [ "$YES" -ne 1 ]; then
  if [ "$BACKGROUND" -eq 1 ]; then
    echo "结果库已存在，后台模式不能交互确认。请加 --yes 叠加，或加 --fresh 重跑。" >&2
    exit 1
  fi
  echo "结果库已存在。继续会在现有数据上叠加："
  echo "  $SONG_ENTRY_DB_PATH"
  read -r -p "仍要继续（叠加）吗？[y/N] " ans
  [ "$ans" = "y" ] || { echo "已取消。"; exit 1; }
fi

python3 - "$SONG_ENTRY_DB_PATH" <<'PY'
import sys
from pathlib import Path

db_path = Path(sys.argv[1])
lock_path = Path(str(db_path) + ".agent.lock")
lock_path.parent.mkdir(parents=True, exist_ok=True)
lock_file = open(lock_path, "a+", encoding="utf-8")
try:
    import fcntl
    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    lock_file.seek(0)
    holder = lock_file.read().strip()
    print("结果库正在被另一个 agent 进程占用，拒绝启动。", file=sys.stderr)
    print(f"Entry DB: {db_path}", file=sys.stderr)
    print(f"Lock: {lock_path}", file=sys.stderr)
    if holder:
        print("当前锁信息:", file=sys.stderr)
        print(holder, file=sys.stderr)
    print("请先结束旧进程，或换一个 --db/--out 后再启动。", file=sys.stderr)
    sys.exit(1)
PY

: > "$LOG_PATH"

if [ "$BACKGROUND" -eq 1 ]; then
  nohup python3 -u agent.py > "$LOG_PATH" 2>&1 &
  pid=$!
  echo "已后台启动 PID=$pid"
  echo "实时看日志："
  echo "  tail -f \"$LOG_PATH\""
else
  python3 -u agent.py 2>&1 | tee "$LOG_PATH"
fi
