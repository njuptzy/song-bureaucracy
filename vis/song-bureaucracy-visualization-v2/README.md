# 宋代官制时序图谱

本目录由 `vis/CBDB-Migration-Map` 复制后独立改造。原CBDB迁居地图保留在原目录中，不与本项目同步修改。

## 数据

- 原始可靠数据库：`../data/song_bureaucracy_best.db`
- 时间标准化工作库：`../data/song_bureaucracy_visualization.db`
- 实时前端数据库：`../data/song_bureaucracy_visualization.db`
- `public/data/song-bureaucracy.json` 是离线快照：实时接口不可用时前端自动回退到它（状态栏显示"离线快照"，接口恢复后自动切回实时），不再是主数据源。

重新生成时间标准化工作库：

```bash
cd ../..
python3 vis/normalize_times.py
```

后端通过只读 SQLite 连接实时装配前端数据。修改工作库并提交事务后，页面会在数秒内检测到主数据库或 WAL 变化并刷新（写入停止约 2 秒后重建缓存，避免批量写入期间反复全量刷新，可用 `--settle-seconds` 调整）；新增或修改 `Timepoints.time` 时会按最新中文时间即时标准化，不依赖旧 `NormalizedTimes`。

## 实时运行（推荐）

```bash
cd vis/song-bureaucracy-visualization-v2
pnpm live
```

打开 <http://127.0.0.1:8643/>。

指定其他数据库：

```bash
python3 ../serve_visualization_v2.py --db /absolute/path/to/database.db
```

数据库始终使用 SQLite `mode=ro` 打开，服务不会写库。

## 前端开发

先在仓库根目录启动 API：

```bash
python3 vis/serve_visualization_v2.py
```

再在另一个终端启动 Vite（`/api` 会代理到 8643）：

```bash
cd vis/song-bureaucracy-visualization-v2
pnpm dev
```

## 构建

```bash
pnpm build
```

如仍需重新生成离线 JSON 快照（离线兜底数据随 `pnpm build` 一起打包）：

```bash
python3 vis/export_visualization_data.py
```

## 测试

在仓库根目录运行（不启动服务、不改库）：

```bash
python3 -m unittest vis.test_live_visualization_data vis.test_normalize_times
```
