# 宋代官制信息提取代理设计 2026-02-05 版本

## 数据结构更新

### 《宋代官制辞典》数据
#### A. Song_Bureaucracy_Dictionary
《宋代官制辞典》词条数据表。
  * id 索引
  * title 词条名称
  * catalog 词条所在目录
  * page 词条所在页码
  * text 词条自带文本
  * fields 词条各字段内容（json2str）

### 官制数据表
#### A. Entities (主词条表)
存储机构或官职的静态身份。

| 字段名 | 类型 | 约束 | 说明 |
| :--- | :--- | :--- | :--- |
| id | INTEGER | PK, AI | 唯一索引 |
| title | TEXT | NOT NULL | 词条名称（如：枢密院、都督府） |
| type | TEXT | - | 词条类型：'机构' 或 '官职' |
| is_template | INTEGER | DEFAULT 0 | 1 为统称词条，0 为实例词条 |
| template_id | INTEGER | FK | 关联的统称 ID（如江淮都督府关联至都督府） |

```sql
CREATE TABLE Entities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  type TEXT CHECK(type IN ('机构', '官职')),
  is_template INTEGER DEFAULT 0, -- 1为统称，0为实例
  template_id INTEGER,
  FOREIGN KEY (template_id) REFERENCES Entities(id)
);
```

#### B. EntityIntervals (时间切片表)
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

#### C. Relationships (关系表)
记录切片之间的二元连接。

| 字段名 | 类型 | 说明 |
| :--- | :--- | :--- |
| id | INTEGER | PK, AI |
| subject_id | INTEGER | FK，主体切片 ID (EntityIntervals.id) |
| object_id | INTEGER | FK，客体切片 ID (EntityIntervals.id) |
| relation_type | TEXT | 上下级机构关系（机构-机构），编制隶属关系（机构-官职）或 前后演变关系 |
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
  relation_type TEXT CHECK(relation_type IN ('上下级机构', '编制隶属', '前后演变')),
  staff_quota INTEGER,         -- 编制数量
  staff_type TEXT,             -- 编制类型
  FOREIGN KEY (subject_id) REFERENCES EntityIntervals(id) ON DELETE CASCADE,
  FOREIGN KEY (object_id) REFERENCES EntityIntervals(id) ON DELETE CASCADE
);
```

#### D. Citations (引用表)
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

### 其他

开启 SQLite 外键，并手动添加一些索引
```sql
-- 开启外键支持（SQLite 默认可能关闭）
PRAGMA foreign_keys = ON;

-- 创建各个表格

-- 补充索引：大幅提升查询性能
CREATE INDEX idx_intervals_entity ON EntityIntervals(entity_id);
CREATE INDEX idx_rels_subject ON Relationships(subject_id);
CREATE INDEX idx_rels_object ON Relationships(object_id);
CREATE INDEX idx_citations_target ON Citations(target_table, target_id);
```

## 工具接口
### 查询工具
#### A. 查询《辞典》数据表
在必要时获取额外的输入信息；主要解决《辞典》中，“同xx词条”等表述；

#### B. 查询一个数据词条
通过目录确认id后，通过id查询到一个词条的全部内容，包括
  * 基本属性
  * 模板类（如果有）
  * 所有时间切片
对于每个时间切片，给出
  * 时间点，事件
  * 基本属性


### 数据更新工具
