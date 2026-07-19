<template>
  <div class="container backgrounded" >
    <img class='lab-logo' src="../assets/logo.svg"/>
    <div class="main-title">中国古代名人迁居地图</div>
    <el-checkbox-group v-model="componentSwitch" class="component-control">
      <el-checkbox v-for="[key, item] in componentList" :label="item.name"/>
    </el-checkbox-group>
    <div class="bottom-line"></div>
  </div>
</template>

<script>

import {mapState} from "vuex";

export default {
  name: "ViewHeader",
  data() {
    return {
      checkList: [],
    }
  },
  computed: {
    ...mapState(["componentsState"]),
    componentSwitch: {
      get() {
        let checkList = [];
        for (let i in this.componentsState) {
          if (this.componentsState[i].enable) {
            checkList.push(this.componentsState[i].name);
          }
        }
        return checkList;
      },
      set(val) {
        console.log(val);
        this.$store.commit("setComponentsState", val);
      }
    },
    componentList() {
      return Object.entries(this.componentsState);
    }
  },
  methods: {

  }
}
</script>

<style scoped lang="scss">
.container {
  color: #724a2b;
  display: flex;
  align-items: center;
  position: relative;


  .lab-logo {
    margin-left: 2vw;
    display: inline-block;
    width: 4vw;
  }

  .main-title {
    font-size: 4vh;
    margin-left: 1vh;
    font-family: FZQINGKBYSJF;
  }

  .component-control {
    display: flex;
    margin-right: 4vh;
    margin-left: auto;

    :deep(.el-checkbox) {
      --el-checkbox-checked-icon-color: #724a2b !important;
    }

    :deep(.el-checkbox__label) {
      vertical-align: middle;
      color: #724a2b;
      font-size: 2vh;
      font-family: FZQINGKBYSJF;
      line-height: 2.2vh;
    }

    :deep(.el-checkbox__inner) {
      height: 2vh;
      width: 2vh;
    }

    :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
      background-color: #724a2b;

    }
  }

  .bottom-line {
    position: absolute;
    bottom: 0vh;
    height: 0vh;
    left: 1.8vw;
    right: 1.8vw;
    border-bottom: 0.3vh solid #724a2b;
  }

}


</style>
