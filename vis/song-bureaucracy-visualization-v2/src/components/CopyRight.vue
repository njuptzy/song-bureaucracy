<template>
  <div class="container copyright">
    <SemiBorderFrame header-padding="0.5vh">
      <template v-slot:header>
        <div class="head-title">项目信息</div>
      </template>
      <div class="content">
        <div class="author text">作者：罗煜楚 李晨 李明宣 袁晓如</div>
        <div class="text">北京大学可视化与可视分析实验室</div>
        <div class="sep"></div>
        <div class="text">
          <b>数据来源：</b>
          <a href="https://projects.iq.harvard.edu/cbdb/home" target="_blank" rel="noopener noreferrer">
            <img src="../assets/link.svg" class="link-icon"/>
            <span>&nbsp;中国历代人物传记资料库(CBDB)</span>
          </a>

        </div>
        <div class="sep"></div>
        <div class="text">*当前版本暂使用现在的中国地图</div>

      </div>
    </SemiBorderFrame>
  </div>
</template>

<script>
import SemiBorderFrame from "@/components/SemiBorderFrame.vue";
export default {
  name: "CopyRight.vue",
  components: { SemiBorderFrame },
};
</script>

<style scoped lang="scss">
.container.copyright {
  font-family: FZQINGKBYSJF;
  color: #5a3a20;
  text-align: left;
  padding: 1.2vh 2vw 2vh 1vw;
  font-size: 1.3vh;
  background: rgba(255, 255, 255, 0.5);
  .link-icon {
    width: 1.5vh;
    vertical-align: middle;
  }
  .head-title {
    font-size: 2vh;
  }
  .content {
    margin-top: 1.5vh;
    padding: 0.7vh;
  }
  .author {
    font-size: 1.5vh;
  }
  .sep {
    height: 0px;
    border-bottom: solid #ac9176 2px;
    margin: 1vh;
  }
  .text {
    padding: 0.5vh;
  }
}
</style>
