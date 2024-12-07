<template>
  <el-button plain @click="fetchAndShowMovieVersions('0740312677')">
    这是一个电影
  </el-button>

  <el-dialog
    v-model="centerDialogVisible"
    title="版本信息"
    width="800"
    align-center
  >
    <span>Open the dialog from the center from the screen</span>
    <ul>
        <li v-for="(version, index) in selectedMovieVersions.original_movies" :key="index">
          <strong>电影名称:</strong> {{ version.movie_name }}<br>
          <strong>导演:</strong> {{ version.movie_director }}<br>
          <strong>演员:</strong> {{ version.movie_actor }}<br>
          <strong>时长:</strong> {{ version.duration_in_minutes }}<br>
          <strong>上映日期:</strong> {{ version.release_date }}<br>
        </li>
      </ul>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="centerDialogVisible = false">Cancel</el-button>
        <el-button type="primary" @click="centerDialogVisible = false">
          Confirm
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>
<script setup>
import { ref } from 'vue'

const centerDialogVisible = ref(false)
const selectedMovieVersions = ref(null);

const fetchAndShowMovieVersions = (movieId) => {
  const apiUrl = `http://47.97.59.189:5000/movie-versions/${movieId}`;
  
  fetch(apiUrl)
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      console.log('Fetched movie versions:', data);  // 调试信息
      centerDialogVisible.value = true;
      selectedMovieVersions.value = data;
      console.log(centerDialogVisible.value);
    })
    .catch(error => {
      console.error('Error fetching movie versions:', error);
    });
};
</script>