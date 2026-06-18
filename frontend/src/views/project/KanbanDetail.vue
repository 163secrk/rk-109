<template>
  <div class="page-card kanban-page">
    <div class="page-header">
      <div class="header-left">
        <n-button text @click="goBack">
          <template #icon>
            <n-icon><ArrowBackOutline /></n-icon>
          </template>
          返回
        </n-button>
        <n-select
          v-model:value="currentProjectId"
          :options="projectOptions"
          style="width: 240px; margin-left: 16px"
          @update:value="handleProjectChange"
        />
      </div>
      <n-button type="primary" :disabled="!currentProjectId" @click="showCreateTaskDrawer = true">
        <template #icon>
          <n-icon><AddOutline /></n-icon>
        </template>
        新建任务
      </n-button>
    </div>

    <div v-if="!currentProjectId" class="empty-project">
      <n-empty description="请先选择一个项目" />
    </div>

    <div v-else class="kanban-board">
      <div
        v-for="col in columns"
        :key="col.key"
        class="kanban-col"
        :class="{ 'drag-over': dragOverCol === col.key }"
        @dragover.prevent="handleDragOver(col.key)"
        @dragleave="handleDragLeave"
        @drop="handleDrop(col.key)"
      >
        <div class="col-header" :style="{ borderLeftColor: col.color }">
          <div class="col-title">
            <span class="col-dot" :style="{ backgroundColor: col.color }"></span>
            {{ col.label }}
          </div>
          <n-tag size="small" round type="default">{{ getTasksByStatus(col.key).length }}</n-tag>
        </div>

        <div class="col-body">
          <div
            v-for="task in getTasksByStatus(col.key)"
            :key="task.id"
            class="task-card"
            draggable="true"
            @dragstart="handleDragStart(task)"
            @dragend="handleDragEnd"
            @click="openTaskDetail(task)"
          >
            <div class="task-top">
              <n-tag
                size="small"
                round
                :type="priorityTagType(task.priority)"
                :bordered="false"
              >
                {{ priorityLabel(task.priority) }}
              </n-tag>
            </div>
            <div class="task-title">{{ task.title }}</div>
            <div class="task-bottom">
              <div class="task-assignee" v-if="task.assignee">
                <n-avatar round size="22" :style="{ backgroundColor: '#2563eb' }">
                  {{ task.assignee.name.charAt(0) }}
                </n-avatar>
                <span class="assignee-name">{{ task.assignee.name }}</span>
              </div>
              <div class="task-assignee unassigned" v-else>
                <n-avatar round size="22" style="background-color: #e2e8f0; color: #94a3b8">
                  ?
                </n-avatar>
                <span class="assignee-name">未指派</span>
              </div>
              <div v-if="task.due_date" class="task-due" :class="{ overdue: isOverdue(task.due_date) }">
                <n-icon size="14"><CalendarOutline /></n-icon>
                {{ formatDate(task.due_date) }}
              </div>
            </div>
          </div>

          <n-empty v-if="getTasksByStatus(col.key).length === 0" description="暂无任务" style="padding: 20px 0" />
        </div>
      </div>
    </div>

    <n-drawer v-model:show="showCreateTaskDrawer" :width="520" placement="right">
      <n-drawer-content title="新建任务" :closable="true">
        <n-form ref="createTaskFormRef" :model="createTaskForm" label-placement="top">
          <n-form-item label="任务标题" path="title" :rule="{ required: true, message: '请输入任务标题' }">
            <n-input v-model:value="createTaskForm.title" placeholder="请输入任务标题" />
          </n-form-item>
          <n-form-item label="任务描述">
            <n-input v-model:value="createTaskForm.description" type="textarea" :rows="4" placeholder="请输入任务描述" />
          </n-form-item>
          <n-form-item label="负责人">
            <n-select
              v-model:value="createTaskForm.assignee_id"
              :options="memberOptions"
              placeholder="请选择负责人"
              clearable
            />
          </n-form-item>
          <n-form-item label="优先级">
            <n-radio-group v-model:value="createTaskForm.priority">
              <n-space>
                <n-radio value="high">
                  <n-tag size="small" round type="error" :bordered="false">高</n-tag>
                </n-radio>
                <n-radio value="medium">
                  <n-tag size="small" round type="warning" :bordered="false">中</n-tag>
                </n-radio>
                <n-radio value="low">
                  <n-tag size="small" round type="default" :bordered="false">低</n-tag>
                </n-radio>
              </n-space>
            </n-radio-group>
          </n-form-item>
          <n-form-item label="截止日期">
            <n-date-picker
              v-model:value="createTaskForm.due_date"
              type="date"
              value-format="yyyy-MM-dd HH:mm:ss"
              :min-date="minDate"
              placeholder="请选择截止日期"
              style="width: 100%"
            />
          </n-form-item>
        </n-form>
        <template #footer>
          <n-space justify="end">
            <n-button @click="showCreateTaskDrawer = false">取消</n-button>
            <n-button type="primary" :loading="creatingTask" @click="handleCreateTask">创建</n-button>
          </n-space>
        </template>
      </n-drawer-content>
    </n-drawer>

    <n-drawer v-model:show="showTaskDetailDrawer" :width="640" placement="right">
      <n-drawer-content v-if="currentTaskDetail" :title="currentTaskDetail.task.title" :closable="true">
        <div class="task-detail">
          <n-form :model="editTaskForm" label-placement="top">
            <n-form-item label="任务标题">
              <n-input v-model:value="editTaskForm.title" placeholder="任务标题" />
            </n-form-item>
            <n-form-item label="任务描述">
              <n-input v-model:value="editTaskForm.description" type="textarea" :rows="3" placeholder="任务描述" />
            </n-form-item>
            <n-space :size="16" style="width: 100%">
              <n-form-item label="状态" style="flex: 1">
                <n-select
                  v-model:value="editTaskForm.status"
                  :options="statusOptions"
                  style="width: 100%"
                />
              </n-form-item>
              <n-form-item label="优先级" style="flex: 1">
                <n-select
                  v-model:value="editTaskForm.priority"
                  :options="priorityOptions"
                  style="width: 100%"
                />
              </n-form-item>
            </n-space>
            <n-space :size="16" style="width: 100%">
              <n-form-item label="负责人" style="flex: 1">
                <n-select
                  v-model:value="editTaskForm.assignee_id"
                  :options="memberOptions"
                  placeholder="请选择负责人"
                  clearable
                  style="width: 100%"
                />
              </n-form-item>
              <n-form-item label="截止日期" style="flex: 1">
                <n-date-picker
                  v-model:value="editTaskForm.due_date"
                  type="date"
                  value-format="yyyy-MM-dd HH:mm:ss"
                  :min-date="minDate"
                  placeholder="请选择截止日期"
                  style="width: 100%"
                />
              </n-form-item>
            </n-space>
          </n-form>

          <n-space justify="end" style="margin-bottom: 20px">
            <n-button type="primary" :loading="updatingTask" @click="handleUpdateTask">保存修改</n-button>
          </n-space>

          <n-divider style="margin: 16px 0" />

          <n-tabs type="line" animated>
            <n-tab-pane name="activity" tab="动态">
              <n-timeline>
                <n-timeline-item
                  v-for="act in sortedActivities"
                  :key="act.id"
                  :type="activityType(act.action)"
                >
                  <template #title>
                    <div class="activity-title">
                      <n-avatar round size="22" style="background-color: #2563eb">
                        {{ act.user.name.charAt(0) }}
                      </n-avatar>
                      <span class="activity-user">{{ act.user.name }}</span>
                      <span class="activity-action">{{ act.detail || actionLabel(act.action) }}</span>
                    </div>
                  </template>
                  <template #time>{{ formatTime(act.created_at) }}</template>
                </n-timeline-item>
                <n-empty v-if="sortedActivities.length === 0" description="暂无动态" style="padding: 20px 0" />
              </n-timeline>
            </n-tab-pane>
            <n-tab-pane name="comments" tab="评论">
              <div class="comment-section">
                <div class="comment-input-wrap">
                  <n-avatar round size="32" style="background-color: #2563eb">
                    {{ userStore.user?.name?.charAt(0) || 'U' }}
                  </n-avatar>
                  <div class="comment-input-box">
                    <n-mention
                      v-model:value="commentContent"
                      :options="mentionOptions"
                      placeholder="添加评论... 输入@提及成员"
                      type="textarea"
                      :autosize="{ minRows: 2, maxRows: 4 }"
                    />
                    <div class="comment-actions">
                      <n-button type="primary" size="small" :loading="addingComment" :disabled="!commentContent.trim()" @click="handleAddComment">
                        发送
                      </n-button>
                    </div>
                  </div>
                </div>
                <n-divider style="margin: 16px 0" />
                <div class="comment-list">
                  <div v-for="comment in currentTaskDetail.comments" :key="comment.id" class="comment-item">
                    <n-avatar round size="32" style="background-color: #2563eb">
                      {{ comment.user.name.charAt(0) }}
                    </n-avatar>
                    <div class="comment-body">
                      <div class="comment-header">
                        <span class="comment-user">{{ comment.user.name }}</span>
                        <span class="comment-time">{{ formatTime(comment.created_at) }}</span>
                      </div>
                      <div class="comment-content">{{ comment.content }}</div>
                    </div>
                  </div>
                  <n-empty v-if="currentTaskDetail.comments.length === 0" description="暂无评论" style="padding: 20px 0" />
                </div>
              </div>
            </n-tab-pane>
            <n-tab-pane name="attachments" tab="附件">
              <div class="attachment-section">
                <div
                  class="upload-dropzone"
                  :class="{ 'drag-over': isDragOver }"
                  @click="triggerFileInput"
                  @dragover.prevent="isDragOver = true"
                  @dragleave="isDragOver = false"
                  @drop.prevent="handleAttachmentDrop"
                >
                  <n-icon size="40" color="#94a3b8"><CloudUploadOutline /></n-icon>
                  <div class="upload-text">点击或拖拽文件到此处上传</div>
                  <div class="upload-hint">支持单个文件最大 50MB，支持多个附件同时添加</div>
                  <input
                    ref="fileInputRef"
                    type="file"
                    style="display: none"
                    multiple
                    @change="handleFileSelect"
                  />
                </div>

                <div v-if="uploadingFiles.length > 0" class="uploading-list">
                  <div v-for="item in uploadingFiles" :key="item.id" class="uploading-item">
                    <div class="uploading-info">
                      <n-icon size="18" color="#2563eb"><DocumentOutline /></n-icon>
                      <span class="uploading-name">{{ item.file.name }}</span>
                      <span class="uploading-size">{{ formatFileSize(item.file.size) }}</span>
                    </div>
                    <div class="uploading-progress">
                      <n-progress
                        type="line"
                        :percentage="item.progress"
                        :show-indicator="true"
                        :height="6"
                        :status="item.progress >= 100 ? 'success' : 'default'"
                      />
                    </div>
                    <n-button
                      v-if="item.progress < 100"
                      text
                      size="small"
                      type="error"
                      @click="cancelUpload(item.id)"
                    >
                      取消
                    </n-button>
                  </div>
                </div>

                <n-divider v-if="currentTaskDetail.attachments.length > 0 && (uploadingFiles.length > 0)" />

                <div v-if="currentTaskDetail.attachments.length > 0" class="attachment-list">
                  <div
                    v-for="att in currentTaskDetail.attachments"
                    :key="att.id"
                    class="attachment-item"
                  >
                    <div class="attachment-icon" :style="{ backgroundColor: getFileIconBg(att.file_name) }">
                      <n-icon size="20" color="#fff">
                        <component :is="getFileIcon(att.file_name)" />
                      </n-icon>
                    </div>
                    <div class="attachment-info" @click="downloadAttachment(att)">
                      <div class="attachment-name">{{ att.file_name }}</div>
                      <div class="attachment-meta">
                        <span>{{ formatFileSize(att.file_size) }}</span>
                        <span>·</span>
                        <span>{{ att.user.name }} 上传</span>
                        <span>·</span>
                        <span>{{ formatTime(att.created_at) }}</span>
                      </div>
                    </div>
                    <n-button
                      text
                      size="small"
                      type="error"
                      :loading="deletingAttachmentId === att.id"
                      @click="handleDeleteAttachment(att)"
                    >
                      删除
                    </n-button>
                  </div>
                </div>
              </div>
            </n-tab-pane>
          </n-tabs>
        </div>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '../../stores/user'
import { useApi } from '../../utils/request'
import {
  listProjectsApi,
  listTasksApi,
  createTaskApi,
  getTaskApi,
  updateTaskApi,
  addTaskCommentApi,
  uploadTaskAttachmentApi,
  deleteTaskAttachmentApi,
} from '../../api/project'
import { getTeamMembersApi } from '../../api/auth'
import {
  AddOutline,
  ArrowBackOutline,
  CalendarOutline,
  CloudUploadOutline,
  DocumentOutline,
  ImageOutline,
  VideocamOutline,
  MusicalNotesOutline,
  ArchiveOutline,
} from '@vicons/ionicons5'
import { NIcon } from 'naive-ui'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const { message, handleError, dialog } = useApi()

const projects = ref([])
const tasks = ref([])
const teamMembers = ref([])
const currentProjectId = ref(null)
const showCreateTaskDrawer = ref(false)
const showTaskDetailDrawer = ref(false)
const createTaskFormRef = ref(null)
const creatingTask = ref(false)
const updatingTask = ref(false)
const addingComment = ref(false)
const currentTaskDetail = ref(null)
const commentContent = ref('')
const dragOverCol = ref(null)
const draggingTask = ref(null)
const fileInputRef = ref(null)
const isDragOver = ref(false)
const uploadingFiles = ref([])
const deletingAttachmentId = ref(null)
const uploadIdCounter = ref(0)
const pendingUploads = new Map()

const columns = [
  { key: 'todo', label: '待办', color: '#94a3b8' },
  { key: 'in_progress', label: '进行中', color: '#2563eb' },
  { key: 'done', label: '已完成', color: '#16a34a' },
]

const statusOptions = [
  { label: '待办', value: 'todo' },
  { label: '进行中', value: 'in_progress' },
  { label: '已完成', value: 'done' },
]

const priorityOptions = [
  { label: '高', value: 'high' },
  { label: '中', value: 'medium' },
  { label: '低', value: 'low' },
]

const projectOptions = computed(() =>
  projects.value.map((p) => ({ label: p.name, value: p.id }))
)

const memberOptions = computed(() =>
  teamMembers.value.map((m) => ({ label: m.user.name, value: m.user.id }))
)

const mentionOptions = computed(() =>
  teamMembers.value.map((m) => ({
    label: m.user.name,
    value: m.user.name,
  }))
)

const sortedActivities = computed(() => {
  if (!currentTaskDetail.value) return []
  return [...currentTaskDetail.value.activities].sort(
    (a, b) => new Date(b.created_at) - new Date(a.created_at)
  )
})

const minDate = computed(() => {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return today.getTime()
})

const formatDateForPicker = (date) => {
  if (!date) return null
  const d = new Date(date)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} 00:00:00`
}

const createTaskForm = reactive({
  title: '',
  description: '',
  priority: 'medium',
  assignee_id: null,
  due_date: null,
})

const editTaskForm = reactive({
  title: '',
  description: '',
  status: 'todo',
  priority: 'medium',
  assignee_id: null,
  due_date: null,
})

const getTasksByStatus = (status) => {
  return tasks.value.filter((t) => t.status === status)
}

const priorityLabel = (p) => {
  const map = { high: '高', medium: '中', low: '低' }
  return map[p] || p
}

const priorityTagType = (p) => {
  const map = { high: 'error', medium: 'warning', low: 'default' }
  return map[p] || 'default'
}

const isOverdue = (date) => {
  if (!date) return false
  return new Date(date) < new Date()
}

const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

const formatTime = (date) => {
  if (!date) return ''
  const d = new Date(date)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const actionLabel = (action) => {
  const map = {
    create: '创建了任务',
    update: '更新了任务',
    comment: '添加了评论',
  }
  return map[action] || action
}

const activityType = (action) => {
  const map = {
    create: 'success',
    update: 'info',
    comment: 'warning',
    upload: 'success',
    delete_attachment: 'error',
  }
  return map[action] || 'default'
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(size < 10 && unitIndex > 0 ? 1 : 0)} ${units[unitIndex]}`
}

const getFileExt = (filename) => {
  const idx = filename.lastIndexOf('.')
  return idx >= 0 ? filename.substring(idx + 1).toLowerCase() : ''
}

const getFileIcon = (filename) => {
  const ext = getFileExt(filename)
  const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico']
  const videoExts = ['mp4', 'avi', 'mov', 'wmv', 'mkv', 'flv', 'webm']
  const audioExts = ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a']
  const archiveExts = ['zip', 'rar', '7z', 'tar', 'gz', 'bz2']
  if (imageExts.includes(ext)) return ImageOutline
  if (videoExts.includes(ext)) return VideocamOutline
  if (audioExts.includes(ext)) return MusicalNotesOutline
  if (archiveExts.includes(ext)) return ArchiveOutline
  return DocumentOutline
}

const getFileIconBg = (filename) => {
  const ext = getFileExt(filename)
  const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'ico']
  const videoExts = ['mp4', 'avi', 'mov', 'wmv', 'mkv', 'flv', 'webm']
  const audioExts = ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a']
  const archiveExts = ['zip', 'rar', '7z', 'tar', 'gz', 'bz2']
  if (imageExts.includes(ext)) return '#f97316'
  if (videoExts.includes(ext)) return '#8b5cf6'
  if (audioExts.includes(ext)) return '#10b981'
  if (archiveExts.includes(ext)) return '#f59e0b'
  return '#3b82f6'
}

const goBack = () => {
  router.push('/project/kanban')
}

const fetchProjects = async () => {
  try {
    const res = await listProjectsApi()
    projects.value = res
  } catch (e) {
    handleError(e, '获取项目列表失败')
  }
}

const fetchTeamMembers = async () => {
  try {
    const teamId = userStore.currentTeam?.id
    if (teamId) {
      const res = await getTeamMembersApi(teamId)
      teamMembers.value = res
    }
  } catch (e) {
    console.error(e)
  }
}

const fetchTasks = async (projectId) => {
  if (!projectId) return
  try {
    const res = await listTasksApi(projectId)
    tasks.value = res
  } catch (e) {
    handleError(e, '获取任务列表失败')
  }
}

const handleProjectChange = async (projectId) => {
  if (projectId) {
    router.push(`/project/kanban/${projectId}`)
  }
  await fetchTasks(projectId)
}

const resetCreateTaskForm = () => {
  createTaskForm.title = ''
  createTaskForm.description = ''
  createTaskForm.priority = 'medium'
  createTaskForm.assignee_id = null
  createTaskForm.due_date = null
}

const handleCreateTask = async () => {
  try {
    await createTaskFormRef.value?.validate()
  } catch (e) {
    return
  }
  creatingTask.value = true
  try {
    const payload = {
      project_id: currentProjectId.value,
      ...createTaskForm,
    }
    await createTaskApi(payload)
    message.success('创建成功')
    showCreateTaskDrawer.value = false
    resetCreateTaskForm()
    await fetchTasks(currentProjectId.value)
  } catch (e) {
    handleError(e, '创建失败')
  } finally {
    creatingTask.value = false
  }
}

const openTaskDetail = async (task) => {
  try {
    const res = await getTaskApi(task.id)
    currentTaskDetail.value = res
    editTaskForm.title = res.task.title
    editTaskForm.description = res.task.description
    editTaskForm.status = res.task.status
    editTaskForm.priority = res.task.priority
    editTaskForm.assignee_id = res.task.assignee?.id || null
    editTaskForm.due_date = formatDateForPicker(res.task.due_date)
    commentContent.value = ''
    showTaskDetailDrawer.value = true
  } catch (e) {
    handleError(e, '获取任务详情失败')
  }
}

const handleUpdateTask = async () => {
  if (!currentTaskDetail.value) return
  updatingTask.value = true
  try {
    await updateTaskApi(currentTaskDetail.value.task.id, editTaskForm)
    message.success('保存成功')
    await fetchTasks(currentProjectId.value)
    const res = await getTaskApi(currentTaskDetail.value.task.id)
    currentTaskDetail.value = res
  } catch (e) {
    handleError(e, '保存失败')
  } finally {
    updatingTask.value = false
  }
}

const handleAddComment = async () => {
  if (!currentTaskDetail.value || !commentContent.value.trim()) return
  addingComment.value = true
  try {
    await addTaskCommentApi(currentTaskDetail.value.task.id, {
      content: commentContent.value,
      mentions: '',
    })
    message.success('发送成功')
    commentContent.value = ''
    const res = await getTaskApi(currentTaskDetail.value.task.id)
    currentTaskDetail.value = res
  } catch (e) {
    handleError(e, '发送失败')
  } finally {
    addingComment.value = false
  }
}

const handleDragStart = (task) => {
  draggingTask.value = task
}

const handleDragEnd = () => {
  draggingTask.value = null
  dragOverCol.value = null
}

const handleDragOver = (colKey) => {
  dragOverCol.value = colKey
}

const handleDragLeave = () => {
  dragOverCol.value = null
}

const handleDrop = async (colKey) => {
  if (!draggingTask.value || draggingTask.value.status === colKey) {
    dragOverCol.value = null
    return
  }
  try {
    await updateTaskApi(draggingTask.value.id, { status: colKey })
    message.success('状态已更新')
    await fetchTasks(currentProjectId.value)
  } catch (e) {
    handleError(e, '更新失败')
  } finally {
    dragOverCol.value = null
    draggingTask.value = null
  }
}

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const handleFileSelect = (e) => {
  const files = Array.from(e.target.files || [])
  if (files.length > 0) {
    startUploadFiles(files)
  }
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

const handleAttachmentDrop = (e) => {
  isDragOver.value = false
  const files = Array.from(e.dataTransfer?.files || [])
  if (files.length > 0) {
    startUploadFiles(files)
  }
}

const startUploadFiles = (files) => {
  if (!currentTaskDetail.value) {
    message.error('请先选择任务')
    return
  }
  const maxSize = 50 * 1024 * 1024
  files.forEach((file) => {
    if (file.size > maxSize) {
      message.error(`文件 ${file.name} 超过 50MB 限制`)
      return
    }
    startSingleUpload(file)
  })
}

const startSingleUpload = async (file) => {
  const uploadId = ++uploadIdCounter.value
  const uploadItem = {
    id: uploadId,
    file,
    progress: 0,
    cancelled: false,
  }
  uploadingFiles.value.push(uploadItem)

  try {
    const taskId = currentTaskDetail.value.task.id
    const res = await uploadTaskAttachmentApi(taskId, file, (percent) => {
      if (!uploadItem.cancelled) {
        uploadItem.progress = percent
      }
    })
    uploadItem.progress = 100
    message.success(`文件 ${file.name} 上传成功`)
    setTimeout(() => {
      uploadingFiles.value = uploadingFiles.value.filter((f) => f.id !== uploadId)
    }, 800)
    const detail = await getTaskApi(taskId)
    currentTaskDetail.value = detail
  } catch (e) {
    if (!uploadItem.cancelled) {
      handleError(e, `文件 ${file.name} 上传失败`)
    }
    uploadingFiles.value = uploadingFiles.value.filter((f) => f.id !== uploadId)
  }
}

const cancelUpload = (uploadId) => {
  const item = uploadingFiles.value.find((f) => f.id === uploadId)
  if (item) {
    item.cancelled = true
    uploadingFiles.value = uploadingFiles.value.filter((f) => f.id !== uploadId)
  }
}

const downloadAttachment = (att) => {
  const url = `/uploads/${att.file_path}`
  const a = document.createElement('a')
  a.href = url
  a.download = att.file_name
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

const handleDeleteAttachment = (att) => {
  if (!currentTaskDetail.value) return
  dialog.warning({
    title: '确认删除',
    content: `确定要删除附件 "${att.file_name}" 吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      deletingAttachmentId.value = att.id
      try {
        await deleteTaskAttachmentApi(currentTaskDetail.value.task.id, att.id)
        message.success('删除成功')
        const res = await getTaskApi(currentTaskDetail.value.task.id)
        currentTaskDetail.value = res
      } catch (e) {
        handleError(e, '删除失败')
      } finally {
        deletingAttachmentId.value = null
      }
    },
  })
}

onMounted(async () => {
  await fetchProjects()
  await fetchTeamMembers()
  const pid = route.params.projectId
  if (pid) {
    currentProjectId.value = Number(pid)
    await fetchTasks(currentProjectId.value)
  }
})

watch(
  () => route.params.projectId,
  (newPid) => {
    if (newPid) {
      currentProjectId.value = Number(newPid)
      fetchTasks(currentProjectId.value)
    }
  }
)
</script>

<style lang="scss" scoped>
.kanban-page {
  min-height: calc(100vh - 140px);
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-left {
  display: flex;
  align-items: center;
}

.empty-project {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.kanban-board {
  display: flex;
  gap: 16px;
  flex: 1;
  min-height: 0;
  overflow-x: auto;
  padding-bottom: 8px;
}

.kanban-col {
  flex: 1;
  min-width: 280px;
  max-width: 360px;
  background: #f8fafc;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  transition: background 0.2s;

  &.drag-over {
    background: #eff6ff;
    outline: 2px dashed #2563eb;
    outline-offset: -2px;
  }
}

.col-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  border-left: 4px solid;
  background: #ffffff;
  border-radius: 12px 12px 0 0;

  .col-title {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
    font-size: 14px;
    font-weight: 600;
    color: #1f2937;
  }

  .col-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }
}

.col-body {
  flex: 1;
  padding: 12px;
  overflow-y: auto;
  min-height: 100px;
}

.task-card {
  background: #ffffff;
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 12px;
  cursor: pointer;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  border: 1px solid #e2e8f0;
  transition: all 0.2s;

  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    border-color: #cbd5e1;
    transform: translateY(-1px);
  }

  &:last-child {
    margin-bottom: 0;
  }
}

.task-top {
  margin-bottom: 10px;
}

.task-title {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  line-height: 1.5;
  margin-bottom: 12px;
  word-break: break-word;
}

.task-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.task-assignee {
  display: flex;
  align-items: center;
  gap: 6px;

  .assignee-name {
    font-size: 12px;
    color: #64748b;
  }

  &.unassigned {
    .assignee-name {
      color: #94a3b8;
    }
  }
}

.task-due {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #64748b;

  &.overdue {
    color: #dc2626;
  }
}

.task-detail {
  padding-right: 8px;
}

.activity-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;

  .activity-user {
    font-weight: 600;
    color: #1f2937;
  }

  .activity-action {
    color: #64748b;
  }
}

.comment-section {
  .comment-input-wrap {
    display: flex;
    gap: 12px;
  }

  .comment-input-box {
    flex: 1;

    .comment-actions {
      display: flex;
      justify-content: flex-end;
      margin-top: 8px;
    }
  }

  .comment-list {
    .comment-item {
      display: flex;
      gap: 12px;
      margin-bottom: 20px;

      &:last-child {
        margin-bottom: 0;
      }
    }

    .comment-body {
      flex: 1;
      background: #f8fafc;
      border-radius: 10px;
      padding: 12px;
    }

    .comment-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 6px;

      .comment-user {
        font-size: 13px;
        font-weight: 600;
        color: #1f2937;
      }

      .comment-time {
        font-size: 11px;
        color: #94a3b8;
      }
    }

    .comment-content {
      font-size: 13px;
      color: #475569;
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: break-word;
    }
  }
}

.attachment-section {
  .upload-dropzone {
    border: 2px dashed #cbd5e1;
    border-radius: 12px;
    padding: 40px 20px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    background: #fafbfc;

    &:hover,
    &.drag-over {
      border-color: #2563eb;
      background: #eff6ff;
    }

    .upload-text {
      font-size: 15px;
      font-weight: 500;
      color: #1f2937;
      margin-top: 12px;
    }

    .upload-hint {
      font-size: 12px;
      color: #94a3b8;
      margin-top: 6px;
    }
  }

  .uploading-list {
    margin-top: 16px;

    .uploading-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px;
      background: #f8fafc;
      border-radius: 8px;
      margin-bottom: 8px;

      &:last-child {
        margin-bottom: 0;
      }
    }

    .uploading-info {
      display: flex;
      align-items: center;
      gap: 8px;
      min-width: 0;
      flex: 1;

      .uploading-name {
        font-size: 13px;
        font-weight: 500;
        color: #1f2937;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        max-width: 200px;
      }

      .uploading-size {
        font-size: 12px;
        color: #94a3b8;
        flex-shrink: 0;
      }
    }

    .uploading-progress {
      width: 140px;
      flex-shrink: 0;
    }
  }

  .attachment-list {
    margin-top: 8px;

    .attachment-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px;
      border-radius: 8px;
      transition: background 0.2s;
      margin-bottom: 4px;

      &:hover {
        background: #f8fafc;
      }

      &:last-child {
        margin-bottom: 0;
      }
    }

    .attachment-icon {
      width: 44px;
      height: 44px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .attachment-info {
      flex: 1;
      min-width: 0;
      cursor: pointer;

      .attachment-name {
        font-size: 14px;
        font-weight: 500;
        color: #1f2937;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        margin-bottom: 4px;
      }

      .attachment-meta {
        font-size: 12px;
        color: #94a3b8;
        display: flex;
        align-items: center;
        gap: 6px;
      }
    }
  }
}
</style>
