import { kdTree } from "@/utils/KDTree";
import { Point } from "@/utils/Geometry";
import * as d3 from "d3";

export function SRC(d) {
    // return [d.src_x_coord, d.src_y_coord];
    return new Point(d.src_x_coord, d.src_y_coord);
}

export function DST(d) {
    // return [d.dst_x_coord, d.dst_y_coord];
    return new Point(d.dst_x_coord, d.dst_y_coord);
}
