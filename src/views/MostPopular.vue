<template>
    <div class="search-by-title">
        <h2>按类型查询最受欢迎的组合</h2>
        <div class="search-container">
            <input v-model="searchQuery" type="text" placeholder="请输入类型..." />
            <button @click="performSearch">搜索</button>
        </div>

        <!-- 展示查询时间对比 -->
        <div v-if="queryTimeMysql !== null || queryTimeNeo4j !== null" class="query-time-comparison">
            <p>MySQL 查询时间: {{ queryTimeMysql }} 秒</p>
            <p>Neo4j 查询时间: {{ queryTimeNeo4j }} 秒</p>
        </div>

        <div v-if="showDirectors && directors.length > 0" class="results-area">
            <h3>相关类型：</h3>
            <div class="director-cards">
                <div v-for="(director, index) in directors" :key="index" class="director-card"
                    @click="showActorCombinationsByGenre(director.genre_name)">
                    <h4>{{ director.genre_name }}</h4>
                </div>
            </div>
        </div>

        <div v-else-if="showDirectors && searchPerformed && !loading" class="no-results">
            <p>没有找到匹配的类型。</p>
        </div>

        <div v-if="loading" class="loading">
            <p>正在加载...</p>
        </div>

        <!-- 显示演员组合 -->
        <div v-if="!showDirectors && actorCombinations.length > 0" class="results-area">
            <h3>{{ currentGenre }} 类型最受欢迎的演员组合：</h3>
            <div class="actor-combination-cards">
                <div v-for="(combination, index) in actorCombinations" :key="index" class="actor-combination-card">
                    <h4>{{ combination.actor1_name }} 和 {{ combination.actor2_name }}</h4>
                    <p>合作次数: {{ combination.cooperation_count }}</p>
                    <p>评论数量: {{ combination.review_count }}</p>
                </div>
            </div>
            <div v-if="queryTime !== null" class="query-time">
                <p>查询时间: {{ queryTime }} 秒</p>
            </div>
            <div class="pagination-controls">
                <button :disabled="currentPage === 1" @click="prevPage">上一页</button>
                <span>第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
                <button :disabled="currentPage === totalPages" @click="nextPage">下一页</button>
            </div>
            <button @click="backToDirectors">返回</button>
        </div>

        <div v-else-if="!showDirectors && searchPerformed && !loading && actorCombinations.length === 0"
            class="no-results">
            <p>该类型没有演员组合记录。</p>
            <button @click="backToDirectors">返回</button>
        </div>
    </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { ElMessage } from 'element-plus'; // 如果你使用的是 Element Plus 消息框

const searchQuery = ref('');
const directors = ref([]);
const loading = ref(false);
const searchPerformed = ref(false);
const queryTime = ref(null);
const showDirectors = ref(true);  // 控制显示导演还是演员组合
const allActorCombinations = ref([]); // 存储所有获取到的演员组合数据
const actorCombinations = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value;
    const end = start + pageSize.value;
    return allActorCombinations.value.slice(start, end);
});
const currentGenre = ref(null);
const queryTimeMysql = ref(null); // 新增的 MySQL 查询时间
const queryTimeNeo4j = ref(null); // 新增的 Neo4j 查询时间

// 分页控制
const currentPage = ref(1);
const pageSize = ref(30);
const totalPages = computed(() => Math.ceil(allActorCombinations.value.length / pageSize.value));

// 执行搜索的方法
const performSearch = () => {
    performSearchmysql();
};

const performSearchmysql = () => {
    loading.value = true;
    searchPerformed.value = true;
    showDirectors.value = true;

    // 构建 API 请求 URL
    const apiUrl = `http://47.97.59.189:5000/search_every_genre/${searchQuery.value}`;

    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            directors.value = data.results;  // 获取查询结果
            queryTimeMysql.value = data.query_time;   // 获取查询时间
            loading.value = false;
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            loading.value = false;
        });
};

// 显示演员组合
const showActorCombinationsByGenre = (genreName) => {
    loading.value = true;
    currentGenre.value = genreName;
    const apiUrl = `http://47.97.59.189:5000/search_actor_combinations_by_genre/${(genreName)}`;

    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            allActorCombinations.value = data.results;  // 获取所有查询结果
            queryTime.value = data.query_time;   // 获取查询时间
            currentPage.value = 1; // 切换到第一页
            loading.value = false;
            showDirectors.value = false;  // 切换到显示演员组合
        })
        .catch(error => {
            console.error('Error fetching actor combinations by genre:', error);
            ElMessage({
                message: '获取演员组合失败，请稍后再试。',
                type: 'error'
            });
            loading.value = false;
        });
};

// 返回到类型列表
const backToDirectors = () => {
    showDirectors.value = true;
    allActorCombinations.value = [];
    currentGenre.value = null;
    currentPage.value = 1;
};

// 翻页操作
const prevPage = () => {
    if (currentPage.value > 1) {
        currentPage.value--;
    }
};
const nextPage = () => {
    if (currentPage.value < totalPages.value) {
        currentPage.value++;
    }
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

.chart-area,
.results-area,
.no-results,
.loading,
.query-time,
.back-button,
.pagination-controls {
    margin-top: 20px;
}

.director-cards,
.actor-combination-cards {
    display: flex;
    flex-wrap: wrap;
}

.director-card,
.actor-combination-card {
    border: 1px solid #ccc;
    padding: 10px;
    margin: 10px;
    cursor: pointer;
    width: 200px;
}

.pagination-controls {
    text-align: center;
}

.pagination-controls button {
    margin: 0 5px;
}

.back-button button {
    display: block;
    margin: 0 auto;
    width: 100px;
}
</style>