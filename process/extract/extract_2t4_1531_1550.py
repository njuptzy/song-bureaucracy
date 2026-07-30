#!/usr/bin/env python3
"""提取 chapter2t4 第1531–1550条：会要、九域图志书局官与诸书局吏。"""
import extract_2t4_1511_1530 as x

base = x.base
base.F = {i: base.load(i) for i in range(1531, 1551)}
F = base.F
W, Q, fe, ft = x.W, x.Q, x.fe, x.ft
cite, tp, rel, chain_all, refine = x.cite, x.tp, x.rel, x.chain_all, x.refine


def field(i, name):
    return Q(i, F[i]["fields"][name], name)


def alias(w, tid, i):
    if "简称" in F[i]["fields"]:
        cite(w, "Timepoints", tid, i, field(i, "简称"),
             f"{F[i]['title']}简称仅作名称证据。", "简称", note="纯简称")


def meeting_office(w):
    return ft(w, fe(w, "编修国朝会要所", "机构"), "南宋")


def book_bureaus(w):
    return [
        ("国史院", ft(w, fe(w, "国史院", "机构"),
                    "南宋绍兴二十八年七月十九日")),
        ("实录院", ft(w, fe(w, "实录院", "机构"),
                    "南宋绍兴十年二月以后")),
        ("会要所", meeting_office(w)),
        ("日历所", ft(w, fe(w, "国史日历所", "机构"),
                    "南宋绍兴十年四月二十八日")),
        ("编类圣政所", ft(w, fe(w, "编类圣政所", "机构"),
                       "南宋绍兴三十二年九月十一日")),
    ]


def meeting_post(i, title, event, officer_type):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"本条直接定义{title}。", quotation=main)
    tid = tp(w, eid, "宋代会要所时期", event, i, main, "会要所史官",
             f"建立{title}节点。", attr_officer_type=officer_type)
    alias(w, tid, i)
    rel(w, meeting_office(w), tid, "编制隶属", i, main,
        f"{title}参与会要所修书。", staff_type=officer_type)
    w.commit()


def entry1534():
    i = 1534
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("定《九域图志》所", "机构",
                   "本条直接定义增订九域图志的专设书局。", quotation=main)
    start = tp(w, eid, "北宋崇宁间", "始置，增订九域图志",
               i, main, "秘书省书局", "建立九域图志所崇宁始置节点。",
               chain="none")
    transfer = tp(w, eid, "北宋宣和二年六月",
                  "置所修九域图志，修书事务归秘书省官",
                  i, main, "秘书省书局", "建立九域图志所宣和节点。",
                  chain="none")
    chain_all(w, eid, [start, transfer], "连接九域图志所崇宁始置与宣和节点。")
    parent = ft(w, fe(w, "秘书省", "机构"), "宋前期")
    rel(w, parent, start, "上下级机构", i, main, "定九域图志所隶秘书省。")
    rel(w, parent, transfer, "上下级机构", i, main, "宣和修九域图志事归秘书省官。")
    w.commit()


def atlas_post(i, title, event, officer_type):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"本条直接定义{title}差遣。",
                   quotation=main)
    tid = tp(w, eid, "北宋九域图志所时期", event,
             i, main, "九域图志所差遣", f"建立{title}节点。",
             attr_officer_type=officer_type)
    rel(w, ft(w, fe(w, "定《九域图志》所", "机构"), "北宋崇宁间"),
        tid, "编制隶属", i, main, f"{title}隶定九域图志所。",
        staff_type=officer_type)
    w.commit()


def shared_book_officer(i, title, event, officer_type):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"本条直接定义诸修书局通设的{title}。",
                   quotation=main)
    tid = tp(w, eid, "宋代各修书局开局期间", event,
             i, main, "诸书局事务官", f"建立{title}诸书局通设节点。",
             attr_officer_type=officer_type)
    alias(w, tid, i)
    for label, bureau_tid in book_bureaus(w):
        rel(w, bureau_tid, tid, "编制隶属", i, main,
            f"{label}开局时设置{title}。", staff_type=officer_type)
    w.commit()


def entry1541():
    i = 1541
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "主管诸司官", "官职")
    generic = tp(
        w, eid, "宋代各修书局开局期间",
        "由内侍官充，可兼数局，指挥诸司人吏备办开局、修书、进呈及酒食物品，位次承受",
        i, main, "诸书局事务官", "建立主管诸司官诸书局通设节点。",
        attr_officer_type="内侍差遣", chain="none",
    )
    alias(w, generic, i)
    existing = ft(w, eid, "南宋乾道六年")
    chain_all(w, eid, [generic, existing],
              "连接主管诸司官通设节点与既有详定一司敕令所节点。")
    for label, bureau_tid in book_bureaus(w):
        rel(w, bureau_tid, generic, "编制隶属", i, main,
            f"{label}开局时设置主管诸司官。", staff_type="内侍差遣")
    w.commit()


def entry1542():
    i = 1542
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "楷书", "官职")
    old = ft(w, eid, "宋前期")
    tid = tp(w, eid, "宋代诸书局时期", "专事抄写书局文字",
             i, main, "书局书吏", "建立楷书诸书局节点。",
             attr_officer_type="吏", chain="none")
    chain_all(w, eid, [old, tid], "连接楷书起居院与诸书局节点。")
    w.commit()


def entry1543():
    i = 1543
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("供检楷书", "官职",
                   "本条定义供检文字、点检文字、楷书三种书吏连称。",
                   quotation=main)
    total = tp(w, eid, "宋代诸书局时期",
               "供检文字、点检文字、楷书三种名目书吏连称",
               i, main, "书局书吏统称", "建立供检楷书连称节点。",
               attr_officer_type="书吏统称")
    instances = [
        ("供检文字", ft(w, fe(w, "供检文字", "官职"), "北宋熙宁三年")),
        ("楷书", ft(w, fe(w, "楷书", "官职"), "宋代诸书局时期")),
    ]
    point_eid = w.entity("点检文字", "官职", "供检楷书条明确列举点检文字。",
                         quotation=main)
    point_tid = tp(w, point_eid, "宋代诸书局时期", "点检书局文字",
                   i, main, "书局书吏", "建立点检文字节点。",
                   attr_officer_type="吏")
    instances.append(("点检文字", point_tid))
    for label, instance_tid in instances:
        rel(w, total, instance_tid, "统称与实例", i, main,
            f"{label}是供检楷书连称的组成书吏。")
    w.commit()


def entry1544():
    i = 1544
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = fe(w, "书库官", "官职")
    north = ft(w, eid, "宋前期")
    generic = tp(w, eid, "宋代诸书局时期", "管理书局修书文稿",
                 i, main, "书局书吏", "建立书库官诸书局节点。",
                 attr_officer_type="吏", chain="none")
    south = ft(w, eid, "南宋（秘书省）")
    chain_all(w, eid, [north, generic, south],
              "连接书库官昭文馆、诸书局与南宋秘书省节点。")
    w.commit()


def simple_clerk(i, title, event, category="书局书吏"):
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity(title, "官职", f"本条直接定义{title}书局吏。",
                   quotation=main)
    tid = tp(w, eid, "宋代诸书局时期", event,
             i, main, category, f"建立{title}节点。", attr_officer_type="吏")
    w.commit()


def entry1547():
    i = 1547
    main = Q(i, F[i]["text"])
    w = W(i)
    eid = w.entity("背印", "官职", "本条直接定义诸书局背印官。",
                   quotation=main)
    seal = tp(w, eid, "宋代诸书局时期", "置于都大提举诸司、承受、主管诸司官名下，掌本司印记",
              i, main, "书局事务吏", "建立背印掌印节点。",
              attr_officer_type="吏", chain="none")
    later = tp(w, eid, "宋代后期", "未必掌印，演变为上司亲吏",
               i, main, "书局事务吏", "建立背印后期演变节点。",
               attr_officer_type="亲吏", chain="none")
    chain_all(w, eid, [seal, later], "连接背印掌印职能与后期亲吏演变节点。")
    w.commit()


def main():
    assert [F[i]["title"] for i in range(1531, 1551)] == [
        "编修会要所编修", "编修会要所参详", "编修会要所检阅文字",
        "定《九域图志》所", "定《九域图志》所详定", "定《九域图志》所参详",
        "定《九域图志》所编修", "都大提举诸司官", "承受官", "提举诸司",
        "主管诸司官", "楷书", "供检楷书", "书库官", "私名", "库子",
        "背印", "投送文字大程官", "投送文字亲事官", "快行亲从",
    ]
    assert F[1540]["fields"].get("__status__") == "placeholder"
    meeting_post(1531, "编修会要所编修", "从官兼任，参提修会要事", "从官兼史官")
    meeting_post(1532, "编修会要所参详", "庶官兼任，参与会要讨论、修订与定稿", "庶官兼史官")
    meeting_post(1533, "编修会要所检阅文字", "会要修书下笔官", "修书官")
    entry1534()
    atlas_post(1535, "定《九域图志》所详定", "侍从官充，主编九域图志增订", "侍从差遣")
    atlas_post(1536, "定《九域图志》所参详", "庶官充，参与修订讨论与定稿", "庶官差遣")
    atlas_post(1537, "定《九域图志》所编修", "庶官充，为修订九域图志执笔官", "庶官差遣")
    shared_book_officer(1538, "都大提举诸司官", "由内侍充，总管排办本院所事务，可跨局通用", "内侍差遣")
    shared_book_officer(1539, "承受官", "由内侍充，可兼二三局，承受进呈修书文字及应办事务，位次都大提举诸司官", "内侍差遣")
    entry1541()
    entry1542()
    entry1543()
    entry1544()
    simple_clerk(1545, "私名", "非正式编制人吏，抄写书局文字，请给依楷书")
    simple_clerk(1546, "库子", "向诸处关借书籍供修史并值守本局书库")
    entry1547()
    simple_clerk(1548, "投送文字大程官", "供远程投送书局文书差使")
    simple_clerk(1549, "投送文字亲事官", "供就近投送书局文书差使")
    simple_clerk(1550, "快行亲从", "置于书局三类事务官名下，随时召唤办理应急事务", "书局亲从")


if __name__ == "__main__":
    main()
