import * as d3 from "d3";
import * as Theme from "@/theme";
import * as Data from "@/data/Data";
import { Tooltip } from "@/utils/Tooltip";
import { getPolygon } from "@/data/Geodata";
import * as SouthChinaSeaLegend from "./southchinasealegend"

const name = "geoMap";
const layerRef = Symbol(name);
let layer = null;
let tooltip;

const inProvince = Data.getInProvince();

function draw(vueComponent) {
    layer
        .selectAll("path")
        .data(Data.getChinaGeojson().features)
        .join("path")
        .attr("d", vueComponent.pathDrawer)
        .attr("fill", "none")
        .attr("stroke", Theme.color.majorFontColor)
        .attr("stroke-width", 0.5)
        // .style("mix-blend-mode", "multiply")
        .on("click", (event, d) => {
            vueComponent.$store.commit("setProvinceSelected", [
                d.name,
                getPolygon(d),
                [d.in, d.out],
            ]);
        })
        .on("dblclick", (e) => {
            vueComponent.zoomWithCenter(0, vueComponent.projection(d3.select(e.target).datum().properties.cp));
        });
}

function registerTooltip(vueComponent) {
    tooltip = Tooltip()
        .extent([
            [0, 0],
            [vueComponent.svg.attr("width"), vueComponent.svg.attr("height")],
        ])
        .tips(
            ["name", "in", "out", "sum"],
            ["", "迁入人数： ", "迁出人数：", "净迁入人数："],
            [null, null, null, null]
        )
        .fontSize(16)
        .padding([8, 4])
        .margin([10, 10]);
    vueComponent.containerWrapper.call(tooltip);
}

function registerProvinceHover(vueComponent) {
    layer
        .selectAll("path")
        .on("mouseenter", (e) => {
            d3.select(e.target)
                .attr(
                    "filter",
                    "drop-shadow(2px 2px 5px rgba(0, 0, 0, 0.3)) brightness(1.05)"
                )
                .attr("transform", "scale(1.01)")
                .attr("transform-origin", d => {
                    let r = vueComponent.projection(d.properties.cp);
                    return `${r[0]} ${r[1]}`;
                });
        })
        .on("mouseleave", (e) => {
            d3.select(e.target).attr("filter", null).attr("transform", null);
        })
        .each(tooltip.events);
}

function updateProvinceStatistics(vueComponent, data) {
    layer
        .selectAll("path")
        .data()
        .forEach((d) => {
            d.name = d.properties.name;
            d.out = 0;
            d.in = 0;
            for (let i of data) {
                if (inProvince[0][d.name][i.name]) {
                    d.out += 1;
                }
                if (inProvince[1][d.name][i.name]) {
                    d.in += 1;
                }
            }
            d.sum = d.in - d.out;
            if (d.name === vueComponent.provinceSelected) {
                vueComponent.$store.commit("setProvinceInOut", [d.in, d.out]);
            }
        });
    vueComponent.$store.commit(
        "setBalanceRange",
        d3.extent(layer.selectAll("path").data(), (d) => d.sum)
    );

    layer
        .selectAll("path")
        .transition()
        .duration(100)
        .attr("fill", (d) => calcColor(vueComponent, d.sum))
        .each((d, i, e) => {
            /* TO-DO ! */
            /* TO-DO ! */
            /* TO-DO ! */
            SouthChinaSeaLegend.getSvgLayer().select(".g-southSeaGeometry").selectAll('path')
                .filter(di => di.properties.name === d.properties.name)
                .attr("fill", calcColor(vueComponent, d.sum));
        })
}

function updateHighlight(name) {
    layer
        .selectAll("path")
        .attr("stroke", (d) => (d.name === name ? "black" : "white"));
    // debugger;
    layer
        .selectAll("path").each(
            function (d) {
                if (d.name === name) {
                    d3.select(this).raise();
                }
            })
}

function calcColor(vueComponent, d) {
    for (let i = 0; i < vueComponent.balanceInterval.length; ++i) {
        if (
            d >= vueComponent.balanceInterval[i][0] &&
            d <= vueComponent.balanceInterval[i][1]
        ) {
            if (vueComponent.componentsState.densityIn.enable
                || vueComponent.componentsState.densityOut.enable
                || vueComponent.componentsState.scatterplotIn.enable
                || vueComponent.componentsState.scatterplotOut.enable) {
                return "#eeeeee";
            }
            return vueComponent.balanceInterval[i][2];
        }
    }
    return "#000000";
}

export function register(vueComponent) {
    vueComponent[layerRef] = vueComponent.container.append("g").classed(name, true);
    layer = vueComponent[layerRef];
    draw(vueComponent)
    registerTooltip(vueComponent);
    registerProvinceHover(vueComponent);
    vueComponent.$watch(
        () => vueComponent.mapData,
        (data) => {
            updateProvinceStatistics(vueComponent, data);
        }
    );
    vueComponent.$watch(
        () => vueComponent.provinceSelected,
        (provinceSelected) => {
            updateHighlight(provinceSelected)
        }
    );
}

export function getSvgLayer() {
    return layer;
}