# 尚书省 Excel / ch2t7 对比可视化

这是独立目录，不修改或替换 8050、8051 的现有可视化。

```bash
cd vis/shangshu-excel-comparison
./run.sh --port 8060
```

打开 `http://127.0.0.1:8060/shangshu-excel-comparison/`。

- Excel 来源：`vis/副本尚书省下机构官职表总表.xlsx`
- 当前数据来源：`data/database/song_bureaucracy_entries_ch2t7.db`
- 默认年份：1080，可在 960–1279 之间自由选择
- 名称匹配：严格使用正式名称，不自动增加别名

如 Excel 更新，可使用项目配置的 `@oai/artifact-tool` 运行：

```bash
node scripts/extract_excel_data.mjs
```
