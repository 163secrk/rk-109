<template>
  <div class="page-card">
    <div class="page-title">数据概览</div>
    <n-grid :cols="4" :x-gap="20" :y-gap="20">
      <n-gi v-for="stat in stats" :key="stat.label">
        <n-card hoverable :bordered="false">
          <div style="color: #64748b; font-size: 13px">{{ stat.label }}</div>
          <div style="font-size: 32px; font-weight: 700; color: #1e293b; margin-top: 8px">
            {{ stat.value }}
          </div>
          <div style="margin-top: 8px; color: #10b981; font-size: 12px">
            较上周 +{{ stat.growth }}%
          </div>
        </n-card>
      </n-gi>
    </n-grid>
    <n-divider />
    <n-empty description="图表区域" style="margin-top: 40px" />
  </div>
</template>

<script setup>
const stats = [
  { label: '团队成员', value: 0, growth: 0 },
  { label: '活跃项目', value: 0, growth: 0 },
  { label: '文档数量', value: 0, growth: 0 },
  { label: '已完成任务', value: 0, growth: 0 },
]
</script>
