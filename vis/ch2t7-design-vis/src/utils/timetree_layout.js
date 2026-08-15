// 时间线树视图的几何布局：左侧层级树（根在左、深度向右）与右侧时间线
// 共享同一套行 y 坐标；x 方向树区与年代区分离，年代映射与演变视图一致
// （960–1279 线性映射）。

// 中央内容区 500—1834 精确二等分：左半是层级树，右半是时间线。
// 两区各自保留内边距，分界线不兼作任何一侧的内容起点。
export const TIMETREE_GEOMETRY = {
  content: { x0: 500, x1: 1834 },
  tree: { x0: 610, depthGap: 145, maxX: 1095 },
  dividerX: 1167,
  plot: { x0: 1192, x1: 1828 },
  axisY: 262,
  rowsTop: 296,
  rowsBottom: 844,
  rowPitch: 52,
};

const CAPSULE_LABEL_FONT_MAX = 17.14;
const CAPSULE_LABEL_FONT_MIN = 9.8;
const CAPSULE_LABEL_SIDE_PADDING = 14;
const CJK_GLYPH_WIDTH_RATIO = 0.94;

/**
 * 横放机构胶囊的文字适配：先缩小字号保留全称，只有超过
 * 最小可读字号仍放不下时才使用省略号。
 */
export function fitTimetreeCapsuleLabel(title, capsuleLength) {
  const glyphs = [...String(title || "暂无资料")];
  const available = Math.max(1, capsuleLength - CAPSULE_LABEL_SIDE_PADDING);
  const fittedFontSize = Math.min(
    CAPSULE_LABEL_FONT_MAX,
    available / Math.max(1, glyphs.length * CJK_GLYPH_WIDTH_RATIO),
  );
  if (fittedFontSize >= CAPSULE_LABEL_FONT_MIN) {
    return { text: glyphs.join(""), fontSize: fittedFontSize };
  }
  const maxGlyphs = Math.max(
    2,
    Math.floor(available / (CAPSULE_LABEL_FONT_MIN * CJK_GLYPH_WIDTH_RATIO)),
  );
  return {
    text: `${glyphs.slice(0, maxGlyphs - 1).join("")}…`,
    fontSize: CAPSULE_LABEL_FONT_MIN,
  };
}

export function timetreeYearToX(year, yearMin, yearMax, plot = TIMETREE_GEOMETRY.plot) {
  const span = Math.max(1, yearMax - yearMin);
  return plot.x0 + (year - yearMin) / span * (plot.x1 - plot.x0);
}

/** 旋转树实际占用的纵向槽位数；父节点居中不会额外增加内容高度。 */
export function timetreeLayoutSpan(rowsOrCount = []) {
  if (typeof rowsOrCount === "number") return Math.max(0, rowsOrCount);
  if (!rowsOrCount.length) return 0;
  return Math.max(...rowsOrCount.map((row) => row.layoutIndex ?? row.rowIndex ?? 0)) + 1;
}

/** 滚动量钳制：内容不足一屏时锁死在 0。 */
export function clampTimetreeScroll(offset, rowsOrCount, geometry = TIMETREE_GEOMETRY) {
  const content = timetreeLayoutSpan(rowsOrCount) * geometry.rowPitch;
  const viewport = geometry.rowsBottom - geometry.rowsTop;
  const maxOffset = Math.max(0, content - viewport);
  return Math.max(0, Math.min(maxOffset, Number.isFinite(offset) ? offset : 0));
}

/** 每行 y 中心（含滚动偏移；视口外的行由渲染层的 clipPath 裁掉）。 */
export function timetreeRowY(layoutIndex, scrollOffset, geometry = TIMETREE_GEOMETRY) {
  return geometry.rowsTop + layoutIndex * geometry.rowPitch
    + geometry.rowPitch / 2 - scrollOffset;
}

/** 树节点标签的 x：深度向右，与"逆时针旋转 90°"后的自上而下树等价。 */
export function timetreeNodeX(depth, geometry = TIMETREE_GEOMETRY) {
  return Math.min(
    geometry.tree.x0 + depth * geometry.tree.depthGap,
    geometry.tree.maxX,
  );
}

/**
 * 左侧具体机构节点到右侧时间车道的关联线范围。
 * 留出少量节点呼吸空间，并固定接到年代区的起点；这条线只表达视图对应关系，
 * 不参与生命周期语义。
 */
export function timetreeLaneLinkSpan(nodeRight, geometry = TIMETREE_GEOMETRY) {
  const x1 = geometry.plot.x0;
  const x0 = Math.min(x1 - 4, Math.max(geometry.content.x0, nodeRight + 5));
  return { x0, x1 };
}

/**
 * 时间线树的点密度联动：当前选中机构展开全部时间点；其他机构只保留
 * 建置、罢废和演变关系端点等关键点，避免总览状态被普通记载淹没。
 */
export function timetreeEventsForLane(events = [], {
  active = false,
  linkedEndpointIds = null,
} = {}) {
  if (active) return events;
  if (linkedEndpointIds instanceof Set) {
    return events.filter((event) => linkedEndpointIds.has(event.id));
  }
  return events.filter((event) => event.expanded);
}

/** 当前有明确机构选择时，只保留直接涉及该机构的前后演变关系。 */
export function timetreeRelationsForEntity(relations = [], entityId = null) {
  if (entityId == null) return relations;
  return relations.filter((relation) => (relation.members || []).some(
    (member) => member.entityId === entityId,
  ));
}

/** 收集当前联动关系的端点，供其他机构车道保留必要的上下文点。 */
export function timetreeRelationEndpointIds(relations = []) {
  return new Set(relations.flatMap((relation) => (relation.members || [])
    .map((member) => member.timepointId)
    .filter((id) => id != null)));
}

const STACK_MIN_GAP = 11;
// 错层位移等级：先上后下交替，最多 5 层，再密则接受重叠（与演变视图
// "密集点错层"同思路，但用固定档位保证确定性）。
const STACK_OFFSETS = [0, -8, 8, -15, 15];

/**
 * 单车道事件布局：同年/近年的点沿 y 错层，displayX 始终落在真实年份上，
 * 错层点带 vertical leader（茎）回指车道线。
 * 输入事件需带 effectiveYear / yearStart / yearEnd / timeType。
 */
export function layoutTimetreeEvents(events, xOf) {
  const laid = events
    .filter((event) => event.effectiveYear != null)
    .map((event) => ({
      ...event,
      baseX: xOf(event.effectiveYear),
      rangeStartX: event.yearStart != null ? xOf(event.yearStart) : null,
      rangeEndX: event.yearEnd != null ? xOf(event.yearEnd) : null,
    }))
    .sort((a, b) => a.baseX - b.baseX || String(a.id).localeCompare(String(b.id), "zh", { numeric: true }));

  const levelLastX = [];
  for (const event of laid) {
    let level = levelLastX.findIndex((lastX) => event.baseX - lastX >= STACK_MIN_GAP);
    if (level === -1) {
      if (levelLastX.length < STACK_OFFSETS.length) {
        levelLastX.push(Number.NEGATIVE_INFINITY);
        level = levelLastX.length - 1;
      } else {
        level = STACK_OFFSETS.length - 1;
      }
    }
    levelLastX[level] = event.baseX;
    event.dy = STACK_OFFSETS[level];
    event.displaced = event.dy !== 0;
  }
  return laid;
}

/** 存续段几何：开放端按 yearMin/yearMax 边界截断。 */
export function layoutTimetreeSegments(segments, xOf) {
  return (segments || []).map((segment) => ({
    ...segment,
    x0: xOf(segment.startYear),
    x1: xOf(segment.endYear),
  }));
}

/**
 * 演变关系端点定位：成员 timepointId → 已布局事件位置。
 * 端点落在离轴区（年代未明等）的关系无法定位，标记为不可画。
 */
export function layoutTimetreeRelations(relations, eventPositionById) {
  const positioned = [];
  for (const relation of relations || []) {
    const locate = (member) => {
      const position = member.timepointId != null
        ? eventPositionById.get(member.timepointId)
        : null;
      return position ? { ...position, timepointId: member.timepointId } : null;
    };
    const sourcePoints = (relation.sourceMembers || []).map(locate).filter(Boolean);
    const targetPoints = (relation.targetMembers || []).map(locate).filter(Boolean);
    positioned.push({
      ...relation,
      sourcePoints,
      targetPoints,
      drawable: sourcePoints.length > 0 && targetPoints.length > 0,
    });
  }
  return positioned;
}
