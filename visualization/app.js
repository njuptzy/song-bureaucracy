/* 职官演变审查界面：按辞典条目逐条审查，原文与结构化数据双向联动。 */

const state = {
  entries: [],
  entities: [],
  meta: null,
  currentEntryId: null,
  currentEntityModalId: null,
  filterText: "",
  onlyIssues: false,
  filterIssueType: null,
  showRecords: false,
};

const $ = (id) => document.getElementById(id);
const entityEmbedMode = new URLSearchParams(location.search).get("embed") === "entity";
if (entityEmbedMode) document.body.classList.add("entity-embed");

function escapeHtml(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderBuildRecords(records) {
  if (!state.showRecords || !records || !records.length) return "";
  const items = records
    .map(
      (br) => `
      <div class="build-record">
        <span class="br-source">${escapeHtml(br.source_entry || "?")}${br.source_page ? ` p${escapeHtml(br.source_page)}` : ""}</span>
        <span class="br-decision">${escapeHtml(br.decision)}</span>
      </div>`
    )
    .join("");
  return `<div class="build-records">${items}</div>`;
}

function renderRecordToggle() {
  const button = $("toggleRecords");
  if (!button) return;
  button.textContent = state.showRecords ? "隐藏 record" : "显示 record";
  button.classList.toggle("record-toggle-active", state.showRecords);
}

function refreshCurrentView() {
  renderRecordToggle();
  if (state.currentEntryId !== null) selectEntry(state.currentEntryId);
}

async function fetchJson(url) {
  const resp = await fetch(url);
  const data = await resp.json();
  if (!resp.ok) throw new Error(data.error || resp.statusText);
  return data;
}

/* ---------------- 顶栏 ---------------- */

function renderMeta() {
  const m = state.meta;
  $("dbPath").textContent = m.entry_db;
  $("metaCounts").innerHTML = Object.entries(m.counts)
    .map(([k, v]) => `<span class="count-pill">${escapeHtml(k)} <b>${v}</b></span>`)
    .join("");

  const chips = Object.entries(m.issue_counts)
    .sort((a, b) => b[1] - a[1])
    .map(
      ([type, n]) => `
      <button class="chip ${state.filterIssueType === type ? "chip-active" : ""}" data-type="${type}">
        ${escapeHtml(m.issue_labels[type] || type)} <b>${n}</b>
      </button>`
    )
    .join("");
  $("issueChips").innerHTML =
    `<span class="chip chip-total">问题总数 <b>${m.issue_total}</b></span>` + chips;

  $("issueChips").querySelectorAll(".chip[data-type]").forEach((el) => {
    el.addEventListener("click", () => {
      state.filterIssueType = state.filterIssueType === el.dataset.type ? null : el.dataset.type;
      renderMeta();
      renderEntryList();
    });
  });
}

/* ---------------- 左栏：条目列表 ---------------- */

function entryVisible(e) {
  const q = state.filterText.trim();
  if (q && !(`${e.title}`.includes(q) || `${e.page}`.includes(q))) return false;
  if (state.onlyIssues && e.issue_count === 0) return false;
  if (state.filterIssueType && !e.issue_types.includes(state.filterIssueType)) return false;
  return true;
}

function matchingEntities() {
  const q = state.filterText.trim();
  if (!q || state.onlyIssues || state.filterIssueType) return [];
  return state.entities
    .filter((entity) => `${entity.title}`.includes(q) || `${entity.id}` === q)
    .map((entity, index) => ({
      entity,
      index,
      // “礼部”应优先命中原词条实体“尚书省礼部”，而不是“礼部尚书”。
      // 后缀匹配只用于检索排序，不生成别名，也不改变数据库标题。
      score: `${entity.title}` === q
        ? 0
        : `${entity.title}`.endsWith(q)
          ? 1
          : `${entity.title}`.startsWith(q)
            ? 2
            : 3,
    }))
    .sort((a, b) => a.score - b.score || a.index - b.index)
    .map(({ entity }) => entity);
}

async function selectSearchedEntity(entity) {
  state.filterText = entity.title;
  if ($("entrySearch")) $("entrySearch").value = entity.title;
  renderEntryList();
  if (entity.primary_entry_id !== null) {
    await selectEntry(entity.primary_entry_id);
  }
  await openEntityModal(entity.id);
}

function renderEntryList() {
  const rows = state.entries.filter(entryVisible);
  const entityRows = matchingEntities();
  const unlinked = state.meta.unlinked_entities.length || state.meta.unlinked_issue_count;
  let html = "";
  if (unlinked && !state.filterText && !state.filterIssueType) {
    html += `
      <div class="entry-item entry-unlinked ${state.currentEntryId === "unlinked" ? "selected" : ""}"
           data-id="unlinked">
        <span class="entry-name">⚠ 未关联条目的实体 / 问题</span>
        <span class="badges">
          <span class="badge badge-entity">${state.meta.unlinked_entities.length} 实体</span>
          ${state.meta.unlinked_issue_count ? `<span class="badge badge-issue">${state.meta.unlinked_issue_count} 问题</span>` : ""}
        </span>
      </div>`;
  }
  if (entityRows.length) {
    html += `<div class="search-section-title">结构化实体</div>`;
    html += entityRows
      .map(
        (entity) => `
      <div class="entry-item entity-search-item" data-entity-id="${entity.id}">
        <span class="entry-name">${escapeHtml(entity.title)} <span class="entry-page">#${entity.id}</span>${entity.primary_entry_title ? `<small class="entity-source">来源：${escapeHtml(entity.primary_entry_title)} p${escapeHtml(entity.primary_entry_page)}</small>` : `<small class="entity-source">未关联辞典词条</small>`}</span>
        <span class="badges"><span class="badge badge-entity">${escapeHtml(entity.type || "实体")}</span></span>
      </div>`
      )
      .join("");
  }
  if (state.filterText.trim() && rows.length) {
    html += `<div class="search-section-title">辞典词条</div>`;
  }
  html += rows
    .map(
      (e) => `
      <div class="entry-item ${state.currentEntryId === e.id ? "selected" : ""}" data-id="${e.id}">
        <span class="entry-name"><span class="entry-no" title="对应 records_${e.record_no}_*.json">#${e.record_no}</span>${escapeHtml(e.title)} <span class="entry-page">p${escapeHtml(e.page)}</span></span>
        <span class="badges">
          ${e.entity_count ? `<span class="badge badge-entity">${e.entity_count} 实体</span>` : `<span class="badge badge-none">无数据</span>`}
          ${e.issue_count ? `<span class="badge badge-issue">${e.issue_count} 问题</span>` : ""}
        </span>
      </div>`
    )
    .join("");
  $("entryList").innerHTML = html || `<p class="placeholder-tip">没有符合条件的条目</p>`;
  $("entryList").querySelectorAll(".entry-item").forEach((el) => {
    el.addEventListener("click", () => {
      if (el.dataset.entityId) {
        const entity = state.entities.find((item) => String(item.id) === el.dataset.entityId);
        if (entity) selectSearchedEntity(entity);
        return;
      }
      selectEntry(el.dataset.id);
    });
  });
}

/* ---------------- 中栏：原文 + 高亮 ---------------- */

function renderTextWithHighlights(text, highlights) {
  if (!text) return `<p class="placeholder-tip">（无原文）</p>`;
  // 后端高亮区间按 Unicode 码点计算，必须用码点数组切片（生僻字占两个 UTF-16 单元）
  const chars = [...text];
  const points = new Set([0, chars.length]);
  highlights.forEach((h) => {
    points.add(Math.max(0, Math.min(h.start, chars.length)));
    points.add(Math.max(0, Math.min(h.end, chars.length)));
  });
  const sorted = [...points].sort((a, b) => a - b);
  let html = "";
  for (let i = 0; i < sorted.length - 1; i++) {
    const [s, e] = [sorted[i], sorted[i + 1]];
    if (s >= e) continue;
    const cover = highlights.filter((h) => h.start <= s && e <= h.end);
    const seg = escapeHtml(chars.slice(s, e).join(""));
    if (cover.length) {
      const cids = cover.map((h) => h.citation_id).join(",");
      const partial = cover.every((h) => h.status === "partial");
      html += `<mark class="hl ${partial ? "hl-partial" : ""}" data-cids="${cids}">${seg}</mark>`;
    } else {
      html += seg;
    }
  }
  return html;
}

function bindHighlightEvents(container) {
  container.querySelectorAll("mark.hl").forEach((el) => {
    el.addEventListener("click", () => {
      const cid = el.dataset.cids.split(",")[0];
      const cite = document.querySelector(`.citation[data-cid="${cid}"]`);
      if (cite) {
        cite.scrollIntoView({ behavior: "smooth", block: "center" });
        flash(cite);
      }
    });
  });
}

function flash(el) {
  el.classList.add("flash");
  setTimeout(() => el.classList.remove("flash"), 1200);
}

function focusHighlight(citationId, textRoot) {
  const root = textRoot || $("entryText");
  root.querySelectorAll("mark.hl.active").forEach((m) => m.classList.remove("active"));
  const marks = [...root.querySelectorAll("mark.hl")].filter((m) =>
    m.dataset.cids.split(",").includes(String(citationId))
  );
  marks.forEach((m) => m.classList.add("active"));
  if (marks.length) marks[0].scrollIntoView({ behavior: "smooth", block: "center" });
}

/* ---------------- 右栏：实体卡片 / 时间线 ---------------- */

function renderCitation(c, currentEntryId) {
  const inThisEntry = c.entry_id !== null && c.entry_id === currentEntryId;
  const badges = [];
  if (c.conflict_flag) badges.push(`<span class="tag tag-red">冲突</span>`);
  if (c.entry_id === null) {
    badges.push(`<span class="tag tag-red">出处未关联</span>`);
  } else if (c.quotation && !c.match) {
    badges.push(`<span class="tag tag-red">原文匹配失败</span>`);
  } else if (c.match && c.match.status === "partial") {
    badges.push(`<span class="tag tag-orange">部分匹配</span>`);
  }
  if (c.entry_id !== null && !inThisEntry) {
    badges.push(
      `<span class="tag tag-gray">出自 ${escapeHtml(c.entry_title)} p${escapeHtml(c.entry_page)}</span>`
    );
  }
  return `
    <div class="citation ${inThisEntry && c.match ? "citation-linked" : ""}" data-cid="${c.id}">
      <div class="citation-quote"><span class="cite-id">#${c.id}</span>${escapeHtml(c.quotation || "（无原文片段）")}</div>
      <div class="citation-src">${escapeHtml(c.citation || "（无出处）")} ${badges.join(" ")}</div>
      ${c.note ? `<div class="citation-note">备注：${escapeHtml(c.note)}</div>` : ""}
      ${renderBuildRecords(c.build_records)}
    </div>`;
}

function relationText(rel) {
  const arrow = rel.role === "subject" ? "→" : "←";
  const other = `${escapeHtml(rel.other_entity_title || "?")}<span class="tp-ref">@${escapeHtml(rel.other_time || "?")}</span>`;
  const extra = [];
  if (rel.staff_quota != null) extra.push(`编制 ${rel.staff_quota} 人`);
  if (rel.staff_type) extra.push(escapeHtml(rel.staff_type));
  return `<b>${escapeHtml(rel.relation_type || "关系")}</b> ${arrow} ${other}
    ${extra.length ? `<span class="rel-extra">（${extra.join("，")}）</span>` : ""}`;
}

function renderTimepoint(tp, currentEntryId) {
  const attrs = [];
  if (tp.attr_category) attrs.push(`类别：${escapeHtml(tp.attr_category)}`);
  if (tp.attr_officer_type) attrs.push(`官职分类：${escapeHtml(tp.attr_officer_type)}`);
  if (tp.attr_grade) attrs.push(`品阶：${escapeHtml(tp.attr_grade)}`);
  const noCite = !tp.citations.length && !tp.is_placeholder;
  return `
    <div class="timepoint ${tp.is_placeholder ? "tp-placeholder" : ""} ${noCite ? "tp-warn" : ""}">
      <div class="tp-head">
        <span class="tp-time">${escapeHtml(tp.time || "—")}${
          tp.normalized_year_label
            ? `<span class="tp-normalized-year">（${escapeHtml(tp.normalized_year_label)}）</span>`
            : ""
        }</span>
        <span class="tp-event">${escapeHtml(tp.event || "")}</span>
        <span class="tp-id">#${tp.id}</span>
        ${tp.is_placeholder ? `<span class="tag tag-red">占位残留</span>` : ""}
        ${noCite ? `<span class="tag tag-orange">无引用</span>` : ""}
      </div>
      ${attrs.length ? `<div class="tp-attrs">${attrs.join(" ｜ ")}</div>` : ""}
      ${renderBuildRecords(tp.build_records)}
      ${tp.citations.map((c) => renderCitation(c, currentEntryId)).join("")}
      ${tp.relationships
        .map(
          (rel) => `
        <div class="relation ${rel.citations.length ? "" : "rel-warn"}">
          <div class="rel-head">${relationText(rel)}
            ${rel.citations.length ? "" : `<span class="tag tag-orange">无引用</span>`}
          </div>
          ${renderBuildRecords(rel.build_records)}
          ${rel.citations.map((c) => renderCitation(c, currentEntryId)).join("")}
        </div>`
        )
        .join("")}
    </div>`;
}

function renderEntityCard(entity, currentEntryId) {
  return `
    <section class="entity-card" data-eid="${entity.id}">
      <header class="entity-head">
        <span class="entity-type ${entity.type === "机构" ? "type-org" : "type-officer"}">${escapeHtml(entity.type || "?")}</span>
        <h3>${escapeHtml(entity.title)}</h3>
        <span class="entity-id">#${entity.id}</span>
        <button class="entity-full" data-eid="${entity.id}">完整实体 →</button>
      </header>
      ${entity.chain_problems.length
        ? `<div class="chain-problems">⚠ ${entity.chain_problems.map(escapeHtml).join("；")}</div>`
        : ""}
      ${renderBuildRecords(entity.build_records)}
      <div class="timeline">
        ${entity.timepoints.map((tp) => renderTimepoint(tp, currentEntryId)).join("")}
      </div>
    </section>`;
}

function bindCitationEvents(container, textRoot) {
  container.querySelectorAll(".citation").forEach((el) => {
    el.addEventListener("mouseenter", () => focusHighlight(el.dataset.cid, textRoot));
    el.addEventListener("click", () => focusHighlight(el.dataset.cid, textRoot));
  });
  container.querySelectorAll(".entity-full").forEach((el) => {
    el.addEventListener("click", (ev) => {
      ev.stopPropagation();
      openEntityModal(Number(el.dataset.eid));
    });
  });
}

/* ---------------- 条目选择 ---------------- */

function scrollSelectedIntoView() {
  const el = document.querySelector(".entry-item.selected");
  if (el && typeof el.scrollIntoView === "function") {
    el.scrollIntoView({ block: "nearest", behavior: "auto" });
  }
}

function readEntryFromHash() {
  const m = /^#entry=(unlinked|\d+)$/.exec(location.hash || "");
  return m ? m[1] : null;
}

function readEntityFromHash() {
  const m = /^#entity=(\d+)$/.exec(location.hash || "");
  return m ? Number(m[1]) : null;
}

async function selectEntry(id) {
  state.currentEntryId = id === "unlinked" ? "unlinked" : Number(id);
  const hashValue = id === "unlinked" ? "unlinked" : String(state.currentEntryId);
  if (location.hash !== `#entry=${hashValue}`) {
    history.replaceState(null, "", `#entry=${hashValue}`);
  }
  renderEntryList();
  scrollSelectedIntoView();
  const data = await fetchJson(id === "unlinked" ? "/api/entry/unlinked" : `/api/entry/${id}`);

  if (data.entry) {
    const meta = state.entries.find((row) => row.id === data.entry.id);
    const noPrefix = meta ? `#${meta.record_no} ` : "";
    $("entryTitle").textContent = `${noPrefix}${data.entry.title} （第 ${data.entry.page} 页）`;
    $("entryText").innerHTML = renderTextWithHighlights(data.entry.text, data.highlights);
    bindHighlightEvents($("entryText"));
  } else {
    $("entryTitle").textContent = "未关联条目的实体 / 问题";
    $("entryText").innerHTML = `<p class="placeholder-tip">这些实体的引用都没有成功解析到辞典条目，无法对照原文。\n请根据右侧引用出处文本人工核查。</p>`;
  }

  const refs = data.referenced_entities || [];
  $("entityCount").textContent =
    `${data.entities.length} 个实体` + (refs.length ? ` ・ ${refs.length} 个借引用` : "");
  $("entryIssues").innerHTML = data.issues.length
    ? `<details class="issue-box" open>
         <summary>本条目相关问题（${data.issues.length}）</summary>
         <ul>${data.issues
           .map(
             (i) =>
               `<li><span class="tag tag-red">${escapeHtml(i.label)}</span> ${escapeHtml(i.message)}</li>`
           )
           .join("")}</ul>
       </details>`
    : "";
  const currentEntryId = data.entry ? data.entry.id : null;
  const primaryHtml = data.entities.length
    ? data.entities.map((e) => renderEntityCard(e, currentEntryId)).join("")
    : `<p class="placeholder-tip">该条目没有主属实体（本身可能未产出实体，或仅被其他词条的实体引用）</p>`;
  const refHtml = refs.length
    ? `<details class="referenced-box">
         <summary>在本词条留有引用的其他实体（${refs.length}）—— 主属其他词条</summary>
         <div class="referenced-cards">${refs
           .map((e) => renderEntityCard(e, currentEntryId))
           .join("")}</div>
       </details>`
    : "";
  $("entityCards").innerHTML = primaryHtml + refHtml;
  bindCitationEvents($("entityCards"), $("entryText"));
}

/* ---------------- 实体全量弹窗 ---------------- */

async function openEntityModal(entityId) {
  const data = await fetchJson(`/api/entity/${entityId}`);
  const e = data.entity;
  state.currentEntityModalId = e.id;
  if (location.hash !== `#entity=${e.id}`) {
    history.replaceState(null, "", `#entity=${e.id}`);
  }
  $("modalTitle").textContent = `${e.title} （${e.type || "?"} #${e.id}）— 跨条目完整时间线`;
  $("modalTimeline").innerHTML =
    (e.chain_problems.length
      ? `<div class="chain-problems">⚠ ${e.chain_problems.map(escapeHtml).join("；")}</div>`
      : "") + e.timepoints.map((tp) => renderTimepoint(tp, null)).join("");
  $("modalEntries").innerHTML = data.entries.length
    ? data.entries
        .map(
          (entry) => `
        <details class="modal-entry" open>
          <summary>${escapeHtml(entry.title)} （第 ${escapeHtml(entry.page)} 页）</summary>
          <article class="entry-text">${renderTextWithHighlights(entry.text, entry.highlights)}</article>
        </details>`
        )
        .join("")
    : `<p class="placeholder-tip">该实体没有关联到任何辞典条目</p>`;
  bindCitationEvents($("modalTimeline"), $("modalEntries"));
  $("entityModal").classList.remove("hidden");
  if (entityEmbedMode && window.parent !== window) {
    window.parent.postMessage(
      { type: "song-bureaucracy:annotation-ready", entityId: e.id },
      "*"
    );
  }
}

function closeEntityModal({ syncHash = true } = {}) {
  if (state.currentEntityModalId === null) return;
  $("entityModal").classList.add("hidden");
  state.currentEntityModalId = null;
  if (!syncHash || state.currentEntryId === null) return;
  const entryId = state.currentEntryId === "unlinked" ? "unlinked" : String(state.currentEntryId);
  history.replaceState(null, "", `#entry=${entryId}`);
}

/* ---------------- 启动 ---------------- */

async function init() {
  [state.meta, state.entries, state.entities] = await Promise.all([
    fetchJson("/api/meta"),
    fetchJson("/api/entries"),
    fetchJson("/api/entities"),
  ]);
  renderMeta();
  renderEntryList();
  renderRecordToggle();

  $("entrySearch").addEventListener("input", (ev) => {
    state.filterText = ev.target.value;
    renderEntryList();
  });
  $("entrySearch").addEventListener("keydown", (ev) => {
    if (ev.key !== "Enter") return;
    const entity = matchingEntities()[0];
    if (entity) {
      ev.preventDefault();
      selectSearchedEntity(entity);
      return;
    }
    const entry = state.entries.find(entryVisible);
    if (entry) {
      ev.preventDefault();
      selectEntry(entry.id);
    }
  });
  $("onlyIssues").addEventListener("change", (ev) => {
    state.onlyIssues = ev.target.checked;
    renderEntryList();
  });
  $("toggleRecords").addEventListener("click", () => {
    state.showRecords = !state.showRecords;
    refreshCurrentView();
  });
  $("modalClose").addEventListener("click", () => closeEntityModal());
  $("entityModal").addEventListener("click", (ev) => {
    if (ev.target === $("entityModal")) closeEntityModal();
  });
  document.addEventListener("keydown", (ev) => {
    if (ev.key === "Escape") closeEntityModal();
  });

  const initialEntityId = readEntityFromHash();
  const initialEntity = state.entities.find((entity) => entity.id === initialEntityId);
  if (initialEntity) {
    await selectSearchedEntity(initialEntity);
  } else {
    const initialEntry = readEntryFromHash();
    if (initialEntry !== null) {
      const exists =
        initialEntry === "unlinked" ||
        state.entries.some((e) => String(e.id) === initialEntry);
      if (exists) {
        await selectEntry(initialEntry);
      }
    }
  }

  window.addEventListener("hashchange", () => {
    const entityId = readEntityFromHash();
    if (entityId !== null) {
      if (entityId === state.currentEntityModalId) return;
      const entity = state.entities.find((item) => item.id === entityId);
      if (entity) selectSearchedEntity(entity);
      return;
    }
    const id = readEntryFromHash();
    if (id === null) return;
    if (state.currentEntityModalId !== null) closeEntityModal({ syncHash: false });
    const sameAsCurrent =
      (id === "unlinked" && state.currentEntryId === "unlinked") ||
      (id !== "unlinked" && Number(id) === state.currentEntryId);
    if (!sameAsCurrent) selectEntry(id);
  });
}

init().catch((err) => {
  document.body.insertAdjacentHTML(
    "afterbegin",
    `<div class="fatal">加载失败：${escapeHtml(err.message)}（请确认 server.py 正在运行）</div>`
  );
});
