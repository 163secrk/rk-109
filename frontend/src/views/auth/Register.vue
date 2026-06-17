<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-logo">
        <h1 class="logo-text">知汇</h1>
        <p class="logo-subtitle">创建账号，开始协作</p>
      </div>

      <n-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        size="large"
        label-placement="top"
        @submit="handleRegister"
      >
        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="formData.email" placeholder="请输入邮箱" type="email">
            <template #prefix>
              <n-icon><MailOutline /></n-icon>
            </template>
          </n-input>
        </n-form-item>

        <n-form-item label="姓名" path="name">
          <n-input v-model:value="formData.name" placeholder="请输入您的姓名">
            <template #prefix>
              <n-icon><PersonOutline /></n-icon>
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

        <n-form-item label="团队名称" path="team_name">
          <n-input v-model:value="formData.team_name" placeholder="请输入您的团队名称">
            <template #prefix>
              <n-icon><PeopleOutline /></n-icon>
            </template>
          </n-input>
        </n-form-item>

        <n-button
          type="primary"
          block
          size="large"
          :loading="loading"
          @click="handleRegister"
          class="submit-btn"
        >
          注 册
        </n-button>
      </n-form>

      <div class="auth-footer">
        <span>已有账号？</span>
        <router-link to="/login" class="auth-link">立即登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '../../stores/user'
import { useApi } from '../../utils/request'
import { MailOutline, PersonOutline, LockClosedOutline, PeopleOutline } from '@vicons/ionicons5'

const router = useRouter()
const userStore = useUserStore()
const { message, loadingBar, handleError } = useApi()

const formRef = ref(null)
const loading = ref(false)

const formData = reactive({
  email: '',
  password: '',
  name: '',
  team_name: '',
})

const rules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱地址', trigger: 'blur' },
  ],
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少6位', trigger: 'blur' },
  ],
  team_name: [
    { required: true, message: '请输入团队名称', trigger: 'blur' },
  ],
}

const handleRegister = async () => {
  try {
    await formRef.value?.validate()
    loading.value = true
    loadingBar.start()
    await userStore.register(formData)
    await userStore.fetchMe()
    await userStore.fetchMenus()
    await userStore.fetchPermissions()
    message.success('注册成功！欢迎加入知汇')
    loadingBar.finish()
    router.push('/')
  } catch (e) {
    if (e?.errors) return
    handleError(e, '注册失败')
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
  padding: 20px;
}

.auth-card {
  width: 440px;
  padding: 40px;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(37, 99, 235, 0.12);
  max-height: 100vh;
  overflow-y: auto;
}

.auth-logo {
  text-align: center;
  margin-bottom: 32px;
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
