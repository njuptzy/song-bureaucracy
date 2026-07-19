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
import {Point} from "@/utils/Geometry";
import {mapState} from "vuex";
import * as Layers from "@/components/map/layers";




export default {
  name: "MainMap",
  props: ["canvasWidth", "canvasHeight"],
  data() {
    return {
      mapScale: 1,
      mapScaleTier: 1,
      mapData: null,
      arrowsLabel: null,
      shortArrows: null,
    };
  },
  computed: {
    ...mapState([      
      "yearRange",

      "provinceSelected",

      "balanceRange",
      "provinceSelectedPolygon",
      
      "arrowInterval",
      "balanceInterval",

      "arrows",
      "arrowHover",
      
      "componentsState",
    ]),
  },
  watch: {
    mapScale: {
      handler() {
        let t = Math.floor(Math.max(1, Math.log(this.mapScale) / Math.log(2)));
        this.mapScaleTier = t;
      }
    },
    yearRange: {
      handler() {
        this.mapData = Data.getDataByTimeRange(this.yearRange[0], this.yearRange[1]);
      },
      deep: true,
    },
  },
  methods: {  
    zoomWithCenter(scale, center) {
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
            this.mapScale = d3.zoomTransform(this.containerWrapper.node()).k;
          })
          .translateExtent([[-300, -100], [2400, 900]]);
      this.containerWrapper.call(this.zoomController).on("dblclick.zoom", null);
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
      this.tooltipContainer = this.containerWrapper.append('g');
      /* back rectangle for click, pan and zoom convience */
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
            this.zoomWithCenter();
          });
      /* projection for map*/
      this.projection = d3
          .geoMercator()
          .center([99, 31])
          .scale(800 * Math.min(width / 1920, height / 734))
          .translate([width * 0.5, height * 0.63]);
      /* svg path drawer for projection */
      this.pathDrawer = d3.geoPath(this.projection);
      /* map of neighbor countries*/
      Layers.NeighborArea.register(this);
      /* map of China, to province granularity*/
      Layers.GeoMap.register(this);
      /* south sea, 9 segments*/
      Layers.SouthChinaSea.register(this);
      Layers.SouthChinaSeaLegend.register(this);
      Layers.ProvinceMap.register(this);
      /* contour & scatterplot for migration in/out */
      Layers.ContourPlot.register(this);
      Layers.ScatterPlot.register(this);
      /* arrows and labels */
      Layers.ShortArrows.register(this);
      Layers.Arrows.register(this);
      Layers.GeoLabels.register(this);
      /* map zoom controller */
      this.registerZoomController(width, height);
      /* initialize */
      this.$store.commit("changeYearRange", [this.yearRange[0], this.yearRange[1]]);
    },
  },
  mounted() {
    this.initialize(this.canvasWidth, this.canvasHeight);
  },
};
</script>

<style scoped lang="scss">
</style>
