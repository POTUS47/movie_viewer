<!--  必须返回查询时间 -->
<template>
    <div class="search-by-title">
        <h2>按评分查询</h2>

        <!-- 评分区间选择 -->
        <div class="rating-selection">
            <label for="min-rating">最低评分:</label>
            <input id="min-rating" v-model.number="minRating" type="number" min="0" max="5" step="0.1" />

            <label for="max-rating">最高评分:</label>
            <input id="max-rating" v-model.number="maxRating" type="number" min="0" max="5" step="0.1" />

            <button @click="performSearch">搜索</button>
        </div>

        <!-- 展示查询时间对比 -->
        <div v-if="processRunning" class="query-time-comparison">
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

        <!-- 按钮区域，选择不同的查询方式 -->
        <div class="query-buttons" v-if="searchPerformed">
            <button @click="selectedQuery = 'mysql'" :class="{ 'active': selectedQuery === 'mysql' }"> 显示MySQL
                查询结果</button>
            <button @click="selectedQuery = 'neo4j'" :class="{ 'active': selectedQuery === 'neo4j' }">显示Neo4j
                查询结果</button>
            <button @click="selectedQuery = 'hive'" :class="{ 'active': selectedQuery === 'hive' }">显示Hive 查询结果</button>
        </div>

        <div v-if="loadingResult" class="resultLoading">
            <p>正在加载结果...</p>
        </div>

        <!-- 根据选中的查询方式展示不同的结果 -->
        <div class="results-area" v-if="selectedQuery && getSearchResults.length > 0">
            <h3>使用{{ selectedQuery }}搜索结果：{{ getSearchResults.length }} 条</h3>
            <div class="movie-cards">
                <div v-for="(result, index) in getSearchResults" :key="index" class="movie-card"
                    @click="showMovieVersions(result.movie_id)">
                    <h4>{{ result.movie_name }}</h4>
                    <p>电影评分: {{ result.rate }}</p>
                </div>
            </div>
        </div>
        <div v-else-if="searchPerformed && !hasResult" class="no-results">
            <p>没有找到匹配的结果。</p>
        </div>

        <el-dialog v-model="centerDialogVisible" title="版本信息" width="800">
            <div v-for="(version, index) in selectedMovieVersions.original_movies" :key="index" class="dialog-item">
                <div><strong>相关电影信息{{ index + 1 }}:</strong> </div>
                <div><strong>电影名称: </strong> {{ version.movie_name }}</div>
                <div><strong>导演: </strong> {{ version.movie_director }}</div>
                <div><strong>演员: </strong> {{ version.movie_actor }}</div>
                <div><strong>时长（分钟）: </strong> {{ version.duration_in_minutes }}</div>
                <div><strong>上映日期: </strong> {{ version.release_date }}</div>
                <div v-if="selectedMovieVersions.original_movies.length - index - 1 > 0">
                    -----------------------------------------------</div>
            </div>
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
import { computed, watch } from 'vue'
import Chart from 'chart.js/auto'; // 导入 Chart.js
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus'; // Element Plus 消息框

const router = useRouter();
const searchQuery = ref('');

const mysqlSearchResults = ref([]);//搜索结果拆成三个
const neo4jSearchResults = ref([]);
const hiveSearchResults = ref([]);
const processRunning = ref(false);
const loading = ref(false);
const loadingResult = ref(false);
const searchPerformed = ref(false);

const centerDialogVisible = ref(false);
const selectedMovieVersions = ref(null);
const queryTimeMysql = ref(0); // 新增的 MySQL 查询时间
const queryTimeNeo4j = ref(0); // 新增的 Neo4j 查询时间
const queryTimeHive = ref(0); // 新增加的Hive查询时间
const selectedQuery = ref('')// 新增的结果查看方式
let chart = null; // Chart.js 图表实例
const hasResult = ref(false);

const minRating = ref(0); // 最低评分
const maxRating = ref(5); // 最高评分

// 监听 processRunning 变化，准备渲染图表
watch(processRunning, (newVal) => {
    if (newVal) {
        setTimeout(() => {
            renderChart();
        }, 0); // 确保 DOM 已更新再初始化图表
    } else if (chart) {
        chart.destroy(); // 如果 processRunning 为 false，销毁现有图表
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

// 获取搜索结果的计算属性
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

const performSearch = () => {
    if (minRating.value > maxRating.value) {
        ElMessage({
            message: '最低评分不能高于最高评分。',
            type: 'warning'
        });
        return;
    }
    processRunning.value = true;//搜索一次后全为true
    searchPerformed.value = false;//和loading作用是不一样的，初值一样，后面全反。
    loading.value = true;
    selectedQuery.value = '';
    queryTimeMysql.value = 0;
    queryTimeNeo4j.value = 0;
    queryTimeHive.value = 0;
    hasResult.value = false;
    performSearchmysql();
    performSearchneo();
    performSearchHive();
}

// 需要返回电影ID和查询时间！！！！！！！！！！！！！
const performSearchmysql = () => {
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
            mysqlSearchResults.value = data.results; // 获取查询结果
            queryTimeMysql.value = data.query_time || 0;   // 获取查询时间
            // 检查结果是否有值并更新 hasResult
            if (data.results && data.results.length > 0) {
                hasResult.value = true;
            }
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            ElMessage({
                message: '查询失败，请稍后再试。',
                type: 'error'
            });
        });
};

//改成正确的URL！！！！！！！！！！！！！！！！！！！！
const performSearchneo = () => {
    let apiUrl1 = new URL(`http://47.97.59.189:5000/search_by_rate`);

    // 构建查询参数
    const params = new URLSearchParams({
        min_rating: minRating.value.toString(),
        max_rating: maxRating.value.toString()
    });

    apiUrl1.search = params.toString();

    fetch(apiUrl1)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            neo4jSearchResults.value = data.results; // 获取查询结果
            queryTimeNeo4j.value = data.query_time || 0;   // 获取查询时间
            // 检查结果是否有值并更新 hasResult
            if (data.results && data.results.length > 0) {
                hasResult.value = true;
            }
        })
        .catch(error => {
            console.error('Error fetching data:', error);
            ElMessage({
                message: '查询失败，请稍后再试。',
                type: 'error'
            });
        });
};

//改成正确的URL！！！！！！！！！！！！！！！！！！！！
const performSearchHive = () => {
    let apiUrl2 = new URL(`http://127.0.0.1:5000/search_by_rate_hive`);

    // 构建查询参数
    const params = new URLSearchParams({
        min_rating: minRating.value.toString(),
        max_rating: maxRating.value.toString()
    });

    apiUrl2.search = params.toString();

    fetch(apiUrl2)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                searchPerformed.value = true;
                loading.value = false;
                throw new Error(data.error);
            }
            hiveSearchResults.value = data.results; // 获取查询结果
            queryTimeHive.value = data.query_time || 0;   // 获取查询时间
            // 检查结果是否有值并更新 hasResult
            if (data.results && data.results.length > 0) {
                hasResult.value = true;
            }
            searchPerformed.value = true;
            loading.value = false;
        })
        .catch(error => {
            searchPerformed.value = true;
            loading.value = false;
            console.error('Error fetching data:', error);
            ElMessage({
                message: '查询失败，请稍后再试。',
                type: 'error'
            });
        });
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

.rating-selection {
    margin-bottom: 20px;
}

.rating-selection input {
    margin-left: 10px;
    margin-right: 10px;
}

.results-area,
.no-results,
.loading,
.query-time,
.back-button {
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

.back-button button {
    display: block;
    margin: 0 auto;
    width: 100px;
}
</style>