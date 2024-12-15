<template>
    <div class="search-by-title">
        <h2>演员和导演关系查询</h2>
        <!-- 查询类型选择 -->
        <div class="query-type-selection" v-if="!showDiagram">
            <label>
                <input type="radio" v-model="queryType" value="actor" @change="onQueryTypeChange"> 查询演员关系
            </label>
            <label>
                <input type="radio" v-model="queryType" value="director" @change="onQueryTypeChange"> 查询导演关系
            </label>
        </div>

        <!-- 根据查询类型显示不同内容 -->
        <div v-if="queryType === 'actor' && !showDiagram">
            <h3>选择查询方式：</h3>
            <div class="query-option-selection">
                <label>
                    <input type="radio" v-model="actorQueryOption" value="co-actor"> 查询合作的演员
                </label>
                <label>
                    <input type="radio" v-model="actorQueryOption" value="co-director"> 查询合作的导演
                </label>
            </div>
            <div class="search-container">
                <input v-model="searchQuery" type="text" placeholder="请输入演员姓名..." @keyup.enter="performSearch" />
                <button @click="performSearch">搜索</button>
            </div>
        </div>

        <div v-else-if="queryType === 'director' && !showDiagram">
            <div class="search-container">
                <input v-model="searchQuery" type="text" placeholder="请输入导演姓名..." @keyup.enter="performSearch" />
                <button @click="performSearch">搜索</button>
            </div>
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

        <!-- 按钮区域，选择不同的查询方式 -->
        <div class="query-buttons" v-if="showDiagram">
            <button @click="selectedQuery = 'mysql'" :class="{ 'active': selectedQuery === 'mysql' }"> 显示MySQL
                查询结果</button>
            <button @click="selectedQuery = 'neo4j'" :class="{ 'active': selectedQuery === 'neo4j' }">显示Neo4j
                查询结果</button>
            <button @click="selectedQuery = 'hive'" :class="{ 'active': selectedQuery === 'hive' }">显示Hive 查询结果</button>
        </div>

        <div v-if="loading" class="loading">
            <p>正在加载...</p>
        </div>

        <!-- 根据选中的查询方式展示不同的结果 -->
        <div class="results-area" v-if="hasResult && !showDiagram">
            <h3>根据关键词检索到的{{ queryType === 'actor' ? '演员' : '导演' }}(共{{ relatedEntities.length }} 条记录)</h3>
            <div class="movie-cards">
                <div v-for="(result, index) in relatedEntities" :key="index" class="movie-card"
                    @click="performRelationshipSearch(result)">
                    <h4>{{ getEntityName(result) }}</h4>
                </div>
            </div>
        </div>
        <div v-else-if="searchPerformed && !hasResult" class="no-results">
            <p>没有找到匹配的结果。</p>
        </div>

        <!-- 显示具体演员或导演的关系 -->
        <div v-if="showDiagram && selectedEntity &&!loading &&selectedQuery" class="details-area">
            <h3>{{ entityName }} 的关系：</h3>
            <table>
                <thead>
                    <tr>
                        <th v-for="header in resultHeaders" :key="header">{{ header }}</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="(result, index) in getSearchResults" :key="index">
                        <td>{{ result.co_name }}</td>
                        <td>{{ result.cooperation_count }}</td>
                    </tr>
                </tbody>
            </table>
            <button @click="backToEntities">返回</button>
        </div>


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
const loading = ref(false);
const searchPerformed = ref(false);

const queryTimeMysql = ref(0); // 新增的 MySQL 查询时间
const queryTimeNeo4j = ref(0); // 新增的 Neo4j 查询时间
const queryTimeHive = ref(0); // 新增加的Hive查询时间
const selectedQuery = ref('')// 新增的结果查看方式
let chart = null; // Chart.js 图表实例
const hasResult = ref(false);

const queryType = ref('actor'); // 默认查询类型为演员关系
const actorQueryOption = ref('co-actor'); // 默认查询合作的演员
const showDiagram = ref(false);
const relatedEntities = ref([]); // 相关演员或导演列表
const selectedEntity = ref(null); // 当前选中的演员或导演
const resultHeaders = ref(['名字', '合作次数']); // 默认表头
const entityName = ref('');

const onQueryTypeChange = () => {
    searchPerformed.value = false;
    hasResult.value = false;
};

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

// 根据查询类型获取实体的名字
const getEntityName = (entity) => {
    if (queryType.value === 'actor') {
        return entity.actor_name || entity.name;
    } else if (queryType.value === 'director') {
        return entity.director_name || entity.name;
    }
    return entity.name; // 默认情况下
};

// 搜索相关演员或导演实体（仅使用MYSQL）
const performSearch = () => {
    showDiagram.value = false;//不显示时间对比图表
    searchPerformed.value = false;//和loading作用是不一样的，初值一样，后面全反。
    loading.value = true;
    hasResult.value = false;
    relatedEntities.value = [];
    sqlSearchEntity();
}

const sqlSearchEntity = () => {
    if (!searchQuery.value.trim()) {
        ElMessage({
            message: '请输入查询的名字。',
            type: 'warning'
        });
        return;
    }
    let apiUrl = '';
    if (queryType.value === 'actor') {
        apiUrl = `http://47.97.59.189:5000/search_every_actor/${searchQuery.value}`;
    } else if (queryType.value === 'director') {
        apiUrl = `http://47.97.59.189:5000/search_every_director/${searchQuery.value}`;
    }

    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            relatedEntities.value = data.results;  // 获取查询结果
            //queryTime.value = data.query_time;   // 获取查询时间
            //queryTimeMysql.value = data.query_time_mysql; // 获取 MySQL 查询时间
            //queryTimeNeo4j.value = data.query_time_neo4j; // 获取 Neo4j 查询时间
            // 检查结果是否有值并更新 hasResult
            if (data.results && data.results.length > 0) {
                hasResult.value = true;
            }
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

// 获取关系搜索结果的计算属性
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

// 搜索具体演员或导演的关系
const performRelationshipSearch = (entity) => {
    entityName.value = getEntityName(entity);
    selectedEntity.value = entity;
    selectedQuery.value = '';
    loading.value = true;
    queryTimeMysql.value = 0;
    queryTimeNeo4j.value = 0;
    queryTimeHive.value = 0;
    showDiagram.value = true;
    performSearchmysql();
    performSearchneo();
    performSearchHive();
}

// MySQL搜索
const performSearchmysql = () => {
    let apiUrl = '';
    if (queryType.value === 'actor') {
        apiUrl = actorQueryOption.value === 'co-actor'
            ? `http://47.97.59.189:5000/relation_actor_actor/${entityName.value}`
            : `http://47.97.59.189:5000/relation_actor_director/${entityName.value}`;
    } else if (queryType.value === 'director') {
        apiUrl = `http://47.97.59.189:5000/relation_director_actor/${entityName.value}`;
    }

    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            mysqlSearchResults.value = data.results;  // 获取查询结果
            queryTimeMysql.value = data.query_time;   // 获取查询时间
        })
        .catch(error => {
            console.error('Error fetching collaborations:', error);
            ElMessage({
                message: '获取合作关系失败，请稍后再试。',
                type: 'error'
            });
        });
};

// 需要修改成正确URL！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
const performSearchneo = () => {
    let apiUrl1 = '';
    if (queryType.value === 'actor') {
        apiUrl1 = actorQueryOption.value === 'co-actor'
            ? `http://47.97.59.189:5000/relation_actor_actor/${entityName.value}`
            : `http://47.97.59.189:5000/relation_actor_director/${entityName.value}`;
    } else if (queryType.value === 'director') {
        apiUrl1 = `http://47.97.59.189:5000/relation_director_actor/${entityName.value}`;
    }

    fetch(apiUrl1)
        .then(response => response.json())
        .then(data => {
            neo4jSearchResults.value = data.results;  // 获取查询结果
            queryTimeNeo4j.value = data.query_time;   // 获取查询时间
        })
        .catch(error => {
            console.error('Error fetching collaborations:', error);
            ElMessage({
                message: '获取合作关系失败，请稍后再试。',
                type: 'error'
            });
        });
};

// 需要修改成正确URL！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！！
const performSearchHive = () => {
    let apiUrl2 = '';
    if (queryType.value === 'actor') {
        apiUrl2 = actorQueryOption.value === 'co-actor'
            ? `http://47.97.59.189:5000/relation_actor_actor/${entityName.value}`
            : `http://47.97.59.189:5000/relation_actor_director/${entityName.value}`;
    } else if (queryType.value === 'director') {
        apiUrl2 = `http://47.97.59.189:5000/relation_director_actor/${entityName.value}`;
    }

    fetch(apiUrl2)
        .then(response => response.json())
        .then(data => {
            hiveSearchResults.value = data.results;  // 获取查询结果
            queryTimeHive.value = data.query_time;   // 获取查询时间
            loading.value = false;
        })
        .catch(error => {
            loading.value = false;
            console.error('Error fetching collaborations:', error);
            ElMessage({
                message: '获取合作关系失败，请稍后再试。',
                type: 'error'
            });
        });
};

// 返回到查询结果卡片
const backToEntities = () => {
    showDiagram.value=false;
};

</script>

<style scoped>
.relationship-query {
    padding: 20px;
}

.query-type-selection {
    margin-bottom: 20px;
}

.query-option-selection {
    margin-bottom: 20px;
}


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

.details-area table {
    width: 100%;
    border-collapse: collapse;
}
.details-area th,
.details-area td {
    border: 1px solid #ccc;
    padding: 8px;
    text-align: left;
}
.details-area button{
    margin-top: 15px;
}

</style>