import * as Data from "@/data/Data";
import * as Theme from "@/theme";

const name = "neighborArea";
const layerRef = Symbol(name);
let layer = null;

function draw(vueComponent) {
    layer
        .selectAll('path')
        .data(Data.getNeighborAreaGeojson().features)
        .join("path")
        .attr("stroke", Theme.color.majorFontColor)
        .attr("stroke-opacity", "0.7")
        .attr("stroke-width", 0.3)
        .attr("fill", "none")
        .attr("d", vueComponent.pathDrawer);

}

function updateHighlight(flag) {
    layer
        .selectAll("path").attr("stroke", (flag ? "#aaa" : Theme.color.majorFontColor));
}

export function register(vueComponent) {
    vueComponent[layerRef] = vueComponent.container.append("g").classed(name, true);
    layer = vueComponent[layerRef];
    draw(vueComponent)
    vueComponent.$watch(
        () => vueComponent.provinceSelected,
        (provinceSelected) => {
            updateHighlight(!!provinceSelected);
        }
    )
}

export function getSvgLayer() {
    return layer;
}