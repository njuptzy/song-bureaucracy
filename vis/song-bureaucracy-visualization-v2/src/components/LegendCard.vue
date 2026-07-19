<template>
  <div class="container" v-if="showInfoCard">
    <SemiBorderFrame class="semiborder" header-padding="0.3vw">
      <template v-slot:header>
        <div class="semiborder-title">净迁入人数</div>
      </template>
      <div class="color-legend legend">
        <div class="color-legend--content legend--content">
          <div class="color-legend--item legend--item" v-for="(item, index) in reversedBalanceInterval" :key="index">
            <svg height="1vw" width="1vw" viewBox="0 0 15 15">
              <rect x="0" y="0" height="15" width="15" :fill="item[2]" stroke="white" stroke-width="2" ></rect>
            </svg>
            <span class="left-span">{{item[0]}}</span>
            <span class="mid-span">~</span>
            <span class="right-span">{{item[1]}}</span>
          </div>
        </div>
      </div>
    </SemiBorderFrame>


    <SemiBorderFrame class="semiborder semiborder-arrow"  header-padding="0.3vw">
      <template v-slot:header>
        <div class="semiborder-title">流动规模</div>
      </template>
    <div class="arrow-legend legend">
      <div class="arrow-legend--content legend--content">
        <div class="arrow-legend--item legend--item" v-for="(item, index) in arrowInterval" :key="index">
          <svg height="2vw" width="2vw" viewBox="-40 -20 40 40">
            <path stroke="url(#arrow-gradient)" stroke-linecap="round" fill="none"  filter="drop-shadow(2px 2px 5px rgba(0, 0, 0, 0.3))" d="M-40,0 L-5,0.1" :stroke-width="item[2]"></path>
            <path stroke="#724a2b" stroke-width="0.5" fill="#ae8e71" :fill-opacity="index == 0 ? 1 : 0.3" :d="getArrowHeadPath(0)"></path>
            <path stroke="#724a2b" stroke-width="0.5" fill="#ae8e71" :fill-opacity="index == 1 ? 1 : 0.3" :d="getArrowHeadPath(1)"></path>
            <path stroke="#724a2b" stroke-width="0.5" fill="#ae8e71" :fill-opacity="index == 2 ? 1 : 0.3" :d="getArrowHeadPath(2)"></path>
          </svg>
          <span class="left-span">{{ item[0] }}</span>
          <span class="mid-span">~</span>
          <span class="right-span">{{ item[1] }}</span>
        </div>
      </div>
    </div>
    </SemiBorderFrame>
  </div>
</template>

<script>


import {mapState} from "vuex";
import SemiBorderFrame from "@/components/SemiBorderFrame.vue";
import * as MapDrawer from "@/utils/MapDrawer"
import {Point} from "@/utils/Geometry"

export default {
  name: "LegendCard",
  components: {SemiBorderFrame},
  data() {
    return {

    }
  },
  computed: {
    ...mapState(["balanceInterval", "arrowInterval", "showInfoCard"]),
    reversedBalanceInterval() {
      return Object.assign([], this.balanceInterval).reverse();
    },
  },
  methods: {
    getArrowHeadPath(tier) {
      const tierLens = [11, 18, 25]
      return MapDrawer.arrowHeadPath(new Point(0, 0), tierLens[tier], new Point(-1, 0), 0);
    }
  }
}
</script>

<style scoped lang="scss">
.container {
  user-select: none;
  padding: 1vh 0 2vh 2vw;
  color: #5a3a20;
  font-size: 2vh;
  display: flex;

  .semiborder {
    padding: 0;
  }
  .semiborder-arrow {
    margin-left: -0.1vh;
  }
  .semiborder-title {
    font-size: 2.5vh;
  }

  .color-legend {
    width: 10vw;
  }
  .arrow-legend {
    width: 10vw;
  }
  .legend {
    display: flex;
    .legend--content {
      flex: 1 1 auto;
      display: grid;
      margin: 3vh 0.8vw 1vh;
      grid-template-columns: repeat(4, auto);
      .legend--item {
        display: contents;
        font-family:Consolas,Monaco,Lucida Console,Liberation Mono,DejaVu Sans Mono,Bitstream Vera Sans Mono,Courier New, monospace;
        svg {
          grid-column: 1;
          margin:auto;
        }
        span {
          margin: auto;
        }
        .left-span {
          grid-column: 2;
        }
        .mid-span {
          grid-column: 3;
        }
        .right-span {
          grid-column: 4;
        }
      }
    }
  }
}

</style>
