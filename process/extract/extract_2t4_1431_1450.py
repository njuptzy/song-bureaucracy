#!/usr/bin/env python3
"""提取 chapter2t4 第1431–1450条：太史局技术官、五官阶官与差遣。"""
import extract_2t4_1411_1430 as x

base = x.base
base.F = {i: base.load(i) for i in range(1431, 1451)}
F = base.F
W, Q, fe, ft = x.W, x.Q, x.fe, x.ft
cite, tp, rel, chain_all, refine = x.cite, x.tp, x.rel, x.chain_all, x.refine


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def alias(w, tid, i):
    for key in ("简称", "简称与别名", "别名"):
        if key in F[i]["fields"]:
            cite(w, "Timepoints", tid, i, field(i, key),
                 f"{F[i]['title']}称谓仅作名称证据。", key,
                 note="纯简称或别名")


def bureau(w, south=False):
    time = "南宋绍兴元年二月十九日" if south else "北宋元丰五年五月"
    return ft(w, fe(w, "太史局", "机构"), time)


def entry1431():
    i = 1431
    main, history, duty, grade = (
        Q(i, F[i]["text"]), field(i, "职源与沿革"),
        field(i, "职掌"), field(i, "官品"),
    )
    w = W(i)
    eid = w.entity("太史局正", "官职", "本条直接定义太史局正。",
                   quotation=main)
    active = tp(
        w, eid, "北宋元丰五年五月",
        "元丰新制始置，与丞同为太史局令佐贰；技术职事另有差遣",
        i, history, "太史局佐贰官", "建立太史局正元丰始置节点。",
        "职源与沿革", attr_officer_type="技术官", attr_grade="正八品",
        chain="none",
    )
    cite(w, "Timepoints", active, i, duty, "补证太史局正职掌。",
         "职掌")
    cite(w, "Timepoints", active, i, grade, "补证正八品。", "官品")
    alias(w, active, i)
    end = tp(
        w, eid, "南宋淳熙四年九月一日", "明令罢置",
        i, history, "太史局佐贰官", "建立太史局正淳熙罢置节点。",
        "职源与沿革", attr_officer_type="技术官", chain="none",
    )
    chain_all(w, eid, [active, end], "连接太史局正始置与罢置节点。")
    rel(w, bureau(w), active, "编制隶属", i, main,
        "太史局正为太史局令佐贰官。", staff_quota=1,
        staff_type="技术官")
    w.commit()


def entry1432():
    i = 1432
    main, history, duty, grade = (
        Q(i, F[i]["text"]), field(i, "职源与沿革"),
        field(i, "职掌"), field(i, "品位"),
    )
    w = W(i)
    eid = fe(w, "太史局丞", "官职")
    han = tp(w, eid, "西汉", "已有太史丞",
             i, history, "前代职源", "建立太史局丞西汉职源节点。",
             "职源与沿革", chain="none")
    tang1 = tp(w, eid, "唐久视元年", "改司天监为浑仪监，始置监丞",
               i, history, "前代职源", "建立太史局丞唐久视职源节点。",
               "职源与沿革", chain="none")
    tang2 = tp(w, eid, "唐开元十四年", "复改太史监为太史局，始置名符其实的太史局丞",
               i, history, "前代职源", "建立太史局丞唐开元职源节点。",
               "职源与沿革", chain="none")
    current = refine(
        w, ft(w, eid, "北宋元丰五年五月"), i, duty,
        "专条细化太史局丞职掌。", "职掌",
        event="元丰改司天监为太史局后置，与太史局正同为局令佐贰",
        category="太史局佐贰官", officer="技术官", grade="从八品",
    )
    cite(w, "Timepoints", current, i, history, "补证太史局丞职源。",
         "职源与沿革")
    cite(w, "Timepoints", current, i, grade, "补证从八品及位次。",
         "品位")
    alias(w, current, i)
    chain_all(w, eid, [han, tang1, tang2, current],
              "连接太史局丞西汉、唐代与北宋节点。")
    rel(w, bureau(w), current, "编制隶属", i, main,
        "太史局丞为太史局令佐贰官。", staff_type="技术官")
    w.commit()


def entry1433():
    i = 1433
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "太史局五官正", "官职")
    tid = refine(
        w, ft(w, eid, "北宋元丰五年五月"), i, main,
        "专条细化太史局五官正统称及判局资格。",
        event="春官正、夏官正、中官正、秋官正、冬官正总称；有资格差充判局官",
        category="太史局技术官统称", officer="技术官",
    )
    alias(w, tid, i)
    chain_all(w, eid, [tid], "确认太史局五官正单节点完整时间链。")
    for title in ("太史局春官正", "太史局夏官正", "太史局中官正",
                  "太史局秋官正", "太史局冬官正"):
        rel(w, tid, ft(w, fe(w, title, "官职"), "北宋元丰五年五月"),
            "统称与实例", i, main, f"{title}为太史局五官正实例。")
    w.commit()


def five_official(i, title):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, title, "官职")
    tid = refine(
        w, ft(w, eid, "北宋元丰五年五月"), i, main,
        f"专条细化{title}。", None,
        event=f"元丰新制由{title.replace('太史局', '司天监')}改名",
        category="太史局五官正", officer="技术官", grade="正八品",
    )
    alias(w, tid, i)
    chain_all(w, eid, [tid], f"确认{title}单节点完整时间链。")
    rel(w, bureau(w), tid, "编制隶属", i, main,
        f"{title}隶太史局。", staff_type="技术官")
    w.commit()


def entry1439():
    i = 1439
    main, history, duty, grade = (
        Q(i, F[i]["text"]), field(i, "职源与沿革"),
        field(i, "职掌"), field(i, "品位"),
    )
    w = W(i)
    eid = w.entity("太史局直长", "官职", "本条直接定义太史局直长。",
                   quotation=main)
    sui = tp(w, eid, "隋代", "直长之名始见，殿内省六尚局均置直长",
             i, history, "前代职源", "建立太史局直长隋代名源节点。",
             "职源与沿革", chain="none")
    song = tp(
        w, eid, "北宋元丰五年五月",
        "元丰新制始置，作为本局迁转官阶；灵台郎转直长，实际职事另有差遣",
        i, duty, "太史局迁转技术官", "建立太史局直长元丰节点。",
        "职掌", attr_officer_type="技术官", attr_grade="从八品",
        chain="none",
    )
    cite(w, "Timepoints", song, i, history, "补证直长名源与始置。",
         "职源与沿革")
    cite(w, "Timepoints", song, i, grade, "补证从八品及位次。",
         "品位")
    alias(w, song, i)
    chain_all(w, eid, [sui, song], "连接太史局直长隋代名源与北宋节点。")
    rel(w, bureau(w), song, "编制隶属", i, main,
        "太史局直长隶太史局。", staff_type="技术官")
    w.commit()


def refine_existing(i, title, event, grade_value, *, origin=None,
                    duty_field=None):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, title, "官职")
    nodes = []
    if origin:
        time, origin_event, source_field = origin
        quote = field(i, source_field) if source_field else main
        nodes.append(tp(
            w, eid, time, origin_event, i, quote, "前代职源",
            f"建立{title}{time}职源节点。", source_field, chain="none",
        ))
    quote = field(i, duty_field) if duty_field else main
    tid = refine(
        w, ft(w, eid, "北宋元丰五年五月"), i, quote,
        f"专条细化{title}。", duty_field,
        event=event, category="太史局技术官", officer="技术官",
        grade=grade_value,
    )
    if "职源与沿革" in F[i]["fields"]:
        cite(w, "Timepoints", tid, i, field(i, "职源与沿革"),
             f"补证{title}沿革。", "职源与沿革")
    if "品位" in F[i]["fields"]:
        cite(w, "Timepoints", tid, i, field(i, "品位"),
             f"补证{title}品位。", "品位")
    alias(w, tid, i)
    chain_all(w, eid, nodes + [tid], f"连接{title}完整时间链。")
    rel(w, bureau(w), tid, "编制隶属", i, main,
        f"{title}隶太史局。", staff_type="技术官")
    w.commit()


def entry1443():
    i = 1443
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("太史局五官大夫", "官职",
                   "本条直接定义五官大夫阶官总称。", quotation=main)
    tid = tp(
        w, eid, "南宋淳熙三年十二月二日",
        "始置春官、夏官、中官、秋官、冬官大夫五阶，供太史局官迁转",
        i, main, "太史局阶官统称", "建立太史局五官大夫始置节点。",
        attr_officer_type="阶官",
    )
    for key in ("职源", "职能", "品位"):
        cite(w, "Timepoints", tid, i, field(i, key),
             f"补证太史局五官大夫{key}。", key)
    alias(w, tid, i)
    rel(w, bureau(w, south=True), tid, "编制隶属", i, main,
        "太史局五官大夫为太史局官迁转阶官统称。",
        staff_type="阶官统称")
    w.commit()


def great_official(i, title, time, rank_event):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"本条直接定义{title}阶官。",
                   quotation=main)
    tid = tp(
        w, eid, time, rank_event, i, main, "太史局阶官",
        f"建立{title}始置节点。", attr_officer_type="阶官",
    )
    alias(w, tid, i)
    rel(w, bureau(w, south=True), tid, "编制隶属", i, main,
        f"{title}为太史局官迁转阶官。", staff_type="阶官")
    collective = ft(
        w, fe(w, "太史局五官大夫", "官职"),
        "南宋淳熙三年十二月二日",
    )
    rel(w, collective, tid, "统称与实例", i, main,
        f"{title}是太史局五官大夫实例。")
    w.commit()


def dispatch(i, title, event, quota=None):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"本条直接定义{title}差遣。",
                   quotation=main)
    tid = tp(
        w, eid, "南宋（太史局时期）", event, i, main, "太史局差遣",
        f"建立{title}南宋节点。", attr_officer_type="差遣",
    )
    alias(w, tid, i)
    rel(w, bureau(w, south=True), tid, "编制隶属", i, main,
        f"{title}由太史局官充任。", staff_quota=quota,
        staff_type="差遣")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1431, 1451)] == [
        "太史局正", "太史局丞", "太史局五官正", "太史局春官正",
        "太史局夏官正", "太史局中官正", "太史局秋官正",
        "太史局冬官正", "太史局直长", "太史局灵台郎",
        "太史局保章正", "太史局挈壶正", "太史局五官大夫",
        "春官大夫", "夏官大夫", "中官大夫", "秋官大夫",
        "冬官大夫", "太史局同知算造", "太史局主管御书神位官",
    ]
    entry1431()
    entry1432()
    entry1433()
    for i, title in enumerate((
        "太史局春官正", "太史局夏官正", "太史局中官正",
        "太史局秋官正", "太史局冬官正",
    ), 1434):
        five_official(i, title)
    entry1439()
    refine_existing(
        1440, "太史局灵台郎",
        "元丰新制由司天监灵台郎改名，灵台郎转官为直长",
        "从八品",
    )
    refine_existing(
        1441, "太史局保章正",
        "元丰新制由司天监保章正改名，掌历法并作为本监官迁转官阶",
        None,
        origin=("唐长安四年", "始置保章正", "职源与沿革"),
        duty_field="职掌",
    )
    refine_existing(
        1442, "太史局挈壶正",
        "元丰新制由司天监挈壶正改名，掌知漏刻",
        "正九品",
        origin=("唐长安二年", "始置太史局挈壶正", "职源与沿革"),
        duty_field="职掌",
    )
    entry1443()
    great_official(1444, "春官大夫", "南宋淳熙三年十二月十二日",
                   "始置；品位比和安大夫，位于夏官大夫之上")
    great_official(1445, "夏官大夫", "南宋淳熙三年十二月二日",
                   "始置；品位比成和大夫，位于中官大夫之上")
    great_official(1446, "中官大夫", "南宋淳熙三年十二月二日",
                   "始置；品位比成安大夫，位于秋官大夫之上")
    great_official(1447, "秋官大夫", "南宋淳熙三年十二月二日",
                   "始置；品位比成全大夫，位于冬官大夫之上")
    great_official(1448, "冬官大夫", "南宋淳熙三年十二月二日",
                   "始置；五官大夫最低一阶，高于五官正")
    dispatch(1449, "太史局同知算造", "由太史局官充，掌算造历书",
             quota=6)
    dispatch(
        1450, "太史局主管御书神位官",
        "由太史局官充，掌祭祀御书天地祖宗神位的安排、制作与守护",
        quota=1,
    )


if __name__ == "__main__":
    main()
