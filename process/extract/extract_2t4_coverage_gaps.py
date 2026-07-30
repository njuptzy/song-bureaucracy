#!/usr/bin/env python3
"""补齐 chapter2t4 全编审计发现的 15 条直接来源覆盖缺口。"""

import extract_2t4_1611_1630 as x


base = x.base
GAP_IDS = (10, 11, 12, 13, 165, 213, 635, 657, 733, 735, 741, 747, 796, 802, 805)
base.F = {i: base.load(i) for i in GAP_IDS}
F = base.F
W, Q, fe, ft = x.W, x.Q, x.fe, x.ft
cite, tp, rel, chain_all = x.cite, x.tp, x.rel, x.chain_all


def main_quote(i):
    return Q(i, F[i]["text"])


def cite_alias(i, targets, decision, note="纯简称、别称或典故称，不另建实体"):
    """把只含称谓证据的词条挂到被称对象，不制造别称实体。"""
    quotation = main_quote(i)
    w = W(i)
    for title, entity_type, time in targets:
        target = ft(w, fe(w, title, entity_type), time)
        cite(
            w,
            "Timepoints",
            target,
            i,
            quotation,
            decision,
            note=note,
        )
    w.commit()


def entry10():
    cite_alias(
        10,
        (("宰相", "官职", "元丰改制前"),),
        "补证首相、独相可称上宰、首台、首宰或冠台席。",
    )


def entry11():
    i = 11
    quotation = main_quote(i)
    w = W(i)
    cite(
        w,
        "Timepoints",
        ft(w, fe(w, "宰相", "官职"), "元丰改制前"),
        i,
        quotation,
        "补证宋前期二相可别称左相、右相。",
        note="纯相位称谓，不另建实体",
    )
    cite(
        w,
        "Timepoints",
        ft(w, fe(w, "侍中", "官职"), "宋前期"),
        i,
        quotation,
        "补证开府仪同三司兼侍中的使相亦可称左相。",
        note="称谓实例，不另建左相实体",
    )
    w.commit()


def entry12():
    cite_alias(
        12,
        (
            ("门下侍郎", "官职", "宋前期"),
            ("同中书门下平章事", "官职", "宋初"),
        ),
        "补证门下侍郎而同平章事者可称门下相。",
        note="复合官衔的简称，不另建实体",
    )


def entry13():
    cite_alias(
        13,
        (
            ("门下侍郎", "官职", "宋前期"),
            ("宰相", "官职", "元丰改制前"),
        ),
        "补证宋前期尚书左仆射兼门下侍郎、同平章事者可称揆门相。",
        note="复合官衔的典故称，不另建实体",
    )


def entry165():
    cite_alias(
        165,
        (("枢密使", "官职", "北宋初"),),
        "补证枢使是避父讳时对枢密使的寄理称。",
        note="寄理称，不另建实体",
    )


def entry213():
    cite_alias(
        213,
        (
            ("枢属", "官职", "未知"),
            ("枢密院编修", "官职", "南宋"),
        ),
        "补证枢掾即枢属，并见枢密院编修官实例。",
        note="简称及实例证据，不另建枢掾实体",
    )


def entry635():
    cite_alias(
        635,
        (("三省", "机构", "南宋"),),
        "补证三省相对于枢密院西府而别称东府。",
        note="机构别称，不另建实体",
    )


def entry657():
    cite_alias(
        657,
        (("二起居", "官职", "宋代（未载具体年月）"),),
        "补证唐宋以柱下史、柱下典称起居郎与起居舍人。",
        note="典故称，不另建实体",
    )


def entry733():
    cite_alias(
        733,
        (("都进奏院", "机构", "北宋太平兴国七年后（未载具体年月）"),),
        "补证都进奏院吏人因奏邸、进邸等称谓而别称邸吏。",
        note="吏人别称；原文未定义独立固定官职，不另建实体",
    )


def entry735():
    cite_alias(
        735,
        (("登闻院", "机构", "北宋雍熙元年七月十二日"),),
        "补证雍熙元年匦改称检及其纳贮投诉文书的器物性质。",
        note="器物名，不属于机构或官职，不另建实体",
    )


def entry741():
    cite_alias(
        741,
        (("登闻检院", "机构", "北宋景德四年五月"),),
        "补证天圣元年重设理检使时匦匣改称检匣。",
        note="器物名，不属于机构或官职，不另建实体",
    )


def entry747():
    cite_alias(
        747,
        (("匦院", "机构", "宋初"),),
        "补证匦院所设四匦的名称、方位与收受文书类别。",
        note="器物制度说明，不另建实体",
    )


def entry796():
    i = 796
    quotation = main_quote(i)
    w = W(i)
    eid = fe(w, "直舍人院", "官职")
    reform = ft(w, eid, "北宋元丰改制")
    south = ft(w, eid, "南宋嘉泰间")
    cite(
        w,
        "Timepoints",
        reform,
        i,
        quotation,
        "专条补证元丰改制罢直舍人院，暂摄者改称权中书舍人。",
    )
    cite(
        w,
        "Timepoints",
        south,
        i,
        quotation,
        "专条补证嘉泰四年李璧避祖讳而将权中书舍人易称直舍人院。",
        note="嘉泰四年的避讳特例",
    )
    rid = base.relation_id(
        w,
        "直舍人院",
        "权中书舍人",
        "前后演变",
        "北宋元丰改制",
        "北宋元丰改制",
    )
    assert rid
    cite(
        w,
        "Relationships",
        rid,
        i,
        quotation,
        "专条补证元丰后以权中书舍人取代暂摄的直舍人院。",
    )
    w.commit()


def entry802():
    i = 802
    quotation = main_quote(i)
    w = W(i)
    eid = w.entity(
        "都检正厅",
        "机构",
        "本条明确都检正厅是设于都堂内的官衙。",
        quotation=quotation,
    )
    tid = tp(
        w,
        eid,
        "北宋中书检正五房公事设置期间",
        "设于都堂内，为中书检正五房公事治所",
        i,
        quotation,
        "宰属官治所",
        "建立都检正厅制度时期节点；原条未给单独置罢年月。",
    )
    chain_all(w, eid, [tid], "确认都检正厅单节点时间链。")
    rel(
        w,
        tid,
        ft(w, fe(w, "检正中书五房公事", "官职"), "北宋熙宁三年九月一日"),
        "编制隶属",
        i,
        quotation,
        "都检正厅是中书检正五房公事的治所。",
        staff_type="官",
    )
    w.commit()


def entry805():
    i = 805
    quotation = main_quote(i)
    w = W(i)
    eid = w.entity(
        "检正厅",
        "机构",
        "本条明确检正厅是中书逐房检正公事的官司与治所。",
        quotation=quotation,
    )
    tid = tp(
        w,
        eid,
        "北宋中书检正逐房公事设置期间",
        "吏、户、礼、刑、孔目各房检正公事治所，置于都堂内",
        i,
        quotation,
        "宰属官治所",
        "建立检正厅制度时期节点；原条未给单独置罢年月。",
    )
    chain_all(w, eid, [tid], "确认检正厅单节点时间链。")
    rel(
        w,
        tid,
        ft(w, fe(w, "检正中书某房公事", "官职"), "北宋熙宁三年九月一日"),
        "编制隶属",
        i,
        quotation,
        "检正厅是中书逐房检正公事的治所。",
        staff_type="官",
    )
    w.commit()


def main():
    entry10()
    entry11()
    entry12()
    entry13()
    entry165()
    entry213()
    entry635()
    entry657()
    entry733()
    entry735()
    entry741()
    entry747()
    entry796()
    entry802()
    entry805()


if __name__ == "__main__":
    main()
