<template>
  <div class="search-by-title">
    <h2>按电影名称查询</h2>
    <div class="search-container">
      <input v-model="searchQuery" type="text" placeholder="请输入电影名称..." />
      <button @click="performSearch">搜索</button>
    </div>
    <!-- 展示查询时间对比 -->
    <div v-if="queryTimeMysql !== null || queryTimeNeo4j !== null" class="query-time-comparison">
      <p>MySQL 查询时间: {{ queryTimeMysql }} 秒</p>
      <p>Neo4j 查询时间: {{ queryTimeNeo4j }} 秒</p>
    </div>

    <div class="results-area" v-if="searchResults.length > 0">
      <h3>搜索结果：</h3>
      <div class="movie-cards">
        <div v-for="(result, index) in searchResults" :key="index" class="movie-card" @click="showMovieVersions(result.movie_id)">
          <h4>{{ result.movie_name }}</h4>
          <p>电影时长: {{ result.movie_runtime }}</p>
          <p>版本: {{ result.version }}</p>
        </div>
      </div>
    </div>
    <div v-else-if="searchPerformed && !loading" class="no-results">
      <p>没有找到匹配的结果。</p>
    </div>
    <div v-if="loading" class="loading">
      <p>正在加载...</p>
    </div>
    <div v-if="queryTime !== null" class="query-time">
      <p>查询时间: {{ queryTime }} 秒</p>
    </div>

    <!-- Dialog for displaying movie versions -->
    <el-dialog
    v-model="centerDialogVisible"
    title="版本信息"
    width="800"
    align-center
  >
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
        <el-button type="primary" @click="centerDialogVisible = false">
          关闭
        </el-button>
      </div>
    </template>
  </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus'; // 如果你使用的是 Element Plus 消息框

const router = useRouter();
const searchQuery = ref('');
const searchResults = ref([]);
const loading = ref(false);
const searchPerformed = ref(false);
const queryTime = ref(null);
const centerDialogVisible = ref(false)
const selectedMovieVersions = ref(null);
const queryTimeMysql = ref(null); // 新增的 MySQL 查询时间
const queryTimeNeo4j = ref(null); // 新增的 Neo4j 查询时间


const performSearch = () => {
  performSearchmysql();
  performSearchneo();  
}
// 执行搜索的方法
const performSearchmysql = () => {
  loading.value = true;
  searchPerformed.value = true;

  // 构建 API 请求 URL
  const apiUrl1 = `http://47.97.59.189:5000/search_by_title/${searchQuery.value}`;

  fetch(apiUrl1)
    .then(response => response.json())
    .then(data => {
      searchResults.value = data.results;  // 获取查询结果
      queryTimeMysql.value = data.query_time;   // 获取查询时间
      loading.value = false;
    })
    .catch(error => {
      console.error('Error fetching data:', error);
      loading.value = false;
    });
};

const performSearchneo = () => {
  loading.value = true;
  searchPerformed.value = true;

  // 构建 API 请求 URL
  const apiUrl = `http://47.97.59.189:5000/search_by_title_neo4j/${searchQuery.value}`;

  fetch(apiUrl)
    .then(response => response.json())
    .then(data => {
      // searchResults.value = data.results;  // 获取查询结果
      queryTimeNeo4j.value = data.query_time;   // 获取查询时间
      //loading.value = false;
    })
    .catch(error => {
      console.error('Error fetching data:', error);
      loading.value = false;
    });
};

// 返回上一页的方法
const goBack = () => {
  router.go(-1);  // 返回上一页
};

// 显示电影版本信息的方法
const showMovieVersions = (movieId) => {
  fetchAndShowMovieVersions(movieId);
};

// 获取并显示电影版本信息的方法
const fetchAndShowMovieVersions = (movieId) => {
  const apiUrl = `http://47.97.59.189:5000/movie_versions/${movieId}`;
  
  fetch(apiUrl)
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      return response.json();
    })
    .then(data => {
      console.log('Fetched movie versions:', data);  // 调试信息
      selectedMovieVersions.value = data;
      centerDialogVisible.value = true;
    })
    .catch(error => {
      console.error('Error fetching movie versions:', error);
      ElMessage({
        message: '获取电影版本信息失败，请稍后再试。',
        type: 'error'
      });
    });
};


</script>

<style scoped>
.search-by-title {
  padding: 20px;
}

.search-container {
  margin-bottom: 20px;
}

.search-container input {
  width: 200px;
  height: 30px;
  margin-right: 10px;
}

.search-container button {
  height: 32px;
}

.chart-area, .results-area, .no-results, .loading, .query-time, .back-button {
  margin-top: 20px;
}

.movie-cards {
  display: flex;
  flex-wrap: wrap;
}

.movie-card {
  border: 1px solid #ccc;
  padding: 10px;
  margin: 10px;
  cursor: pointer;
  width: 200px;
}

.back-button button {
  display: block;
  margin: 0 auto;
  width: 100px;
}
</style>