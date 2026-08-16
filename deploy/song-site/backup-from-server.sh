#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "$0")/../.." && pwd)"
remote_host="${SONG_DEPLOY_HOST:-pkuvis}"
backup_dir="${SONG_BACKUP_DIR:-$repo_root/data/server-latest}"
remote_tmp="$(ssh "$remote_host" 'mktemp -d /tmp/song-bureaucracy-backup.XXXXXX')"
staging_dir="${backup_dir}.tmp.$$"
old_dir="${backup_dir}.old.$$"

cleanup() {
    ssh "$remote_host" "rm -rf -- '$remote_tmp'" >/dev/null 2>&1 || true
    rm -rf -- "$staging_dir" "$old_dir"
}
trap cleanup EXIT

mkdir -p "$staging_dir"
mkdir -p "$staging_dir/code"

# 同步当前运行 release 的代码和设计素材；不包含服务器正式数据库。
ssh "$remote_host" "tar -C /opt/song-bureaucracy/current -cf - vis" \
    | tar -C "$staging_dir/code" -xf -

# SQLite .backup 在服务器端生成一致快照，避免直接复制正在写入的主库。
ssh "$remote_host" "set -e
sqlite3 /var/lib/song-bureaucracy/song_bureaucracy_entries_ch1t12.db '.backup $remote_tmp/song_bureaucracy_entries_ch1t12.db'
sqlite3 /var/lib/song-bureaucracy/song_bureaucracy_dictionary_ch1t12.db '.backup $remote_tmp/song_bureaucracy_dictionary_ch1t12.db'
sqlite3 /var/lib/song-bureaucracy/song_bureaucracy_entries_ch1t12.revisions.db '.backup $remote_tmp/song_bureaucracy_entries_ch1t12.revisions.db'
"

scp -q "$remote_host:$remote_tmp/song_bureaucracy_entries_ch1t12.db" "$staging_dir/"
scp -q "$remote_host:$remote_tmp/song_bureaucracy_dictionary_ch1t12.db" "$staging_dir/"
scp -q "$remote_host:$remote_tmp/song_bureaucracy_entries_ch1t12.revisions.db" "$staging_dir/"
printf 'source=%s\nretrieved_at=%s\n' "$remote_host" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$staging_dir/README.txt"
printf 'release=%s\n' "$(ssh "$remote_host" 'readlink -f /opt/song-bureaucracy/current')" >> "$staging_dir/README.txt"

mkdir -p "$(dirname "$backup_dir")"
if [[ -e "$backup_dir" ]]; then
    mv "$backup_dir" "$old_dir"
fi
mv "$staging_dir" "$backup_dir"
rm -rf -- "$old_dir"
trap - EXIT
ssh "$remote_host" "rm -rf -- '$remote_tmp'"
printf 'backup=%s\n' "$backup_dir"
