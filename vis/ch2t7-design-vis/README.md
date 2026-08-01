# ch2t7-design-vis · 原 SVG 模板驱动可视化

两张设计师 SVG 画板就是实际界面，不再由前端仿画。Vue 3 保存当前视图、实体与年份；D3 把 SVG 内已有的文字和图形槽位绑定到 ch2t7 的真实实体、关系、编制、时间点与辞典原文。

## 数据与设计源

- 结构化数据：`data/database/song_bureaucracy_entries_ch2t7.db`（只读）
- 辞典原文：`data/database/song_bureaucracy_dictionary_ch2t7.db`（只读）
- 层级画板：`svg格式/宋代职官体系可视化界面_画板 1 副本 4-01.svg`
- 编制画板：`svg格式/宋代职官体系可视化界面_画板 1 副本 4-02.svg`
- 字体直接读取设计包内 `FZQingKBYSJW-M.TTF` 与 `AdobeSongStd-Light.otf`

## 实现原则

- 标题、机构分类、说明框、机构节点、官职槽位、编制矩形、时间线、图例和纸纹全部来自原 SVG。
- 前端不重新绘制这些模块，只替换 SVG 文字槽位并绑定交互。
- 点击 SVG 中能匹配数据库的机构或官职，会在原说明框内写入当前年份的真实时间点、编制和下级机构。
- 点击原 SVG 的“层级视图 / 编制视图”切换两张原画板。
- 拖动原时间轴下方的三角指针选择起止年份；三角上方虚线随选择移动，机构树、编制、详情与时间点按所选区间同步过滤，年代未明的数据保留。

## 技术栈

- Vue 3：状态与数据加载
- D3.js：SVG DOM 数据绑定、年份映射和交互
- Vite：前端构建
- Python 标准库：只读 SQLite API 与原设计资源服务

## 启动

```bash
cd vis/ch2t7-design-vis
./run.sh
```

默认地址：`http://127.0.0.1:8650/`

`node_modules` 与 legacy 项目共用，不要在本目录运行 `pnpm install`。

## 主要文件

```text
server.py
src/App.vue
src/components/DesignTemplateCanvas.vue
```

## 接口

- `/api/data`：ch2t7 实体、时间点、层级关系、编制关系、引用和辞典原文
- `/api/design/hierarchy.svg`：原始可编辑层级画板
- `/api/design/composition.svg`：原始可编辑编制画板
- `/api/design/*.ttf|otf`：设计包字体
- `/api/health`：服务状态

## 当前边界

- SVG 中已有的示例机构名称会按数据库同名实体绑定；设计稿没有预留槽位的额外实体不会凭空新增图形。
- 辞典按实体标题精确匹配，标题不一致的实体可能暂时没有辞典正文。
