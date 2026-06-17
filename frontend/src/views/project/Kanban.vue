<template>
  <div class="page-card">
    <div class="page-title">看板</div>
    <n-space :size="20" style="width: 100%">
      <div v-for="col in columns" :key="col" class="kanban-col">
        <n-card :title="col" size="small" hoverable :bordered="false">
          <n-empty description="暂无任务" style="padding: 20px 0" />
        </n-card>
      </div>
    </n-space>
  </div>
</template>

<script setup>
const columns = ['待办', '进行中', '已完成', '已归档']
</script>

<style lang="scss" scoped>
.kanban-col {
  flex: 1;
  min-width: 240px;
}
</style>
