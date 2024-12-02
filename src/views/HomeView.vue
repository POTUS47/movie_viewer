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
  <div class="home">
    <img alt="Vue logo" src="../assets/logo.png">
    <HelloWorld msg="Welcome to Your Vue.js App" />
    <button @click="jump_test">jump test</button>
    <button @click="minimize_win">aa</button>
  </div>
</template>

<script>
// @ is an alias to /src
import HelloWorld from '@/components/HelloWorld.vue'

export default {
  name: 'HomeView',
  components: {
    HelloWorld
  }
}
</script>
