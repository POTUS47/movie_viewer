<template>
  <div class="search-by-title">
    <h2>按电影名称查询</h2>
    <div class="search-container">
      <input  type="text" placeholder="请输入电影名称..." />
      <button >搜索</button>
    </div>
    <div class="chart-area" >
      <!-- <line-chart :data="chartData" :options="chartOptions"></line-chart> -->
    </div>
    <div class="results-area" >
      <h3>搜索结果：</h3>
      
    </div>
    <div class="no-results">
      <p>没有找到匹配的结果。</p>
    </div>
    
  </div>
</template>



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

.chart-area, .results-area, .no-results, .loading {
  margin-top: 20px;
}
</style>