<template>
    <div class="search-by-title">
        <h2>按类型查询最受欢迎的组合</h2>
        <div class="search-container">
            <input v-model="searchQuery" type="text" placeholder="请输入想查询的类型名称..." @keyup.enter="performSearch" />
            <button @click="performSearch">搜索</button>
        </div>
        <!-- 展示查询时间对比 -->
        <div v-if="showDiagram" class="query-time-comparison">
            <div class="chart-area">
                <canvas id="queryTimeChart"></canvas> <!-- 图表 -->
            </div>
            <div class="text-area">
                <p><strong>MySQL 查询时间: </strong>{{ queryTimeMysql }} 秒</p>
                <p><strong>Neo4j 查询时间: </strong>{{ queryTimeNeo4j }} 秒</p>
                <p><strong>Hive 查询时间: </strong>{{ queryTimeHive }} 秒</p>
            </div>
        </div>

        <div v-if="loading" class="loading">
            <p>正在加载...</p>
        </div>

        <!-- 按钮区域，选择不同的组合查询方式 -->
        <div class="query-buttons" v-if="searchPerformed && showDiagram &&hasResult">
            <button @click="selectedQuery = 'mysql'" :class="{ 'active': selectedQuery === 'mysql' }">显示MySQL
                查询结果</button>
            <button @click="selectedQuery = 'neo4j'" :class="{ 'active': selectedQuery === 'neo4j' }">显示Neo4j
                查询结果</button>
            <button @click="selectedQuery = 'hive'" :class="{ 'active': selectedQuery === 'hive' }">显示Hive 查询结果</button>
        </div>

        <div v-else-if="searchPerformed && !hasResult" class="no-results">
            <p>没有找到匹配的结果。</p>
        </div>

        <!-- 根据选中的查询方式展示不同的导演结果 -->
        <div class="results-area" v-if="!showDiagram && hasResult && !loading">
            <h3>搜索类型结果 (共{{ genreResults.length }}条相关记录)</h3>
            <div class="movie-cards">
                <div v-for="(result, index) in genreResults" :key="index" class="movie-card"
                    @click="searchGroupsByGenre(result.genre_name)">
                    <h4>{{ result.genre_name }}</h4>
                </div>
            </div>
        </div>

        <!-- 根据选中的查询方式展示不同的电影结果 -->
        <div class="results-area" v-if="showDiagram && selectedQuery && getSearchResults.length > 0">
            <h3> 使用{{ selectedQuery }}搜索{{ currentGenre }} <br>最受欢迎的演员组合结果：{{ getSearchResults.length }}条</h3>
            <div class="movie-cards">
                <div v-for="(result, index) in getSearchResultsByPage" :key="index" class="movie-card">
                    <h4>{{ result.actor1_name }} 和 {{ result.actor2_name }}</h4>
                    <p>合作次数: {{ result.cooperation_count }}</p>
                    <p>评论数量: {{ result.review_count }}</p>
                </div>
            </div>
            <div class="pagination-controls">
                <button :disabled="currentPage === 1" @click="prevPage">上一页</button>
                <span>第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
                <button :disabled="currentPage === totalPages" @click="nextPage">下一页</button>
            </div>
        </div>

        <button v-if="showDiagram" @click="backToGenres" class="back-button">返回</button>

    </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { computed, watch } from 'vue'
import Chart from 'chart.js/auto'; // 导入 Chart.js
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus'; // Element Plus 消息框

const router = useRouter();
const searchQuery = ref('');

const genreResults = ref([]);

const selectedQuery = ref('')

const mysqlSearchResults = ref([]);
const neo4jSearchResults = ref([]);
const hiveSearchResults = ref([]);

const queryTimeMysql = ref(0); // 新增的 MySQL 查询时间
const queryTimeNeo4j = ref(0); // 新增的 Neo4j 查询时间
const queryTimeHive = ref(0); // 新增加的Hive查询时间

const showDiagram = ref(false);
const loading = ref(false);
const searchPerformed = ref(false);

let chart = null; // Chart.js 图表实例
const hasResult = ref(false);
const currentGenre = ref('');//当前展示类型

// 分页控制
const currentPage = ref(1);
const pageSize = ref(30);
const totalPages = computed(() => Math.ceil(getSearchResults.value.length / pageSize.value));
const getSearchResultsByPage = computed(() => {
    const start = (currentPage.value - 1) * pageSize.value;
    const end = start + pageSize.value;
    return getSearchResults.value.slice(start, end);
});


// 监听 showDiagram 变化，准备渲染图表
watch(showDiagram, (newVal) => {
    if (newVal) {
        setTimeout(() => {
            renderChart();
        }, 0); // 确保 DOM 已更新再初始化图表
    } else if (chart) {
        chart.destroy(); // 如果 showDiagram 为 false，销毁现有图表
        chart = null;
    }
});

// 初始化图表的函数
const renderChart = () => {
    const ctx = document.getElementById('queryTimeChart').getContext('2d');

    chart = new Chart(ctx, {
        type: 'bar', // 图表类型：柱状图
        data: {
            labels: ['MySQL', 'Neo4j', 'Hive'], // 横轴标签
            datasets: [{
                label: '查询时间 (秒)',
                data: [queryTimeMysql.value, queryTimeNeo4j.value, queryTimeHive.value], // 数据
                backgroundColor: ['#42A5F5', '#66BB6A', '#FF7043'], // 柱状图颜色
                borderColor: ['#1E88E5', '#388E3C', '#D32F2F'], // 边框颜色
                borderWidth: 1 // 边框宽度
            }]
        },
        options: {
            responsive: true, // 自适应大小
            scales: {
                y: {
                    beginAtZero: true, // Y轴从0开始
                    ticks: {
                        stepSize: 0.5 // 刻度步长
                    }
                }
            }
        }
    });
};

// 动态更新图表数据
watch([queryTimeMysql, queryTimeNeo4j, queryTimeHive], () => {
    if (chart) {
        chart.data.datasets[0].data = [
            queryTimeMysql.value,
            queryTimeNeo4j.value,
            queryTimeHive.value
        ];
        chart.update(); // 更新图表
    }
});

// 搜索类型（仅使用MYSQL）
const performSearch = () => {
    showDiagram.value = false;
    searchPerformed.value = false;//和loading作用是不一样的，初值一样，后面全反。
    loading.value = true;
    hasResult.value = false;
    performSearchmysql();
}

const performSearchmysql = () => {
    // 构建 API 请求 URL
    const apiUrl1 = `http://47.97.59.189:5000/search_every_genre/${searchQuery.value}`;

    fetch(apiUrl1)
        .then(response => response.json())
        .then(data => {
            genreResults.value = data.results;  // 获取查询结果
            searchPerformed.value = true;
            loading.value = false;
            // 检查结果是否有值并更新 hasResult
            if (data.results && data.results.length > 0) {
                hasResult.value = true;
            }
        })
        .catch(error => {
            searchPerformed.value = true;
            loading.value = false;
            console.error('Error fetching data:', error);
        });
};

// 获取组合搜索结果的计算属性
const getSearchResults = computed(() => {
    if (selectedQuery.value === 'mysql') {
        return mysqlSearchResults.value;
    } else if (selectedQuery.value === 'neo4j') {
        return neo4jSearchResults.value;
    } else if (selectedQuery.value === 'hive') {
        return hiveSearchResults.value;
    }
    return [];
});

// 搜索类型下的组合
const searchGroupsByGenre = (genreName) => {
    showDiagram.value = true;
    queryTimeMysql.value = 0;
    queryTimeNeo4j.value = 0;
    queryTimeHive.value = 0;
    selectedQuery.value = '';
    searchPerformed.value = false;
    loading.value = true;
    hasResult.value = false;
    currentPage.value = 1; // 切换到第一页
    currentGenre.value = genreName;
    SqlSearchGroups(genreName);
    Neo4jSearchGroups(genreName);
    HiveSearchGroups(genreName);
}

// MYSQL
const SqlSearchGroups = (genreName) => {
    const apiUrl = `http://47.97.59.189:5000/search_actor_combinations_by_genre/${(genreName)}`;
    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            mysqlSearchResults.value = data.results;  // 获取所有查询结果
            queryTimeMysql.value = data.query_time;   // 获取查询时间
            // 检查结果是否有值并更新 hasResult
            if (data.results && data.results.length > 0) {
                hasResult.value = true;
            }
        })
        .catch(error => {
            console.error('Error fetching actor combinations by genre:', error);
            ElMessage({
                message: '获取演员组合失败，请稍后再试。',
                type: 'error'
            });
        });
};

// 改成正确的URL！！！！！！！！！！！！！！！！！
const Neo4jSearchGroups = (genreName) => {
    const apiUrl1 = `http://47.97.59.189:5000/search_actor_combinations_by_genre/${(genreName)}`;
    fetch(apiUrl1)
        .then(response => response.json())
        .then(data => {
            neo4jSearchResults.value = data.results;  // 获取所有查询结果
            queryTimeNeo4j.value = data.query_time;   // 获取查询时间
            // 检查结果是否有值并更新 hasResult
            if (data.results && data.results.length > 0) {
                hasResult.value = true;
            }
        })
        .catch(error => {
            console.error('Error fetching actor combinations by genre:', error);
            ElMessage({
                message: '获取演员组合失败，请稍后再试。',
                type: 'error'
            });
        });
};

// 改成正确URL！！！！！！！！！
const HiveSearchGroups = (genreName) => {
    const apiUrl2 = `http://127.0.0.1:5000/search_actor_combinations_by_genre_hive/${(genreName)}`;
    fetch(apiUrl2)
        .then(response => response.json())
        .then(data => {
            hiveSearchResults.value = data.results;  // 获取所有查询结果
            queryTimeHive.value = data.query_time;   // 获取查询时间
            loading.value = false;
            searchPerformed.value = true;
            // 检查结果是否有值并更新 hasResult
            if (data.results && data.results.length > 0) {
                hasResult.value = true;
            }
        })
        .catch(error => {
            console.error('Error fetching actor combinations by genre:', error);
            loading.value = false;
            searchPerformed.value = true;
            ElMessage({
                message: '获取演员组合失败，请稍后再试。',
                type: 'error'
            });
        });
};

// 返回到类型
const backToGenres = () => {
    showDiagram.value = false;
    hasResult.value=true;
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
/* 让图表容器有适当的大小 */
.query-time-comparison {
    display: flex;
    margin: 0 auto;
    /* 水平居中 */
    justify-content: center;
    /*水平方向对齐子元素*/
    align-items: center;
    /*垂直方向对齐子元素*/
    width: 100%;
    height: 30vh;
    /* 使用视口高度 */
    overflow: hidden;
    /* 溢出部分隐藏 */
}

.chart-area {
    flex: 8;
    /* 左侧占比 70% */
    display: flex;
    justify-content: flex-end;
    /* 内容偏右对齐 */
    align-items: center;
    /* 垂直居中 */
    padding-right: 10px;
    /* 给图表一点右侧间距 */
    margin-top: 0;
    /* 确保没有外边距 */
    padding-top: 0;
    /* 确保没有内边距 */
}

.text-area {
    flex: 2;
    /* 右侧占比 30% */
    display: flex;
    flex-direction: column;
    /* 按列布局 */
    justify-content: space-evenly;
    /* 三行文字均匀分布 */
    align-items: flex-start;
    /* 向左对齐文字 */
    padding-left: 10px;
    /* 给文字一点左侧间距 */
}

.text-area p {
    margin: 0;
    /* 去除段落的默认外边距 */
    font-size: 13px;
    /* 文字大小根据需要调整 */
}

canvas {
    width: 50%;
    /* 图表宽度调整以适应容器 */
    height: 50%;
    /* 图表高度保持适中 */
    max-width: 100%;
    /* 最大宽度不能超过父级 */
    max-height: 100%;
    /* 最大高度不能超过父级 */
    object-fit: contain;
    /* 保证内容适配 */
}


.query-buttons {
    width: 50%;
    /* 占父级容器宽度的 50% */
    margin: 2px auto 0;
    display: flex;
    /* 使用 Flexbox 布局 */
    justify-content: space-around;
    /* 按钮之间均匀分布并留有间隔 */
    align-items: center;
    /* 垂直居中对齐 */
}

.query-buttons button {
    cursor: pointer;
    /* 鼠标悬停时显示手型 */
}

/* 设置每个电影详情项 */
.dialog-item {
    padding-left: 20px;
    /* 左边距 */
    text-align: left;
    /* 确保内容左对齐 */
    margin-bottom: 10px;
    /* 每项之间的间隔 */
}

/* 确保每一行文本都在左边显示 */
.dialog-item div {
    margin-bottom: 5px;
    /* 每行之间的间隔 */
}


.search-by-title {
    padding: 20px;
}

.search-container {
    margin-bottom: 0px;
}

.search-container input {
    width: 200px;
    height: 30px;
    margin-right: 10px;
}

.search-container button {
    height: 32px;
}

.results-area,
.no-results,
.loading,
.query-time,
.pagination-controls {
    margin-top: 10px;
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

.back-button {
    display: block;
    /* width: 100px; */
    cursor: pointer;
    /* padding: 10px 20px; */
    margin:10px auto;
    /* 内边距，控制大小 */
}

.pagination-controls button {
    margin: auto 10px;
}
</style>