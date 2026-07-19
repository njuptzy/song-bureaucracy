<template>
  <div class="container">
    <svg>
      <defs>
        <marker
            id="arrow-head"
            orient="auto"
            viewBox="0 0 10 7.6"
            markerWidth="7.5"
            markerHeight="5.7"
            refX="3.8"
            refY="2.8"
        >
          <path
              d="M0,0 L3.6,2.8 H9.6 Z"
              fill="#754b2a"
              stroke="#754b2a"
              stroke-width="0.1"
              opacity="1"
          />
          <path
              d="M0,5.6 L3.6,2.8 H9.6 Z"
              fill="#ffffff"
              stroke="#754b2a"
              stroke-width="0.1"
              opacity="1"
          />
        </marker>
        <linearGradient id="arrow-gradient">
          <stop offset="0" stop-color="#c1a98d" stop-opacity="0.5"></stop>
          <stop offset="0.25" stop-color="#b9a084" stop-opacity="0.7"></stop>
          <stop offset="1" stop-color="#754b2a" stop-opacity="0.8"></stop>
        </linearGradient>
        <filter id="drop-shadow">
          <feOffset result="offOut" in="SourceGraphic" dx="2" dy="2"/>
          <feGaussianBlur result="blurOut" in="offOut" stdDeviation="2"/>
          <feBlend in="SourceGraphic" in2="blurOut" mode="normal"/>
        </filter>
      </defs>
    </svg>
  </div>
</template>

<script>
import * as d3 from "d3";
import * as Data from "@/data/Data";
import {Tooltip} from "@/utils/Tooltip";
import {Point} from "@/utils/Geometry";
import {SRC, DST} from "@/utils/ODSample";
import {mapState} from "vuex";
import ODSampleWorker from "@/utils/ODSample.worker.js?worker";
import * as MapDrawer from "@/utils/MapDrawer.js";
import * as theme from "@/theme";
import {
  getChinaInlineSouthSeaGeojson,
  getChinaSouthSeaIslandsPath,
} from "@/data/Data";
import {getPolygon} from "@/data/Geodata";
import {straightArrow} from "@/utils/MapDrawer.js";

class ODSampleDispatcher {
  constructor() {
    this._queue = [];
    this._worker = new ODSampleWorker();
    this._worker.onmessage = (e) => this._queue.shift().resolve(e.data);
    this._worker.onerror = (e) => this._queue.shift().reject(e.error);
  }

  dispatch(...args) {
    return new Promise((resolve, reject) => {
      this._queue.push({resolve, reject});
      this._worker.postMessage(args);
    });
  }
}

const dispatcher = new ODSampleDispatcher();
const inProvince = Data.getInProvince();

export default {
  name: "MainMap",
  props: ["canvasWidth", "canvasHeight"],
  data() {
    return {
      mapScale: 1,
      mapScaleTier: 1,
    };
  },
  computed: {
    ...mapState([
      "balanceRange",
      "balanceInterval",
      "yearRange",
      "provinceSelected",
      "provinceSelectedPolygon",
      "arrowHover",
      "arrowInterval",
      "componentsState",

      "axisAngle",
      "axisLength",
    ]),
  },
  watch: {
    mapScale: {
      handler() {
        // console.log(this.mapScale);
        let t = Math.floor(Math.max(1, Math.log(this.mapScale) / Math.log(2)));
        let updateFlag = false;
        if (this.mapScaleTier !== t) {
          updateFlag = true;
        }
        this.mapScaleTier = t;
        if (updateFlag) {
          this.updateMigration({scaleChange: true});
        }
      }
    },
    axisAngle: {
      handler() {
        this.g.remove();
        this.drawMapAxis();
      },
    },
    axisLength: {
      handler() {
        this.g.remove();
        this.drawMapAxis();
      },
    },
    yearRange: {
      handler() {
        this.updateMigration({timeChange: true});
      },
      deep: true,
    },
    provinceSelected: {
      handler(newVal) {
        this.geoMap
            .selectAll("path")
            .attr("stroke", (d) => (d.name === newVal ? "black" : "white"));
        // debugger;
        this.geoMap.selectAll("path").each(function (d) {
          if (d.name === newVal) {
            d3.select(this).raise();
          }
        })
        this.neighborArea.selectAll("path").attr("stroke", (newVal ? "#aaa" : theme.color.majorFontColor));
        this.updateMigration();
      },
    },
    arrowHover: {
      handler() {
        this.updateArrowHighlight();
      },
    },
    componentsState: {
      handler() {
        this.updateMigration({componentChange: true});
      },
      deep: true,
    }
  },
  methods: {
    calcColor(d) {
      for (let i = 0; i < this.balanceInterval.length; ++i) {
        if (
            d >= this.balanceInterval[i][0] &&
            d <= this.balanceInterval[i][1]
        ) {
          if (this.componentsState.densityIn.enable || this.componentsState.densityOut.enable
              || this.componentsState.scatterplotIn.enable
              || this.componentsState.scatterplotOut.enable) {
            return "#eeeeee";
          }
          return this.balanceInterval[i][2];
        }
      }
      return "#000000";
    },

    calcArrowHeadLayer(d) {
      for (let i = 0; i < this.arrowInterval.length; ++i) {
        if (d >= this.arrowInterval[i][0] && d <= this.arrowInterval[i][1]) {
          return i;
        }
      }
      return this.arrowInterval.length - 1;
    },

    calcWidth(d) {
      for (let i of this.arrowInterval) {
        if (d >= i[0] && d <= i[1]) {
          return i[2];
        }
      }
      return 4;
    },

    zoomCenter(scale, center) {
      let cScale = d3.zoomTransform(this.containerWrapper.node()).k;
      if (!center) {
        this.containerWrapper
            .transition()
            .call(this.zoomController.transform, d3.zoomIdentity);
      }
      else {
        let nScale = Math.min(cScale * 2, 8);
        let nTranslate = new Point(...this.zoomController.extent()()[1]).mul(0.5).sub(new Point(...center).mul(nScale));
        this.containerWrapper
          .transition()
          .call(this.zoomController.transform, d3.zoomIdentity.translate(...nTranslate).scale(nScale));
      }
    },

    //update arrow selected to highlighted
    updateArrowHighlight() {
      this.arrows.selectAll("g").attr("filter", (d, i, e) => {
        if (d.id == this.arrowHover) {
          d3.select(e[i]).raise();
          return (
              "drop-shadow(2px 2px 10px rgba(117, 75, 42, 0.7))" +
              " brightness(1.5)"
          );
        } else {
          return "drop-shadow(2px 2px 5px rgba(0, 0, 0, 0.3))";
        }
      });
    },
    //draw arrow with arc shape
    drawArrowsStyle2(arrowData) {
      const arrowHeadStyle = (len, tier) => {
        return (p) => {
          p.attr("stroke", theme.color.majorFontColor)
              .attr("stroke-width", 0.5 / this.mapScaleTier)
              .attr("fill", theme.color.mapArrowColor)
              .attr("fill-opacity", (d) =>
                  tier <= this.calcArrowHeadLayer(d.value) ? "1" : "0.1"
              )
              // .attr("d", (d) => arrowHeadPath(DST(d).projection(this.projection), len, SRC(d).projection(this.projection), d.dAng));
              .attr("d", (d) =>
                  MapDrawer.arrowHeadPath(DST(d), len, SRC(d), d.dAng)
              );
        };
      };

      this.arrows.selectAll("g").remove();
      this.arrows
          .selectAll("g")
          .data(arrowData)
          .join("g")
          .classed("arrow-head", true)
          .call((g) => {
            g.append("path")
                // .attr('stroke', "red")
                .attr("stroke", "url(#arrow-gradient)")
                .attr("stroke-linecap", "round")
                .attr("stroke-opacity", 0.8)
                .attr("fill", "none")
                .attr("stroke-width", (d) => this.calcWidth(d.value) / this.mapScaleTier)
                // .attr('marker-end', "url(#arrow-head)")
                // .attr("filter", "drop-shadow(2px 2px 5px rgba(0, 0, 0, 0.3))")
                // .attr("d", d => calcArrowD(...this.projection(SRC(d)), ...this.projection(DST(d)), d.dAng)[0])
                // .attr("transform", d => calcArrowD(...this.projection(SRC(d)), ...this.projection(DST(d)), d.dAng)[1])
                .attr(
                    "d",
                    (d) =>
                        MapDrawer.calcArrowPath_deviation(
                            ...SRC(d),
                            ...DST(d),
                            d.dAng,
                            this.mapScaleTier
                        )[0]
                )
                .attr(
                    "transform",
                    (d) =>
                        MapDrawer.calcArrowPath_deviation(
                            ...SRC(d),
                            ...DST(d),
                            d.dAng,
                            this.mapScaleTier
                        )[1]
                );
            g.append("path").call(arrowHeadStyle(11 / this.mapScaleTier, 0));
            g.append("path").call(arrowHeadStyle(18 / this.mapScaleTier, 1));
            g.append("path").call(arrowHeadStyle(25 / this.mapScaleTier, 2));
          });
      this.arrows
          .selectAll("g")
          .on("mouseenter", (e, d) => {
            this.$store.commit("setArrowHover", d.id);
          })
          .on("mouseleave", (e, d) => {
            this.$store.commit("resetArrowHover", d.id);
          })
          .each(this.tooltipArrow.events);
    },
    //draw arrow with black and white style
    drawArrows(arrowData) {
      this.arrows
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
                      ...this.projection(SRC(d)),
                      ...this.projection(DST(d))
                  )[0]
          )
          .attr(
              "transform",
              (d) =>
                  MapDrawer.calcArrowPath(
                      ...this.projection(SRC(d)),
                      ...this.projection(DST(d))
                  )[1]
          )
          .attr("stroke-width", (d) => this.calcWidth(d.value));
      // .attr("transform-origin", d => calcArrowD(...this.projection(SRC(d)), ...this.projection(DST(d)))[2]);
      // this.arrows
      //     .selectAll("path")
      //     .on("mouseenter", (e, d) => {
      //       this.$store.commit("setArrowHover", d.id);
      //     })
      //     .on("mouseleave", (e, d) => {
      //       this.$store.commit("resetArrowHover", d.id);
      //     })
      //     .each(this.tooltipArrow.events);
    },
    drawShortArrows(arrowData) {
      console.log(arrowData);

      const arrowHeadStyle = (len, tier) => {
        return (p) => {
          p.attr("stroke", theme.color.majorFontColor)
              .attr("stroke-width", 0.5 / this.mapScaleTier)
              .attr("fill", theme.color.mapArrowColor)
              .attr("fill-opacity", "1")
              // .attr("d", (d) => arrowHeadPath(DST(d).projection(this.projection), len, SRC(d).projection(this.projection), d.dAng));
              .attr("d", (d) =>
                  MapDrawer.arrowHeadPath(DST(d).projection(this.projection), len, SRC(d).projection((this.projection)), Math.PI / 12)
              );
        };
      };

      this.shortArrows.selectAll("g").remove();
      if (this.mapScaleTier < 2) {
        return;
      }
      this.shortArrows
          .selectAll("g")
          .data(arrowData)
          .join("g")
          .classed("arrow-head", true)
          .call((g) => {
            g.append("path")
                // .attr('stroke', "red")
                .attr("stroke", "url(#arrow-gradient)")
                .attr("stroke-linecap", "round")
                .attr("stroke-opacity", 0.9)
                .attr("fill", "none")
                .attr("stroke-width", (d) => this.calcWidth(d.value) / this.mapScaleTier)
                // .attr('marker-end', "url(#arrow-head)")
                // .attr("filter", "drop-shadow(2px 2px 5px rgba(0, 0, 0, 0.3))")
                // .attr("d", d => calcArrowD(...this.projection(SRC(d)), ...this.projection(DST(d)), d.dAng)[0])
                // .attr("transform", d => calcArrowD(...this.projection(SRC(d)), ...this.projection(DST(d)), d.dAng)[1])
                .attr(
                    "d",
                    (d) =>
                        MapDrawer.calcArrowPath_deviation(
                            ...SRC(d).projection(this.projection),
                            ...DST(d).projection(this.projection),
                            Math.PI / 12,
                            4
                        )[0]
                )
                .attr(
                    "transform",
                    (d) =>
                        MapDrawer.calcArrowPath_deviation(
                            ...SRC(d).projection(this.projection),
                            ...DST(d).projection(this.projection),
                            Math.PI / 12,
                            4
                        )[1]
                );
            g.append("path").call(arrowHeadStyle(15 / this.mapScaleTier, 2));
            const getSrcTextPos = (d) => {
              // return SRC(d).sub(DST(d)).mul(0.1).add(SRC(d)).projection(this.projection);
              return SRC(d).projection(this.projection);
            }
            const getDstTextPos = (d) => {
              // return DST(d).sub(SRC(d)).mul(0.07).add(DST(d)).projection(this.projection);
              return DST(d).projection(this.projection);
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
                .attr("fill", theme.color.majorFontColor);
              let ang = DST(d).sub(SRC(d)).angle();
              let textSrc = textFilter(d.counter[0].slice(0, 2).map(di => di[0])).join('，');
              let textDst = textFilter(d.counter[1].slice(0, 2).map(di => di[0])).join('，');
              let rSrc = new Point(1, textSrc.length).len() * smallArrowLabelFontSize;
              let rDst = new Point(1, textDst.length).len() * smallArrowLabelFontSize;
              // rSrc = rDst = 0;

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
      this.shortArrows
          .selectAll("g")
          .each(this.tooltipShortArrow.events);


      // this.shortArrows
      //     .selectAll("path")
      //     .data(arrowData)
      //     .join("path")
      //     // .attr("stroke", "url(#arrow-gradient)")
      //     .attr("stroke", "#754b2a")
      //     .attr("stroke-opacity", "0.7")
      //     .attr("stroke-linecap", "round")
      //     .attr("fill", "none")
      //     // .attr("marker-end", "url(#arrow-head)")
      //     .attr("filter", "drop-shadow(2px 2px 5px rgba(0, 0, 0, 0.3))")
      //     .attr(
      //         "d",
      //         (d) =>
      //             MapDrawer.straightArrow(
      //                 ...this.projection(SRC(d)),
      //                 ...this.projection(DST(d))
      //             )
      //     )
      //     .attr("stroke-width", "1");
    },
    //draw labels for geo location
    drawGeoLabels(geoLabels) {
      //split the labels to multiple line trying to squarify the final bounding box
      function squareSplit(labels) {
        let s = d3.sum(labels.map(d => d[0].length));
        let sq = Math.ceil(Math.sqrt(s));
        let r = [];
        let acc = 0;
        for (let i of labels) {
          if (r.length === 0 || acc + 1 + i[0].length > sq) {
            r.push([i]);
            acc = i[0].length;
          } else {
            r[r.length - 1].push(i);
            acc += i[0].length;
          }
        }
        return [r, [d3.max(r, ri => d3.sum(ri, rii => rii[0].length)), r.length]];
      }

      let labelFontSize = 10 / this.mapScaleTier;
      this.geoLabels.selectAll('g').remove();
      this.geoLabels.selectAll('g')
          .data(geoLabels.filter(d => d.labels.length > 0))
          .join("g")
          .call(g => {
            g.append('text')
                .attr("transform", d => {
                  let [_, [w, h]] = squareSplit(d.labels);
                  h = h / 2 * labelFontSize;
                  w = w / 2 * labelFontSize;
                  let len = new Point(w, h).len() + 5;
                  return `translate(${d.pos[0] + Math.cos(d.ang) * len - w}, ${d.pos[1] + Math.sin(d.ang) * len - h})`;
                })
                .attr("fill", theme.color.mapDarkerBrown)
                .attr("stroke", "#ceaf91")
                .attr("stroke-width", 0.5)
                .style('paint-order', "stroke")
                .style("pointer-events", "none")
                .attr("font-family", "FZQINGKBYSJF")
                .attr("font-size", labelFontSize)
                .selectAll('tspan')
                .data(d => squareSplit(d.labels)[0])
                .join('tspan')
                .text(d => d.map(t => t[0]).join('，'))
                .attr("dy", labelFontSize)
                .attr("x", 0);
          });
      //draw dots
      this.geoLabels.selectAll('g')
          .filter((d) => d.labels.length > 0)
          .append('circle')
          .attr("r", 2)
          .attr("fill", theme.color.majorFontColor)
          .attr("cx", d => d.pos[0])
          .attr("cy", d => d.pos[1]);
    },
    // 主轴绘制
    drawMapAxis() {
      let angle = this.axisAngle;
      let radius = this.axisLength;

      let center_x = 107;
      let center_y = 31;

      // 弧度制
      let theta = (angle / 360) * 2 * Math.PI;

      // 箭头两个端点 point_1 和 point_2 (注意这里是左手系!!!!!) and adopt map projection
      let [x1, y1] = this.projection([center_x - radius * Math.cos(theta), center_y - radius * Math.sin(theta)]);
      let [x2, y2] = this.projection([center_x + radius * Math.cos(theta), center_y + radius * Math.sin(theta)]);

      // 开始绘制 (渲染两层以模拟边缘和内部)
      this.axis
          .append("path")
          .attr("d", Data.generateArrow(x1, y1, x2, y2, 10))
          .style("fill", "none")
          .style("stroke", theme.color.mapDarkerBrown)
          .style("stroke-width", 3.5);

      // 绘制中心点
      this.axis
          .append("circle")
          .attr("cx", (x1 + x2) / 2)
          .attr("cy", (y1 + y2) / 2)
          .attr("r", 5)
          .style("fill", theme.color.mapDarkerBrown);

      // 绘制另一端点
      this.axis
          .append("circle")
          .attr("cx", x1)
          .attr("cy", y1)
          .attr("r", 5)
          .style("fill", theme.color.mapDarkerBrown);

      this.axis.attr("id", "axis");
    },
    // update migration data
    updateMigration({timeChange, componentChange, scaleChange} = {}) {
      let data = Data.getDataByTimeRange(this.yearRange[0], this.yearRange[1]);

      if (timeChange || componentChange || scaleChange) {
        if (this.componentsState.densityIn.enable || this.componentsState.densityOut.enable) {
          this.drawContour([].concat(data.map(di => [...this.projection([di.src_x_coord, di.src_y_coord]), -1]), data.map(di => [...this.projection([di.dst_x_coord, di.dst_y_coord]), 1])));
        }
        else {
          this.drawContour([]);
        }

        if (this.componentsState.scatterplotIn.enable || this.componentsState.scatterplotOut.enable) {
          if (scaleChange) {
            this.scatterPlot.selectAll("circle").attr('r', 2 / this.mapScaleTier);
          }
          else {
            this.drawScatterPlot([].concat(data.map(di => [...this.projection([di.src_x_coord, di.src_y_coord]), -1]), data.map(di => [...this.projection([di.dst_x_coord, di.dst_y_coord]), 1])));
          }
        }
        else {
          this.drawScatterPlot([]);
        }
      }

      this.drawProvinceMap(this.provinceSelected);


      //update province stat
      this.geoMap
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
            if (d.name === this.provinceSelected) {
              this.$store.commit("setProvinceInOut", [d.in, d.out]);
            }
          });
      this.$store.commit(
          "setBalanceRange",
          d3.extent(this.geoMap.selectAll("path").data(), (d) => d.sum)
      );
      this.geoMap
          .selectAll("path")
          .transition()
          .duration(100)
          .attr("fill", (d) => this.calcColor(d.sum))
          .each((d, i, e) => {
            this.southSeaLegend.select(".g-southSeaGeometry").selectAll('path')
                .filter(di => di.properties.name === d.properties.name)
                .attr("fill", this.calcColor((d.sum)));
          })

      //arrow pattern discovery
      let cl = (d) => (d ? JSON.parse(JSON.stringify(d)) : d);
      dispatcher
          .dispatch(
              Data.getDataByTimeRange(this.yearRange[0], this.yearRange[1]),
              this.provinceSelected ? 2 : 4,
              this.provinceSelected ? 10 : 20,
              cl(this.provinceSelectedPolygon),
          )
          .then((d) => {
            let {arrows: arrowsAggregated, labels: geoLabels} = Data.arrowAggregation(d[0], this.projection);
            this.$store.commit("setArrows", arrowsAggregated);
            this.drawArrowsStyle2(arrowsAggregated);
            this.drawGeoLabels(geoLabels);
            // this.drawArrows(d[0]);
          })
          .catch((err) => console.log(err));
      //short arrow
      if (this.provinceSelected) {
        dispatcher
            .dispatch(
                Data.getDataByTimeRange(this.yearRange[0], this.yearRange[1]),
                1,
                10,
                cl(this.provinceSelectedPolygon),
                2
            )
            .then((d) => {
              // this.$store.commit("setArrows", arrowsAggregated);
              this.drawShortArrows(d[0]);
            })
            .catch((err) => console.log(err));
      }
      else {
        this.shortArrows.selectAll('g').remove();
      }
    },
    //draw map
    drawSouthChinaSea() {
      let features = Data.getChinaSouthSeaGeojson().features;
      this.southSea
          .selectAll("g")
          .data(features)
          .enter()
          .append("g")
          .attr("class", "g-small-province")
          .attr("id", (d) => "map-small-province-" + d.properties.id)
          .append("path")
          .attr("class", "small-province")
          .attr("stroke", theme.color.majorFontColor)
          .attr("stroke-width", 0.5)
          .attr("fill", (d) =>
              d.properties.name == "九段线" ? "none" : "#f5e0cc"
          )
          .attr("d", this.pathDrawer);
    },
    drawSouthChinaSeaLegend() {
      let displayRange = [
        new Point(...this.projection([106, 23])),
        new Point(...this.projection([122, 2])),
      ];
      this.southSeaLegend
          .attr("transform", `translate(${350}, ${150}) scale(0.35)`)
          .attr("transform-origin", "center");
      this.southSeaLegend
          .append("rect")
          .attr("id", "map_nanhai_box")
          .attr("x", displayRange[0].x)
          .attr("y", displayRange[0].y)
          .attr("width", displayRange[1].x - displayRange[0].x)
          .attr("height", displayRange[1].y - displayRange[0].y)
          .attr("fill", "none")
          .attr("stroke", theme.color.majorFontColor);

      this.southSeaLegend
          .append("clipPath") // define a clip path
          .attr("id", "clip-path-southSeaLegend") // give the clipPath an ID
          .append("rect")
          .attr("x", displayRange[0].x)
          .attr("y", displayRange[0].y)
          .attr("width", displayRange[1].x - displayRange[0].x)
          .attr("height", displayRange[1].y - displayRange[0].y)
          .attr("fill", "none");
      let southSeaMapGroup = this.southSeaLegend
          .append("g")
          .attr("class", "g-southSeaGeometry")
          .attr("clip-path", "url(#clip-path-southSeaLegend)");

      southSeaMapGroup
          .selectAll("path")
          .data(getChinaInlineSouthSeaGeojson().features)
          .join("path")
          .attr("stroke", theme.color.majorFontColor)
          .attr("fill", (d) => (d.properties.name == "九段线" ? "none" : "#eee"))
          .attr("stroke-width", "2")
          .attr("d", this.pathDrawer);

      this.southSeaLegend
          .append("svg")
          .attr("x", displayRange[0].x)
          .attr("y", displayRange[0].y)
          .attr("width", displayRange[1].x - displayRange[0].x)
          .attr("height", displayRange[1].y - displayRange[0].y)
          .attr("viewBox", "-11 -18 115 130")
          .selectAll("path")
          .data(getChinaSouthSeaIslandsPath())
          .join("path")
          .attr("d", (d) => d)
          .attr("stroke", "none")
          .attr("fill", theme.color.majorFontColor);

      this.southSeaLegend
          .append("text")
          .text("南海诸岛")
          .style("font-size", 32)
          .style("font-family", "FZQINGKBYSJF")
          .attr("x", displayRange[1].x - 5)
          .attr("y", displayRange[1].y - 10)
          .attr("fill", theme.color.mapDarkerBrown)
          .attr("text-anchor", "end")
          .attr("vertical-alignment", "bottom");
    },
    drawNeighborArea() {
      this.neighborArea
          .selectAll('path')
          .data(Data.getNeighborAreaGeojson().features)
          .join("path")
          .attr("stroke", theme.color.majorFontColor)
          .attr("stroke-opacity", "0.7")
          .attr("stroke-width", 0.3)
          .attr("fill", "none")
          .attr("d", this.pathDrawer);

    },
    drawProvinceMap(name) {
      this.provinceMap.selectAll("path").remove();
      if (name && this.mapScaleTier >= 2) {
        this.provinceMap
            .selectAll("path")
            .data(Data.getProvinceGeojson(name).features)
            .join("path")
            .attr("d", this.pathDrawer)
            .attr("fill", "none")
            .attr("stroke", theme.color.majorFontColor)
            .attr("stroke-width", 0.2)
            .attr("stroke-opacity", 0.2)
            .style("pointer-events", "none");
        // this.geoMap.selectAll("path").attr("visibility", d => ((d.properties.name === name) ? 'hidden' : 'visible'));
      }
      else {
        // this.geoMap.selectAll("path").attr("visibility", 'visible');
      }
    },
    drawGeoMap() {
      this.geoMap
          .selectAll("path")
          .data(Data.getChinaGeojson().features)
          .join("path")
          .attr("d", this.pathDrawer)
          .attr("fill", "none")
          .attr("stroke", theme.color.majorFontColor)
          .attr("stroke-width", 0.5)
          // .style("mix-blend-mode", "multiply")
          .on("click", (event, d) => {
            this.$store.commit("setProvinceSelected", [
              d.name,
              getPolygon(d),
              [d.in, d.out],
            ]);
          })
          .on("dblclick", (e) => {
            this.zoomCenter(0, this.projection(d3.select(e.target).datum().properties.cp));
          });
    },
    drawScatterPlot(points) {
      this.scatterPlot.selectAll('g').remove();
      if (this.componentsState.scatterplotOut.enable) {
        this.scatterPlot.append('g').selectAll("circle")
            .data(points.filter(d => d[2] === -1))
            .join('circle')
            .attr("stroke", "none")
            .attr("fill", theme.color.mapLegendColor0)
            .attr("fill-opacity", "0.3")
            .attr("cx", d => d[0])
            .attr("cy", d => d[1])
            .attr("r", 2 / this.mapScaleTier)
            .style("pointer-events", "none")
      }
      if (this.componentsState.scatterplotIn.enable) {
        this.scatterPlot.append('g').selectAll("circle")
            .data(points.filter(d => d[2] === 1))
            .join('circle')
            .attr("stroke", "none")
            .attr("fill", theme.color.mapLegendColor8)
            .attr("fill-opacity", "0.3")
            .attr("cx", d => d[0])
            .attr("cy", d => d[1])
            .attr("r", 2 / this.mapScaleTier)
            .style("pointer-events", "none")
      }
    },
    drawContour(points) {
      this.contourPlot.selectAll('g').remove();
      let contourGenerator = d3.contourDensity()
          .x((d) => d[0])
          .y((d) => d[1])
          .weight((d) => d[2])
          .size([2000, 2000])
          .bandwidth(8)
          .cellSize(2)
          .thresholds(20);
      // In contour
      if (this.componentsState.densityIn.enable) {
        let contourPositive = contourGenerator(points);
        this.contourPlot.append('g')
            .style("pointer-events", "none")
            .selectAll("path")
            .data(contourPositive)
            .join("path")
            .attr("fill", theme.color.mapLegendColor8)
            .attr("fill-opacity", "0.1")
            .attr("stroke", "#666")
            .attr("stroke-linejoin", "round")
            .attr("stroke-width", (d, i) => i % 5 ? 0.05 : 0.25)
            .attr("d", d3.geoPath());
      }
      //Out contour
      if (this.componentsState.densityOut.enable) {
        for (let i of points) {
          i[2] *= -1;
        }
        let contourNegative = contourGenerator(points);
        this.contourPlot.append('g')
            .style("pointer-events", "none")
            .selectAll("path")
            .data(contourNegative)
            .join("path")
            .attr("fill", theme.color.mapLegendColor0)
            .attr("fill-opacity", "0.1")
            .attr("stroke", "#666")
            .attr("stroke-linejoin", "round")
            .attr("stroke-width", (d, i) => i % 5 ? 0.05 : 0.25)
            .attr("d", d3.geoPath());
      }
    },

    //map zoom and pan
    registerZoomController(width, height) {
      this.zoomController = d3
          .zoom()
          .extent([
            [0, 0],
            [width, height],
          ])
          .scaleExtent([1, 8])
          .on("zoom", (e) => {
            this.container.attr("transform", e.transform);
            // console.log(this.zoomController, d3.zoomTransform(this.containerWrapper.node()));
            this.mapScale = d3.zoomTransform(this.containerWrapper.node()).k;
            console.log(this.mapScale);
          })
          .translateExtent([[-300, -100], [2400, 900]]);
      this.containerWrapper.call(this.zoomController).on("dblclick.zoom", null);
    },
    //tooltip for province
    registerTooltipProvince() {
      this.tooltipProvince = Tooltip()
          .extent([
            [0, 0],
            [this.svg.attr("width"), this.svg.attr("height")],
          ])
          .tips(
              ["name", "in", "out", "sum"],
              ["", "迁入人数： ", "迁出人数：", "净迁入人数："],
              [null, null, null, null]
          )
          .fontSize(16)
          .padding([8, 4])
          .margin([10, 10]);
      this.containerWrapper.call(this.tooltipProvince);
    },
    //tooltip for arrow
    registerTooltipArrow() {
      this.tooltipArrow = Tooltip()
          .extent([
            [0, 0],
            [this.svg.attr("width"), this.svg.attr("height")],
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
      this.containerWrapper.call(this.tooltipArrow);
    },
    registerTooltipShortArrow() {
      this.tooltipShortArrow = Tooltip()
          .extent([
            [0, 0],
            [this.svg.attr("width"), this.svg.attr("height")],
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
      this.containerWrapper.call(this.tooltipShortArrow);
    },

    //province mouse hover highligh
    registerProvinceHover() {
      this.geoMap
          .selectAll("path")
          .on("mouseenter", (e) => {
            d3.select(e.target)
                .attr(
                    "filter",
                    "drop-shadow(2px 2px 5px rgba(0, 0, 0, 0.3)) brightness(1.05)"
                )
                .attr("transform", "scale(1.01)")
                .attr("transform-origin", d => {
                  let r = this.projection(d.properties.cp);
                  return `${r[0]} ${r[1]}`;
                });
          })
          .on("mouseleave", (e) => {
            d3.select(e.target).attr("filter", null).attr("transform", null);
          })
          .each(this.tooltipProvince.events);
    },
    //initialize
    initialize(sWidth, sHeight) {
      const width = 1920;
      const height = (sHeight / sWidth) * width;
      this.svg = d3.select(this.$el).select("svg");
      this.svg
          .attr("width", sWidth)
          .attr("height", sHeight)
          .attr("viewBox", `0 0 ${width} ${height}`);
      this.containerWrapper = this.svg.append("g");
      this.container = this.containerWrapper.append("g");

      //back rectangle for click, pan and zoom convience
      this.containerWrapper
          .append("rect")
          .attr("width", width)
          .attr("height", height)
          .attr("x", 0)
          .attr("y", 0)
          .attr("fill-opacity", 0)
          .lower()
          .on("click", () => {
            this.$store.commit("setProvinceSelected", ["", null, null]);
          })
          .on("dblclick", () => {
            this.zoomCenter();
          });


      //geo map
      this.projection = d3
          .geoMercator()
          .center([99, 31])
          .scale(800 * Math.min(width / 1920, height / 734))
          .translate([width * 0.5, height * 0.63]);
      this.pathDrawer = d3.geoPath(this.projection);

      //draw map: neighboring area
      this.neighborArea = this.container.append('g');
      this.drawNeighborArea();
      //draw map: chinese province
      this.geoMap = this.container.append("g");
      this.drawGeoMap();
      //draw map: china south sea and nine-dash line
      this.southSea = this.container.append("g");
      this.drawSouthChinaSea();
      this.southSeaLegend = this.container.append("g");
      this.drawSouthChinaSeaLegend();
      this.provinceMap = this.container.append('g').classed("provincemap", true);
      //scatter plot
      this.contourPlot = this.container.append('g').classed("contourplot", true);
      this.scatterPlot = this.container.append('g').classed("scatterplot", true);


      //arrows and axis
      this.shortArrows = this.container.append('g').classed("shortarrows", true);
      this.arrows = this.container.append("g");


      // this.axis = this.container.append("g");
      // this.drawMapAxis();

      this.geoLabels = this.container.append('g');

      this.registerZoomController(width, height);
      this.registerTooltipProvince();

      this.registerProvinceHover();

      this.registerTooltipArrow();

      this.registerTooltipShortArrow();

      //tooltip for arrows
      this.updateMigration({timeChange: true, componentChange: true});
    },
  },
  mounted() {
    this.initialize(this.canvasWidth, this.canvasHeight);
  },
};
</script>

<style scoped lang="scss">
</style>
