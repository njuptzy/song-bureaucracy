import * as Data from "@/data/Data";
import * as Theme from "@/theme";

const name = "mapAxis";
const layerRef = Symbol(name);
let layer = null;

function draw(vueComponent) {
    let angle = vueComponent.axisAngle;
    let radius = vueComponent.axisLength;

    let center_x = 107;
    let center_y = 31;

    // 弧度制
    let theta = (angle / 360) * 2 * Math.PI;

    // 箭头两个端点 point_1 和 point_2 (注意这里是左手系!!!!!) and adopt map projection
    let [x1, y1] = vueComponent.projection([center_x - radius * Math.cos(theta), center_y - radius * Math.sin(theta)]);
    let [x2, y2] = vueComponent.projection([center_x + radius * Math.cos(theta), center_y + radius * Math.sin(theta)]);

    // 开始绘制 (渲染两层以模拟边缘和内部)
    layer
        .append("path")
        .attr("d", Data.generateArrow(x1, y1, x2, y2, 10))
        .style("fill", "none")
        .style("stroke", theme.color.mapDarkerBrown)
        .style("stroke-width", 3.5);

    // 绘制中心点
    layer
        .append("circle")
        .attr("cx", (x1 + x2) / 2)
        .attr("cy", (y1 + y2) / 2)
        .attr("r", 5)
        .style("fill", theme.color.mapDarkerBrown);

    // 绘制另一端点
    layer
        .append("circle")
        .attr("cx", x1)
        .attr("cy", y1)
        .attr("r", 5)
        .style("fill", theme.color.mapDarkerBrown);

    layer.attr("id", "axis");
}

export function register(vueComponent) {
    vueComponent[layerRef] = vueComponent.container.append("g");
    layer = vueComponent[layerRef];
}

export function getSvgLayer() {
    return layer;
}