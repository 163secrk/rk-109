import { defineStore } from 'pinia'
import { loginApi, registerApi, getMeApi, getMenusApi, getPermissionsApi, switchTeamApi, getUnreadCountApi } from '../api/auth'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('zhihui_token') || '',
    user: JSON.parse(localStorage.getItem('zhihui_user') || 'null'),
    currentTeam: null,
    currentRole: null,
    teams: [],
    menus: [],
    permissions: [],
    unreadCount: 0,
  }),
  getters: {
    isLoggedIn: (state) => !!state.token,
  },
  actions: {
    async login(formData) {
      const res = await loginApi(formData)
      this.setToken(res.access_token)
      this.setUser(res.user)
      return res
    },
    async register(formData) {
      const res = await registerApi(formData)
      this.setToken(res.access_token)
      this.setUser(res.user)
      return res
    },
    setToken(token) {
      this.token = token
      localStorage.setItem('zhihui_token', token)
    },
    setUser(user) {
      this.user = user
      localStorage.setItem('zhihui_user', JSON.stringify(user))
    },
    async fetchMe() {
      try {
        const res = await getMeApi()
        this.user = res.user
        this.currentTeam = res.current_team
        this.currentRole = res.current_role
        this.teams = res.teams
        localStorage.setItem('zhihui_user', JSON.stringify(res.user))
      } catch (e) {
        console.error('获取用户信息失败', e)
      }
    },
    async fetchMenus(teamId) {
      try {
        const res = await getMenusApi(teamId)
        this.menus = res
      } catch (e) {
        console.error('获取菜单失败', e)
      }
    },
    async fetchPermissions(teamId) {
      try {
        const res = await getPermissionsApi(teamId)
        this.permissions = res.permissions
      } catch (e) {
        console.error('获取权限失败', e)
      }
    },
    async switchTeam(teamId) {
      const res = await switchTeamApi({ team_id: teamId })
      this.currentTeam = res.team
      this.currentRole = res.role
      this.permissions = res.permissions
      await this.fetchMenus(teamId)
      return res
    },
    async fetchUnreadCount() {
      try {
        const res = await getUnreadCountApi()
        this.unreadCount = res.unread_count
      } catch (e) {
        console.error('获取未读数失败', e)
      }
    },
    logout() {
      this.token = ''
      this.user = null
      this.currentTeam = null
      this.currentRole = null
      this.teams = []
      this.menus = []
      this.permissions = []
      this.unreadCount = 0
      localStorage.removeItem('zhihui_token')
      localStorage.removeItem('zhihui_user')
    },
  },
})
