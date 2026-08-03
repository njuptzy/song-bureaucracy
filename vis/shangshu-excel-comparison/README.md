# 尚书省 Excel 独立可视化

本目录把 `vis/副本尚书省下机构官职表总表.xlsx` 转换为现有 8050
可视化的数据契约，并直接复用 `vis/ch2t7-design-vis/dist/` 的界面。

它不读取当前官制数据库，也不修改原 8050/8051 的代码、构建文件或数据。

```bash
cd vis/shangshu-excel-comparison
./run.sh --port 8060
```

打开 `http://127.0.0.1:8060/`，即可按用户选择的年份查看 Excel 中的机构、
官职、上下级关系、编制隶属和前后演变。

Excel 更新后，使用项目配置的 `@oai/artifact-tool` 重新提取：

```bash
node scripts/extract_excel_data.mjs
```
