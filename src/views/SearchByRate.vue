<template>
    <div class="movie-search-by-rating">
        <h2>根据评分筛选电影</h2>

        <!-- 评分区间选择 -->
        <div class="rating-selection">
            <label for="min-rating">最低评分:</label>
            <input id="min-rating" v-model.number="minRating" type="number" min="0" max="5" step="0.1" />

            <label for="max-rating">最高评分:</label>
            <input id="max-rating" v-model.number="maxRating" type="number" min="0" max="5" step="0.1" />

            <button @click="performSearch">搜索</button>
        </div>

        <!-- 搜索结果 -->
        <div v-if="loading" class="loading">
            <p>正在加载...</p>
        </div>

        <div v-else-if="searchResults.length > 0" class="search-results">
            <h3>找到 {{ searchResults.length }} 部电影：</h3>
            <ul>
                <li v-for="(movie, index) in searchResults" :key="index">
                    <strong>{{ movie.movie_name }}</strong> - 评分: {{ movie.rate }}
                </li>
            </ul>
        </div>

        <div v-else-if="searchPerformed && !loading" class="no-results">
            <p>没有找到匹配的电影。</p>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus'; // 如果你使用的是 Element Plus 消息框

const minRating = ref(0); // 最低评分
const maxRating = ref(10); // 最高评分
const loading = ref(false); // 加载状态
const searchResults = ref([]); // 搜索结果
const searchPerformed = ref(false); // 是否已经执行过搜索

// 执行搜索的方法
const performSearch = () => {
    if (minRating.value > maxRating.value) {
        ElMessage({
            message: '最低评分不能高于最高评分。',
            type: 'warning'
        });
        return;
    }

    loading.value = true;
    searchPerformed.value = true;

    let apiUrl = new URL(`http://47.97.59.189:5000/search_by_rate`);

    // 构建查询参数
    const params = new URLSearchParams({
        min_rating: minRating.value.toString(),
        max_rating: maxRating.value.toString()
    });

    apiUrl.search = params.toString();

    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            searchResults.value = data.results; // 获取查询结果
            loading.value = false;
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            ElMessage({
                message: '查询失败，请稍后再试。',
                type: 'error'
            });
            loading.value = false;
        });
};
</script>

<style scoped>
.movie-search-by-rating {
    padding: 20px;
}

.rating-selection {
    margin-bottom: 20px;
}

.rating-selection label,
.rating-selection input {
    display: inline-block;
    margin-right: 10px;
}

.rating-selection button {
    margin-left: 20px;
}

.search-results ul {
    list-style-type: none;
    padding: 0;
}

.search-results li {
    margin: 5px 0;
}
</style>