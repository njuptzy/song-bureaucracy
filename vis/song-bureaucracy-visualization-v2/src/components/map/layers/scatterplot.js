import * as Data from "@/data/Data";
import * as Theme from "@/theme";
import * as d3 from "d3";

const layerRef = Symbol("scatterPlot");
let layer = null;

function draw(points, scatterPlotIn, scatterplotOut, mapScaleTier) {
    layer.selectAll('g').remove();
    if (scatterplotOut.enable) {
    layer.append('g').selectAll("circle")
        .data(points.filter(d => d[2] === -1))
        .join('circle')
        .attr("stroke", "none")
        .attr("fill", Theme.color.mapLegendColor0)
        .attr("fill-opacity", "0.3")
        .attr("cx", d => d[0])
        .attr("cy", d => d[1])
        .attr("r", 2 / mapScaleTier)
        .style("pointer-events", "none")
    }
    if (scatterPlotIn.enable) {
    layer.append('g').selectAll("circle")
        .data(points.filter(d => d[2] === 1))
        .join('circle')
        .attr("stroke", "none")
        .attr("fill", Theme.color.mapLegendColor8)
        .attr("fill-opacity", "0.3")
        .attr("cx", d => d[0])
        .attr("cy", d => d[1])
        .attr("r", 2 / mapScaleTier)
        .style("pointer-events", "none")
    }
}

function reScale(mapScaleTier) {
    layer.selectAll("circle").attr('r', 2 / mapScaleTier);
}

export function register(vueComponent) {
    vueComponent[layerRef] = vueComponent.container.append("g").classed("scatterplot", true);
    layer = vueComponent[layerRef];
    vueComponent.$watch(
        () => vueComponent.mapScaleTier,
        (mapScaleTier) => {
            reScale(mapScaleTier);
        },
    );
    vueComponent.$watch(
        () => [
            vueComponent.mapData,
            vueComponent.componentsState.scatterplotIn, 
            vueComponent.componentsState.scatterplotOut],
        ([data, scatterPlotIn, scatterPlotOut]) => {
            draw(
                [].concat(
                    data.map(di => [...vueComponent.projection([di.src_x_coord, di.src_y_coord]), -1]),
                    data.map(di => [...vueComponent.projection([di.dst_x_coord, di.dst_y_coord]), 1])),
                scatterPlotIn,
                scatterPlotOut,
                vueComponent.mapScaleTier
            );
        },
        {
            deep: true,
        }
    )
}