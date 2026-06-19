import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/auth/Login.vue'),
    meta: { title: '登录 - 知汇', requiresAuth: false },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/auth/Register.vue'),
    meta: { title: '注册 - 知汇', requiresAuth: false },
  },
  {
    path: '/',
    component: () => import('../views/layout/MainLayout.vue'),
    meta: { requiresAuth: true },
    redirect: '/workspace/quadrant',
    children: [
      {
        path: 'workspace/quadrant',
        name: 'WorkspaceQuadrant',
        component: () => import('../views/workspace/Quadrant.vue'),
        meta: { title: '任务四象限 - 知汇', breadcrumb: ['我的工作台', '任务四象限'] },
      },
      {
        path: 'workspace/calendar',
        name: 'WorkspaceCalendar',
        component: () => import('../views/workspace/Calendar.vue'),
        meta: { title: '日历视图 - 知汇', breadcrumb: ['我的工作台', '日历视图'] },
      },
      {
        path: 'project/kanban',
        name: 'ProjectKanban',
        component: () => import('../views/project/Kanban.vue'),
        meta: { title: '项目看板 - 知汇', breadcrumb: ['项目管理', '项目看板'] },
      },
      {
        path: 'project/kanban/:projectId',
        name: 'ProjectKanbanDetail',
        component: () => import('../views/project/KanbanDetail.vue'),
        meta: { title: '看板详情 - 知汇', breadcrumb: ['项目管理', '项目看板', '看板详情'] },
      },
      {
        path: 'project/gantt',
        name: 'ProjectGantt',
        component: () => import('../views/project/Gantt.vue'),
        meta: { title: '甘特图 - 知汇', breadcrumb: ['项目管理', '甘特图'] },
      },
      {
        path: 'project/templates',
        name: 'ProjectTemplates',
        component: () => import('../views/project/Templates.vue'),
        meta: { title: '模板 - 知汇', breadcrumb: ['项目管理', '模板'] },
      },
      {
        path: 'document/knowledge',
        name: 'DocumentKnowledge',
        component: () => import('../views/document/Knowledge.vue'),
        meta: { title: '知识库 - 知汇', breadcrumb: ['文档协作', '知识库'] },
      },
      {
        path: 'document/mindmap',
        name: 'DocumentMindmap',
        component: () => import('../views/document/Mindmap.vue'),
        meta: { title: '思维导图 - 知汇', breadcrumb: ['文档协作', '思维导图'] },
      },
      {
        path: 'document/flowchart',
        name: 'DocumentFlowchart',
        component: () => import('../views/document/Flowchart.vue'),
        meta: { title: '流程图 - 知汇', breadcrumb: ['文档协作', '流程图'] },
      },
      {
        path: 'document/flowchart/:chartId',
        name: 'DocumentFlowchartEditor',
        component: () => import('../views/document/FlowchartEditor.vue'),
        meta: { title: '流程图编辑 - 知汇', breadcrumb: ['文档协作', '流程图', '编辑'] },
      },
      {
        path: 'team/chat',
        name: 'TeamChat',
        component: () => import('../views/team/Chat.vue'),
        meta: { title: '即时聊天 - 知汇', breadcrumb: ['团队沟通', '即时聊天'] },
      },
      {
        path: 'team/files',
        name: 'TeamFiles',
        component: () => import('../views/team/Files.vue'),
        meta: { title: '文件管理 - 知汇', breadcrumb: ['团队沟通', '文件管理'] },
      },
      {
        path: 'stats/dashboard',
        name: 'StatsDashboard',
        component: () => import('../views/stats/Dashboard.vue'),
        meta: { title: '数据概览 - 知汇', breadcrumb: ['统计看板', '数据概览'] },
      },
      {
        path: 'settings/members',
        name: 'SettingsMembers',
        component: () => import('../views/settings/Members.vue'),
        meta: { title: '成员管理 - 知汇', breadcrumb: ['团队设置', '成员管理'] },
      },
      {
        path: 'settings/info',
        name: 'SettingsInfo',
        component: () => import('../views/settings/Info.vue'),
        meta: { title: '团队信息 - 知汇', breadcrumb: ['团队设置', '团队信息'] },
      },
      {
        path: 'settings/profile',
        name: 'SettingsProfile',
        component: () => import('../views/settings/Profile.vue'),
        meta: { title: '个人设置 - 知汇', breadcrumb: ['个人设置'] },
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    redirect: '/',
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  if (to.meta.title) {
    document.title = to.meta.title
  }

  const userStore = useUserStore()

  if (to.meta.requiresAuth === false) {
    if (userStore.isLoggedIn && (to.name === 'Login' || to.name === 'Register')) {
      return next('/')
    }
    return next()
  }

  if (!userStore.isLoggedIn) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }

  if (!userStore.user || userStore.teams.length === 0) {
    try {
      await userStore.fetchMe()
    } catch (e) {
      userStore.logout()
      return next('/login')
    }
  }

  if (userStore.menus.length === 0) {
    await userStore.fetchMenus(userStore.currentTeam?.id)
    await userStore.fetchPermissions(userStore.currentTeam?.id)
    await userStore.fetchUnreadCount()
  }

  next()
})

export default router
