#!/usr/bin/env python3
"""提取 chapter2t4 第1411–1430条：三式官、司天监属院与太史局前段。"""
import extract_2t4_1391_1410 as x

base = x.base
base.F = {i: base.load(i) for i in range(1411, 1431)}
F = base.F
W, Q, fe, ft = x.W, x.Q, x.fe, x.ft
cite, tp, rel, chain_all, refine = x.cite, x.tp, x.rel, x.chain_all, x.refine


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def alias(w, tid, i):
    for key in ("简称", "别名"):
        if key in F[i]["fields"]:
            cite(w, "Timepoints", tid, i, field(i, key),
                 f"{F[i]['title']}称谓仅作名称证据。", key, note="纯简称或别名")


def monitor(w):
    return ft(w, fe(w, "司天监", "机构"), "北宋端拱元年九月")


def bureau(w, time="北宋元丰五年五月"):
    return ft(w, fe(w, "太史局", "机构"), time)


def specialty(i, title, event):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, title, "官职")
    tid = refine(
        w, ft(w, eid, "北宋（司天监时期）"), i, main,
        f"专条细化{title}职掌。",
        event=event, category="司天监三式技术官", officer="技术官",
    )
    chain_all(w, eid, [tid], f"确认{title}单节点完整时间链。")
    rel(
        w, ft(w, fe(w, "司天监三式科", "机构"), "北宋（司天监时期）"),
        tid, "编制隶属", i, main, f"{title}隶司天监三式科。",
        staff_type="技术官",
    )
    w.commit()


def simple_monitor_post(i, title, time, event, officer):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"第{i}条直接定义{title}。", quotation=main)
    tid = tp(w, eid, time, event, i, main, "司天监差遣",
             f"建立{title}节点。", attr_officer_type=officer)
    rel(w, monitor(w), tid, "编制隶属", i, main, f"{title}由司天监系统差充。",
        staff_type=officer)
    w.commit()


def entry1415():
    i = 1415
    main, history, duty, staff = Q(i, F[i]["text"]), field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制")
    w = W(i)
    old_e = w.entity("司天监天文院", "机构", "本条直接定义司天监天文院。", quotation=main)
    old_t = tp(w, old_e, "北宋初", "始置；浑仪台昼夜观测天象，每日汇送司天监并与翰林天文院结果勘比",
               i, history, "司天监观测机构", "建立司天监天文院北宋节点。", "职源与沿革")
    cite(w, "Timepoints", old_t, i, duty, "补证司天监天文院职掌。", "职掌")
    cite(w, "Timepoints", old_t, i, staff, "补证司天监天文院编制。", "编制")
    alias(w, old_t, i)
    new_e = w.entity("太史局天文院", "机构", "元丰五年改称太史局天文院。", quotation=history)
    new_t = tp(w, new_e, "北宋元丰五年", "由司天监天文院改置，掌浑仪台昼夜观测天象",
               i, history, "太史局观测机构", "建立太史局天文院元丰节点。", "职源与沿革")
    rel(w, monitor(w), old_t, "上下级机构", i, main, "司天监设置天文院。")
    rel(w, bureau(w), new_t, "上下级机构", i, history, "元丰后天文院隶太史局。", "职源与沿革")
    rel(w, old_t, new_t, "前后演变", i, history, "元丰五年司天监天文院改太史局天文院。", "职源与沿革")
    w.commit()


def staff_post(i, title, parent_title, event, officer, quota=None, time="北宋（司天监时期）"):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"第{i}条直接定义{title}。", quotation=main)
    tid = tp(w, eid, time, event, i, main, f"{parent_title}官属",
             f"建立{title}北宋节点。", attr_officer_type=officer)
    alias(w, tid, i)
    parent_time = "北宋初" if parent_title == "司天监天文院" else "北宋初"
    rel(w, ft(w, fe(w, parent_title, "机构"), parent_time), tid, "编制隶属",
        i, main, f"{title}隶{parent_title}。", staff_quota=quota, staff_type=officer)
    w.commit()


def entry1417():
    i = 1417
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("刻择官", "官职", "本条直接定义刻择官。", quotation=main)
    north = tp(w, eid, "北宋（司天监时期）", "掌祠祭、冠婚丧葬择吉避忌并供京百司择日",
               i, main, "天文院阴阳官", "建立刻择官司天监时期节点。",
               attr_officer_type="技术人", chain="none")
    reform = tp(w, eid, "北宋元丰五年以后", "改隶太史局天文院，继续掌择日",
                i, main, "天文院阴阳官", "建立刻择官元丰后节点。",
                attr_officer_type="技术人", chain="none")
    alias(w, north, i)
    chain_all(w, eid, [north, reform], "连接刻择官司天监与太史局时期节点。")
    rel(w, ft(w, fe(w, "司天监天文院", "机构"), "北宋初"), north, "编制隶属",
        i, main, "刻择官隶司天监天文院。", staff_quota=8, staff_type="技术人")
    rel(w, ft(w, fe(w, "太史局天文院", "机构"), "北宋元丰五年"), reform, "编制隶属",
        i, main, "元丰后刻择官改隶太史局天文院。", staff_type="技术人")
    w.commit()


def entry1419():
    i = 1419
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "测验浑仪刻漏所", "机构")
    north = tp(w, eid, "北宋（司天监时期）", "隶司天监，测验浑仪、窥测天象并考校历法",
               i, main, "天文观测机构", "建立测验浑仪刻漏所司天监时期节点。", chain="none")
    reform = tp(w, eid, "北宋元丰五年五月", "改隶太史局，统隶秘书省",
                i, main, "太史局所属机构", "建立测验浑仪刻漏所元丰节点。", chain="none")
    south = ft(w, eid, "南宋绍兴元年以后")
    cite(w, "Timepoints", south, i, main, "本条补证南宋沿太史局、秘书省系统。")
    alias(w, north, i)
    chain_all(w, eid, [north, reform, south], "连接测验浑仪刻漏所北宋至南宋节点。")
    rel(w, monitor(w), north, "上下级机构", i, main, "宋前期测验浑仪刻漏所隶司天监。")
    rel(w, bureau(w), reform, "上下级机构", i, main, "元丰后测验浑仪刻漏所隶太史局。")
    w.commit()


def entry1420():
    i = 1420
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("浑仪丞", "官职", "本条直接定义因事特置的浑仪丞。", quotation=main)
    tid = tp(w, eid, "北宋太平兴国四年正月", "张思训改造机械自动运转浑仪，因人临事特命为浑仪丞，原无此官",
             i, main, "测验浑仪刻漏所技术官", "建立浑仪丞特置节点。",
             attr_officer_type="技术官")
    rel(w, ft(w, fe(w, "测验浑仪刻漏所", "机构"), "北宋（司天监时期）"),
        tid, "编制隶属", i, main, "浑仪丞隶测验浑仪刻漏所。",
        staff_type="临时特置技术官")
    w.commit()


def entry1421():
    i = 1421
    main, history, duty, staff = Q(i, F[i]["text"]), field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制")
    w = W(i)
    eid = w.entity("钟鼓院", "机构", "本条直接定义司天监钟鼓院。", quotation=main)
    north = tp(w, eid, "北宋初", "始置，掌文德殿钟鼓楼击钟鼓报更、点、时并昼进时辰牌",
               i, history, "报时机构", "建立钟鼓院北宋初节点。", "职源与沿革", chain="none")
    reform = tp(w, eid, "北宋元丰五年五月", "改隶太史局，统隶秘书省",
                i, history, "太史局所属机构", "建立钟鼓院元丰节点。", "职源与沿革", chain="none")
    cite(w, "Timepoints", north, i, duty, "补证钟鼓院职掌。", "职掌")
    cite(w, "Timepoints", north, i, staff, "补证钟鼓院编制。", "编制")
    chain_all(w, eid, [north, reform], "连接钟鼓院司天监与太史局时期节点。")
    rel(w, monitor(w), north, "上下级机构", i, main, "宋初钟鼓院隶司天监。")
    rel(w, bureau(w), reform, "上下级机构", i, history, "元丰后钟鼓院隶太史局。", "职源与沿革")
    w.commit()


def entry1423():
    i = 1423
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("鸡唱", "官职", "本条直接定义钟鼓院鸡唱。", quotation=main)
    zhou = tp(w, eid, "先秦《周礼》", "已有鸡人氏报晓", i, main, "前代职源",
              "建立鸡唱周礼职源节点。", attr_officer_type="吏", chain="none")
    tang = tp(w, eid, "唐代", "有鸡人", i, main, "前代职源",
              "建立鸡唱唐代职源节点。", attr_officer_type="吏", chain="none")
    song = tp(w, eid, "北宋（钟鼓院）", "称鸡唱，昼间改时、夜间改更引唱专词",
              i, main, "钟鼓院吏人", "建立鸡唱北宋节点。",
              attr_officer_type="吏", chain="none")
    chain_all(w, eid, [zhou, tang, song], "连接鸡唱周礼、唐与宋代节点。")
    rel(w, ft(w, fe(w, "钟鼓院", "机构"), "北宋初"), song, "编制隶属",
        i, main, "鸡唱隶司天监钟鼓院。", staff_quota=3, staff_type="吏")
    w.commit()


def entry1424():
    i = 1424
    main, history, duty, staff = Q(i, F[i]["text"]), field(i, "职源与沿革"), field(i, "职掌"), field(i, "编制")
    w = W(i)
    eid = fe(w, "太史局", "机构")
    tang = tp(w, eid, "唐武德四年", "改太史监为太史局，太史局称谓之始",
              i, history, "前代职源", "建立太史局唐代名源节点。", "职源与沿革", chain="none")
    north = refine(w, ft(w, eid, "北宋元丰五年五月"), i, duty, "专条细化太史局元丰职掌。", "职掌",
                   event="元丰新制由司天监改置，观测天文、考定历法、占候奏闻、颁历并为礼仪择日",
                   category="中央天文机构")
    south = refine(w, ft(w, eid, "南宋绍兴元年二月十九日"), i, staff,
                   "专条补证南宋太史局沿置及复杂官属编制。", "编制",
                   event="南宋沿置；官属兼具迁转官阶与实际差遣，庆元五年另定职额",
                   category="中央天文机构")
    cite(w, "Timepoints", north, i, history, "补证元丰由司天监改太史局。", "职源与沿革")
    alias(w, north, i)
    chain_all(w, eid, [tang, north, south], "连接太史局唐代名源、北宋与南宋节点。")
    for child, ctime in (("太史局天文院", "北宋元丰五年"), ("测验浑仪刻漏所", "北宋元丰五年五月"), ("钟鼓院", "北宋元丰五年五月")):
        rel(w, north, ft(w, fe(w, child, "机构"), ctime), "上下级机构",
            i, staff, f"{child}为太史局所属机构。", "编制")
    w.commit()


def entry1425_1426():
    i = 1425
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("提举太史局所", "机构", "本条直接定义提举太史局所。", quotation=main)
    tid = tp(w, eid, "南宋绍熙五年闰十月十九日", "始置；统领太史局官属公事（占候由属官自奏），可直达奏闻",
             i, main, "太史局提举机构", "建立提举太史局所始置节点。")
    rel(w, tid, bureau(w, "南宋绍兴元年二月十九日"), "上下级机构",
        i, main, "提举太史局所统领太史局官属公事。")
    w.commit()
    i = 1426
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("提举太史局", "官职", "本条直接定义提举太史局差遣。", quotation=main)
    tid = tp(w, eid, "南宋绍熙五年闰十月十九日", "始置，以大两省以上侍从官充，提领太史局公事",
             i, main, "太史局提举差遣", "建立提举太史局始置节点。", attr_officer_type="差遣")
    alias(w, tid, i)
    rel(w, ft(w, fe(w, "提举太史局所", "机构"), "南宋绍熙五年闰十月十九日"),
        tid, "编制隶属", i, main, "提举太史局在提举太史局所治事。", staff_type="差遣")
    w.commit()


def judge(i, title, event):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"本条直接定义{title}差遣。", quotation=main)
    tid = tp(w, eid, "宋代太史局时期", event, i, main, "太史局判局差遣",
             f"建立{title}宋代节点。", attr_officer_type="差遣")
    alias(w, tid, i)
    rel(w, bureau(w), tid, "编制隶属", i, main, f"{title}判太史局事。", staff_type="差遣")
    w.commit()


def entry1429():
    i = 1429
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("判局官", "官职", "本条定义判太史局、同判太史局合称。", quotation=main)
    tid = tp(w, eid, "宋代太史局时期", "判太史局、同判太史局的合称",
             i, main, "太史局判局官统称", "建立判局官统称节点。", attr_officer_type="差遣统称")
    for title in ("判太史局", "同判太史局"):
        rel(w, tid, ft(w, fe(w, title, "官职"), "宋代太史局时期"), "统称与实例",
            i, main, f"{title}是判局官实例。")
    w.commit()


def entry1430():
    i = 1430
    main, history, duty, grade = Q(i, F[i]["text"]), field(i, "职源与沿革"), field(i, "职掌"), field(i, "官品")
    w = W(i)
    eid = w.entity("太史局令", "官职", "本条直接定义太史局令。", quotation=main)
    qin = tp(w, eid, "秦代", "有太史令胡毋敬", i, history, "前代职源",
             "建立太史局令秦代职源节点。", "职源与沿革", chain="none")
    tang = tp(w, eid, "唐武德四年", "始有太史局令之名", i, history, "前代职源",
              "建立太史局令唐代名源节点。", "职源与沿革", chain="none")
    song = tp(w, eid, "北宋元丰五年五月", "始置，为太史局长官，总一局之事",
              i, duty, "太史局长官", "建立太史局令元丰节点。", "职掌",
              attr_officer_type="技术官", attr_grade="从七品", chain="none")
    cite(w, "Timepoints", song, i, grade, "补证从七品。", "官品")
    alias(w, song, i)
    end = tp(w, eid, "南宋淳熙四年九月一日", "明令罢去不置",
             i, history, "太史局长官", "建立太史局令淳熙罢置节点。", "职源与沿革",
             attr_officer_type="技术官", chain="none")
    chain_all(w, eid, [qin, tang, song, end], "连接太史局令秦唐职源、元丰始置与淳熙罢置节点。")
    rel(w, bureau(w), song, "编制隶属", i, main, "太史局令为太史局长官。",
        staff_quota=1, staff_type="技术官")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1411, 1431)] == [
        "司天监三式科太乙", "司天监三式科遁甲", "监造历", "知算造",
        "司天监天文院", "测验记注", "刻择官", "押更", "测验浑仪刻漏所",
        "浑仪丞", "钟鼓院", "直官", "鸡唱", "太史局", "提举太史局所",
        "提举太史局", "判太史局", "同判太史局", "判局官", "太史局令",
    ]
    specialty(1411, "司天监三式科太乙", "以太乙岁时所居方位占卜祸福吉凶，又称符天术")
    specialty(1412, "司天监三式科遁甲", "以六甲循环推数占吉凶，又称雷公式")
    simple_monitor_post(1413, "监造历", "宋代（临时）", "内侍临时监督造历官改新历，新历成即罢", "差遣")
    simple_monitor_post(1414, "知算造", "北宋太平兴国年间", "由司天监官差充，掌推算、造历", "差遣")
    entry1415()
    staff_post(1416, "测验记注", "司天监天文院", "测验浑仪、记录日月星辰变化并每日上报", "技术官", 2)
    entry1417()
    staff_post(1418, "押更", "司天监天文院", "夜间轮流守更，及时报更报点", "吏", 15)
    entry1419()
    entry1420()
    entry1421()
    staff_post(1422, "直官", "钟鼓院", "白天卯至酉时逐时进象牙时辰牌", "吏", 3, "北宋（钟鼓院）")
    entry1423()
    entry1424()
    entry1425_1426()
    judge(1427, "判太史局", "由太史局五官正以上差充，判本局事")
    judge(1428, "同判太史局", "由太史局丞以上差充，资浅者带同字")
    entry1429()
    entry1430()


if __name__ == "__main__":
    main()
