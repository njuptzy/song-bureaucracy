#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/../.." && pwd)"
remote_host="${SONG_DEPLOY_HOST:-pkuvis}"
release_id="${SONG_RELEASE_ID:-$(date +%Y%m%d-%H%M%S)}"
remote_release="/opt/song-bureaucracy/releases/${release_id}"

cd "$repo_root/vis/ch2t7-design-vis"
if command -v pnpm >/dev/null 2>&1; then
    pnpm build
else
    node node_modules/vite/bin/vite.js build
fi

ssh "$remote_host" "install -d -m 0755 '$remote_release'"

# tar 流完整保留设计资源目录名末尾的空格，避免远端 shell 二次拆词。
tar -C "$repo_root" -cf - \
    vis/ch2t7-design-vis/dist \
    vis/ch2t7-design-vis/server.py \
    vis/ch2t7-design-vis/revision_store.py \
    vis/backend/normalize_times.py \
    vis/backend/institution_categories.py \
    data/database/song_bureaucracy_entries_ch1t12.db \
    data/database/song_bureaucracy_dictionary_ch1t12.db \
    "vis/宋代职官体系可视化打包文件 /svg格式/宋代职官体系可视化界面_画板 1 副本 4-01.svg" \
    "vis/宋代职官体系可视化打包文件 /svg格式/宋代职官体系可视化界面_画板 1 副本 4-02.svg" \
    "vis/宋代职官体系可视化打包文件 /svg格式/宋代职官体系可视化界面字体转曲_画板 1 副本 4-01.svg" \
    "vis/宋代职官体系可视化打包文件 /字体/FZQingKBYSJW-M.TTF" \
    "vis/宋代职官体系可视化打包文件 /字体/AdobeSongStd-Light.otf" \
    | ssh "$remote_host" "tar -C '$remote_release' -xf -"

ssh "$remote_host" "find '$remote_release' -type d -exec chmod 0755 {} +; \
    find '$remote_release' -type f -exec chmod 0644 {} +; \
    ln -sfn '$remote_release' /opt/song-bureaucracy/current"

printf 'release=%s\n' "$release_id"
