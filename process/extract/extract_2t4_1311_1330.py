#!/usr/bin/env python3
"""提取 chapter2t4 第1311–1330条：秘书省诸案、四库与专门书库。"""
import extract_2t4_1291_1310 as x


base = x.base
base.F = {i: base.load(i) for i in range(1311, 1331)}
F = base.F
W = x.W
Q = x.Q
fe = x.fe
ft = x.ft
cite = x.cite
tp = x.tp
rel = x.rel
chain_all = x.chain_all
refine = x.refine
ft_any = x.ft_any


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def secretary_parent(w, time):
    return ft(w, fe(w, "秘书省", "机构"), time)


def entry1311():
    i = 1311
    main = Q(i, F[i]["text"])
    alias = field(i, "简称")
    w = W(i)
    eid = w.entity("秘书省都监司", "机构", "本条直接定义秘书省都监司。",
                   quotation=main)
    tid = tp(
        w, eid, "南宋（具体年月未载）", "秘书省都监治所",
        i, main, "秘书省所属机构", "建立秘书省都监司南宋节点。",
    )
    cite(
        w, "Timepoints", tid, i, alias,
        "简称“都监司”仅作称谓证据。", "简称", note="纯简称",
    )
    rel(
        w, secretary_parent(w, "南宋绍兴元年二月十九日"), tid,
        "上下级机构", i, main, "秘书省都监司是秘书省所属治所。",
    )
    w.commit()


def entry1312():
    i = 1312
    main = Q(i, F[i]["text"])
    alias = field(i, "简称")
    w = W(i)
    eid = w.entity("秘书省都监", "官职", "本条直接定义秘书省都监差遣。",
                   quotation=main)
    tid = tp(
        w, eid, "南宋（具体年月未载）",
        "由内侍充任，坐局监督抄写功课、本省出纳及临时排办公事",
        i, main, "秘书省内侍差遣", "建立秘书省都监南宋节点。",
        attr_officer_type="内侍",
    )
    cite(
        w, "Timepoints", tid, i, alias,
        "简称“都监”仅作称谓证据。", "简称", note="纯简称",
    )
    unit_e = fe(w, "秘书省都监司", "机构")
    rel(
        w, ft(w, unit_e, "南宋（具体年月未载）"), tid, "编制隶属",
        i, main, "秘书省都监在都监司治事。",
        staff_type="内侍官",
    )
    w.commit()


def entry1313():
    i = 1313
    main = Q(i, F[i]["text"])
    alias = field(i, "简称")
    w = W(i)
    eid = w.entity("秘书省承受官", "官职",
                   "本条直接定义秘书省承受官差遣。", quotation=main)
    tid = tp(
        w, eid, "北宋宣和间",
        "始置，由内侍充任，专治秘书省事，长贰听命",
        i, main, "秘书省内侍差遣", "建立秘书省承受官宣和节点。",
        attr_officer_type="内侍",
    )
    cite(
        w, "Timepoints", tid, i, alias,
        "简称“承受”及梁师成任职仅作称谓、实例证据。",
        "简称", note="简称兼任职实例",
    )
    rel(
        w, secretary_parent(w, "北宋宣和三年十一月"), tid, "编制隶属",
        i, main, "宣和间秘书省置承受官。",
        staff_type="内侍官",
    )
    w.commit()


def entry1314_1315():
    i = 1314
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "秘书省国史案", "机构")
    reform = refine(
        w, ft(w, eid, "北宋元丰五年五月"), i, main,
        "专条细化国史案职掌。", None,
        event="掌修国史、实录与编修日历，旧史馆、日历所并入",
        category="秘书省办事机构",
    )
    yuanyou = tp(
        w, eid, "北宋元祐元年",
        "修国史、实录事务转归门下省国史院",
        i, main, "秘书省办事机构", "建立国史案元祐事务转出节点。",
        chain="none",
    )
    shaosheng = tp(
        w, eid, "北宋绍圣二年三月二十四日",
        "改名秘书省日历案",
        i, main, "秘书省办事机构", "建立国史案改名节点。",
        chain="none",
    )
    shaoxing = tp(
        w, eid, "南宋绍兴十年二月",
        "史馆罢置，修史事务复归秘书省国史案",
        i, main, "秘书省办事机构", "建立国史案绍兴复掌修史节点。",
        chain="none",
    )
    chain_all(
        w, eid, [reform, yuanyou, shaosheng, shaoxing],
        "连接秘书省国史案元丰至绍兴完整时间链。",
    )
    rel(
        w, secretary_parent(w, "北宋元丰五年五月"), reform, "上下级机构",
        i, main, "元丰秘书省设置国史案。",
    )
    rel(
        w, secretary_parent(w, "南宋绍兴五年八月三日"), shaoxing,
        "上下级机构", i, main, "绍兴十年史馆罢归秘书省国史案。",
    )
    w.commit()

    i = 1315
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("秘书省日历案", "机构",
                   "本条直接定义秘书省日历案。", quotation=main)
    start = tp(
        w, eid, "北宋绍圣二年三月二十四日",
        "由秘书省国史案改名，专掌修日历，又称秘书省日历所",
        i, main, "秘书省办事机构", "建立秘书省日历案始置节点。",
        chain="none",
    )
    end = tp(
        w, eid, "北宋宣和二年八月二十二日", "罢置",
        i, main, "秘书省办事机构", "建立秘书省日历案罢置节点。",
        chain="none",
    )
    chain_all(w, eid, [start, end], "连接秘书省日历案始置与罢置节点。")
    old_e = fe(w, "秘书省国史案", "机构")
    rel(
        w, ft(w, old_e, "北宋绍圣二年三月二十四日"), start,
        "前后演变", i, main, "绍圣二年国史案改名日历案。",
    )
    rel(
        w, secretary_parent(w, "北宋政和六年"), start, "上下级机构",
        i, main, "秘书省日历案隶秘书省。",
    )
    w.commit()


def refine_case(i, title, times, event):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, title, "机构")
    tids = []
    for time in times:
        tids.append(refine(
            w, ft(w, eid, time), i, main,
            f"专条细化{title}{time}职掌。", None,
            event=event, category="秘书省办事机构",
        ))
    chain_all(w, eid, tids, f"确认{title}完整时间链。")
    w.commit()


def entry1320():
    i = 1320
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "秘书省道教案", "机构")
    north = refine(
        w, ft_any(w, eid, "北宋政和六年", "北宋政和六年二月八日"), i, main,
        "专条细化秘书省道教案精确始置日与职掌。", None,
        time="北宋政和六年二月八日",
        event="鸿胪寺道教事务拨归秘书省，设案掌道录院道官名籍与迁转",
        category="秘书省办事机构",
    )
    south = tp(
        w, eid, "南宋", "不置",
        i, main, "秘书省办事机构", "建立秘书省道教案南宋不置节点。",
        chain="none",
    )
    chain_all(w, eid, [north, south], "连接道教案政和始置与南宋不置节点。")
    rel(
        w, secretary_parent(w, "北宋政和六年"), north, "上下级机构",
        i, main, "政和六年秘书省设置道教案。",
    )
    w.commit()


def grouped_libraries(i, title, instance_titles, *, alias_field=None):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "机构", f"第{i}条直接定义秘书省书库合称{title}。",
                   quotation=main)
    tid = tp(
        w, eid, "南宋（具体年月未载）", "秘书省书库合称",
        i, main, "秘书省书库统称", f"建立{title}南宋节点。",
    )
    if alias_field:
        cite(
            w, "Timepoints", tid, i, field(i, alias_field),
            f"{title}简称仅作称谓证据。", alias_field, note="纯简称",
        )
    rel(
        w, secretary_parent(w, "南宋绍兴元年二月十九日"), tid,
        "上下级机构", i, main, f"{title}隶秘书省。",
    )
    for instance_title in instance_titles:
        instance_e = w.entity(
            instance_title, "机构", f"{title}由{instance_title}等实例组成。",
            quotation=main,
        )
        instance_t = tp(
            w, instance_e, "南宋（具体年月未载）", f"{title}的分库",
            i, main, "秘书省书库", f"建立{instance_title}南宋节点。",
        )
        rel(
            w, tid, instance_t, "统称与实例", i, main,
            f"{instance_title}是{title}的实例。",
        )
    w.commit()


def library(i, title, event):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "机构", f"第{i}条直接定义秘书省所属{title}。",
                   quotation=main)
    tid = tp(
        w, eid, "南宋（具体年月未载）", event,
        i, main, "秘书省书库", f"建立{title}南宋节点。",
    )
    rel(
        w, secretary_parent(w, "南宋绍兴元年二月十九日"), tid,
        "上下级机构", i, main, f"{title}隶秘书省。",
    )
    if i == 1329:
        post_e = w.entity(
            "公使库监库官", "官职", "公使库条明确置监库官一名。",
            quotation=main,
        )
        post_t = tp(
            w, post_e, "南宋（具体年月未载）",
            "监督公使钱及公用银器什物收支，由有官品吏人充任",
            i, main, "秘书省库官", "建立公使库监库官南宋节点。",
            attr_officer_type="有官品吏人",
        )
        rel(
            w, tid, post_t, "编制隶属", i, main,
            "公使库置监库官一名。",
            staff_quota=1, staff_type="有官品吏人",
        )
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1311, 1331)] == [
        "秘书省都监司", "秘书省都监", "秘书省承受官", "秘书省国史案",
        "秘书省日历案", "秘书省知杂案", "秘书省经籍案", "秘书省祝版案",
        "秘书省太史案", "秘书省道教案", "经、史、子、集四库",
        "续搜访经、史、子、集四库", "秘阁上、下库",
        "御制御札名贤墨迹图画库", "古器库", "印板书库", "印板库",
        "碑石库", "公使库", "国史库",
    ]
    entry1311()
    entry1312()
    entry1313()
    entry1314_1315()
    refine_case(
        1316, "秘书省知杂案",
        ["北宋元丰五年五月", "南宋绍兴元年二月十九日"],
        "掌省官到替迁转、祠祭差充献官及吏人迁补等杂事",
    )
    refine_case(
        1317, "秘书省经籍案",
        ["北宋元丰五年五月", "南宋绍兴元年二月十九日"],
        "掌秘阁御制书画及四库书籍、典故检阅、御前索书画与祠祭乐章",
    )
    refine_case(
        1318, "秘书省祝版案", ["南宋绍兴元年二月十九日"],
        "掌祠祭祝版制造、祝文撰写及宗室以上葬礼祭文",
    )
    refine_case(
        1319, "秘书省太史案",
        ["北宋元丰五年五月", "南宋绍兴元年二月十九日"],
        "掌太史局、历日所、钟鼓院、浑仪刻漏所官员与局生迁补",
    )
    entry1320()
    grouped_libraries(
        1321, "经、史、子、集四库", ["经库", "史库", "子库", "集库"],
    )
    grouped_libraries(
        1322, "续搜访经、史、子、集四库",
        ["续搜访经库", "续搜访史库", "续搜访子库", "续搜访集库"],
        alias_field="简称",
    )
    grouped_libraries(
        1323, "秘阁上、下库", ["秘阁上库", "秘阁下库"],
    )
    for i, title, event in (
        (1324, "御制御札名贤墨迹图画库",
         "收藏本朝帝王名臣诗词文章、书法与图画"),
        (1325, "古器库", "收藏历代青铜、玉石及金银器物"),
        (1326, "印板书库", "收藏诸州雕板印刷书籍"),
        (1327, "印板库", "收藏已雕印板，供随时重印书籍"),
        (1328, "碑石库", "收藏御书、历代书法墨迹及本朝题名石刻"),
        (1329, "公使库", "掌收支公使钱及公用银器什物"),
        (1330, "国史库", "收藏本朝日历、时政记、起居注等当代史籍"),
    ):
        library(i, title, event)


if __name__ == "__main__":
    main()
