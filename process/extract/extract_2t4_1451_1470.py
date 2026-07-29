#!/usr/bin/env python3
"""提取 chapter2t4 第1451–1470条：太史局三科、别局、差遣与局生。"""
import extract_2t4_1431_1450 as x

base = x.base
base.F = {i: base.load(i) for i in range(1451, 1471)}
F = base.F
W, Q, fe, ft = x.W, x.Q, x.fe, x.ft
cite, tp, rel, chain_all, refine = x.cite, x.tp, x.rel, x.chain_all, x.refine


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def alias(w, tid, i):
    if "简称" in F[i]["fields"]:
        cite(w, "Timepoints", tid, i, field(i, "简称"),
             f"{F[i]['title']}简称仅作名称证据。", "简称", note="纯简称")


def bureau(w, south=False):
    time = "南宋绍兴元年二月十九日" if south else "北宋元丰五年五月"
    return ft(w, fe(w, "太史局", "机构"), time)


def monitor(w):
    return ft(w, fe(w, "司天监", "机构"), "北宋端拱元年九月")


def branch(i, title, former):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "机构", f"本条直接定义{title}。", quotation=main)
    tid = tp(w, eid, "北宋元丰五年五月", f"元丰新制由{former}改名",
             i, main, "太史局教学机构", f"建立{title}元丰节点。")
    rel(w, bureau(w), tid, "上下级机构", i, main, f"{title}隶太史局。")
    rel(w, ft(w, fe(w, former, "机构"), "北宋（司天监时期）"),
        tid, "前后演变", i, main, f"元丰新制{former}改名为{title}。")
    w.commit()


def dispatch(i, title, event, parent=None, quota=None, time="南宋（太史局时期）"):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"本条直接定义{title}差遣。",
                   quotation=main)
    tid = tp(w, eid, time, event, i, main, "太史局差遣",
             f"建立{title}节点。", attr_officer_type="差遣")
    alias(w, tid, i)
    if parent == "太史局天文院":
        parent_tid = ft(w, fe(w, parent, "机构"), "北宋元丰五年")
    elif parent == "测验浑仪刻漏所":
        parent_time = (
            "南宋绍兴元年以后"
            if time.startswith("南宋") else "北宋元丰五年五月"
        )
        parent_tid = ft(w, fe(w, parent, "机构"), parent_time)
    elif parent == "钟鼓院":
        parent_time = (
            "南宋（秘书省太史局时期）"
            if time.startswith("南宋") else "北宋元丰五年五月"
        )
        parent_tid = ft(w, fe(w, parent, "机构"), parent_time)
    else:
        parent_tid = bureau(w, south=True)
    rel(w, parent_tid, tid, "编制隶属", i, main,
        f"{title}由太史局官差充。", staff_quota=quota,
        staff_type="差遣")
    w.commit()


def entry1452():
    i = 1452
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("太史局天文官", "官职", "本条直接定义太史局天文官差遣。",
                   quotation=main)
    tid = tp(w, eid, "宋代太史局时期",
             "由太史局官充，观测天象、值宿宫内备顾问并教习天文学生",
             i, main, "太史局天文差遣", "建立太史局天文官节点。",
             attr_officer_type="差遣")
    alias(w, tid, i)
    rel(w, bureau(w), tid, "编制隶属", i, main,
        "太史局天文官由太史局官充。", staff_type="差遣")
    rel(w, ft(w, fe(w, "司天监天文官", "官职"), "北宋（司天监时期）"),
        tid, "前后演变", i, main,
        "元丰改制后司天监天文官改属太史局系统。")
    w.commit()


def entry1454():
    i = 1454
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("太史局历算", "官职", "本条直接定义太史局历算差遣。",
                   quotation=main)
    tid = tp(w, eid, "北宋元丰五年五月", "元丰新制由司天监历算改名",
             i, main, "太史局历算差遣", "建立太史局历算元丰节点。",
             attr_officer_type="差遣")
    alias(w, tid, i)
    rel(w, bureau(w), tid, "编制隶属", i, main,
        "太史局历算由太史局官充。", staff_type="差遣")
    rel(w, ft(w, fe(w, "司天监历算", "官职"), "北宋（司天监时期）"),
        tid, "前后演变", i, main, "元丰新制司天监历算改名太史局历算。")
    w.commit()


def entry1456():
    i = 1456
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("太史局三科", "机构", "本条定义太史局天文、历算、三式科总称。",
                   quotation=main)
    tid = tp(w, eid, "北宋元丰五年五月",
             "由司天监三科改名，为太史局天文、历算、三式科总称",
             i, main, "太史局教学机构统称", "建立太史局三科统称节点。")
    alias(w, tid, i)
    for title in ("太史局天文科", "太史局历算科", "太史局三式科"):
        rel(w, tid, ft(w, fe(w, title, "机构"), "北宋元丰五年五月"),
            "统称与实例", i, main, f"{title}是太史局三科实例。")
    w.commit()


def entry1457():
    i = 1457
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "太史局天文院", "机构")
    tid = refine(w, ft(w, eid, "北宋元丰五年"), i, main,
                 "专条补证太史局天文院隶属与改名。",
                 event="元丰新制由司天监天文院改名，隶秘书省太史局",
                 category="太史局观测机构")
    alias(w, tid, i)
    chain_all(w, eid, [tid], "确认太史局天文院单节点完整时间链。")
    rel(w, bureau(w), tid, "上下级机构", i, main, "太史局天文院隶太史局。")
    w.commit()


def entry1459():
    i = 1459
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "测验浑仪刻漏所", "机构")
    reform = ft(w, eid, "北宋元丰五年五月")
    cite(w, "Timepoints", reform, i, main,
         "专条补证元丰后测验浑仪刻漏所改隶太史局、统隶秘书省。")
    alias(w, reform, i)
    w.commit()


def entry1462():
    i = 1462
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("秤漏官", "官职", "本条直接定义秤漏官差遣。",
                   quotation=main)
    tid = tp(w, eid, "南宋（太史局时期）",
             "及时移动漏刻平准水位的水秤，使漏刻正常运转、计时准确",
             i, main, "刻漏差遣", "建立秤漏官南宋节点。",
             attr_officer_type="差遣")
    rel(w, ft(w, fe(w, "测验浑仪刻漏所", "机构"), "南宋绍兴元年以后"),
        tid, "编制隶属", i, main, "秤漏官掌漏刻水秤。",
        staff_quota=1, staff_type="差遣")
    w.commit()


def entry1463():
    i = 1463
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "钟鼓院", "机构")
    north = ft(w, eid, "北宋初")
    reform = ft(w, eid, "北宋元丰五年五月")
    south = tp(w, eid, "南宋（秘书省太史局时期）",
               "沿置文德殿钟鼓院，掌钟鼓楼刻漏、进牌报时",
               i, main, "太史局报时机构", "建立钟鼓院南宋节点。",
               chain="none")
    cite(w, "Timepoints", north, i, main, "补证改制前钟鼓院原隶司天监。")
    cite(w, "Timepoints", reform, i, main, "补证元丰后钟鼓院改隶太史局。")
    alias(w, south, i)
    chain_all(w, eid, [north, reform, south], "连接钟鼓院北宋初、元丰与南宋节点。")
    rel(w, bureau(w, south=True), south, "上下级机构", i, main,
        "南宋文德殿钟鼓院隶秘书省太史局。")
    w.commit()


def entry1466():
    i = 1466
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("印历所", "机构", "本条直接定义印历所监当局。",
                   quotation=main)
    north = tp(w, eid, "北宋（司天监时期）", "隶司天监，印造颁赐新历",
               i, main, "印历机构", "建立印历所司天监时期节点。",
               chain="none")
    reform = tp(w, eid, "北宋元丰五年五月",
                "改隶秘书省太史局，承印笺注后的新历",
                i, main, "太史局所属机构", "建立印历所元丰节点。",
                chain="none")
    south = tp(w, eid, "南宋乾道四年五月",
               "印毕雕板移交榷货务，挖去臣字后加印向民间出售，每本三百文",
               i, main, "太史局所属机构", "建立印历所乾道节点。",
               chain="none")
    chain_all(w, eid, [north, reform, south], "连接印历所司天监、太史局与乾道节点。")
    rel(w, monitor(w), north, "上下级机构", i, main, "元丰前印历所隶司天监。")
    rel(w, bureau(w), reform, "上下级机构", i, main, "元丰后印历所隶太史局。")
    w.commit()


def entry1467():
    i = 1467
    main, history, function = Q(i, F[i]["text"]), field(i, "职源与沿革"), field(i, "职能")
    w = W(i)
    eid = w.entity("司历", "官职", "本条直接定义太史局司历。", quotation=main)
    lu = tp(w, eid, "鲁襄公二十七年", "始见司历官名",
            i, history, "前代职源", "建立司历先秦名源节点。",
            "职源与沿革", chain="none")
    sui = tp(w, eid, "隋代", "置司历官", i, history, "前代职源",
             "建立司历隋代节点。", "职源与沿革", chain="none")
    song = tp(w, eid, "宋代太史局时期",
              "参与造历，并作为历生递迁出职之阶",
              i, function, "太史局历官", "建立司历宋代节点。",
              "职能", attr_officer_type="历官", chain="none")
    chain_all(w, eid, [lu, sui, song], "连接司历先秦、隋与宋代节点。")
    rel(w, bureau(w), song, "编制隶属", i, main, "司历隶太史局。",
        staff_type="历官")
    w.commit()


def entry1468():
    i = 1468
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("局生", "官职", "本条直接定义太史局局生官阶。",
                   quotation=main)
    tid = tp(w, eid, "南宋淳熙四年八月十四日",
             "定为天文官十六阶最低阶；诸处学生祗应五年试补，艺业精通者转挈壶正",
             i, main, "太史局技术官阶", "建立局生淳熙定阶节点。",
             attr_officer_type="官名、阶名")
    rel(w, bureau(w, south=True), tid, "编制隶属", i, main,
        "局生为太史局学生试补之官阶。", staff_type="技术官阶")
    rel(w, tid, ft(w, fe(w, "太史局挈壶正", "官职"), "北宋元丰五年五月"),
        "前后演变", i, main, "局生经考试艺业精通转为挈壶正。")
    w.commit()


def entry1469_1470():
    i = 1469
    main = Q(i, F[i]["text"])
    w = W(i)
    total_e = w.entity("礼历生", "官职", "本条定义太史局礼生、历生连称。",
                       quotation=main)
    total_t = tp(w, total_e, "宋代太史局时期", "太史局礼生、历生连称",
                 i, main, "太史局吏人统称", "建立礼历生统称节点。",
                 attr_officer_type="吏人统称")
    children = {}
    for title in ("太史局礼生", "太史局历生"):
        eid = w.entity(title, "官职", f"礼历生条明确列举{title}。",
                       quotation=main)
        tid = tp(w, eid, "宋代太史局时期", "太史局行遣文字吏人",
                 i, main, "太史局吏人", f"建立{title}节点。",
                 attr_officer_type="吏")
        children[title] = (eid, tid)
        rel(w, total_t, tid, "统称与实例", i, main,
            f"{title}是礼历生实例。")
    w.commit()

    i = 1470
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "太史局历生", "官职")
    tid = refine(
        w, ft(w, eid, "宋代太史局时期"), i, main,
        "专条细化太史局历生来源、职掌和类别。",
        event="由局学生试补，掌行遣文字，或在司历下习学供职；分司历历生与行遣文字历生",
        category="太史局吏人", officer="吏",
    )
    chain_all(w, eid, [tid], "确认太史局历生单节点完整时间链。")
    rel(w, bureau(w), tid, "编制隶属", i, main, "历生隶太史局。",
        staff_type="吏")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1451, 1471)] == [
        "太史局天文科", "太史局天文官", "太史局历算科",
        "太史局历算", "太史局三式科", "太史局三科", "太史局天文院",
        "酉点天文日状官", "测验浑仪刻漏所", "主管测验浑仪刻漏所",
        "主管影表官", "秤漏官", "文德殿钟鼓院", "主管文德殿钟鼓院",
        "星漏官", "印历所", "司历", "局生", "礼历生", "历生",
    ]
    branch(1451, "太史局天文科", "司天监天文科")
    entry1452()
    branch(1453, "太史局历算科", "司天监历算科")
    entry1454()
    branch(1455, "太史局三式科", "司天监三式科")
    entry1456()
    entry1457()
    dispatch(1458, "酉点天文日状官",
             "每夜将天文院所占星辰、风云、流星等祯祥灾异书状奏闻",
             parent="太史局天文院", quota=2,
             time="南宋庆元五年二月")
    entry1459()
    dispatch(1460, "主管测验浑仪刻漏所", "掌领测验浑仪刻漏所公事",
             parent="测验浑仪刻漏所")
    dispatch(1461, "主管影表官",
             "测验圭表日影长短，以正方位、定时节、考闰朔")
    entry1462()
    entry1463()
    dispatch(1464, "主管文德殿钟鼓院",
             "掌领钟鼓院刻漏、进时辰牌等报时公事",
             parent="钟鼓院", quota=2)
    dispatch(1465, "星漏官", "掌钟鼓院刻漏计更、计点",
             parent="钟鼓院")
    entry1466()
    entry1467()
    entry1468()
    entry1469_1470()


if __name__ == "__main__":
    main()
