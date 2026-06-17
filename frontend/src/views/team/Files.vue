<template>
  <div class="page-card">
    <div class="page-title">文件管理</div>
    <n-space vertical :size="16" style="width: 100%">
      <n-space>
        <n-button type="primary">新建文件夹</n-button>
        <n-button>上传文件</n-button>
      </n-space>
      <n-data-table
        :columns="columns"
        :data="files"
        :pagination="pagination"
      />
    </n-space>
  </div>
</template>

<script setup>
const columns = [
  { title: '名称', key: 'name' },
  { title: '类型', key: 'type' },
  { title: '大小', key: 'size' },
  { title: '修改时间', key: 'time' },
  { title: '操作', key: 'actions', render: () => '下载 共享 删除' },
]
const files = []
const pagination = { pageSize: 10 }
</script>
