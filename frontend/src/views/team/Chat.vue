<template>
  <div class="page-card">
    <div class="page-title">即时聊天</div>
    <n-layout has-sider style="height: calc(100vh - 180px)">
      <n-layout-sider width="260" bordered style="background: #fff">
        <div style="padding: 16px; border-bottom: 1px solid #f1f5f9; font-weight: 600">
          频道
        </div>
        <n-list bordered="false">
          <n-list-item v-for="c in channels" :key="c">
            <template #prefix>
              <n-tag round type="primary" size="small">#</n-tag>
            </template>
            {{ c }}
          </n-list-item>
        </n-list>
      </n-layout-sider>
      <n-layout-content style="padding: 24px; background: #fff; display: flex; flex-direction: column">
        <div style="flex: 1; display: flex; align-items: center; justify-content: center">
          <n-empty description="暂无消息，快来发送第一条消息吧" />
        </div>
      </n-layout-content>
    </n-layout>
  </div>
</template>

<script setup>
const channels = ['公告', '产品讨论', '技术交流', '前端组', '后端组']
</script>
