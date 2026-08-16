# song.zywingspan.com 部署

公网部署使用 `vis/ch2t7-design-vis` 与 ch2t7 两个数据库。运行结构为：

```text
Cloudflare -> Caddy :443 -> 127.0.0.1:8650 -> Python visualization server
```

- `deploy.sh` 构建前端并上传一个不可变 release，再原子切换 `/opt/song-bureaucracy/current`。
- `song-bureaucracy.service` 以非特权用户运行，正式数据文件只读，修订旁路库单独放在 `/var/lib/song-bureaucracy/`。
- `Caddyfile.song` 把公网修订状态固定为“只读”，阻断所有修订写请求；本地项目仍保留完整修订功能。
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

最后一条必须返回 `403`。
