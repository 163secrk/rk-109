<template>
  <div class="page-card">
    <div class="page-title">成员管理</div>
    <n-data-table :columns="columns" :data="members" />
  </div>
</template>

<script setup>
const columns = [
  { title: '成员', key: 'name' },
  { title: '邮箱', key: 'email' },
  { title: '角色', key: 'role' },
  { title: '加入时间', key: 'joined' },
  { title: '状态', key: 'status' },
  { title: '操作', key: 'actions' },
]
const members = []
</script>
