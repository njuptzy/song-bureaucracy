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

ssh "$remote_host" "install -d -m 0755 \
    '$remote_release/vis/ch2t7-design-vis/dist' \
    '$remote_release/vis/backend' \
    '$remote_release/data/database' \
    '$remote_release/vis/宋代职官体系可视化打包文件 /svg格式' \
    '$remote_release/vis/宋代职官体系可视化打包文件 /字体'"

rsync -a --delete "$repo_root/vis/ch2t7-design-vis/dist/" \
    "$remote_host:$remote_release/vis/ch2t7-design-vis/dist/"
rsync -a \
    "$repo_root/vis/ch2t7-design-vis/server.py" \
    "$repo_root/vis/ch2t7-design-vis/revision_store.py" \
    "$remote_host:$remote_release/vis/ch2t7-design-vis/"
rsync -a \
    "$repo_root/vis/backend/normalize_times.py" \
    "$repo_root/vis/backend/institution_categories.py" \
    "$remote_host:$remote_release/vis/backend/"
rsync -a \
    "$repo_root/data/database/song_bureaucracy_entries_ch2t7.db" \
    "$repo_root/data/database/song_bureaucracy_dictionary_ch2t7.db" \
    "$remote_host:$remote_release/data/database/"
rsync -a \
    "$repo_root/vis/宋代职官体系可视化打包文件 /svg格式/宋代职官体系可视化界面_画板 1 副本 4-01.svg" \
    "$repo_root/vis/宋代职官体系可视化打包文件 /svg格式/宋代职官体系可视化界面_画板 1 副本 4-02.svg" \
    "$repo_root/vis/宋代职官体系可视化打包文件 /svg格式/宋代职官体系可视化界面字体转曲_画板 1 副本 4-01.svg" \
    "$remote_host:$remote_release/vis/宋代职官体系可视化打包文件 /svg格式/"
rsync -a \
    "$repo_root/vis/宋代职官体系可视化打包文件 /字体/FZQingKBYSJW-M.TTF" \
    "$repo_root/vis/宋代职官体系可视化打包文件 /字体/AdobeSongStd-Light.otf" \
    "$remote_host:$remote_release/vis/宋代职官体系可视化打包文件 /字体/"

ssh "$remote_host" "find '$remote_release' -type d -exec chmod 0755 {} +; \
    find '$remote_release' -type f -exec chmod 0644 {} +; \
    ln -sfn '$remote_release' /opt/song-bureaucracy/current"

printf 'release=%s\n' "$release_id"
