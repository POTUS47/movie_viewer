<template>
  <!-- <nav>
    <router-link to="/">Home</router-link> |
    <router-link to="/about">About</router-link>
  </nav> -->
  <el-button v-if="router.currentRoute.value.path !== '/'" @click="goBack" class="sysbtn" style="position: absolute; top: 10px; left: 10px; z-index: 50;">
    <el-icon>
      <Back />
    </el-icon>
  </el-button>
  <div style="position: absolute; top: 0; left: 0; width: 100vw; height: 100vh; overflow-x: hidden;">
    <router-view />
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router';
import { Back } from '@element-plus/icons-vue'
const router = useRouter();
// 返回上一页的方法
const goBack = () => {
  console.log(router.currentRoute)
  router.go(-1);  // 返回上一页
};
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

nav {
  padding: 30px;
}

nav a {
  font-weight: bold;
  color: #2c3e50;
}

nav a.router-link-exact-active {
  color: #42b983;
}

.results-area {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.movie-cards {
  justify-content: center
}

.el-button.sysbtn {
  border: 2px solid rgba(0, 128, 128, 0.226);
  border-radius: 6px;
  color: black;
  transition: 0.2s all;
}

.el-button.sysbtn:hover {
  border: 2px solid teal;
  background-color: #cbe0d76b;
  color: black;
  transform: scale(1.05);
}
</style>
