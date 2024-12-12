<template>
    <div class="time-based-search">
        <h2>按时间查询及统计</h2>
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



        <div v-if="queryTime !== null" class="query-time">
            <p>查询时间: {{ queryTime }} 秒</p>
        </div>
        <h3>查询结果：</h3>
        <!-- 显示检索到的电影数量 -->
        <div v-if="searchResults.length > 0" class="results-summary">
            <p>检索到 {{ searchResults.length }} 部电影。</p>
        </div>

        <!-- 展示电影卡片 -->
        <div class="movie-cards" v-if="searchResults.length > 0">
            <div class="card" v-for="(movie, index) in searchResults" :key="index">
                <h4>{{ movie.movie_name }}</h4>
                <p>平均评分: {{ movie.average_score }}</p>
                <p>上映日期: {{ formatDate(movie.release_date) }}</p>
            </div>
        </div>
        <div v-else-if="searchPerformed && !loading" class="no-results">
            <p>没有找到匹配的结果。</p>
        </div>
        <div v-if="loading" class="loading">
            <p>正在加载...</p>
        </div>

    </div>
</template>

<script setup>
import { ref, computed } from 'vue';

// 定义响应式数据
const queryType = ref('year'); // 默认查询类型为按年查询
const year = ref('');
const month = ref('');
const quarter = ref('');
const weekday = ref('1'); // 默认星期几为周一
const searchResults = ref([]);
const loading = ref(false);
const searchPerformed = ref(false);
const queryTime = ref(null);

// 计算属性，用于控制输入框显示
const showYearInput = computed(() => ['year', 'month', 'quarter', 'weekday'].includes(queryType.value));
const showMonthInput = computed(() => ['month', 'weekday'].includes(queryType.value));
const showQuarterInput = computed(() => queryType.value === 'quarter');
const showWeekdayInput = computed(() => queryType.value === 'weekday');

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, '0')}.${String(date.getDate()).padStart(2, '0')}`;
}

// 方法：执行查询
const performSearch = async () => {
    loading.value = true;
    searchPerformed.value = true;

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
        searchResults.value = data.results;  // 获取查询结果
        queryTime.value = data.query_time;   // 获取查询时间
    } catch (error) {
        console.error('Error fetching data:', error);
        alert('获取数据时出错，请检查网络连接或稍后再试。');
    } finally {
        loading.value = false;
    }
};
</script>

<style scoped>
.time-based-search {
    padding: 20px;
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



.results-area,
.no-results,
.loading,
.query-time {
    margin-top: 20px;
}

/* 电影卡片样式 */
.movie-cards {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
}

.card {
    background-color: #f9f9f9;
    border: 1px solid #ddd;
    border-radius: 8px;
    padding: 16px;
    width: calc(33.333% - 20px);
    /* 三列布局 */
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.card h4 {
    margin: 0 0 8px;
    font-size: 1.2em;
}

.card p {
    margin: 0;
    color: #555;
}
</style>