<!-- 问题：电影ID待返回！！！！！！ -->
<template>
    <div class="search-by-title">
        <h2>按按时间查询</h2>
        <form @submit.prevent="performSearch">
            <div class="search-options">
                <div> <label for="queryType">选择查询类型:</label>
                    <select v-model="queryType" id="queryType">
                        <option value="year">按年查询</option>
                        <option value="month">按年和月查询</option>
                        <option value="quarter">按年和季度查询</option>
                        <option value="weekday">按年和月的星期几查询</option>
                    </select>
                </div>

                <div v-if="showYearInput || showWeekdayInput">
                    <label for="year">选择年份:</label>
                    <input type="number" v-model="year" id="year" placeholder="请输入年份..." />
                </div>

                <div v-if="showMonthInput || showWeekdayInput">
                    <label for="month">选择月份:</label>
                    <input type="number" v-model="month" id="month" placeholder="请输入月份..." min="1" max="12" />
                </div>

                <div v-if="showQuarterInput">
                    <label for="quarter">选择季度:</label>
                    <input type="number" v-model="quarter" id="quarter" placeholder="请输入季度..." min="1" max="4" />
                </div>

                <div v-if="showWeekdayInput">
                    <label for="weekday">选择星期几:</label>
                    <select v-model="weekday" id="weekday">
                        <option value="7">周日</option>
                        <option value="1">周一</option>
                        <option value="2">周二</option>
                        <option value="3">周三</option>
                        <option value="4">周四</option>
                        <option value="5">周五</option>
                        <option value="6">周六</option>
                    </select>
                </div>

                <button type="submit">查询</button>
            </div>
        </form>
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
                    <p>电影ID: {{ result.movie_id }}</p>
                    <p>平均评分: {{ result.average_score }}</p>
                    <p>上映日期: {{ formatDate(result.release_date) }}</p>
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

const queryType = ref('year'); // 默认查询类型为按年查询
const year = ref('');
const month = ref('');
const quarter = ref('');
const weekday = ref('1'); // 默认星期几为周一

// 计算属性，用于控制输入框显示
const showYearInput = computed(() => ['year', 'month', 'quarter', 'weekday'].includes(queryType.value));
const showMonthInput = computed(() => ['month', 'weekday'].includes(queryType.value));
const showQuarterInput = computed(() => queryType.value === 'quarter');
const showWeekdayInput = computed(() => queryType.value === 'weekday');

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')}`;
}

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

// SQL返回电影ID字段！！！！！！！！！！！
const performSearchmysql = async () => {
    let apiUrl = new URL(`http://47.97.59.189:5000/search_by_time`);
    const params = new URLSearchParams({
        type: queryType.value,
        ...(showYearInput.value && { year: year.value }),
        ...(showMonthInput.value && { month: month.value }),
        ...(showQuarterInput.value && { quarter: quarter.value }),
        ...(showWeekdayInput.value && { weekday: weekday.value })
    });
    apiUrl.search = params.toString();

    try {
        const response = await fetch(apiUrl);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        mysqlSearchResults.value = data.results;  // 获取查询结果
        queryTimeMysql.value = data.query_time;   // 获取查询时间
        // 检查结果是否有值并更新 hasResult
        if (data.results && data.results.length > 0) {
            hasResult.value = true;
        }
    } catch (error) {
        console.error('Error fetching data:', error);
        alert('获取数据时出错，请检查网络连接或稍后再试。');
    } finally {
    }
};

// 需要修改成正确URL！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
const performSearchneo = async () => {
    let apiUrl1 = new URL(`http://47.97.59.189:5000/search_by_time`);
    const params = new URLSearchParams({
        type: queryType.value,
        ...(showYearInput.value && { year: year.value }),
        ...(showMonthInput.value && { month: month.value }),
        ...(showQuarterInput.value && { quarter: quarter.value }),
        ...(showWeekdayInput.value && { weekday: weekday.value })
    });
    apiUrl1.search = params.toString();

    try {
        const response = await fetch(apiUrl1);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        neo4jSearchResults.value = data.results;  // 获取查询结果
        queryTimeNeo4j.value = data.query_time;   // 获取查询时间
        // 检查结果是否有值并更新 hasResult
        if (data.results && data.results.length > 0) {
            hasResult.value = true;
        }
    } catch (error) {
        console.error('Error fetching data:', error);
        alert('获取数据时出错，请检查网络连接或稍后再试。');
    } finally {
    }
};

// 需要修改成正确URL！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
const performSearchHive = async () => {
    let apiUrl2 = new URL(`http://127.0.0.1:5000/search_by_time_hive`);
    const params = new URLSearchParams({
        type: queryType.value,
        ...(showYearInput.value && { year: year.value }),
        ...(showMonthInput.value && { month: month.value }),
        ...(showQuarterInput.value && { quarter: quarter.value }),
        ...(showWeekdayInput.value && { weekday: weekday.value })
    });
    apiUrl2.search = params.toString();

    try {
        const response = await fetch(apiUrl2);
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        const data = await response.json();
        hiveSearchResults.value = data.results;  // 获取查询结果
        queryTimeHive.value = data.query_time;   // 获取查询时间
        // 检查结果是否有值并更新 hasResult
        if (data.results && data.results.length > 0) {
            hasResult.value = true;
        }
    } catch (error) {
        console.error('Error fetching data:', error);
        searchPerformed.value = true;
        loading.value = false;
        //alert('获取数据时出错，请检查网络连接或稍后再试。');
    } finally {
        searchPerformed.value = true;
        loading.value = false;
    }
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

.search-options {
    margin-bottom: 20px;
}

.search-options>div {
    margin-bottom: 10px;
    /* 每个 div 之间的间距 */
}

.search-options select {
    width: 12%;
    margin-bottom: 10px;
    margin-left: 10px;
}

.search-options input {
    width: 12%;
    margin-bottom: 10px;
    margin-left: 10px;
}

.search-options button {
    width: 10%;
}

</style>