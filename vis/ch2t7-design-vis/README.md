# ch2t7-design-vis · 宋代职官设计稿版可视化

按《宋代职官可视化设计.pdf》（`vis/宋代职官体系可视化打包文件 /`）的设计稿实现的可视分析系统，数据源为 ch2t7（辞典二至七编）结构化结果库。

- 技术栈：Vue 3 + d3.js（Vite 构建）+ Python 标准库只读后端
- 数据源（只读，不修改）：
  - `data/database/song_bureaucracy_entries_ch2t7.db`（四表 + BuildRecords）
  - `data/database/song_bureaucracy_dictionary_ch2t7.db`（表 `chapter2t7`，辞典原文）

## 启动

```bash
cd vis/ch2t7-design-vis
./run.sh                 # 构建前端并启动服务（默认 127.0.0.1:8650）
# 或分开：
node node_modules/vite/bin/vite.js build   # 等价 pnpm build（shell 无 pnpm 时用）
python3 server.py [--port 8650]            # 只读 API + 托管 dist/
```

开发模式：`python3 server.py` 先启动，再 `pnpm dev`（vite 代理 `/api` 到 8650）。

**依赖**：`node_modules` 是指向 `../legacy/CBDB-Migration-Map/node_modules` 的符号链接（与 v2 共用），**不要在本目录运行 `pnpm install`**。

## 接口

- `GET /api/data`：一次返回全部 JSON（启动后惰性构建并缓存）：`entities`、`timepoints`（按实体分组）、`hierarchyEdges`（上下级机构，实体 id 对）、`staffEdges`（编制隶属，含 staff_quota/staff_type）、`citations`（按 T{id}/R{id} 分组）、`dictionary`（按 title 匹配辞典词条，含 page/catalog/summary/origin/duty）、`meta` 统计。
- `GET /api/health`：健康检查。
- 其余路径：`dist/` 静态文件，SPA 回退到 index.html。

## 设计稿对应关系

以最终界面画板（`svg格式/宋代职官体系可视化界面字体转曲_画板 1 副本 4-01.svg`）为准；配色（#351704/#563905/#918069/#a5a68d/#866d6d 等）、节点几何（官职条 15.4×101.6、节距 21.1）、纸张纹理背景均直接从该 SVG 提取，字体用设计打包文件里的方正清刻本悦宋（`字体/FZQingKBYSJW-M.TTF`）。

| 设计稿 | 实现 |
| --- | --- |
| 机构 = 竖排书脊：白底细描边 + 顶部灰绿小签 + 竖排题名；书脊宽度按层级递减（图例：省/部/司/案及以下） | `InstitutionTree.vue` 书脊 SVG 节点（LEVEL_W/LEVEL_FONT 五档） |
| 树连线 = 直角折线；顶部"皇帝"装饰总根（2px 暗褐框） | `linkPath()` 肘形连线 + emperor 节点 |
| 官职 = 竖排官职条 + 顶签四色（图例"官职类分类"：差遣官/职事官/阶官/吏），虚线浮动面板不影响布局；员额注为「n人」 | `OfficialHats.vue`（按 attr_category 归类四色，品阶排序） |
| 设定按钮：展开全部 / 展开指定下级；单个点击展开 | 顶栏 `展开全部`/`全部收起`/`展开到第 N 层` + 节点点击切换 |
| hover 浮动说明卡（职源与沿革/职掌） | `App.vue` hover-card（不动布局） |
| 左侧 机构分类 五类竖排按钮（内廷/中央/路级/州县/军队）+ 当前机构说明 | `NavPanel.vue`（按 attr_category + 题名关键词归类） |
| 底部 朝代/年份 两行时间线 + 右下角"编码信息"图例（机构级别、官职类分类、数据来源） | `SongTimelineBar.vue`（帝系数据取自 v2 `SongTimeline.vue`） |
| 选中机构详情：下级机构、编制隶属官职、时间点 + 引用（Citations）、辞典词条 | `DetailPanel.vue` |
| 显示官职开关 | 顶栏复选框；未勾选时选中单个机构也会展出其官职面板（对应"单个浮动展开"） |

## 目录结构

```
server.py            # 只读数据服务（API + dist 托管）
run.sh               # 构建并启动
vite.config.js       # /api 代理到 8650
src/
  App.vue            # 页面壳：顶栏 / 左导航 / 主画布 / 详情 / 底部时间线
  assets/            # FZQingKBYSJW-M.TTF（设计字体）、paper-texture.png（设计稿提取的纸纹）
  components/
    InstitutionTree.vue   # d3 树主视图（书脊节点、缩放平移、展开控制）
    OfficialHats.vue      # 官职虚线浮动面板
    NavPanel.vue          # 左侧五类机构导航 + 当前机构说明
    DetailPanel.vue       # 实体详情（下级机构、编制官职、时间点、引用）
    SongTimelineBar.vue   # 底部朝代/年份时间线 + 编码信息图例
```

## 已知偏差 / 未实现

- 底部时间线仅静态展示，未做 brush 框选过滤（设计稿也只是背景参照）。
- 辞典按 title 精确匹配，部分实体（如"吏部"）因词条名不一致暂无匹配，hover 卡显示"无匹配辞典词条"。
- 早期 PDF 概念页（p5–p8）的"装订线格数 = 下级数"和"官帽图标"在最终画板中已被设计师放弃（改为顶部小签 + 虚线官职面板），本实现跟随最终画板。
- 官职四色按 attr_category 关键词归类（差遣官/职事官/阶官/吏），个别归类可能与设计预期有出入；每机构官职条最多展出 8 列，其余以 +n 提示。
- 设计稿第二张画板的"编制视图"（书架式布局）未实现。
