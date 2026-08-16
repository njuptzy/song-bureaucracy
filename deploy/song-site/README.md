# song.zywingspan.com 部署

公网部署使用 `vis/ch1t12-design-vis`，数据源与当前本地 8050 服务一致：
`song_bureaucracy_entries_ch1t12.db`、`song_bureaucracy_dictionary_ch1t12.db`
和辞典表 `chapter1t12`。运行结构为：

```text
Cloudflare -> Caddy :443 -> 127.0.0.1:8650 -> Python visualization server
```

- `deploy.sh` 只构建并上传代码、静态资源和设计素材，不上传数据库；发布时不会覆盖服务器数据。
- `song-bureaucracy.service` 以非特权用户运行，服务器正式数据库和修订旁路库都位于 `/var/lib/song-bureaucracy/`，网站修订直接写入服务器数据库。
- `Caddyfile.song` 将所有请求转发到应用，包括修订接口；公网与本地使用同一套修订能力。
- `backup-from-server.sh` 把服务器当前 release 的代码/设计素材和 SQLite 在线备份得到的结果库、辞典库、修订库拉到本地 `data/server-latest/`，每次运行只保留最新一份；不会自动覆盖 Git 跟踪的正式源码或数据库。
- 历史 release 不自动删除，回退时把 `current` 链接切回上一目录并重启服务即可。

部署后验证：

```bash
curl -fsS http://127.0.0.1:8650/api/health
curl -fsS https://song.zywingspan.com/api/health
curl -fsS https://song.zywingspan.com/api/version
curl -fsS https://song.zywingspan.com/api/revisions/state
curl -sS -o /dev/null -w '%{http_code}\n' \
  -X POST https://song.zywingspan.com/api/revisions/draft/discard
```

最后一条应返回 `200`，且修订状态中的 `edit_locked` 应为 `false`。

同步服务器当前版本：

```bash
deploy/song-site/backup-from-server.sh
```

同步后，运行代码副本位于 `data/server-latest/code/vis/`；正式发布代码仍使用 `deploy.sh`，发布过程不会上传或覆盖服务器数据库。
