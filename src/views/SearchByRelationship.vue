<template>
    <div class="relationship-query">
        <h2>演员和导演关系查询</h2>

        <!-- 查询类型选择 -->
        <div class="query-type-selection">
            <label>
                <input type="radio" v-model="queryType" value="actor" @change="onQueryTypeChange"> 查询演员关系
            </label>
            <label>
                <input type="radio" v-model="queryType" value="director" @change="onQueryTypeChange"> 查询导演关系
            </label>
        </div>

        <!-- 根据查询类型显示不同内容 -->
        <div v-if="queryType === 'actor'">
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
                <input v-model="searchQuery" type="text" placeholder="请输入演员姓名..." />
                <button @click="performSearch">搜索</button>
            </div>
        </div>

        <div v-else-if="queryType === 'director'">
            <div class="search-container">
                <input v-model="searchQuery" type="text" placeholder="请输入导演姓名..." />
                <button @click="performSearch">搜索</button>
            </div>
        </div>

        <!-- 展示查询时间对比 -->
        <div v-if="queryTimeMysql !== null || queryTimeNeo4j !== null" class="query-time-comparison">
            <p>MySQL 查询时间: {{ queryTimeMysql }} 秒</p>
            <p>Neo4j 查询时间: {{ queryTimeNeo4j }} 秒</p>
        </div>

        <div v-if="loading" class="loading">
            <p>正在加载...</p>
        </div>

        <div v-if="queryTime !== null" class="query-time">
            <p>查询时间: {{ queryTime }} 秒</p>
        </div>

        <!-- 显示相关演员或导演卡片 -->
        <div v-if="showResults && relatedEntities.length > 0" class="results-area">
            <h3>相关{{ queryType === 'actor' ? '演员' : '导演' }}：</h3>
            <div class="entity-cards">
                <div v-for="(entity, index) in relatedEntities" :key="index" class="entity-card"
                    @click="showEntityRelationship(entity)">
                    <h4>{{ getEntityName(entity) }}</h4>
                </div>
            </div>
        </div>
        <div v-else-if="showResults && searchPerformed && !loading" class="no-results">
            <p>没有找到匹配的相关{{ queryType === 'actor' ? '演员' : '导演' }}。</p>
        </div>

        <!-- 显示具体演员或导演的关系 -->
        <div v-if="showDetails && selectedEntity" class="details-area">
            <h3>{{ theName }} 的关系：</h3>
            <table>
                <thead>
                    <tr>
                        <th v-for="header in resultHeaders" :key="header">{{ header }}</th>
                    </tr>
                </thead>
                <tbody>
                    <tr v-for="(result, index) in entityRelationships" :key="index">
                        <td>{{ result.co_name }}</td>
                        <td>{{ result.cooperation_count }}</td>
                    </tr>
                </tbody>
            </table>
            <button @click="backToResults">返回</button>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue';
import { ElMessage } from 'element-plus'; // 如果你使用的是 Element Plus 消息框

const queryType = ref('actor'); // 默认查询类型为演员关系
const actorQueryOption = ref('co-actor'); // 默认查询合作的演员
const searchQuery = ref('');
const theName = ref('');
const loading = ref(false);
const searchPerformed = ref(false);
const showResults = ref(false); // 控制是否显示查询结果卡片
const showDetails = ref(false); // 控制是否显示详细关系
const queryTime = ref(null);
const relatedEntities = ref([]); // 相关演员或导演列表
const selectedEntity = ref(null); // 当前选中的演员或导演
const entityRelationships = ref([]); // 选中实体的关系列表
const resultHeaders = ref(['名字', '合作次数']); // 默认表头
const queryTimeMysql = ref(null); // 新增的 MySQL 查询时间
const queryTimeNeo4j = ref(null); // 新增的 Neo4j 查询时间

// 监听查询类型变化
const onQueryTypeChange = () => {
    // 清空之前的选择和结果
    searchQuery.value = '';
    relatedEntities.value = [];
    entityRelationships.value = [];
    selectedEntity.value = null;
    showResults.value = false;
    showDetails.value = false;
};

// 根据查询类型获取实体的名字
const getEntityName = (entity) => {
    if (queryType.value === 'actor') {
        return entity.actor_name || entity.name;
    } else if (queryType.value === 'director') {
        return entity.director_name || entity.name;
    }
    return entity.name; // 默认情况下
};

// 执行搜索的方法
const performSearch = () => {
    if (!searchQuery.value.trim()) {
        ElMessage({
            message: '请输入查询的名字。',
            type: 'warning'
        });
        return;
    }

    loading.value = true;
    searchPerformed.value = true;

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
            queryTime.value = data.query_time;   // 获取查询时间
            queryTimeMysql.value = data.query_time_mysql; // 获取 MySQL 查询时间
            queryTimeNeo4j.value = data.query_time_neo4j; // 获取 Neo4j 查询时间
            loading.value = false;
            showResults.value = true;
            showDetails.value = false;
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

// 显示具体演员或导演的关系
const showEntityRelationship = (entity) => {
    loading.value = true;
    selectedEntity.value = entity;
    theName.value = getEntityName(entity);

    let apiUrl = '';
    if (queryType.value === 'actor') {
        apiUrl = actorQueryOption.value === 'co-actor'
            ? `http://47.97.59.189:5000/relation_actor_actor/${theName.value}`
            : `http://47.97.59.189:5000/relation_actor_director/${theName.value}`;
    } else if (queryType.value === 'director') {
        apiUrl = `http://47.97.59.189:5000/relation_director_actor/${theName.value}`;
    }

    fetch(apiUrl)
        .then(response => response.json())
        .then(data => {
            entityRelationships.value = data.results;  // 获取查询结果
            queryTime.value = data.query_time;   // 获取查询时间
            loading.value = false;
            showDetails.value = true;
            showResults.value = false;
        })
        .catch(error => {
            console.error('Error fetching collaborations:', error);
            ElMessage({
                message: '获取合作关系失败，请稍后再试。',
                type: 'error'
            });
            loading.value = false;
        });
};

// 返回到查询结果卡片
const backToResults = () => {
    showResults.value = true;
    showDetails.value = false;
    selectedEntity.value = null;
    entityRelationships.value = [];
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
.back-button {
    margin-top: 20px;
}

.entity-cards {
    display: flex;
    flex-wrap: wrap;
}

.entity-card {
    border: 1px solid #ccc;
    padding: 10px;
    margin: 10px;
    cursor: pointer;
    width: 200px;
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

.back-button button {
    display: block;
    margin: 0 auto;
    width: 100px;
}
</style>