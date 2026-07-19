import * as d3 from "d3";
import * as Data from "@/data/Data";
import * as Theme from "@/theme";
import * as MapDrawer from "@/utils/MapDrawer";

import { Tooltip } from "@/utils/Tooltip";
import { Point } from "@/utils/Geometry"
import { SRC, DST } from "@/utils/ODSample";
import * as Copy from "@/utils/copy"

import { ODSampleDispatcher } from "@/core/ODSample"

const name = "shortArrows";
const layerRef = Symbol(name);
let layer = null;
let tooltip;

const dispatcher = new ODSampleDispatcher();


function registerTooltip(vueComponent) {
    tooltip = Tooltip()
        .extent([
            [0, 0],
            [vueComponent.svg.attr("width"), vueComponent.svg.attr("height")],
        ])
        .tips(
            ["counter", "counter", "value"],
            ["迁出地：", "迁入地：", "人数："],
            [
                (d) =>
                    d[0]
                        .slice(0, 3)
                        .map((i) => i[0])
                        .join("，") + "一带",
                (d) =>
                    d[1]
                        .slice(0, 3)
                        .map((i) => i[0])
                        .join("，") + "一带",
                null,
            ]
        )
        .fontSize(16)
        .padding([8, 4])
        .margin([10, 10]);
    vueComponent.tooltipContainer.call(tooltip);
}

export function draw(vueComponent, arrowData, mapScaleTier) {
    const arrowHeadStyle = (len, tier) => {
        return (p) => {
            p.attr("stroke", Theme.color.majorFontColor)
                .attr("stroke-width", 0.5 / mapScaleTier)
                .attr("fill", Theme.color.mapArrowColor)
                .attr("fill-opacity", "1")
                .attr("d", (d) =>
                    MapDrawer.arrowHeadPath(DST(d).projection(vueComponent.projection), len, SRC(d).projection((vueComponent.projection)), Math.PI / 12)
                );
        };
    };

    layer.selectAll("g").remove();
    if (vueComponent.mapScaleTier < 2) {
        return;
    }
    layer
        .selectAll("g")
        .data(arrowData)
        .join("g")
        .classed("arrow-head", true)
        .call((g) => {
            g.append("path")
                .attr("stroke", "url(#arrow-gradient)")
                .attr("stroke-linecap", "round")
                .attr("stroke-opacity", 0.9)
                .attr("fill", "none")
                .attr("stroke-width", (d) => calcWidth(vueComponent.arrowInterval, d.value) / vueComponent.mapScaleTier)
                .attr(
                    "d",
                    (d) =>
                        MapDrawer.calcArrowPath_deviation(
                            ...SRC(d).projection(vueComponent.projection),
                            ...DST(d).projection(vueComponent.projection),
                            Math.PI / 12,
                            4
                        )[0]
                )
                .attr(
                    "transform",
                    (d) =>
                        MapDrawer.calcArrowPath_deviation(
                            ...SRC(d).projection(vueComponent.projection),
                            ...DST(d).projection(vueComponent.projection),
                            Math.PI / 12,
                            4
                        )[1]
                );
            g.append("path").call(arrowHeadStyle(15 / vueComponent.mapScaleTier, 2));
            const getSrcTextPos = (d) => {
                return SRC(d).projection(vueComponent.projection);
            }
            const getDstTextPos = (d) => {
                return DST(d).projection(vueComponent.projection);
            }
            let existedText = [];
            const textFilter = (a) => {
                let r = [];
                for (let i of a) {
                    if (existedText.indexOf(i) === -1) {
                        r.push(i);
                        existedText.push(i);
                    }
                }
                return r;
            }
            let smallArrowLabelFontSize = 3;
            g.each(function (d) {

                let textG = d3.select(this).append('g')
                    .attr("font-size", smallArrowLabelFontSize)
                    .attr("stroke", "#ceaf91")
                    .attr("stroke-width", 0.1)
                    .style('paint-order', "stroke")
                    .style("pointer-events", "none")
                    .attr("font-family", "FZQINGKBYSJF")
                    .attr("fill", Theme.color.majorFontColor);
                let ang = DST(d).sub(SRC(d)).angle();
                let textSrc = textFilter(d.counter[0].slice(0, 2).map(di => di[0])).join('，');
                let textDst = textFilter(d.counter[1].slice(0, 2).map(di => di[0])).join('，');
                let rSrc = new Point(1, textSrc.length).len() * smallArrowLabelFontSize;
                let rDst = new Point(1, textDst.length).len() * smallArrowLabelFontSize;

                textG.append('text')
                    .attr("x", getSrcTextPos(d).x - smallArrowLabelFontSize * textSrc.length / 2 + Math.cos(ang) * rSrc)
                    .attr("y", getSrcTextPos(d).y + Math.sin(ang) * rSrc / 3)
                    .text(textSrc);
                textG.append('text')
                    .attr("x", getDstTextPos(d).x - smallArrowLabelFontSize * textDst.length / 2 - Math.cos(ang) * rDst)
                    .attr("y", getDstTextPos(d).y - Math.sin(ang) * rDst / 3)
                    .text(textDst);

            })
        });
    layer
        .selectAll("g")
        .each(tooltip.events);
}

function aggregateShortArrows(vueComponent, provinceSelected, mapData) {
    if (vueComponent.provinceSelected) {
        dispatcher
            .dispatch(
                Copy.jsonCopy(mapData),
                1,
                10,
                Copy.jsonCopy(vueComponent.provinceSelectedPolygon),
                2
            )
            .then((d) => {
                vueComponent.shortArrows = d[0];
            })
            .catch((err) => console.log(err));
    }
    else {
        // layer.selectAll('g').remove();
        vueComponent.shortArrows = []
    }
}

function calcWidth(arrowInterval, d) {
    for (let i of arrowInterval) {
        if (d >= i[0] && d <= i[1]) {
            return i[2];
        }
    }
    return 4;
}

export function register(vueComponent) {
    vueComponent[layerRef] = vueComponent.container.append("g").classed(name, true);
    layer = vueComponent[layerRef];
    registerTooltip(vueComponent);
    vueComponent.$watch(
        () => [vueComponent.provinceSelected, vueComponent.mapData],
        ([provinceSelected, mapData]) => {
            aggregateShortArrows(
                vueComponent,
                provinceSelected,
                mapData,
            )
        }
    );
    vueComponent.$watch(
        () => [vueComponent.shortArrows, vueComponent.mapScaleTier],
        ([shortArrows, mapScaleTier]) => {
            draw(vueComponent, shortArrows, mapScaleTier);
        }
    );
}

export function getSvgLayer() {
    return layer;
}