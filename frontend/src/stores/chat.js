import { defineStore } from 'pinia'
import {
  listChatSessionsApi,
  getChatMessagesApi,
  sendChatMessageApi,
  markSessionReadApi,
  getSessionMembersApi,
  getChatUnreadCountApi,
  createPrivateSessionApi,
  getTeamMembersApi,
} from '../api/chat'

export const useChatStore = defineStore('chat', {
  state: () => ({
    sessions: [],
    activeSessionId: null,
    messages: [],
    sessionMembers: [],
    teamMembers: [],
    loadingSessions: false,
    loadingMessages: false,
    sendingMessage: false,
    totalUnread: 0,
    ws: null,
    wsConnected: false,
    onlineUserIds: new Set(),
  }),
  getters: {
    activeSession: (state) => {
      return state.sessions.find((s) => s.id === state.activeSessionId) || null
    },
    sessionsByType: (state) => {
      const team = state.sessions.filter((s) => s.session_type === 'team')
      const project = state.sessions.filter((s) => s.session_type === 'project')
      const private_ = state.sessions.filter((s) => s.session_type === 'private')
      return { team, project, private: private_ }
    },
  },
  actions: {
    async fetchSessions() {
      this.loadingSessions = true
      try {
        const res = await listChatSessionsApi()
        this.sessions = res.sessions || []
        return this.sessions
      } finally {
        this.loadingSessions = false
      }
    },

    async fetchMessages(sessionId, page = 1, pageSize = 50) {
      this.loadingMessages = true
      try {
        const res = await getChatMessagesApi(sessionId, page, pageSize)
        if (page === 1) {
          this.messages = res.messages || []
        } else {
          this.messages = [...(res.messages || []), ...this.messages]
        }
        return res
      } finally {
        this.loadingMessages = false
      }
    },

    async sendMessage(sessionId, content, mentions = []) {
      this.sendingMessage = true
      try {
        const res = await sendChatMessageApi(sessionId, content, mentions)
        if (res.message && this.activeSessionId === sessionId) {
          const exists = this.messages.find((m) => m.id === res.message.id)
          if (!exists) {
            this.messages.push(res.message)
          }
        }
        this.updateSessionLastMessage(sessionId, res.message)
        return res.message
      } finally {
        this.sendingMessage = false
      }
    },

    updateSessionLastMessage(sessionId, message) {
      const session = this.sessions.find((s) => s.id === sessionId)
      if (session) {
        session.last_message = {
          content: message.content,
          sender_name: message.sender?.name || '',
          created_at: message.created_at,
        }
        session.updated_at = message.created_at
      }
      this.sortSessions()
    },

    sortSessions() {
      this.sessions.sort((a, b) => {
        const ta = a.last_message?.created_at || a.updated_at || ''
        const tb = b.last_message?.created_at || b.updated_at || ''
        return tb.localeCompare(ta)
      })
    },

    async markAsRead(sessionId) {
      const session = this.sessions.find((s) => s.id === sessionId)
      if (session) {
        session.unread_count = 0
      }
      try {
        await markSessionReadApi(sessionId)
      } catch (e) {
        console.error(e)
      }
      await this.recalcTotalUnread()
    },

    async fetchSessionMembers(sessionId) {
      try {
        const res = await getSessionMembersApi(sessionId)
        this.sessionMembers = res.members || []
        this.onlineUserIds = new Set(
          this.sessionMembers.filter((m) => m.is_online).map((m) => m.id)
        )
        return this.sessionMembers
      } catch (e) {
        console.error(e)
        return []
      }
    },

    async fetchTeamMembers(teamId) {
      try {
        const res = await getTeamMembersApi(teamId)
        this.teamMembers = res.members?.map((m) => m.user) || []
        return this.teamMembers
      } catch (e) {
        console.error(e)
        return []
      }
    },

    async createPrivateSession(userId) {
      const res = await createPrivateSessionApi(userId)
      if (res.session) {
        const exists = this.sessions.find((s) => s.id === res.session.id)
        if (!exists) {
          this.sessions.unshift(res.session)
        }
      }
      return res.session
    },

    async recalcTotalUnread() {
      try {
        const res = await getChatUnreadCountApi()
        this.totalUnread = res.total || 0
        if (res.sessions) {
          for (const item of res.sessions) {
            const s = this.sessions.find((x) => x.id === item.session_id)
            if (s) s.unread_count = item.unread_count
          }
        }
      } catch (e) {
        this.totalUnread = this.sessions.reduce(
          (sum, s) => sum + (s.unread_count || 0),
          0
        )
      }
    },

    setActiveSession(sessionId) {
      this.activeSessionId = sessionId
      if (sessionId) {
        this.markAsRead(sessionId)
      }
    },

    addIncomingMessage(message) {
      const sessionId = message.session_id
      if (this.activeSessionId === sessionId) {
        const exists = this.messages.find((m) => m.id === message.id)
        if (!exists) {
          this.messages.push(message)
        }
      }
      const session = this.sessions.find((s) => s.id === sessionId)
      if (session) {
        if (this.activeSessionId !== sessionId) {
          session.unread_count = (session.unread_count || 0) + 1
        }
        session.last_message = {
          content: message.content,
          sender_name: message.sender?.name || '',
          created_at: message.created_at,
        }
        session.updated_at = message.created_at
      }
      this.sortSessions()
      this.recalcTotalUnread()
    },

    connectWebSocket() {
      if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
        return
      }

      const token = localStorage.getItem('zhihui_token')
      if (!token) return

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const host = window.location.hostname
      const port = window.location.port || (window.location.protocol === 'https:' ? '443' : '80')
      const wsUrl = `${protocol}//${host}:${port}/api/team/ws/chat?token=${encodeURIComponent(token)}`

      try {
        this.ws = new WebSocket(wsUrl)

        this.ws.onopen = () => {
          this.wsConnected = true
          this._startHeartbeat()
        }

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            this._handleWsMessage(data)
          } catch (e) {
            console.error('WS parse error', e)
          }
        }

        this.ws.onclose = () => {
          this.wsConnected = false
          this._stopHeartbeat()
          setTimeout(() => {
            if (this.activeSessionId) {
              this.connectWebSocket()
            }
          }, 3000)
        }

        this.ws.onerror = () => {
          try {
            this.ws.close()
          } catch (e) {}
        }
      } catch (e) {
        console.error('WS connect error', e)
      }
    },

    disconnectWebSocket() {
      this._stopHeartbeat()
      if (this.ws) {
        try {
          this.ws.close()
        } catch (e) {}
        this.ws = null
      }
      this.wsConnected = false
    },

    _heartbeatTimer: null,

    _startHeartbeat() {
      this._stopHeartbeat()
      this._heartbeatTimer = setInterval(() => {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
          try {
            this.ws.send(JSON.stringify({ type: 'ping' }))
          } catch (e) {}
        }
      }, 30000)
    },

    _stopHeartbeat() {
      if (this._heartbeatTimer) {
        clearInterval(this._heartbeatTimer)
        this._heartbeatTimer = null
      }
    },

    _handleWsMessage(data) {
      switch (data.type) {
        case 'new_message':
          if (data.message) {
            this.addIncomingMessage(data.message)
          }
          break
        case 'user_online':
          if (data.user_id) {
            this.onlineUserIds.add(data.user_id)
            this.sessionMembers = this.sessionMembers.map((m) =>
              m.id === data.user_id ? { ...m, is_online: true } : m
            )
          }
          break
        case 'user_offline':
          if (data.user_id) {
            this.onlineUserIds.delete(data.user_id)
            this.sessionMembers = this.sessionMembers.map((m) =>
              m.id === data.user_id ? { ...m, is_online: false } : m
            )
          }
          break
        case 'pong':
          break
      }
    },
  },
})
