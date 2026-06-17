<template>
  <div class="page-card">
    <div class="page-title">四象限任务</div>
    <n-grid :cols="2" :x-gap="20" :y-gap="20">
      <n-gi>
        <n-card title="重要且紧急" :bordered="true" style="background: #fef2f2">
          <n-empty description="暂无任务" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="重要不紧急" :bordered="true" style="background: #eff6ff">
          <n-empty description="暂无任务" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="紧急不重要" :bordered="true" style="background: #fffbeb">
          <n-empty description="暂无任务" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="不重要不紧急" :bordered="true" style="background: #f0fdf4">
          <n-empty description="暂无任务" />
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>
