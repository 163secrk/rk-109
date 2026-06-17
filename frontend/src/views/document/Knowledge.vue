<template>
  <div class="page-card">
    <div class="page-title">知识库</div>
    <n-layout has-sider style="height: calc(100vh - 180px)">
      <n-layout-sider width="240" bordered style="background: #fff">
        <n-tree block-line :data="treeData" />
      </n-layout-sider>
      <n-layout-content style="padding: 24px; background: #fff">
        <n-empty description="请选择左侧文档或创建新文档" />
      </n-layout-content>
    </n-layout>
  </div>
</template>

<script setup>
const treeData = [
  {
    key: 1,
    label: '团队规范',
    children: [
      { key: 11, label: '代码规范' },
      { key: 12, label: '设计规范' },
    ],
  },
  {
    key: 2,
    label: '产品文档',
    children: [
      { key: 21, label: '需求文档' },
      { key: 22, label: '产品路线图' },
    ],
  },
]
</script>
