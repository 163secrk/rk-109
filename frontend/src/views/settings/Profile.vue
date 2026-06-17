<template>
  <div class="page-card">
    <div class="page-title">个人设置</div>
    <n-grid :cols="2" :x-gap="40">
      <n-gi>
        <n-card title="基本信息" :bordered="false">
          <n-form label-placement="top" style="margin-top: 12px">
            <n-form-item label="头像">
              <n-avatar round size="64" style="background-color: #2563eb; font-size: 24px">
                {{ userStore.user?.name?.charAt(0) }}
              </n-avatar>
            </n-form-item>
            <n-form-item label="姓名">
              <n-input :value="userStore.user?.name" />
            </n-form-item>
            <n-form-item label="邮箱">
              <n-input :value="userStore.user?.email" disabled />
            </n-form-item>
            <n-button type="primary">保存</n-button>
          </n-form>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="修改密码" :bordered="false">
          <n-form label-placement="top" style="margin-top: 12px">
            <n-form-item label="当前密码">
              <n-input type="password" placeholder="请输入当前密码" show-password-on="click" />
            </n-form-item>
            <n-form-item label="新密码">
              <n-input type="password" placeholder="请输入新密码" show-password-on="click" />
            </n-form-item>
            <n-form-item label="确认新密码">
              <n-input type="password" placeholder="请确认新密码" show-password-on="click" />
            </n-form-item>
            <n-button type="primary">修改密码</n-button>
          </n-form>
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup>
import { useUserStore } from '../../stores/user'
const userStore = useUserStore()
</script>
