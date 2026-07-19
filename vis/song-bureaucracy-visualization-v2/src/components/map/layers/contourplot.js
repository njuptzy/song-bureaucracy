import * as Data from "@/data/Data";
import * as Theme from "@/theme";
import * as d3 from "d3";

const layerRef = Symbol("contourPlot");
let layer = null;


function draw(points, densityIn, densityOut) {
    layer.selectAll('g').remove();
    let contourGenerator = d3.contourDensity()
        .x((d) => d[0])
        .y((d) => d[1])
        .weight((d) => d[2])
        .size([2000, 2000])
        .bandwidth(8)
        .cellSize(2)
        .thresholds(20);
    // In contour
    if (densityIn.enable) {
    let contourPositive = contourGenerator(points);
    layer.append('g')
        .style("pointer-events", "none")
        .selectAll("path")
        .data(contourPositive)
        .join("path")
        .attr("fill", Theme.color.mapLegendColor8)
        .attr("fill-opacity", "0.1")
        .attr("stroke", "#666")
        .attr("stroke-linejoin", "round")
        .attr("stroke-width", (d, i) => i % 5 ? 0.05 : 0.25)
        .attr("d", d3.geoPath());
    }
    //Out contour
    if (densityOut.enable) {
    for (let i of points) {
        i[2] *= -1;
    }
    let contourNegative = contourGenerator(points);
    layer.append('g')
        .style("pointer-events", "none")
        .selectAll("path")
        .data(contourNegative)
        .join("path")
        .attr("fill", Theme.color.mapLegendColor0)
        .attr("fill-opacity", "0.1")
        .attr("stroke", "#666")
        .attr("stroke-linejoin", "round")
        .attr("stroke-width", (d, i) => i % 5 ? 0.05 : 0.25)
        .attr("d", d3.geoPath());
    }
}


export function register(vueComponent) {
    vueComponent[layerRef] = vueComponent.container.append("g").classed("contourplot", true);
    layer = vueComponent[layerRef];
    vueComponent.$watch(
        () => [
            vueComponent.mapData,
            vueComponent.componentsState.densityIn, 
            vueComponent.componentsState.densityOut],
        ([data, densityIn, densityOut]) => {
            draw(
                [].concat(
                    data.map(di => [...vueComponent.projection([di.src_x_coord, di.src_y_coord]), -1]),
                    data.map(di => [...vueComponent.projection([di.dst_x_coord, di.dst_y_coord]), 1])),
                densityIn,
                densityOut,
            );
        },
        {
            deep: true,
        }
    )
}