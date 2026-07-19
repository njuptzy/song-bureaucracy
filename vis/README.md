# 可视化工作区

`vis/` 只保留当前可视化及其直接依赖，按职责分为：

| 目录 | 内容 |
| --- | --- |
| `song-bureaucracy-visualization-v2/` | 当前 Vue 3 + Vite 前端 |
| `backend/` | 时间标准化、浏览器数据导出、实时只读服务 |
| `tests/` | 可视化数据层单元测试 |
| `data/` | 只读源库、标准化工作库及数据库备份 |
| `docs/` | 时间标准化等流程说明 |
| `reports/` | 脚本生成的当前运行报告 |
| `resources/reference/` | 外部 Excel 等参考资料 |
| `legacy/` | 独立旧项目，仅供追溯，不参与当前业务代码修改 |

常用命令均从仓库根目录执行：

```bash
python3 vis/backend/normalize_times.py
python3 vis/backend/export_visualization_data.py
python3 vis/backend/serve_visualization_v2.py
python3 -m unittest vis.tests.test_live_visualization_data vis.tests.test_normalize_times
```

前端开发与构建见 [`song-bureaucracy-visualization-v2/README.md`](song-bureaucracy-visualization-v2/README.md)。
