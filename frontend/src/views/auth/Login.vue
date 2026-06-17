<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-logo">
        <h1 class="logo-text">知汇</h1>
        <p class="logo-subtitle">在线协作工具</p>
      </div>

      <n-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        size="large"
        label-placement="top"
        @submit="handleLogin"
      >
        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="formData.email" placeholder="请输入邮箱" type="email">
            <template #prefix>
              <n-icon><MailOutline /></n-icon>
            </template>
          </n-input>
        </n-form-item>

        <n-form-item label="密码" path="password">
          <n-input
            v-model:value="formData.password"
            placeholder="请输入密码"
            type="password"
            show-password-on="click"
          >
            <template #prefix>
              <n-icon><LockClosedOutline /></n-icon>
            </template>
          </n-input>
        </n-form-item>

        <n-button
          type="primary"
          block
          size="large"
          :loading="loading"
          @click="handleLogin"
          class="submit-btn"
        >
          登 录
        </n-button>
      </n-form>

      <div class="auth-footer">
        <span>还没有账号？</span>
        <router-link to="/register" class="auth-link">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../../stores/user'
import { useApi } from '../../utils/request'
import { MailOutline, LockClosedOutline } from '@vicons/ionicons5'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const { message, loadingBar, handleError } = useApi()

const formRef = ref(null)
const loading = ref(false)

const formData = reactive({
  email: '',
  password: '',
})

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
}

const handleLogin = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true
    loadingBar.start()
    await userStore.login(formData)
    await userStore.fetchMe()
    await userStore.fetchMenus()
    await userStore.fetchPermissions()
    await userStore.fetchUnreadCount()
    message.success('登录成功！')
    loadingBar.finish()
    const redirect = route.query.redirect || '/'
    router.push(redirect)
  } catch (e) {
    if (e?.errors) return
    handleError(e, '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
.auth-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #eff6ff 0%, #ffffff 50%, #f0f9ff 100%);
}

.auth-card {
  width: 420px;
  padding: 48px 40px;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(37, 99, 235, 0.12);
}

.auth-logo {
  text-align: center;
  margin-bottom: 36px;
}

.logo-text {
  font-size: 36px;
  font-weight: 700;
  color: #2563eb;
  margin: 0;
  letter-spacing: 8px;
}

.logo-subtitle {
  font-size: 14px;
  color: #64748b;
  margin-top: 8px;
  margin-bottom: 0;
}

.submit-btn {
  margin-top: 8px;
  height: 44px;
  font-size: 16px;
  font-weight: 500;
}

.auth-footer {
  margin-top: 24px;
  text-align: center;
  font-size: 14px;
  color: #64748b;

  .auth-link {
    color: #2563eb;
    margin-left: 4px;
    font-weight: 500;

    &:hover {
      color: #1d4ed8;
      text-decoration: underline;
    }
  }
}
</style>
