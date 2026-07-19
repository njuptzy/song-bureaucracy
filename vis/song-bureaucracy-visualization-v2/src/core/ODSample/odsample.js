import {kdTree} from "@/utils/KDTree";
import {Point} from "@/utils/Geometry";
import * as d3 from "d3";

export function SRC(d) {
    // return [d.src_x_coord, d.src_y_coord];
    return new Point(d.src_x_coord, d.src_y_coord);
}

export function DST(d) {
    // return [d.dst_x_coord, d.dst_y_coord];
    return new Point(d.dst_x_coord, d.dst_y_coord);
}

function distance(a, b) {
    return Math.sqrt((a[0] - b[0]) * (a[0] - b[0]) + (a[1] - b[1]) * (a[1] - b[1]));
}

export function ODSample(odData, theta, selectNum, polygon = null, longSkipCondition) {
    // let srcKdTree = new kdTree(odData.map((d, i) => ({id: i, x: SRC(d)[0], y: SRC(d)[1]})), distance_kdTree, ['x', 'y']);
    // let dstKdTree = new kdTree(odData.map((d, i) => ({id: i, x: DST(d)[0], y: DST(d)[1]})), distance_kdTree, ['x', 'y']);
    let candidate = [];
    let selected = [];
    // console.log(polygon);
    let skip = d3.range(odData.length);
    let short_skip = d3.range(odData.length);
    for (let i = 0; i < odData.length; ++i) {
        skip[i] = false;
        if (!longSkipCondition) {
            short_skip[i] = (distance(SRC(odData[i]), DST(odData[i])) < theta);
        }
        else {
            short_skip[i] = distance(SRC(odData[i]), DST(odData[i])) > longSkipCondition || distance(SRC(odData[i]), DST(odData[i])) < theta / 2;
        }

        if (polygon) {
            if (!d3.polygonContains(polygon, SRC(odData[i])) && !d3.polygonContains(polygon, DST(odData[i]))) {
                skip[i] = true;
            }
        }
    }
    for (let i = 0; i < odData.length; ++i) {
        if (skip[i] || short_skip[i]) {
            continue;
        }
        let cur = {};
        candidate.push(cur);
        let src_x = 0, src_y = 0, dst_x = 0, dst_y = 0;
        let cnt = 0;
        let counter = [{}, {}];
        let personList = [];
        for (let j = 0; j < odData.length; ++j) {
            if (skip[j] || short_skip[j]) {
                continue;
            }
            let sd = distance(SRC(odData[i]), SRC(odData[j]));
            let dd = distance(DST(odData[i]), DST(odData[j]));
            if (sd <= theta && dd <= theta) {
                cnt += 1;
                src_x += odData[j].src_x_coord;
                src_y += odData[j].src_y_coord;
                dst_x += odData[j].dst_x_coord;
                dst_y += odData[j].dst_y_coord;
                if (!counter[0][odData[j].src_name]) {
                    counter[0][odData[j].src_name] = 0;
                }
                counter[0][odData[j].src_name]++;
                if (!counter[1][odData[j].dst_name]) {
                    counter[1][odData[j].dst_name] = 0;
                }
                counter[1][odData[j].dst_name]++;
                personList.push(odData[j]);
            }
            if (sd < theta / 3 && dd < theta / 3) {
                skip[j] = true;
            }
        }
        cur.value = cnt;
        cur.src_x_coord = src_x / cnt;
        cur.src_y_coord = src_y / cnt;
        cur.dst_x_coord = dst_x / cnt;
        cur.dst_y_coord = dst_y / cnt;
        cur.ang = SRC(cur).sub(DST(cur)).angle();
        cur.counter = counter.map(c => Object.entries(c).sort((a, b) => b[1] - a[1]).slice(0, 5));
        cur.personList = personList;
    }
    candidate.sort((a, b) => a.value - b.value);
    candidate.reverse();
    // console.log(candidate);
    for (let i = 0; i < selectNum; ++i) {
        for (let j = 0; j < candidate.length; ++j) {
            let flag = true;
            for (let k = 0; k < i; ++k) {
                let sd = distance(SRC(candidate[j]), SRC(selected[k]));
                let dd = distance(DST(candidate[j]), DST(selected[k]));
                if (sd < 2 * theta && dd < 2 * theta) {
                    flag = false;
                    break;
                }
            }
            if (flag) {
                candidate[j].id = i;
                selected.push(candidate[j]);
                break;
            }
        }
    }
    // console.log(selected);
    let points = [[], []]
    for (let i = 0; i < odData.length; ++i) {
        if (!short_skip[i]) {
            points[0].push(SRC(odData[i]));
            points[1].push(DST(odData[i]));
        }
    }
    return [selected, points];
}
