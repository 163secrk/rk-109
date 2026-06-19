<template>
  <div class="chat-page">
    <n-layout has-sider class="chat-layout">
      <n-layout-sider width="280" bordered class="sider-left">
        <div class="sider-header">
          <div class="sider-title">消息</div>
          <n-button
            quaternary
            circle
            size="small"
            @click="refreshSessions"
            :loading="chatStore.loadingSessions"
          >
            <template #icon>
              <n-icon size="18"><RefreshOutline /></n-icon>
            </template>
          </n-button>
        </div>

        <div class="sider-search">
          <n-input v-model:value="searchKeyword" placeholder="搜索会话" clearable>
            <template #prefix>
              <n-icon size="16" color="#94a3b8"><SearchOutline /></n-icon>
            </template>
          </n-input>
        </div>

        <div class="sessions-list" ref="sessionsListRef">
          <div v-if="filteredTeamSessions.length > 0" class="session-group">
            <div class="group-title">群聊</div>
            <div
              v-for="s in filteredTeamSessions"
              :key="s.id"
              class="session-item"
              :class="{ active: chatStore.activeSessionId === s.id }"
              @click="selectSession(s.id)"
            >
              <div class="session-avatar team-avatar">
                <n-icon size="20" color="#fff"><PeopleOutline /></n-icon>
              </div>
              <div class="session-info">
                <div class="session-name-row">
                  <span class="session-name">{{ s.name }}</span>
                  <n-badge
                    v-if="s.unread_count > 0"
                    :value="s.unread_count"
                    :max="99"
                    class="unread-badge"
                    type="error"
                  />
                </div>
                <div class="session-preview">
                  {{ s.last_message ? (s.last_message.sender_name ? s.last_message.sender_name + ': ' : '') + (s.last_message.content || '') : '暂无消息' }}
                </div>
              </div>
            </div>
          </div>

          <div v-if="filteredProjectSessions.length > 0" class="session-group">
            <div class="group-title">项目组</div>
            <div
              v-for="s in filteredProjectSessions"
              :key="s.id"
              class="session-item"
              :class="{ active: chatStore.activeSessionId === s.id }"
              @click="selectSession(s.id)"
            >
              <div class="session-avatar project-avatar">
                <n-icon size="20" color="#fff"><FolderOutline /></n-icon>
              </div>
              <div class="session-info">
                <div class="session-name-row">
                  <span class="session-name">{{ s.name }}</span>
                  <n-badge
                    v-if="s.unread_count > 0"
                    :value="s.unread_count"
                    :max="99"
                    class="unread-badge"
                    type="error"
                  />
                </div>
                <div class="session-preview">
                  {{ s.last_message ? (s.last_message.sender_name ? s.last_message.sender_name + ': ' : '') + (s.last_message.content || '') : '暂无消息' }}
                </div>
              </div>
            </div>
          </div>

          <div v-if="filteredPrivateSessions.length > 0" class="session-group">
            <div class="group-title">私聊</div>
            <div
              v-for="s in filteredPrivateSessions"
              :key="s.id"
              class="session-item"
              :class="{ active: chatStore.activeSessionId === s.id }"
              @click="selectSession(s.id)"
            >
              <div class="session-avatar private-avatar">
                {{ s.name?.charAt(0) || 'U' }}
              </div>
              <div class="session-info">
                <div class="session-name-row">
                  <span class="session-name">{{ s.name }}</span>
                  <n-badge
                    v-if="s.unread_count > 0"
                    :value="s.unread_count"
                    :max="99"
                    class="unread-badge"
                    type="error"
                  />
                </div>
                <div class="session-preview">
                  {{ s.last_message ? (s.last_message.sender_name ? s.last_message.sender_name + ': ' : '') + (s.last_message.content || '') : '暂无消息' }}
                </div>
              </div>
            </div>
          </div>

          <n-empty v-if="allFilteredSessions.length === 0" description="暂无会话" class="empty-sessions" />
        </div>
      </n-layout-sider>

      <n-layout class="chat-center">
        <div v-if="!chatStore.activeSession" class="chat-empty">
          <n-empty description="请选择一个会话开始聊天" />
        </div>

        <template v-else>
          <div class="chat-header">
            <div class="chat-header-left">
              <div class="chat-session-name">{{ chatStore.activeSession?.name }}</div>
              <div class="chat-session-meta">
                <n-icon size="14" color="#94a3b8"><PeopleOutline /></n-icon>
                <span>{{ chatStore.activeSession?.members_count || 0 }} 位成员</span>
                <n-tag
                  v-if="chatStore.wsConnected"
                  size="tiny"
                  type="success"
                  round
                  class="ws-tag"
                >
                  已连接
                </n-tag>
                <n-tag v-else size="tiny" type="warning" round class="ws-tag">
                  连接中
                </n-tag>
              </div>
            </div>
          </div>

          <div class="messages-area" ref="messagesAreaRef">
            <div v-if="chatStore.loadingMessages && chatStore.messages.length === 0" class="messages-loading">
              <n-spin size="small" />
            </div>

            <div v-else class="messages-list">
              <div
                v-for="(msg, index) in chatStore.messages"
                :key="msg.id"
                class="message-wrap"
                :class="{ 'is-self': isSelf(msg.sender_id) }"
              >
                <div v-if="shouldShowTime(index)" class="time-divider">
                  <span class="time-label">{{ formatMsgTime(msg.created_at) }}</span>
                </div>

                <div class="message-content">
                  <n-avatar
                    v-if="!isSelf(msg.sender_id)"
                    round
                    size="36"
                    class="msg-avatar"
                    :style="{ background: avatarColor(msg.sender_id) }"
                  >
                    {{ msg.sender?.name?.charAt(0) || 'U' }}
                  </n-avatar>

                  <div class="msg-bubble-wrap">
                    <div v-if="!isSelf(msg.sender_id)" class="msg-sender-name">
                      {{ msg.sender?.name || '用户' }}
                    </div>
                    <div
                      class="msg-bubble"
                      :class="{ 'bubble-self': isSelf(msg.sender_id), 'has-mention': hasMyMention(msg) }"
                    >
                      <span
                        v-for="(part, i) in parseMessageParts(msg)"
                        :key="i"
                        :class="{ 'mention-text': part.isMention }"
                      >{{ part.text }}</span>
                    </div>
                    <div class="msg-time" :class="{ 'text-right': isSelf(msg.sender_id) }">
                      {{ formatMsgTimeDetail(msg.created_at) }}
                    </div>
                  </div>

                  <n-avatar
                    v-if="isSelf(msg.sender_id)"
                    round
                    size="36"
                    class="msg-avatar"
                    :style="{ background: avatarColor(msg.sender_id) }"
                  >
                    {{ msg.sender?.name?.charAt(0) || userStore.user?.name?.charAt(0) || 'U' }}
                  </n-avatar>
                </div>
              </div>

              <div ref="bottomAnchorRef"></div>
            </div>
          </div>

          <div class="input-area">
            <div class="mention-bar" v-if="sessionMembersForMention.length > 0">
              <span class="mention-tip">快速@：</span>
              <n-tag
                v-for="m in sessionMembersForMention"
                :key="m.id"
                size="small"
                round
                class="mention-tag"
                :class="{ disabled: m.id === userStore.user?.id }"
                @click="handleMentionClick(m)"
              >
                @{{ m.name }}
              </n-tag>
            </div>

            <div class="input-toolbar">
              <n-popover trigger="hover" placement="top" :show-arrow="false">
                <template #trigger>
                  <n-button quaternary size="small" @click="showMentionDropdown = !showMentionDropdown">
                    <template #icon>
                      <n-icon size="18" :color="showMentionDropdown ? '#2563eb' : '#64748b'"><AtOutline /></n-icon>
                    </template>
                    <span style="font-size: 13px">提及</span>
                  </n-button>
                </template>
                <span>@某人</span>
              </n-popover>

              <n-popover
                v-if="showMentionDropdown"
                :show="showMentionDropdown"
                trigger="manual"
                placement="bottom-start"
                :show-arrow="false"
                @update:show="(v) => (showMentionDropdown = v)"
              >
                <template #trigger>
                  <span></span>
                </template>
                <div class="mention-dropdown">
                  <div
                    v-for="m in sessionMembersForMention"
                    :key="m.id"
                    class="mention-dropdown-item"
                    :class="{ disabled: m.id === userStore.user?.id }"
                    @click="handleMentionClick(m)"
                  >
                    <n-avatar round size="28" :style="{ background: avatarColor(m.id) }">
                      {{ m.name?.charAt(0) || 'U' }}
                    </n-avatar>
                    <span class="mention-dropdown-name">{{ m.name }}</span>
                  </div>
                </div>
              </n-popover>
            </div>

            <div class="input-box-wrap">
              <n-input
                v-model:value="inputText"
                type="textarea"
                placeholder="输入消息，按 Enter 发送，Shift+Enter 换行"
                :autosize="{ minRows: 2, maxRows: 6 }"
                :disabled="chatStore.sendingMessage"
                @keydown="handleInputKeydown"
                class="chat-textarea"
              />
              <div class="send-row">
                <div class="input-hint">Enter 发送 · Shift+Enter 换行</div>
                <n-button
                  type="primary"
                  :disabled="!inputText.trim() || chatStore.sendingMessage"
                  :loading="chatStore.sendingMessage"
                  @click="handleSend"
                  size="small"
                >
                  发送
                </n-button>
              </div>
            </div>
          </div>
        </template>
      </n-layout>

      <n-layout-sider width="240" bordered class="sider-right" v-if="chatStore.activeSession">
        <div class="sider-right-header">
          <div class="sider-right-title">在线成员</div>
          <div class="sider-right-count">
            {{ onlineMembers.length }} / {{ chatStore.sessionMembers.length }} 在线
          </div>
        </div>

        <div class="members-list">
          <div class="member-section">
            <div class="member-section-title">
              <n-icon size="14" color="#10b981"><CheckmarkCircleOutline /></n-icon>
              <span>在线</span>
              <span class="member-count-tag">{{ onlineMembers.length }}</span>
            </div>
            <div
              v-for="m in onlineMembers"
              :key="'on-' + m.id"
              class="member-item"
              @click="handleMemberClick(m)"
            >
              <div class="member-avatar-wrap">
                <n-avatar round size="32" :style="{ background: avatarColor(m.id) }">
                  {{ m.name?.charAt(0) || 'U' }}
                </n-avatar>
                <div class="online-dot"></div>
              </div>
              <div class="member-info">
                <div class="member-name">{{ m.name }}</div>
                <div class="member-status">在线</div>
              </div>
            </div>
            <n-empty v-if="onlineMembers.length === 0" description="暂无在线成员" size="small" />
          </div>

          <div class="member-section" v-if="offlineMembers.length > 0">
            <div class="member-section-title offline">
              <n-icon size="14" color="#94a3b8"><EllipseOutline /></n-icon>
              <span>离线</span>
              <span class="member-count-tag">{{ offlineMembers.length }}</span>
            </div>
            <div
              v-for="m in offlineMembers"
              :key="'off-' + m.id"
              class="member-item offline"
              @click="handleMemberClick(m)"
            >
              <div class="member-avatar-wrap">
                <n-avatar round size="32" :style="{ background: avatarColor(m.id), opacity: 0.6 }">
                  {{ m.name?.charAt(0) || 'U' }}
                </n-avatar>
              </div>
              <div class="member-info">
                <div class="member-name">{{ m.name }}</div>
                <div class="member-status">离线</div>
              </div>
            </div>
          </div>
        </div>
      </n-layout-sider>
    </n-layout>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onBeforeUnmount, watch } from 'vue'
import { useChatStore } from '../../stores/chat'
import { useUserStore } from '../../stores/user'
import { useApi } from '../../utils/request'
import {
  PeopleOutline,
  SearchOutline,
  RefreshOutline,
  AtOutline,
  FolderOutline,
  CheckmarkCircleOutline,
  EllipseOutline,
} from '@vicons/ionicons5'

const chatStore = useChatStore()
const userStore = useUserStore()
const { message, handleError } = useApi()

const searchKeyword = ref('')
const inputText = ref('')
const showMentionDropdown = ref(false)
const currentMentions = ref([])

const sessionsListRef = ref(null)
const messagesAreaRef = ref(null)
const bottomAnchorRef = ref(null)

const avatarColors = [
  '#2563eb', '#7c3aed', '#db2777', '#dc2626',
  '#ea580c', '#ca8a04', '#16a34a', '#0891b2',
  '#4f46e5', '#9333ea',
]

const avatarColor = (id) => {
  const idx = (Number(id) || 0) % avatarColors.length
  return avatarColors[idx]
}

const isSelf = (senderId) => {
  return Number(senderId) === Number(userStore.user?.id)
}

const hasMyMention = (msg) => {
  if (!msg.mentions || msg.mentions.length === 0) return false
  const myId = Number(userStore.user?.id)
  return msg.mentions.some((id) => Number(id) === myId)
}

const filteredTeamSessions = computed(() => {
  const list = chatStore.sessionsByType.team
  if (!searchKeyword.value) return list
  const kw = searchKeyword.value.toLowerCase()
  return list.filter((s) => s.name.toLowerCase().includes(kw))
})

const filteredProjectSessions = computed(() => {
  const list = chatStore.sessionsByType.project
  if (!searchKeyword.value) return list
  const kw = searchKeyword.value.toLowerCase()
  return list.filter((s) => s.name.toLowerCase().includes(kw))
})

const filteredPrivateSessions = computed(() => {
  const list = chatStore.sessionsByType.private
  if (!searchKeyword.value) return list
  const kw = searchKeyword.value.toLowerCase()
  return list.filter((s) => s.name.toLowerCase().includes(kw))
})

const allFilteredSessions = computed(() => [
  ...filteredTeamSessions.value,
  ...filteredProjectSessions.value,
  ...filteredPrivateSessions.value,
])

const onlineMembers = computed(() => {
  return chatStore.sessionMembers.filter((m) => m.is_online)
})

const offlineMembers = computed(() => {
  return chatStore.sessionMembers.filter((m) => !m.is_online)
})

const sessionMembersForMention = computed(() => {
  return chatStore.sessionMembers.filter((m) => m.id !== userStore.user?.id)
})

const formatMsgTime = (time) => {
  if (!time) return ''
  const d = new Date(time)
  const now = new Date()
  const diff = (now - d) / 1000

  if (diff < 300) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (d.toDateString() === now.toDateString()) {
    return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (d.toDateString() === yesterday.toDateString()) {
    return '昨天 ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
}

const formatMsgTimeDetail = (time) => {
  if (!time) return ''
  const d = new Date(time)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}

const shouldShowTime = (index) => {
  if (index === 0) return true
  const cur = chatStore.messages[index]?.created_at
  const prev = chatStore.messages[index - 1]?.created_at
  if (!cur || !prev) return true
  const diff = (new Date(cur) - new Date(prev)) / 1000
  return diff > 300
}

const parseMessageParts = (msg) => {
  const content = msg.content || ''
  if (!msg.mentions || msg.mentions.length === 0) {
    return [{ text: content, isMention: false }]
  }
  const memberMap = {}
  for (const m of chatStore.sessionMembers) {
    memberMap[m.id] = m.name
  }
  const parts = []
  let remaining = content
  const mentionPattern = /@([^\s@]+)/g
  let lastIndex = 0
  let match

  while ((match = mentionPattern.exec(content)) !== null) {
    const name = match[1]
    const mentionedMember = chatStore.sessionMembers.find(
      (m) => m.name === name
    )
    if (mentionedMember) {
      if (match.index > lastIndex) {
        parts.push({
          text: content.slice(lastIndex, match.index),
          isMention: false,
        })
      }
      parts.push({
        text: match[0],
        isMention: Number(mentionedMember.id) === Number(userStore.user?.id),
      })
      lastIndex = match.index + match[0].length
    }
  }
  if (lastIndex < content.length) {
    parts.push({ text: content.slice(lastIndex), isMention: false })
  }
  if (parts.length === 0) {
    parts.push({ text: content, isMention: false })
  }
  return parts
}

const scrollToBottom = async () => {
  await nextTick()
  if (bottomAnchorRef.value) {
    bottomAnchorRef.value.scrollIntoView({ behavior: 'smooth', block: 'end' })
  } else if (messagesAreaRef.value) {
    messagesAreaRef.value.scrollTop = messagesAreaRef.value.scrollHeight
  }
}

const refreshSessions = async () => {
  try {
    await chatStore.fetchSessions()
    await chatStore.recalcTotalUnread()
    syncUnreadCountToHeader()
  } catch (e) {
    handleError(e, '刷新会话失败')
  }
}

const selectSession = async (sessionId) => {
  if (chatStore.activeSessionId === sessionId) return
  chatStore.setActiveSession(sessionId)
  currentMentions.value = []
  await Promise.all([
    chatStore.fetchMessages(sessionId),
    chatStore.fetchSessionMembers(sessionId),
  ])
  syncUnreadCountToHeader()
  await nextTick()
  scrollToBottom()
}

const handleInputKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}

const handleSend = async () => {
  const text = inputText.value.trim()
  if (!text || !chatStore.activeSessionId) return

  const mentions = extractMentionsFromText(text)

  try {
    await chatStore.sendMessage(chatStore.activeSessionId, text, mentions)
    inputText.value = ''
    currentMentions.value = []
    showMentionDropdown.value = false
    await nextTick()
    scrollToBottom()
  } catch (e) {
    handleError(e, '发送失败')
  }
}

const extractMentionsFromText = (text) => {
  const mentions = []
  const mentionPattern = /@([^\s@]+)/g
  let match
  while ((match = mentionPattern.exec(text)) !== null) {
    const name = match[1]
    const member = chatStore.sessionMembers.find((m) => m.name === name)
    if (member && !mentions.includes(member.id)) {
      mentions.push(member.id)
    }
  }
  return mentions
}

const handleMentionClick = (member) => {
  if (member.id === userStore.user?.id) return
  showMentionDropdown.value = false
  inputText.value = (inputText.value ? inputText.value + ' ' : '') + `@${member.name} `
  if (!currentMentions.value.includes(member.id)) {
    currentMentions.value.push(member.id)
  }
}

const handleMemberClick = async (member) => {
  if (member.id === userStore.user?.id) return
  try {
    const session = await chatStore.createPrivateSession(member.id)
    if (session) {
      await selectSession(session.id)
    }
  } catch (e) {
    handleError(e, '创建私聊失败')
  }
}

const syncUnreadCountToHeader = async () => {
  try {
    await userStore.fetchUnreadCount()
  } catch (e) {
    console.error(e)
  }
}

let refreshTimer = null

onMounted(async () => {
  try {
    await chatStore.fetchSessions()
    await chatStore.recalcTotalUnread()
    await userStore.fetchUnreadCount()

    if (chatStore.sessions.length > 0 && !chatStore.activeSessionId) {
      await selectSession(chatStore.sessions[0].id)
    }

    chatStore.connectWebSocket()

    refreshTimer = setInterval(async () => {
      try {
        await chatStore.fetchSessions()
        await chatStore.recalcTotalUnread()
        syncUnreadCountToHeader()
      } catch (e) {
        console.error(e)
      }
    }, 15000)
  } catch (e) {
    handleError(e, '加载聊天失败')
  }
})

watch(
  () => chatStore.messages.length,
  (newLen, oldLen) => {
    if (newLen > oldLen) {
      scrollToBottom()
    }
  }
)

watch(
  () => chatStore.totalUnread,
  () => {
    syncUnreadCountToHeader()
  }
)

onBeforeUnmount(() => {
  chatStore.disconnectWebSocket()
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style lang="scss" scoped>
.chat-page {
  width: 100%;
  min-height: calc(100vh - 140px);
}

.chat-layout {
  height: calc(100vh - 140px);
  min-height: 560px;
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
}

.sider-left {
  background: #fafbfc !important;
  border-right: 1px solid #eef2f7;
  display: flex;
  flex-direction: column;
}

.sider-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 16px 12px;
  border-bottom: 1px solid #eef2f7;

  .sider-title {
    font-size: 17px;
    font-weight: 700;
    color: #0f172a;
  }
}

.sider-search {
  padding: 12px;
}

.sessions-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px 16px;
}

.session-group {
  margin-top: 12px;

  &:first-child {
    margin-top: 4px;
  }
}

.group-title {
  font-size: 12px;
  color: #94a3b8;
  font-weight: 600;
  padding: 4px 10px 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s ease;
  margin-bottom: 2px;

  &:hover {
    background: #eef2f7;
  }

  &.active {
    background: #dbeafe;

    .session-name {
      color: #1d4ed8;
      font-weight: 600;
    }

    .session-preview {
      color: #64748b;
    }
  }
}

.session-avatar {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 600;
  font-size: 16px;

  &.team-avatar {
    background: linear-gradient(135deg, #2563eb, #60a5fa);
  }

  &.project-avatar {
    background: linear-gradient(135deg, #7c3aed, #a78bfa);
  }

  &.private-avatar {
    background: linear-gradient(135deg, #0891b2, #22d3ee);
  }
}

.session-info {
  flex: 1;
  min-width: 0;
}

.session-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
}

.session-name {
  font-size: 14px;
  color: #1e293b;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.unread-badge {
  flex-shrink: 0;
}

.session-preview {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 3px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.empty-sessions {
  padding: 40px 20px;
}

.chat-center {
  background: #fff;
  display: flex;
  flex-direction: column;
}

.chat-empty {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chat-header {
  height: 60px;
  padding: 0 20px;
  border-bottom: 1px solid #eef2f7;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.chat-header-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.chat-session-name {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
}

.chat-session-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748b;

  .ws-tag {
    margin-left: 8px;
  }
}

.messages-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px 24px;
  background: #f8fafc;
}

.messages-loading {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.messages-list {
  max-width: 900px;
  margin: 0 auto;
}

.time-divider {
  text-align: center;
  margin: 16px 0;

  .time-label {
    font-size: 11px;
    color: #94a3b8;
    background: #e2e8f0;
    padding: 3px 10px;
    border-radius: 20px;
  }
}

.message-wrap {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;

  &.is-self {
    align-items: flex-end;

    .message-content {
      flex-direction: row-reverse;
    }

    .msg-bubble-wrap {
      align-items: flex-end;
    }
  }
}

.message-content {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  max-width: 75%;
}

.msg-avatar {
  flex-shrink: 0;
  margin-top: 4px;
}

.msg-bubble-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 100%;
}

.msg-sender-name {
  font-size: 12px;
  color: #64748b;
  padding: 0 4px;
  font-weight: 500;
}

.msg-bubble {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  padding: 10px 14px;
  border-radius: 4px 14px 14px 14px;
  font-size: 14px;
  line-height: 1.55;
  color: #1e293b;
  word-break: break-word;
  white-space: pre-wrap;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);

  &.bubble-self {
    background: linear-gradient(135deg, #2563eb, #3b82f6);
    border-color: transparent;
    color: #fff;
    border-radius: 14px 4px 14px 14px;

    .mention-text {
      background: rgba(255, 255, 255, 0.25);
      color: #fff;
    }
  }

  &.has-mention {
    background: #fffbeb;
    border-color: #fbbf24;
  }
}

.mention-text {
  background: #dbeafe;
  color: #1d4ed8;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  margin: 0 1px;
}

.msg-time {
  font-size: 11px;
  color: #94a3b8;
  padding: 0 4px;

  &.text-right {
    text-align: right;
  }
}

.input-area {
  border-top: 1px solid #eef2f7;
  padding: 12px 20px 16px;
  background: #fff;
  flex-shrink: 0;
}

.mention-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 8px;

  .mention-tip {
    font-size: 12px;
    color: #64748b;
    flex-shrink: 0;
  }
}

.mention-tag {
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover:not(.disabled) {
    opacity: 0.8;
  }

  &.disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
}

.input-toolbar {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 8px;
  position: relative;
}

.mention-dropdown {
  min-width: 200px;
  max-height: 280px;
  overflow-y: auto;
}

.mention-dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  cursor: pointer;
  transition: background 0.15s ease;

  &:hover {
    background: #f1f5f9;
  }

  &.disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }
}

.mention-dropdown-name {
  font-size: 13px;
  color: #1e293b;
}

.input-box-wrap {
  background: #f8fafc;
  border-radius: 10px;
  padding: 10px;
  border: 1px solid #e2e8f0;
  transition: all 0.2s ease;

  &:focus-within {
    border-color: #3b82f6;
    background: #fff;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
}

.chat-textarea :deep(.n-input__textarea) {
  background: transparent;
  border: none;
  padding: 0;
}

.chat-textarea :deep(.n-input__textarea-el) {
  background: transparent;
  resize: none;
  font-size: 14px;
  line-height: 1.6;
}

.chat-textarea :deep(.n-input__border) {
  display: none;
}

.send-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 8px;
}

.input-hint {
  font-size: 11px;
  color: #94a3b8;
}

.sider-right {
  background: #fafbfc !important;
  border-left: 1px solid #eef2f7;
  display: flex;
  flex-direction: column;
}

.sider-right-header {
  padding: 16px;
  border-bottom: 1px solid #eef2f7;
  flex-shrink: 0;

  .sider-right-title {
    font-size: 15px;
    font-weight: 600;
    color: #0f172a;
  }

  .sider-right-count {
    font-size: 12px;
    color: #64748b;
    margin-top: 4px;
  }
}

.members-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.member-section {
  margin-bottom: 16px;
}

.member-section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #1e293b;
  padding: 0 6px 8px;

  &.offline {
    color: #64748b;
  }
}

.member-count-tag {
  font-size: 11px;
  color: #94a3b8;
  margin-left: auto;
  font-weight: 400;
}

.member-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s ease;

  &:hover {
    background: #eef2f7;
  }

  &.offline {
    opacity: 0.6;
  }
}

.member-avatar-wrap {
  position: relative;
  flex-shrink: 0;
}

.online-dot {
  position: absolute;
  right: -1px;
  bottom: -1px;
  width: 10px;
  height: 10px;
  background: #10b981;
  border: 2px solid #fff;
  border-radius: 50%;
}

.member-info {
  flex: 1;
  min-width: 0;
}

.member-name {
  font-size: 13px;
  color: #1e293b;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.member-status {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 2px;
}
</style>
