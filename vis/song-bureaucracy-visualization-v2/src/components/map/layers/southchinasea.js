import * as Data from "@/data/Data";
import * as Theme from "@/theme";

const name = "southSea";
const layerRef = Symbol(name);
let layer = null;

function drawSouthChinaSea(vueComponent) {
    let features = Data.getChinaSouthSeaGeojson().features;
    layer
        .selectAll("g")
        .data(features)
        .enter()
        .append("g")
        .attr("class", "g-small-province")
        .attr("id", (d) => "map-small-province-" + d.properties.id)
        .append("path")
        .attr("class", "small-province")
        .attr("stroke", Theme.color.majorFontColor)
        .attr("stroke-width", 0.5)
        .attr("fill", (d) =>
            d.properties.name == "九段线" ? "none" : "#f5e0cc"
        )
        .attr("d", vueComponent.pathDrawer);
}

export function register(vueComponent) {
    vueComponent[layerRef] = vueComponent.container.append("g");
    layer = vueComponent[layerRef];
    drawSouthChinaSea(vueComponent)
}

export function getSvgLayer() {
    return layer;
}