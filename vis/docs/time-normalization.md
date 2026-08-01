# 宋代官制时间标准化流程

## 目标

为全宋时间线提供公元年份，并保留原始年号、月、闰月和日的信息。

- 主时间线只精确到公元年。
- 月、闰月、日只用于同一年内排序和详情展示。
- 不把宋代农历月日换算成公历月日。
- 不修改只读源库 `vis/data/song_bureaucracy_best.db`。
- 输出可重复生成的工作库 `vis/data/song_bureaucracy_visualization.db`。

## 资料来源

1. 教育部《重编国语辞典修订本》附录“中国历代年号表”，用于核对宋代年号的元年、末年及宋朝整体范围。
   - https://dict.revised.moe.edu.tw/appendix.jsp?ID=3&page=5&ver=5
2. 中央研究院数位文化中心“两千年中西历转换”，用于确认中国传统纪年与中西历转换的资料边界。
   - https://sinocal.sinica.edu.tw/

当前版本只换算公元年份，不使用第二项资料换算公历月日。

## 转换规则

脚本：`vis/backend/normalize_times.py`

1. 识别宋代年号及年号年。
2. 使用“年号元年公元年 + 年号年 - 1”得到公元年。
3. 提取农历月、闰月和日，保存在独立字段中。
4. 月日只计算同年排序值，不作为主时间线刻度。
5. 原文明示起止年的表达保存为 `range`，可在时间轴上显示为连续区间。
6. 朝代、帝王在位期、改制前后、阶段词及“未载具体年月”等只提供边界的表达
   保存为 `bounded`，并写入一个可用于截面计算的数值锚点。锚点不把原文升级为
   精确纪年：例如“宋前期”取宋朝起点 960 年，“南宋初”取 1127 年，
   “元丰改制后”取元丰五年改制的 1082 年。
7. 阶段词优先采用其明确事件边界；只有朝代范围而无其他线索时采用该朝代起点。
   `bounded` 的 `year_start/year_end` 均写为锚点年，避免截面算法等到整个朝代末年。
8. 宋前源流保存为 `pre_song`；能换算的年号和朝代泛称同时写入公元数值年，
   但仍不进入 960—1279 主时间线。
9. 无法可靠识别、不是时间或年号年次非法的内容保存为 `unresolved`。非法年号
   年次不能退化成年号的完整范围。
10. 原始时间始终保留在 `Timepoints.time` 和 `NormalizedTimes.raw_time`。

## 结果类型

| 类型 | 含义 |
| --- | --- |
| `exact` | 能定位到一个公元年 |
| `range` | 原文明示起止，可作为连续区间显示 |
| `bounded` | 原文不是精确纪年，但已选取可审计的数值边界锚点 |
| `undated` | 宋代时间尚未建立锚点；全库审核要求此类数量为零 |
| `pre_song` | 宋前源流；尽量保留数值年，但不进入 960—1279 主时间线 |
| `unresolved` | 不是时间、疑似错误或无法识别 |

## 生成命令

```bash
python3 vis/backend/normalize_times.py
```

运行时同时更新 `vis/reports/time-normalization-report.md`，保存本次各类型数量、待复核项和资料来源。

可显式指定输入和输出：

```bash
python3 vis/backend/normalize_times.py \
  --source vis/data/song_bureaucracy_best.db \
  --output vis/data/song_bureaucracy_visualization.db
```

## 输出内容

工作库保留原有业务表，并新增：

- `NormalizedTimes`：每个时间节点的年份、月日、排序值和解析类型。
- `TimeNormalizationMetadata`：版本、生成时间、规则说明和资料来源。
- `vis/reports/time-normalization-report.md`：本次运行结果和待复核清单。

## 测试命令

```bash
python3 -m unittest vis.tests.test_normalize_times
```

## 验证要求

- `Timepoints` 与 `NormalizedTimes` 行数一致。
- 源数据库不发生修改。
- 没有开始年晚于结束年的记录。
- 月份在 1—12，日期在 1—30。
- 闰月排在同名普通月之后、下一月之前。
- SQLite `integrity_check` 返回 `ok`。
- 除 `unresolved` 外，每条标准化记录都有 `year_start`；`undated` 数量必须为零。
- `unresolved` 项逐条保留，不能静默丢弃或猜测。
