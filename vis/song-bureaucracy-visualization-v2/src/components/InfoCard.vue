<template>
  <div class="container infocard" :style="calcPaddingBottomStyle">
    <semi-border-frame header-align="left-2vh" footer-align="right-2vh" footer-padding="1.5vh"
                       @click="changeShowInfoCard">
      <template v-slot:header>
        <div class="province">
          {{ provinceName }}
        </div>
      </template>
      <template v-slot:footer>
        <div class="year-range">
          <span>公元</span>{{ (yearRange[0] > 0) ? yearRange[0] : "前" + (-yearRange[0]) }} -
          <span>公元</span>{{ (yearRange[1] > 0) ? yearRange[1] : "前" + (-yearRange[1]) }}
        </div>
      </template>
      <div class='sep'></div>
    </semi-border-frame>


    <div class="province-stat" v-if="provinceSelected && showInfoCard">
      <div class="in-stat stat">
        <div>迁入</div>
        <div class="stat-vertical-sep"></div>
        <img class="stat-icon" src="../assets/add.svg"/>
        <div class="stat-num">{{ this.provinceInOut[0] }}</div>
      </div>
      <div class="stat-horizon-sep"></div>
      <div class="out-stat">
        <div class="out-stat stat">
          <div>迁出</div>
          <div class="stat-vertical-sep"></div>
          <img class="stat-icon" src="../assets/sub.svg"/>
          <div class="stat-num">{{ this.provinceInOut[1] }}</div>
        </div>
      </div>
    </div>

    <!--    <div class="province-stat" v-if="provinceSelected">-->
    <!--      {{ inOutDescription }}-->
    <!--    </div>-->
    <div class="description-group" :style="calcMaxHeightStyle" v-if="showInfoCard">
      <div class="description-item"
           v-for="(item, index) in routeDescription"
           :key="index"
      >
        <div
            class="route-description"
            @mouseenter="routeMouseEnterHandler(item.id)"
            @mouseleave="routeMouseLeaveHandler(item.id)"
        >
          <img src="../assets/expand.svg" class="route-detail--button" @click="showPersonList(item.id)" :style="`transform: ${personDetailVisible[item.id] ? 'rotate(180deg)' : ''}`"/>
          <div class="route-description--text" :class="{ 'route-hover': isHighLight(item.id) }">{{
              item.value
            }}人：{{ item.src }}等地 → {{ item.dst }}等地。
          </div>
        </div>
        <div class="description-item__detail" v-if="personDetailVisible[item.id]">
          <!--          <RecycleScroller-->
          <!--              class="description-item__detail__scrolllist"-->
          <!--              :items="item.detail"-->
          <!--              :item-size="itemHeight"-->
          <!--              key-field="personid"-->
          <!--              v-slot="{ item }"-->
          <!--          >-->
          <!--            <div class="description-item__detail__item">-->
          <!--              {{ item.name}}, {{ item }}-->
          <!--            </div>-->
          <!--          </RecycleScroller>-->
          <div class="description-item__detail__scrolllist">
            <div class="description-item__detail__item"
                 v-for="(cItem, index) in item.detail"
                 :key="index"
            >
              <span class="c-name">
                {{cItem.name }}
              </span>
              <span class="c-src_name">
                {{cItem.src_name }} ({{cItem.index_year }})
              </span>
              <span class="c-dst_name">
                {{cItem.dst_name }}
              </span>
            </div>
          </div>
        </div>
        <!--        <div class="description-detail" v-if="personDetailVisible[item.id]">-->
        <!--          <el-table style="color: #5a3a20; max-height: 20vh; overflow: auto" :data="item.detail">-->
        <!--            <el-table-column property="name" label="姓名"/>-->
        <!--            <el-table-column property="index_year" label="出生日期"/>-->
        <!--            <el-table-column property="src_name" label="户籍地"/>-->
        <!--            <el-table-column property="dst_name" label="最后记载的任官/居住所在地"/>-->
        <!--          </el-table>-->
        <!--        </div>-->
      </div>
    </div>

  </div>
</template>

<script>
import {mapState} from "vuex";
import * as Data from "@/data/Data";
import SemiBorderFrame from "@/components/SemiBorderFrame.vue";

export default {
  name: "InfoCard",
  components: {
    SemiBorderFrame,
  },
  data() {
    return {
      personDetailVisible: {},
      personDetailData: [],
    };
  },
  computed: {
    ...mapState([
      "yearRange",
      "provinceSelected",
      "provinceInOut",
      "arrows",
      "arrowHover",
      "showInfoCard"
    ]),
    expandIconTransform() {

    },
    itemHeight() {
      console.log(window.innerHeight / 100 * 2);
      return window.innerHeight / 100 * 2;
    },
    calcMaxHeightStyle() {
      if (this.provinceSelected) {
        return "height: 35vh;"
      } else {
        return "height: 44vh;"
      }
    },
    calcPaddingBottomStyle() {
      if (!this.showInfoCard) {
        return "padding-bottom: 2vh"
      } else return "";
    },
    provinceName() {
      return this.provinceSelected ? this.provinceSelected : "全国";
    },
    inOutDescription() {
      return `总计${this.provinceInOut[0]}人迁入，${this.provinceInOut[1]}人迁出`;
    },
    routeDescription() {
      return this.arrows.slice(0, 20).map((d) => {
        let src = d.counter[0]
            .slice(0, 2)
            .map((d) => d[0])
            .join("，");
        let dst = d.counter[1]
            .slice(0, 2)
            .map((d) => d[0])
            .join("，");
        let value = d.value;
        let id = d.id;
        return {src, dst, value, id, detail: d.personList};
      });
    },
  },
  methods: {
    isHighLight(id) {
      return id == this.arrowHover;
    },
    routeMouseEnterHandler(id) {
      this.$store.commit("setArrowHover", id);
    },
    routeMouseLeaveHandler(id) {
      this.$store.commit("resetArrowHover", id);
    },
    changeShowInfoCard() {
      this.$store.commit("revertShowInfoCard");
    },
    showPersonList(id) {
      this.personDetailVisible[id] = !this.personDetailVisible[id];
    }
  },
  mounted() {
    this.provinceData = Data.getProvinceGeoData().features;
  },
};
</script>

<style scoped lang="scss">
.container.infocard {
  font-family: FZQINGKBYSJF;
  color: #5a3a20;
  text-align: left;
  padding-left: 2vw;
  padding-top: 1vh;
  padding-right: 1vw;
  padding-bottom: 30vh;

  background: rgba(255, 255, 255, 0.5);

  .year-range {
    font-size: 2.5vh;

    span {
      font-size: 2.5vh;
    }
  }

  .sep {
    height: 8vh;
    min-width: 20vw;
  }

  .province {
    font-size: 3.5vh;
  }

  .province-stat {
    border: solid #5a3a20 0.1vh;
    padding: 0.5vh;
    margin-top: 1vh;
    font-size: 2.5vh;

    .stat-horizon-sep {
      height: 0vh;
      border-top: solid #5a3a20 0.1vh;
    }

    .stat {
      display: flex;
      align-items: center;
      padding: 0.2vh 1vh 0.2vh;

      .stat-vertical-sep {
        height: 2.2vh;
        margin-left: 2vh;
        border-right: solid #5a3a20 0.3vh;
      }

      .stat-icon {
        width: 3vh;
        margin-left: auto;
      }

      .stat-num {
        text-align: right;
        min-width: 6vh;
      }
    }

  }

  .description-group {
    margin-top: 0.2vh;
    overflow-y: auto;

    .description-item__detail {
      direction: rtl;
      font-size: 1.6vh;
      overflow: auto;
      height: 15vh;

      .description-item__detail__scrolllist {
        direction: ltr;
        display: grid;
        grid-template-columns: 20% 40% 40%;

        .description-item__detail__item {
          direction: ltr;
          padding: 0.2vh;
          display: contents;

          //margin: 0.2vh 0.7vh;
          .c-name {
            grid-column: 1;
            margin-left: 1vh;
            text-align: left;
          }
          .c-src_name {
            grid-column: 2;
            margin-left: 2vh;
            text-align: left;
          }
          .c-dst_name {
            grid-column: 3;
            margin-right: 1vh;
            margin-left: auto;
            text-align: right;
          }
        }
      }
    }
  }

  .route-description {
    //width: 45vh;
    cursor: pointer;
    padding: 0.2vh;
    margin-top: 1vh;
    font-size: 2vh;
    border: solid rgba(0, 0, 0, 0) 0.1vh;
    display: flex;

    .route-detail--button {
      vertical-align: middle;
      width: 2.2vh;
      padding-right: 1vh;
      display: inline-block;
      transform-origin: 30% center;
      transition: all 0.5s;

      &:hover {
        opacity: 0.5;
      }
    }


    route-description--text {
      display: inline-block;
    }
  }

  .route-hover {
    border: solid #5a3a20 0.1vh;
  }

  :deep(.el-dialog__body) {
    max-height: 50vh;
    overflow: auto;
  }
}
</style>
