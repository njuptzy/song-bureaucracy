import * as d3 from "d3";
import * as Theme from "@/theme";
import * as MapDrawer from "@/utils/MapDrawer";
import * as Data from "@/data/Data"

import { Tooltip } from "@/utils/Tooltip";
import { SRC, DST } from "@/utils/ODSample";

import { ODSampleDispatcher } from "@/core/ODSample"
import * as Copy from "@/utils/copy";

const name = "arrows";
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

function draw2(vueComponent, arrowData) {
    layer
        .selectAll("path")
        .data(arrowData)
        .join("path")
        .attr("stroke", "url(#arrow-gradient)")
        .attr("stroke-linecap", "round")
        .attr("fill", "none")
        .attr("marker-end", "url(#arrow-head)")
        .attr("filter", "drop-shadow(2px 2px 5px rgba(0, 0, 0, 0.3))")
        .attr(
            "d",
            (d) =>
                MapDrawer.calcArrowPath(
                    ...vueComponent.projection(SRC(d)),
                    ...vueComponent.projection(DST(d))
                )[0]
        )
        .attr(
            "transform",
            (d) =>
                MapDrawer.calcArrowPath(
                    ...vueComponent.projection(SRC(d)),
                    ...vueComponent.projection(DST(d))
                )[1]
        )
        .attr("stroke-width", (d) => calcWidth(vueComponent.arrowInterval, d.value));
}


export function draw(vueComponent, arrowData, mapScaleTier) {
    const arrowHeadStyle = (len, tier) => {
        return (p) => {
            p.attr("stroke", Theme.color.majorFontColor)
                .attr("stroke-width", 0.5 / mapScaleTier)
                .attr("fill", Theme.color.mapArrowColor)
                .attr("fill-opacity", (d) =>
                    tier <= calcArrowHeadLayer(vueComponent.arrowInterval, d.value) ? "1" : "0.1"
                )
                .attr("d", (d) =>
                    MapDrawer.arrowHeadPath(DST(d), len, SRC(d), d.dAng)
                );
        };
    };

    layer.selectAll("g").remove();
    layer
        .selectAll("g")
        .data(arrowData)
        .join("g")
        .classed("arrow-head", true)
        .call((g) => {
            g.append("path")
                .attr("stroke", "url(#arrow-gradient)")
                .attr("stroke-linecap", "round")
                .attr("stroke-opacity", 0.8)
                .attr("fill", "none")
                .attr("stroke-width", (d) => calcWidth(vueComponent.arrowInterval, d.value) / vueComponent.mapScaleTier)
                .attr(
                    "d",
                    (d) =>
                        MapDrawer.calcArrowPath_deviation(
                            ...SRC(d),
                            ...DST(d),
                            d.dAng,
                            vueComponent.mapScaleTier
                        )[0]
                )
                .attr(
                    "transform",
                    (d) =>
                        MapDrawer.calcArrowPath_deviation(
                            ...SRC(d),
                            ...DST(d),
                            d.dAng,
                            vueComponent.mapScaleTier
                        )[1]
                );
            g.append("path").call(arrowHeadStyle(11 / vueComponent.mapScaleTier, 0));
            g.append("path").call(arrowHeadStyle(18 / vueComponent.mapScaleTier, 1));
            g.append("path").call(arrowHeadStyle(25 / vueComponent.mapScaleTier, 2));
        });
    layer
        .selectAll("g")
        .on("mouseenter", (e, d) => {
            vueComponent.$store.commit("setArrowHover", d.id);
        })
        .on("mouseleave", (e, d) => {
            vueComponent.$store.commit("resetArrowHover", d.id);
        })
        .each(tooltip.events);
}

function updateArrowHighlight(vueComponent) {
    layer.selectAll("g").attr("filter", (d, i, e) => {
        if (d.id == vueComponent.arrowHover) {
            d3.select(e[i]).raise();
            return (
                "drop-shadow(2px 2px 10px rgba(117, 75, 42, 0.7))" +
                " brightness(1.5)"
            );
        } else {
            return "drop-shadow(2px 2px 5px rgba(0, 0, 0, 0.3))";
        }
    });
}

function aggregateArrows(vueComponent, provinceSelected, data, provinceSelectedPolygon, projection) {
    dispatcher
        .dispatch(
            Copy.jsonCopy(data),
            provinceSelected ? 2 : 4,
            provinceSelected ? 10 : 20,
            Copy.jsonCopy(provinceSelectedPolygon),
        )
        .then((d) => {
            let { arrows: arrowsAggregated, labels: geoLabels } = Data.arrowAggregation(d[0], projection);
            vueComponent.$store.commit("setArrows", arrowsAggregated);
            // Layers.Arrows.draw(this, arrowsAggregated);
            // Layers.GeoLabels.draw(this, geoLabels);
            vueComponent.arrowsLabel = geoLabels;
            // this.drawArrows(d[0]);
        })
        .catch((err) => console.log(err));
}

function calcArrowHeadLayer(arrowInterval, d) {
    for (let i = 0; i < arrowInterval.length; ++i) {
        if (d >= arrowInterval[i][0] && d <= arrowInterval[i][1]) {
            return i;
        }
    }
    return arrowInterval.length - 1;
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
        () => vueComponent.arrowHover,
        (newVal) => {
            updateArrowHighlight(vueComponent);
        }
    )
    vueComponent.$watch(
        () => [vueComponent.provinceSelected, vueComponent.mapData],
        ([provinceSelected, mapData]) => {
            aggregateArrows(
                vueComponent,
                provinceSelected,
                mapData,
                vueComponent.provinceSelectedPolygon,
                vueComponent.projection
            )
        },
        {
            deep: true,
        }
    )
    vueComponent.$watch(
        () => [vueComponent.arrows, vueComponent.mapScaleTier],
        ([arrows, mapScaleTier]) => {
            draw(vueComponent, arrows, mapScaleTier);
        }
    )
}

export function getSvgLayer() {
    return layer;
}