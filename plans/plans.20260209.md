# 官制数据结构化代理

2026-02-09 起修订版本

使用代理系统，从《宋代官制辞典》数据中提取官制信息，并转化为结构化数据。

## 数据

### 输入数据

输入数据包含一项，即《宋代官制辞典》书本经过 OCR 处理后的结构化数据。

### 输出数据

输出数据包含四张结构化表格
 * Entities: 主词条表（机构/官职的静态身份）
 * EntityIntervals: 时间切片表（词条在特定时段的动态属性）
 * Relationships: 关系表（切片之间的二元连接）
 * Citations: 引用表（所有数据的史料依据）

### 数据处理流程

1. 提供《辞典》中的若干条词条
2. 代理分析输入的词条信息，识别其中的官制实体并提取其中的关系信息
3. 将识别与提取结果记录到输出数据中，并保留溯源引用信息

## 项目工作流程

 * [x] 对《辞典》影印 PDF 文件进行 OCR 处理并转为半结构化数据
 * [x] 设计输出数据表细节
 * [ ] 设计数据库接口并实现相应功能
 * [ ] 设计代理行为空间，并实现相应功能
 * [ ] 设计代理整体流程框架并实现
 * [ ] 运行代理得到相应结果，并进行初步验证




# 《辞典》结果 OCR 处理

目前使用 OCR 获取了其中第八至十编的内容，并转化为了半结构化数据，存储在 Song_Bureaucracy_Dictionary 表中。
后续可以进一步扩展到整本书。
目前包含 833 个词条，并与书籍目录进行了对照，完成了初步校验。

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | PK, AI | 唯一索引 |
| title | TEXT | - | 词条在《辞典》中的名称 |
| catalog | TEXT | - | 词条在《辞典》中的目录结构 |
| page | TEXT | - | 词条在《辞典》中的页数 |
| text | TEXT | - | 词条名称后紧跟的说明文本 |
| fields | TEXT | json2str 结构字符串 | 词条带有小标题的文本信息集合 |

目前上述数据在 SQLite 数据库中\
```python
db_path = r"D:\git-projects\vis-context-agent\song-bureaucracy\data\database\song_bureaucracy_dictionary.db"
table_name = "chapter8t10"
```

```sql
CREATE TABLE IF NOT EXISTS chapter8t10 (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  catalog TEXT NOT NULL,
  page TEXT NOT NULL,
  text TEXT NOT NULL,
  fields TEXT
)
```

# 输出数据表定义

输出数据包含四张结构化表格
 * Entities: 主词条表（机构/官职的静态身份）
 * EntityIntervals: 时间切片表（词条在特定时段的动态属性）
 * Relationships: 关系表（切片之间的二元连接）
 * Citations: 引用表（所有数据的史料依据）

## A. Entities (主词条表)
存储机构或官职的静态身份。

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | PK, AI | 唯一索引 |
| title | TEXT | NOT NULL | 词条名称（如：枢密院、都督府） |
| type | TEXT | - | 词条类型：'机构' 或 '官职' |

<!-- 
| is_template | INTEGER | DEFAULT 0 | 1 为统称词条，0 为实例词条 |
| template_id | INTEGER | FK | 关联的统称 ID（如江淮都督府关联至都督府）仅在实例词条中存在 |
-->

```sql
CREATE TABLE Entities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  type TEXT CHECK(type IN ('机构', '官职')),
  -- is_template INTEGER DEFAULT 0, -- 1为统称，0为实例
  -- template_id INTEGER,
  -- FOREIGN KEY (template_id) REFERENCES Entities(id)
);
```

**优先将统称词条也作为普通词条；统称与实例关系加入到下面的关系中；主要考虑到在地方官制中基本上都是统称（在不同地区均会设立机构或职位），且不一定会有具体的实例信息（如在某个州县设立的具体的机构或官职）；统称和实例可能存在一定的信息冗余，后续再处理。** 

## B. EntityIntervals (时间切片表)
存储词条在特定时段的动态属性。

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | INTEGER | PK, AI。关系表与引用表关联的核心 ID |
| entity_id | INTEGER | FK，关联的主词条 |
| bgn_time | TEXT | 起点时间（文字描述，如“建炎元年正月”） |
| bgn_event | TEXT | 起点事件（如“设立”、“改名自...”） |
| end_time | TEXT | 结束时间（文字描述，如“元丰五年”） |
| end_event | TEXT | 结束事件（如“罢置”、“合并入...”） |
| detail_category | TEXT | 细节分类（如：官司名，官署名，官职名，军职名，军职差遣名等） |
| officer_type | TEXT | 官职分类：差遣官或阶官 |
| grade | TEXT | 官职品阶描述（如：正三品、从五品等） |

```sql
CREATE TABLE EntityIntervals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  entity_id INTEGER NOT NULL,
  bgn_time TEXT,
  bgn_event TEXT,
  end_time TEXT,
  end_event TEXT,
  detail_category TEXT, -- 机构/官职属性细分类
  officer_type TEXT,    -- 差遣官 或 阶官
  grade TEXT,           -- 品阶
  FOREIGN KEY (entity_id) REFERENCES Entities(id) ON DELETE CASCADE
);
```

**一个辞典条目可以对应与多个时间切片数据项；这些时间切片带有天然的顺序性，且通常前后相连；相同辞典条目的前后时间切片属性具有继承性，即若当前切片属性为空值，则可以向前寻找同一个条目的切片是否包含该属性；**

## C. Relationships (关系表)
记录切片之间的二元连接。

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | INTEGER | PK, AI |
| subject_id | INTEGER | FK，主体切片 ID (EntityIntervals.id) |
| object_id | INTEGER | FK，客体切片 ID (EntityIntervals.id) |
| relation_type | TEXT | 上下级机构关系（机构-机构），编制隶属关系（机构-官职）或 前后演变关系 或 统称与实例关系 |
| staff_quota | INTEGER | 编制关系中的官职人数 |
| staff_type | TEXT | 编制关系中的职位类别，如官或吏 |

> **前后演变逻辑说明：**
> - **继承**：A(Interval) $\to$ B(Interval) (一条 evolution 记录)
> - **分裂**：A $\to$ B, A $\to$ C (多条记录由同一主体指向不同客体)
> - **合并**：A $\to$ C, B $\to$ C (多条记录由不同主体指向同一客体)

```sql
CREATE TABLE Relationships (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  subject_id INTEGER NOT NULL, -- 对应 EntityIntervals.id
  object_id INTEGER NOT NULL,  -- 对应 EntityIntervals.id
  relation_type TEXT CHECK(relation_type IN ('上下级机构', '编制隶属', '前后演变', '统称与实例')),
  staff_quota INTEGER,         -- 编制数量
  staff_type TEXT,             -- 编制类型
  FOREIGN KEY (subject_id) REFERENCES EntityIntervals(id) ON DELETE CASCADE,
  FOREIGN KEY (object_id) REFERENCES EntityIntervals(id) ON DELETE CASCADE
);
```

## D. Citations (引用表)
记录所有数据的史料依据。

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | INTEGER | PK, AI |
| target_table | TEXT | 关联的表名 ('EntityIntervals' 或 'Relationships') |
| target_id | INTEGER | 对应表中的行 ID |
| citation | TEXT | 引文出处（如《宋代官制辞典》111页，枢密院条目，执掌字段） |
| quotation | TEXT | 史料原文内容 |
| note | TEXT | 必要的考证说明或备注 |

```sql
CREATE TABLE Citations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  target_table TEXT NOT NULL, -- 'EntityIntervals' 或 'Relationships'
  target_id INTEGER NOT NULL,
  citation TEXT,              -- 引文信息，如某书某页某段
  quotation TEXT,             -- 引述内容
  note TEXT                   -- 引用备注/考证说明
);
```

# 数据库接口

## 针对《辞典》数据表查询
辞典数据表中包含不可被更改的数据，源自《辞典》书籍的 OCR 结果。
目前包含的第八至十编的 833 个条目，可以通过“名称+所在页码”的方式唯一索引。

查询接口：search_dictionary(title, page)

返回值： 词条对象结构

```javascript
interface DictionaryEntry{
  id: str
  title: str
  catalog: str
  page: str
  text: str
  [opt_field_name]: str
}
```
转为结构化文本（用于输出到屏幕或构建提示词）
```python
f"""{entry["title"]}
文本来源：{entry["catalog"]} {entry["page"]}页
基本介绍：{entry["text"]}
{"\n".join([f"{key}: {value}" for key, value in entry["fields"].items()])}
"""
```

## 针对输出数据表

虽然输出数据表包含 4 个表格，但他们是相互关联的，因此无论是查询还是修改，一般会涉及到联动统一操作；

主要的操作包括
  * [ ] 查询
  <!-- * [ ] 考据查询（涉及到引用依赖） -->
  * [ ] 创建新词条
  * [ ] 创建词条时间切片
  * [ ] 更新时间切片属性
  * [ ] 更新时间切片关系
  * [ ] 更新引用依赖

**这里词条是对机构或官职条目的简称；一个机构或官职条目可以对应多个时间切片数据项；引用主要针对时间切片的具体属性更新；**

### 查询操作

查询会获取一个辞典条目的全部信息，包括本体词条，所有时间切片信息，与其他词条的关系，以及相应的溯源信息；
正常来说通过提供的词条目录查询到索引，再根据索引获取词条信息；

查询接口：get_entity(id)

返回值：辞典条目全部结构化信息

Entities 表中获取到的数据
```javascript
interface Entity {
  id: str
  title: str
  type: "官职" | "机构"
  // is_template: bool
  // template_id: str | null
}
```

EntityIntervals 表中获取到的数据
```javascript
interface EntityInterval {
  id: str
  entity_id: str
  bgn_time: str
  bgn_event: str
  end_time: str
  end_event: str
  detail_catagory: str
  officer_type: str | null
  grade: str | null
}
```

Relationships 表中获取到的数据
```javascript
interface Relationship {
  id: str
  subject_id: str
  object_id: str
  relation_type: "上下级机构" | "编制隶属" | "前后演变" | "统称与实例"
  staff_quota: number
  staff_type: str
}
```

Citations 表中获取到的数据
```javascript
interface Citation {
  id: str
  target_table: "EntityIntervals" | "Relationships" | "Citations"
  target_id: str
  citation: str
  quotation: str
  note: str
}
```

按照主词条 id 获取信息将同时获取以上信息；
同时可以从关系信息中找到其他相关的维度信息；
```javascript
interface EntityInfo {
  entity: Entity
  intervals: { [key: str]: EntityInterval }
  relationships: { [key: str]: Relationship }
  citations: { [key: str]: Citation }
}
```

将上述信息转化为结构化文本，用于输出或提示词；
采用递进式的方式总结信息，即时间点+变化+引用依赖；
```text
# {type: "机构"|"官职"} {title}
存在概念统称词条：{template_id} {template_title}
## 存在实例词条：
  * {instance_id} {instance_title}
## 时间切片
1. {时间文本} {事件文本} - {时间文本} {事件文本}
属性变化
  * {属性名}：{属性值}
相关引用
  * 引用文本，引用信息
```

<!--
查看基础信息时不提供引用依赖信息；仅在存在前后矛盾时对依赖进行检查；

### 考据查询

在查询的基础上，增加引用依赖信息，主要用于解决存在冲突的情况；

查询接口：get_citation(table, table_id)

获取到全部的与
-->

### 创建词条时间切片

指定一个词条后，创建一个时间切片，并将其插入到
  * 最前面
  * 最后面
  * 某个现有时间切片中间（覆盖原时间段的前半或后半部分）

接口 insert_timepoint(entity_id, interval, 'front' | 'end', )
