<template>
  <div class="container"></div>
</template>

<script>
import { mapState } from "vuex";
import * as d3 from "d3";
import * as Data from "@/data/Data";

const margin = {
  top: 0.08,
  left: 0.02,
  right: 0.02,
  bottom: 0.25,
};

export default {
  name: "TimeLine",
  props: [
    "canvasWidth",
    "canvasHeight",
    "timeStart",
    "timeEnd",
    "isEvent",
    "isDynasty",
    // "timeGran",
  ],
  data() {
    return {
      // isEvent: true,
      // isDynasty: true,
      timeGran: "year",
    };
  },
  computed: {
    ...mapState(["yearRange"]),
  },
  methods: {
    initializeTimeline(
      sWidth,
      sHeight,
      // 下列参数值改为可变形式
      yearStart,
      yearEnd,
      dynasty,
      event,
      yearStep = 50
    ) {
      const width = 2560;
      const height = (sHeight / sWidth) * width;
      let ih = height * (1 - margin.top - margin.bottom);
      let iw = width * (1 - margin.left - margin.right);

      // 控制栏总宽度
      let cw = iw / 10;

      this.bins = Data.getBins(yearStart, yearEnd, yearStep);
      this.periodLegendData = Data.getPeriodLegend();
      this.bigEventData = Data.getBigEvent();

      this.timeScale = d3
        .scaleLinear()
        .domain([yearStart, yearEnd])
        .range([cw, iw]);

      this.yScale = d3
        .scaleLinear()
        .domain([0, d3.max(this.bins, (d) => d[2])])
        .range([ih, 0]);

      let stepWidth =
        this.timeScale(yearStart + yearStep) - this.timeScale(yearStart);
      let bandWidth = stepWidth / 3;
      let gapWidth = (stepWidth - bandWidth) / 2;

      // container
      this.svg = d3
        .select(this.$el)
        .append("svg")
        .attr("height", `${sHeight}`)
        .attr("width", `${sWidth}`)
        .attr("viewBox", `0 0 ${width} ${height}`);
      this.container = this.svg
        .append("g")
        .attr(
          "transform",
          `translate(${width * margin.left}, ${height * margin.top})`
        );

      let bottomAxis = d3
        .axisBottom(this.timeScale)
        .ticks((yearEnd - yearStart) / yearStep)
        .tickFormat((d) => d);

      // 分割线与文字分隔竖线之间的距离
      let gap = ih / 15;
      // 分割线起始位置
      let divloc = ih / 3;
      // 文字分割线高度
      let th = (ih * 3) / 15;
      // 时间范围轴的宽度
      let rw = 10;

      // 控制栏

      // 分割线
      this.container.append("g").call((g) => {
        g.append("line")
          .attr("transform", `translate(0, ${1.5})`)
          .attr("stroke", "#6a4c2a")
          .attr("x1", 0)
          .attr("x2", cw - 2 * gap)
          .attr("stroke-width", 1.5);
      });

      this.container.append("g").call((g) => {
        g.append("line")
          .attr("transform", `translate(${0}, ${ih})`)
          .attr("stroke", "#6a4c2a")
          .attr("x1", 0)
          .attr("x2", cw - 2 * gap)
          .attr("stroke-width", 1.5);
      });
      // 文字提示方框+文字
      this.container.append("g").call((g) => {
        g.append("rect")
          .attr("x", 0)
          .attr("y", divloc / 4)
          .attr("width", divloc / 4)
          .attr("height", divloc / 4)
          .attr("stroke", "#6a4c2a")
          // .attr("stroke-width", 1.5)
          .attr("fill", "#6a4c2a");

        g.append("text")
          .attr("x", divloc / 2)
          .attr("y", divloc / 2)
          .style("fill", "#6a4c2a")
          .attr("font-size", 18)
          .attr("font-family", "FZQINGKBYSJF")
          .text("年");
      });

      if (dynasty == true) {
        this.container.append("g").call((g) => {
          g.append("rect")
            .attr("x", 0)
            .attr("y", divloc / 4 + divloc)
            .attr("width", divloc / 4)
            .attr("height", divloc / 4)
            .attr("stroke", "#6a4c2a")
            .attr("fill", "#6a4c2a");

          g.append("text")
            .attr("x", divloc / 2)
            .attr("y", divloc + divloc / 2)
            .style("fill", "#6a4c2a")
            .attr("font-size", 18)
            .attr("font-family", "FZQINGKBYSJF")
            .text("朝代");
        });
      }

      if (event == true) {
        this.container.append("g").call((g) => {
          g.append("rect")
            .attr("x", 0)
            .attr("y", divloc / 4 + 2 * divloc)
            .attr("width", divloc / 4)
            .attr("height", divloc / 4)
            .attr("stroke", "#6e4d2b")
            .attr("fill", "#6e4d2b");

          g.append("text")
            .attr("x", divloc / 2)
            .attr("y", 2 * divloc + divloc / 2)
            .style("fill", "#6e4d2b")
            .attr("font-size", 18)
            .attr("font-family", "FZQINGKBYSJF")
            .text("重大事件");
        });
      }

      this.container
        .append("g")
        // .attr("transform", `translate(${0}, ${ih})`)
        .call(bottomAxis)
        .call((g) => {
          g.select(".domain")
            .attr("stroke", "#6a4c2a")
            .attr("stroke-width", 2)
            .attr("transform", `translate(0, ${1.5})`);
          g.selectAll(".tick")
            .append("line")
            .attr("stroke", "#ad9278")
            .attr("y2", function (d) {
              if (d % (10 * yearStep) == 0) return 18;
              else return 8;
            })
            .attr("stroke-width", 1);
          g.selectAll("text")
            .text(function (d) {
              if (d == 0) return 1;
              else return d;
            })
            .attr("font-size", function (d) {
              if (d % (10 * yearStep) == 0) return 15;
              else return 12;
            })
            .attr("dy", function (d) {
              if (d % (10 * yearStep) == 0) return 13;
              else return 5;
            })
            .attr("fill", "#5a3a20")
            .attr("alignment-baseline", "hanging");
        });

      // 分隔线
      if (dynasty == true) {
        this.container
          .append("g")
          .attr("transform", `translate(${0}, ${divloc})`)
          .call((g) => {
            g.append("line")
              .attr("stroke", "#ad9278")
              .attr("x1", cw)
              .attr("x2", iw)
              .attr("stroke-width", 0.8);
          });

        // period legend
        this.container
          .append("g")
          .selectAll("g")
          .data(this.periodLegendData)
          .join("g")
          .attr("x", (d) => this.timeScale(d[0]))
          .attr("transform", (d) => `translate(${this.timeScale(d[1])}, 0)`)
          .call((g) => {
            g.append("line")
              .attr("transform", `translate(${0}, ${divloc + gap})`)
              .attr("stroke", "#ad9278")
              .attr("y2", th)
              .attr("stroke-width", 0.8);
            g.append("text")
              .attr("transform", `translate(${3}, ${divloc + gap + th / 2})`)
              // .selectAll("tspan")
              // .data((d) => d[0])
              // .join("tspan")
              .text((d) => d[0])
              .attr(
                "x",
                (d) => 0.5 * (this.timeScale(d[2]) - this.timeScale(d[1])) - 3
              )
              .attr("y", -5);
            g.selectAll("text")
              .attr("font-family", "FZQINGKBYSJF")
              .attr("font-size", 15)
              .attr("fill", "#6e4d2b")
              .attr("alignment-baseline", "hanging")
              .attr("text-anchor", "middle");
            //special adjustment on font-size for "五代十国" due to the limited space
            g.selectAll("text").each((d, i, e) => {
              if (d[0] == '五代十国') {
                d3.select(e[0]).attr("font-size", 12);
              }
            })
          });
      }

      // 分割线

      this.container
        .append("g")
        .attr("transform", `translate(${0}, ${divloc + gap * 2 + th})`)
        .call((g) => {
          g.append("line")
            .attr("stroke", "#ad9278")
            .attr("x1", cw)
            .attr("x2", iw)
            .attr("stroke-width", 0.8);
        });

      // events
      if (event == true) {
        this.container
          .append("g")
          .selectAll("g")
          .data(this.bigEventData)
          .join("g")
          .attr("x", (d) => this.timeScale(d[0]))
          .attr("transform", (d) => `translate(${this.timeScale(d[1])}, 0)`)
          .call((g) => {
            g.append("line")
              .attr("transform", `translate(${0}, ${divloc + gap * 2 + th})`)
              .attr("stroke", "#ac9176")
              .attr("y2", th / 4)
              .attr("stroke-width", 1.5);

            g.append("text")
              .attr(
                "transform",
                `translate(${0}, ${divloc + gap * 4 + th + th / 4})`
              )
              .text((d) => d[0])
              .attr("y", -10);
            // .selectAll("tspan")
            // .data((d) => d[0])
            // .join("tspan")
            // .text((d) => d)
            // .attr("y", 0);
            g.selectAll("text")
              .attr("font-size", 18)
              .attr("fill", "#6e4d2b")
              .attr("alignment-baseline", "hanging")
              .attr("font-family", "FZQINGKBYSJF")
              .attr("text-anchor", "middle");
          });
      }

      // 拖动轴
      this.container
        .append("line")
        .attr("transform", `translate(${0}, ${ih})`)
        .attr("x1", cw)
        .attr("x2", iw)
        .attr("stroke", "#6a4c2a")
        .attr("stroke-width", 2);

      let brushX = d3.brushX().extent([
        [cw, ih - rw / 2],
        [iw, ih + rw / 2],
      ]);
      this.brushG = this.container.append("g").call(brushX);


      //enlarge the height of overlay for friendly touch interaction
      this.brushG
      .select('.overlay')
          .attr("y", this.brushG.select(".overlay").attr("y") - 50)
      .attr('height', 100);

      this.brushG
        .select(".selection")
        .attr("fill", "#a78d73")
        .attr("fill-opacity", 1)
        .attr("stroke", "#6a4c2a")
        .attr("stroke-width", 1);

      this.brushG
        .transition()
        .duration(100)
        .call(brushX.move, [
          this.timeScale(this.yearRange[0]),
          this.timeScale(this.yearRange[1]),
        ]);

      let that = this;

      let lastStartPos;
      brushX.on("start", (e) => {
        if (e.mode === 'handle' && e.selection) {
          lastStartPos =  e.selection[0];
        }
      });
      brushX.on("end", function (event) {
        // console.log("end", event);
        // 确定所选中的brush区间
        const selection = event.selection;
        let x0 = 0,
          x1 = 0;
        if (event.mode === "handle" && !selection) {
          x0 = d3.pointer(event, that.brushG.select(".overlay").node())[0];
          x1 = x0;
          if (!x0 || !x1) {
            x0 = x1 = lastStartPos;
          }
          x0 -= 10;
          x1 += 10;
          // console.log(x0, x1, lastStartPos);
        } else if (!!event.sourceEvent && !!selection) {
          [x0, x1] = selection;
          if (x0 > x1) [x0, x1] = [x1, x0];
        } else {
          return;
        }

        let x0Year =
          ((that.timeScale.invert(x0) - yearStart) / yearStep) * yearStep +
          yearStart;
        // Math.floor((that.timeScale.invert(x0) - yearStart) / yearStep) *
        //   yearStep +
        // yearStart;
        x0 = that.timeScale(x0Year);
        let x1Year =
          ((that.timeScale.invert(x1) - yearStart) / yearStep) * yearStep +
          yearStart;
        // Math.ceil((that.timeScale.invert(x1) - yearStart) / yearStep) *
        //   yearStep +
        //   yearStart;
        x1 = that.timeScale(x1Year);
        that.brushG.transition().duration(100).call(brushX.move, [x0, x1]);
        that.$store.commit("changeYearRange", [
          Math.floor(x0Year),
          Math.ceil(x1Year),
        ]);
      });
    },
  },
  mounted() {
    this.initializeTimeline(
      this.canvasWidth,
      this.canvasHeight,
      this.timeStart,
      this.timeEnd,
      this.isDynasty,
      this.isEvent
    );
  },
};
</script>

<style scoped lang="scss">
.container {
  user-select: none;
}
</style>
