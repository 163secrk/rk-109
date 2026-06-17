<template>
  <div class="page-card">
    <div class="page-title">团队信息</div>
    <n-form label-placement="left" label-width="100" style="max-width: 520px">
      <n-form-item label="团队名称">
        <n-input placeholder="请输入团队名称" />
      </n-form-item>
      <n-form-item label="团队描述">
        <n-input type="textarea" placeholder="请输入团队描述" />
      </n-form-item>
      <n-form-item label="创建时间">
        <n-input disabled placeholder="-" />
      </n-form-item>
      <n-form-item>
        <n-space>
          <n-button type="primary">保存修改</n-button>
          <n-button>取消</n-button>
        </n-space>
      </n-form-item>
    </n-form>
  </div>
</template>
