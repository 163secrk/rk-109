<template>
  <n-layout has-sider class="main-layout">
    <n-layout-sider
      width="240"
      bordered
      collapse-mode="width"
      :collapsed-width="64"
      :collapsed="collapsed"
      show-trigger
      :trigger-value="!collapsed"
      class="layout-sider"
    >
      <div class="logo-area" @click="handleLogoClick">
        <div class="logo-icon">知</div>
        <span v-if="!collapsed" class="logo-text">知汇</span>
      </div>

      <div v-if="!collapsed" class="team-selector">
        <n-dropdown
          :options="teamDropdownOptions"
          @select="handleSwitchTeam"
          trigger="click"
        >
          <div class="team-box">
            <div class="team-info">
              <div class="team-name">{{ currentTeam?.name || '选择团队' }}</div>
              <div class="team-role">{{ currentRole?.display_name || '' }}</div>
            </div>
            <n-icon size="16" color="#64748b"><ChevronDownOutline /></n-icon>
          </div>
        </n-dropdown>
      </div>

      <n-menu
        v-model:value="activeMenu"
        :options="menuOptions"
        :collapsed="collapsed"
        :collapsed-width="64"
        :collapsed-icon-size="22"
        class="side-menu"
        @update:value="handleMenuClick"
      />
    </n-layout-sider>

    <n-layout>
      <n-layout-header bordered class="layout-header">
        <div class="header-left">
          <n-breadcrumb>
            <n-breadcrumb-item v-for="(item, index) in breadcrumbItems" :key="index">
              {{ item }}
            </n-breadcrumb-item>
          </n-breadcrumb>
        </div>

        <div class="header-right">
          <n-popover
            trigger="click"
            placement="bottom-end"
            :show-arrow="false"
            trigger="click"
          >
            <template #trigger>
              <n-badge :value="userStore.unreadCount" :max="99" :show-zero="false">
                <n-button quaternary circle size="large" @click="handleRefreshUnread">
                  <template #icon>
                    <n-icon size="20"><NotificationsOutline /></n-icon>
                  </template>
                </n-button>
              </n-badge>
            </template>
            <div class="notification-panel">
              <div class="notification-header">
                <span>通知中心</span>
                <n-button text type="primary" size="tiny" @click="handleMarkAllRead">
                  全部已读
                </n-button>
              </div>
              <n-divider style="margin: 8px 0" />
              <n-empty v-if="notifications.length === 0" description="暂无通知" />
              <div v-else class="notification-list">
                <div
                  v-for="item in notifications"
                  :key="item.id"
                  class="notification-item"
                  :class="{ unread: !item.is_read }"
                  @click="handleMarkRead(item.id)"
                >
                  <div class="notif-title">{{ item.title }}</div>
                  <div class="notif-content">{{ item.content }}</div>
                  <div class="notif-time">{{ formatTime(item.created_at) }}</div>
                </div>
              </div>
            </div>
          </n-popover>

          <n-dropdown
            :options="userDropdownOptions"
            @select="handleUserDropdownSelect"
            trigger="click"
          >
            <div class="user-box">
              <n-avatar round size="36" style="background-color: #2563eb">
                {{ userStore.user?.name?.charAt(0) || 'U' }}
              </n-avatar>
              <div class="user-info">
                <div class="user-name">{{ userStore.user?.name || '用户' }}</div>
                <div class="user-email">{{ userStore.user?.email || '' }}</div>
              </div>
              <n-icon size="16" color="#64748b"><ChevronDownOutline /></n-icon>
            </div>
          </n-dropdown>
        </div>
      </n-layout-header>

      <n-layout-content class="layout-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup>
import { ref, computed, onMounted, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../../stores/user'
import { useApi } from '../../utils/request'
import { getNotificationsApi, markReadApi, markAllReadApi } from '../../api/auth'
import {
  DashboardOutlined,
  ClipboardListOutlined,
  DocOutline,
  PeopleOutline,
  BarChartOutline,
  SettingsOutline,
  NotificationsOutline,
  ChevronDownOutline,
  PersonCircleOutline,
  LogOutOutline,
} from '@vicons/ionicons5'
import { NIcon } from 'naive-ui'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const { message } = useApi()

const collapsed = ref(false)
const activeMenu = ref('workspace.quadrant')
const notifications = ref([])

const iconMap = {
  DashboardOutlined,
  ClipboardListOutlined,
  DocOutline,
  PeopleOutline,
  BarChartOutline,
  SettingsOutline,
}

const renderIcon = (iconName) => {
  const icon = iconMap[iconName]
  return () => h(NIcon, null, { default: () => h(icon) })
}

const currentTeam = computed(() => userStore.currentTeam)
const currentRole = computed(() => userStore.currentRole)

const menuOptions = computed(() => {
  return userStore.menus.map((menu) => ({
    key: menu.key,
    label: menu.name,
    icon: renderIcon(menu.icon),
    children: (menu.children || []).map((child) => ({
      key: child.key,
      label: child.name,
    })),
  }))
})

const teamDropdownOptions = computed(() => {
  return userStore.teams.map((t) => ({
    label: `${t.team.name} - ${t.role.display_name}`,
    key: t.team.id,
  }))
})

const userDropdownOptions = [
  {
    label: '个人设置',
    key: 'profile',
    icon: () => h(NIcon, null, { default: () => h(PersonCircleOutline) }),
  },
  {
    label: '退出登录',
    key: 'logout',
    icon: () => h(NIcon, null, { default: () => h(LogOutOutline) }),
  },
]

const breadcrumbItems = computed(() => route.meta.breadcrumb || [])

const handleMenuClick = (key) => {
  const flatMenus = userStore.menus.flatMap((m) => m.children || [])
  const item = flatMenus.find((c) => c.key === key)
  if (item?.path) {
    router.push(item.path)
  }
}

const handleLogoClick = () => {
  router.push('/')
}

const handleSwitchTeam = async (teamId) => {
  try {
    await userStore.switchTeam(teamId)
    message.success('已切换团队')
    router.push('/')
  } catch (e) {
    console.error(e)
  }
}

const handleUserDropdownSelect = (key) => {
  if (key === 'profile') {
    router.push('/settings/profile')
  } else if (key === 'logout') {
    userStore.logout()
    router.push('/login')
    message.success('已退出登录')
  }
}

const handleRefreshUnread = async () => {
  try {
    await userStore.fetchUnreadCount()
    const res = await getNotificationsApi()
    notifications.value = res
  } catch (e) {
    console.error(e)
  }
}

const handleMarkRead = async (id) => {
  try {
    await markReadApi(id)
    await handleRefreshUnread()
  } catch (e) {
    console.error(e)
  }
}

const handleMarkAllRead = async () => {
  try {
    await markAllReadApi()
    await handleRefreshUnread()
    message.success('已全部标记为已读')
  } catch (e) {
    console.error(e)
  }
}

const formatTime = (time) => {
  const d = new Date(time)
  return d.toLocaleString('zh-CN')
}

onMounted(async () => {
  activeMenu.value = route.path.split('/').slice(1).join('.')
  try {
    await handleRefreshUnread()
  } catch (e) {
    console.error(e)
  }
})
</script>

<style lang="scss" scoped>
.main-layout {
  height: 100vh;
  min-height: 100vh;
}

.layout-sider {
  background: #ffffff !important;
}

.logo-area {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 64px;
  padding: 0 20px;
  border-bottom: 1px solid #f1f5f9;
  cursor: pointer;

  .logo-icon {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
    color: #fff;
    font-weight: 700;
    font-size: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .logo-text {
    font-size: 20px;
    font-weight: 700;
    color: #1e293b;
    letter-spacing: 2px;
  }
}

.team-selector {
  padding: 16px 12px;
  border-bottom: 1px solid #f1f5f9;

  .team-box {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 10px 12px;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.2s;
    background: #f8fafc;

    &:hover {
      background: #eff6ff;
    }

    .team-info {
      flex: 1;
      min-width: 0;

      .team-name {
        font-size: 14px;
        font-weight: 600;
        color: #1e293b;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }

      .team-role {
        font-size: 12px;
        color: #64748b;
        margin-top: 2px;
      }
    }
  }
}

.side-menu {
  border: none !important;
  padding: 8px !important;
}

.layout-header {
  background: #ffffff !important;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.header-left {
  flex: 1;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-box {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: #f8fafc;
  }

  .user-info {
    text-align: left;

    .user-name {
      font-size: 14px;
      font-weight: 600;
      color: #1e293b;
      line-height: 1.2;
    }

    .user-email {
      font-size: 12px;
      color: #94a3b8;
      margin-top: 2px;
      max-width: 140px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
}

.layout-content {
  padding: 20px 24px;
  background: #f5f7fa;
}

.notification-panel {
  width: 360px;
  max-height: 420px;

  .notification-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 600;
    color: #1e293b;
  }

  .notification-list {
    max-height: 320px;
    overflow-y: auto;
  }

  .notification-item {
    padding: 12px;
    border-radius: 8px;
    cursor: pointer;
    margin-bottom: 4px;
    transition: background 0.2s;

    &:hover {
      background: #f8fafc;
    }

    &.unread {
      background: #eff6ff;

      &:hover {
        background: #dbeafe;
      }
    }

    .notif-title {
      font-size: 14px;
      font-weight: 500;
      color: #1e293b;
    }

    .notif-content {
      font-size: 13px;
      color: #64748b;
      margin-top: 4px;
    }

    .notif-time {
      font-size: 11px;
      color: #94a3b8;
      margin-top: 6px;
    }
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
