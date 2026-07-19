<template>
  <div class="container" id="container">
    <input
      type="range"
      class="range-bar"
      id="kernel-width"
      min="0.1"
      max="2"
      step="0.1"
      value="this.kernel_width"
      @input="changeKernelWidth"
    />
    <input
      type="range"
      class="range-bar"
      id="axis-angle"
      min="0"
      max="360"
      step="0.1"
      value="this.axisAngle"
      @input="changeAxisAngle"
    />
    <input
      type="range"
      class="range-bar"
      id="axis-length"
      min="1"
      max="20"
      step="0.1"
      value="this.axisLength"
      @input="changeAxisLength"
    />
  </div>
</template>

<script>
import * as d3 from "d3";
import { mapState } from "vuex";
import * as Data from "@/data/Data";

export default {
  name: "PrimaryAxis",
  data() {
    return {};
  },
  props: ["Width", "Height"],
  computed: {
    ...mapState([
      "yearRange",
      "provinceSelected",
      "provinceInOut",
      "arrows",
      "arrowHover",
      "kernel_width",
      "axisLength",
      "axisAngle",
      "axisTag",
    ]),
  },
  watch: {
    yearRange: {
      handler() {
        this.desmap.remove();
        // this.desmap.remove();
        // this.drawAxis("all", this.Width, this.Height);
        this.drawAxis(this.axisTag, this.Width, this.Height);
      },
    },
    kernel_width: {
      handler() {
        this.desmap.remove();
        // this.drawAxis("all", this.Width, this.Height);
        this.drawAxis(this.axisTag, this.Width, this.Height);
      },
    },

    axisLength: {
      handler() {
        this.desmap.remove();
        // this.drawAxis("all", this.Width, this.Height);
        this.drawAxis(this.axisTag, this.Width, this.Height);
      },
    },

    axisAngle: {
      handler() {
        this.desmap.remove();
        // this.drawAxis("all", this.Width, this.Height);
        this.drawAxis(this.axisTag, this.Width, this.Height);
      },
    },
    axisTag: {
      handler() {
        this.desmap.remove();
        this.drawAxis(this.axisTag, this.Width, this.Height);
      },
    },
  },
  methods: {
    changeKernelWidth(e) {
      this.$store.commit("changeKernelWidth", e.target.value);
    },
    changeAxisAngle(e) {
      this.$store.commit("changeAxisAngle", e.target.value);
    },
    changeAxisLength(e) {
      this.$store.commit("changeAxisLength", e.target.value);
    },
    changeTag(s) {
      // console.log(s);
      this.$store.commit("changeTag", s);
    },

    drawAxis(tag, width, height) {
      let color;
      let jinshi_color = "#e2dce2";
      let junwang_color = "#cdd5db";
      let guanzhi_color = "#eae9e1";
      let ori_data;
      if (tag == "all") {
        let data_all = Data.getFilteredElites({ year: this.yearRange[1] });
        ori_data = data_all.map((d) => d.getPos(this.yearRange[1]));
        color = "#ac9176";
      } else if (tag == "进士") {
        let jinshi_data = Data.getFilteredElites({
          year: this.yearRange[1],
          type: "进士",
        });
        ori_data = jinshi_data.map((d) => d.getPos(this.yearRange[1]));
        color = jinshi_color;
      } else if (tag == "郡望") {
        let junwang_data = Data.getFilteredElites({
          year: this.yearRange[1],
          type: "郡望",
        });
        ori_data = junwang_data.map((d) => d.getPos(this.yearRange[1]));
        color = junwang_color;
      } else {
        let guanzhi_data = Data.getFilteredElites({
          year: this.yearRange[1],
          type: "官职",
        });
        ori_data = guanzhi_data.map((d) => d.getPos(this.yearRange[1]));
        color = guanzhi_color;
      }

      let data = Data.getProjected1DPos(
        ori_data,
        this.axisLength,
        this.axisAngle
      );

      let bandwidth = this.kernel_width * 0.51;

      let svg = this.container;

      // 方框高度
      let ih = height;
      // 方框宽度
      let iw = width;
      let gap = ih / 35;

      let margin = {
        left: 0.1 * iw,
        right: 0.1 * iw,
        top: 0.1 * ih,
        bottom: 0.1 * ih,
      };
      let L = -this.axisLength;
      let R = this.axisLength;
      // x 轴方向的比例尺
      const x = d3
        .scaleLinear()
        .domain([L, R])
        .range([margin.left, width - margin.right]);

      // 采样点
      const sample = x.ticks(1000); // --> [-10, -9.98, -9.96, -9.94,..., 9.98, 10]
      let density = Data.kde_1d(bandwidth, sample, data);
      // x 轴方向的比例尺
      const y = d3
        .scaleLinear()
        .domain([0, d3.max(density, (d) => d[1])])
        .nice()
        .range([0.3 * ih, margin.top]); //y轴方向的比例尺

      const area = d3
        .area()
        .curve(d3.curveBasis)
        .x((d) => x(d[0]))
        .y0(y(0))
        .y1((d) => y(d[1]));

      // 绘制前的缩放
      density = density.map(([x, y]) => [x, 1.0 * y]);

      // 绘制密度图
      this.desmap = svg
        .append("path")
        .datum(density)
        .attr("fill", color)
        .attr("d", area);

      // 箭头两个端点
      let x1 = margin.left;
      let y1 = 0.3 * ih;
      let x2 = width - margin.right;
      let y2 = 0.3 * ih;

      // 开始绘制 (渲染两层以模拟边缘和内部)
      let g = svg.append("g");

      // 绘制箭头
      let head_size = width * 0.02;
      // g.append("path")
      //   .attr("d", this.generateArrow(x1, y1, x2, y2, head_size))
      //   .style("fill", "none")
      //   .style("stroke", "#aa9cff")
      //   .style("stroke-width", 4);
      g.append("path")
        .attr("d", Data.generateArrow(x1, y1, x2, y2, head_size))
        .style("fill", "none")
        .style("stroke", "#5a3a20")
        .style("stroke-width", 1.5);

      // 绘制中心点
      g.append("circle")
        .attr("cx", (x1 + x2) / 2)
        .attr("cy", (y1 + y2) / 2)
        .attr("r", 3.75)
        .style("fill", "#5a3a20");

      // 绘制另一端点
      g.append("circle")
        .attr("cx", x1)
        .attr("cy", y1)
        .attr("r", 3.75)
        .style("fill", "#5a3a20");
    },

    // 完成主轴控制静态部分的绘制
    // 一维轴线在0.3ih的地方绘制，其他控制组件和文字对齐
    drawWrap(width, height) {
      // 方框高度
      let ih = height;
      // 方框宽度
      let iw = width;
      let gap = ih / 35;

      this.svg = d3
        .select(this.$el)
        .append("svg")
        .attr("height", `${height}`)
        .attr("width", `${width}`);
      this.container = this.svg.append("g");
      // 三个标题信息
      this.container.append("g").call((g) => {
        g.append("line")
          .attr("stroke", "#ac9176")
          .attr("x1", 0)
          .attr("x2", iw * 0.1)
          .attr("stroke-width", 4);
        g.append("text")
          .attr("font-size", 20)
          .attr("x", iw * 0.1 + gap)
          .attr("y", 16)
          .attr("fill", "#5a3a20")
          .attr("font-family", "FZQINGKBYSJF")
          .attr("font-weight", 700)
          .text("主轴");
        g.append("line")
          .attr("stroke", "#ac9176")
          .attr("x1", 0.1 * iw + 2 * gap + 40)
          .attr("x2", iw)
          .attr("stroke-width", 4);
      });

      this.container.append("g").call((g) => {
        g.append("line")
          .attr("transform", `translate(0, ${0.6 * ih})`)
          .attr("stroke", "#ac9176")
          .attr("x1", 0)
          .attr("x2", iw * 0.1)
          .attr("stroke-width", 2);
        g.append("text")
          .attr("transform", `translate(0, ${0.6 * ih})`)
          .attr("font-size", 20)
          .attr("x", iw * 0.1 + gap)
          .attr("y", 16)
          .attr("fill", "#5a3a20")
          .attr("font-family", "FZQINGKBYSJF")
          .attr("font-weight", 700)
          .text("主轴选项");
        g.append("line")
          .attr("transform", `translate(0, ${0.6 * ih})`)
          .attr("stroke", "#ac9176")
          .attr("x1", 0.1 * iw + 2 * gap + 80)
          .attr("x2", iw)
          .attr("stroke-width", 2);
      });

      this.all_data = this.container.append("g").call((g) => {
        g.append("line")
          .attr("transform", `translate(0, ${0.9 * ih})`)
          .attr("stroke", "#ac9176")
          .attr("x1", 0)
          .attr("x2", iw * 0.1)
          .attr("stroke-width", 2);
        g.append("text")
          .attr("transform", `translate(0, ${0.9 * ih})`)
          .attr("font-size", 20)
          .attr("x", iw * 0.1 + gap)
          .attr("y", 16)
          .attr("fill", "#5a3a20")
          .attr("font-family", "FZQINGKBYSJF")
          .attr("font-weight", 700)
          .text("精英类别");
        g.append("line")
          .attr("transform", `translate(0, ${0.9 * ih})`)
          .attr("stroke", "#ac9176")
          .attr("x1", 0.1 * iw + 2 * gap + 80)
          .attr("x2", iw)
          .attr("stroke-width", 2);
      });

      // 更换按钮
      this.jinshi_button = this.container.append("g").call((g) => {
        g.append("text")
          .attr("transform", `translate(0, ${ih})`)
          .attr("font-size", 15)
          .attr("x", iw * 0.1 + 2 * gap)
          .attr("y", -2)
          .attr("fill", "#5a3a20")
          .attr("font-family", "FZQINGKBYSJF")
          .attr("font-weight", 400)
          .text("进士");

        g.append("rect")
          .attr("x", iw * 0.1 + 0.5 * gap)
          .attr("y", ih - gap)
          .attr("width", gap)
          .attr("height", gap)
          .attr("stroke", "#e2dce2")
          .attr("fill", "#e2dce2");
      });

      this.junwang_button = this.container.append("g").call((g) => {
        g.append("text")
          .attr("transform", `translate(0, ${ih})`)
          .attr("font-size", 15)
          .attr("x", 0.2 * iw + 5 * gap + 30)
          .attr("y", -2)
          .attr("fill", "#5a3a20")
          .attr("font-family", "FZQINGKBYSJF")
          .attr("font-weight", 400)
          .text("郡望");
        g.append("rect")
          .attr("x", 0.2 * iw + 3.5 * gap + 30)
          .attr("y", ih - gap)
          .attr("width", gap)
          .attr("height", gap)
          .attr("stroke", "#cdd5db")
          .attr("fill", "#cdd5db");
      });

      this.guanzhi_button = this.container.append("g").call((g) => {
        g.append("text")
          .attr("transform", `translate(0, ${ih})`)
          .attr("font-size", 15)
          .attr("x", 0.3 * iw + 8 * gap + 60)
          .attr("y", -2)
          .attr("fill", "#5a3a20")
          .attr("font-family", "FZQINGKBYSJF")
          .attr("font-weight", 400)
          .text("官职");

        g.append("rect")
          .attr("x", 0.3 * iw + 6.5 * gap + 60)
          .attr("y", ih - gap)
          .attr("width", gap)
          .attr("height", gap)
          .attr("stroke", "#eae9e1")
          .attr("fill", "#eae9e1");
      });

      // 边框
      this.container.append("g").call((g) => {
        g.append("line")
          .attr("transform", `translate(0, ${ih})`)
          .attr("stroke", "#ac9176")
          .attr("x1", 0)
          .attr("x2", iw * 0.1)
          .attr("stroke-width", 4);

        g.append("line")
          .attr("transform", `translate(0, ${ih})`)
          .attr("stroke", "#ac9176")
          .attr("x1", 0.1 * iw + 3 * gap + 30)
          .attr("x2", 0.2 * iw + 3 * gap + 30)
          .attr("stroke-width", 4);

        g.append("line")
          .attr("transform", `translate(0, ${ih})`)
          .attr("stroke", "#ac9176")
          .attr("x1", 0.2 * iw + 6 * gap + 60)
          .attr("x2", 0.3 * iw + 6 * gap + 60)
          .attr("stroke-width", 4);

        g.append("line")
          .attr("transform", `translate(0, ${ih})`)
          .attr("stroke", "#ac9176")
          .attr("x1", 0.3 * iw + 9 * gap + 90)
          .attr("x2", iw)
          .attr("stroke-width", 4);
      });

      this.container.append("g").call((g) => {
        g.append("line")
          .attr("stroke", "#ac9176")
          .attr("y1", 0)
          .attr("y2", 0.3 * ih - gap)
          .attr("stroke-width", 4);
      });
      this.container.append("g").call((g) => {
        g.append("line")
          .attr("stroke", "#ac9176")
          .attr("y1", 0.3 * ih + gap)
          .attr("y2", ih)
          .attr("stroke-width", 4);
      });

      this.container.append("g").call((g) => {
        g.append("line")
          .attr("stroke", "#ac9176")
          .attr("y1", 0)
          .attr("y2", 0.3 * ih - gap)
          .attr("x1", iw)
          .attr("x2", iw)
          .attr("stroke-width", 4);
      });
      this.container.append("g").call((g) => {
        g.append("line")
          .attr("stroke", "#ac9176")
          .attr("y1", 0.3 * ih + gap)
          .attr("y2", ih)
          .attr("x1", iw)
          .attr("x2", iw)
          .attr("stroke-width", 4);
      });
      // 提示文字
      this.container.append("g").call((g) => {
        g.append("text")
          .attr("transform", `translate(0, ${0.7 * ih})`)
          .attr("font-size", 15)
          .attr("x", iw * 0.1 + gap)
          .attr("y", 0)
          .attr("fill", "#5a3a20")
          .attr("font-family", "FZQINGKBYSJF")
          .attr("font-weight", 400)
          .text("平滑程度");

        g.append("text")
          .attr("transform", `translate(0, ${0.7 * ih})`)
          .attr("font-size", 15)
          .attr("x", iw * 0.1 + gap)
          .attr("y", 2.5 * gap)
          .attr("fill", "#5a3a20")
          .attr("font-family", "FZQINGKBYSJF")
          .attr("font-weight", 400)
          .text("主轴旋转");

        g.append("text")
          .attr("transform", `translate(0, ${0.7 * ih})`)
          .attr("font-size", 15)
          .attr("x", iw * 0.1 + gap)
          .attr("y", 5 * gap)
          .attr("fill", "#5a3a20")
          .attr("font-family", "FZQINGKBYSJF")
          .attr("font-weight", 400)
          .text("主轴长度");
      });
    },

    drawControler() {
      this.jinshi_button.on("click", (e) => this.changeTag("进士"));
      this.junwang_button.on("click", (e) => this.changeTag("郡望"));
      this.guanzhi_button.on("click", (e) => this.changeTag("官职"));
      this.all_data.on("click", (e) => this.changeTag("all"));
    },
  },

  mounted() {
    this.drawWrap(this.Width, this.Height);
    // this.drawAxis("all", this.Width, this.Height);
    this.drawAxis(this.axisTag, this.Width, this.Height);
    this.drawControler();
  },
};
</script>

<style scoped lang="scss">
.container {
  font-family: FZQINGKBYSJF;
  color: #5a3a20;
  text-align: left;
  font-size: 2vh;
  padding-right: 2vw;
  padding-top: 1vw;
  position: relative;
  .range-bar {
    position: absolute;
    width: 55% !important;
    -webkit-appearance: none;
    height: 2vh;
    background-color: rgba(0, 0, 0, 0);
  }
  .range-bar::-webkit-slider-runnable-track {
    -webkit-appearance: none;
    background: #ac9176;
    height: 0.2vh;
  }
  .range-bar::-webkit-slider-thumb {
    height: 1vh;
    width: 1vh;
    margin-top: -0.4vh; /*使滑块超出轨道部分的偏移量相等*/
    -webkit-appearance: none; /*清除系统默认样式*/
    border-radius: 50%;
    background-color: #5a3a20;
  }
  #kernel-width {
    margin-top: 30vh;
    margin-left: 7vw;
  }
  #axis-angle {
    margin-top: 33.3vh;
    margin-left: 7vw;
  }
  #axis-length {
    margin-top: 36.6vh;
    margin-left: 7vw;
  }
}
</style>
