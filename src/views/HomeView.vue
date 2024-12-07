<script setup>
import { useRouter } from 'vue-router'
import { ipcRenderer } from 'electron';
const router = useRouter()
function jump_test() {
  router.push('/test')
}
function minimize_win() {
  ipcRenderer.send("minWin")
}
</script>

<template>
  <!-- <div class="home">
    <img alt="Vue logo" src="../assets/logo.png">
    <HelloWorld msg="Welcome to Your Movie Searcher" />
    <button @click="jump_test">jump test</button>
    <button @click="minimize_win">aa</button>
  </div> -->
  <div class="home">
    <h1>电影查询</h1>
    <div class="options">
      <button @click="navigateTo('/search-by-title')">按电影名称查询</button>
      <button @click="navigateTo('/search-by-actor')">按演员名称查询</button>
      <button @click="navigateTo('/search-by-director')">按导演名称查询</button>
      <button @click="navigateTo('/search-by-time')">按时间查询</button>
      <!-- 更多选项可在此处添加 -->
    </div>
  </div>
</template>

<script>
// @ is an alias to /src
// import HelloWorld from '@/components/HelloWorld.vue'

// export default {
//   name: 'HomeView',
//   components: {
//     HelloWorld
//   }
// }
export default {
  name: 'Home',
  methods: {
    navigateTo(path) {
      this.$router.push(path);
    }
  }
}
</script>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
}

.options button {
  margin: 10px;
  padding: 10px 20px;
  font-size: 16px;
  cursor: pointer;
}
</style>