# 宋代官制时序图谱

本目录由 `vis/CBDB-Migration-Map` 复制后独立改造。原CBDB迁居地图保留在原目录中，不与本项目同步修改。

## 数据

- 原始可靠数据库：`../data/song_bureaucracy_best.db`
- 时间标准化工作库：`../data/song_bureaucracy_visualization.db`
- 浏览器数据：`public/data/song-bureaucracy.json`

重新生成时间和前端数据（`export_visualization_data.py` 默认输出到本目录 v2 的 `public/data/song-bureaucracy.json`；如需同步 v1，追加 `--output vis/song-bureaucracy-visualization/public/data/song-bureaucracy.json`）：

```bash
cd ../..
python3 vis/normalize_times.py
python3 vis/export_visualization_data.py
```

## 本地运行

```bash
pnpm dev
```

## 构建

```bash
pnpm build
```
