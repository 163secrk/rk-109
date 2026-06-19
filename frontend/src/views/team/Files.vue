<template>
  <div class="files-page">
    <div class="page-header">
      <div class="breadcrumb-area">
        <n-breadcrumb>
          <n-breadcrumb-item @click="navigateTo(null)">
            <span class="breadcrumb-root">全部文件</span>
          </n-breadcrumb-item>
          <n-breadcrumb-item
            v-for="(item, index) in breadcrumb"
            :key="item.id"
            @click="navigateTo(item.id)"
          >
            <span class="breadcrumb-link">{{ item.name }}</span>
          </n-breadcrumb-item>
        </n-breadcrumb>
      </div>
      <div class="header-actions">
        <n-input
          v-model:value="searchKeyword"
          placeholder="搜索文件或文件夹..."
          clearable
          size="medium"
          class="search-input"
          @input="handleSearch"
          @clear="handleClearSearch"
        >
          <template #prefix>
            <n-icon><SearchOutline /></n-icon>
          </template>
        </n-input>
        <n-space :size="8">
          <n-button type="primary" @click="showCreateFolder = true">
            <template #icon>
              <n-icon><AddOutline /></n-icon>
            </template>
            新建文件夹
          </n-button>
          <n-button type="success" @click="triggerUpload">
            <template #icon>
              <n-icon><CloudUploadOutline /></n-icon>
            </template>
            上传文件
          </n-button>
          <n-button-group size="small" class="view-toggle">
            <n-button
              :type="viewMode === 'grid' ? 'primary' : 'default'"
              @click="viewMode = 'grid'"
            >
              <n-icon><GridOutline /></n-icon>
            </n-button>
            <n-button
              :type="viewMode === 'list' ? 'primary' : 'default'"
              @click="viewMode = 'list'"
            >
              <n-icon><ListOutline /></n-icon>
            </n-button>
          </n-button-group>
        </n-space>
      </div>
    </div>

    <div v-if="searchMode" class="search-results-header">
      搜索结果：找到 {{ searchResult.folders.length }} 个文件夹，{{ searchResult.files.length }} 个文件
      <n-button text type="primary" size="small" @click="clearSearch">返回</n-button>
    </div>

    <div v-if="uploadTasks.length > 0" class="upload-panel">
      <div class="upload-panel-header">
        <span>上传任务 ({{ uploadTasks.filter(t => t.status !== 'done').length }} 个进行中)</span>
        <n-button text size="tiny" @click="clearDoneUploads">清除已完成</n-button>
      </div>
      <div v-for="task in uploadTasks" :key="task.id" class="upload-task">
        <div class="upload-task-info">
          <n-icon class="upload-icon" :color="getUploadIconColor(task.status)">
            <DocumentTextOutline v-if="task.status !== 'error'" />
            <AlertCircleOutline v-else />
          </n-icon>
          <span class="upload-task-name">{{ task.name }}</span>
          <span class="upload-task-size">{{ formatFileSize(task.size) }}</span>
        </div>
        <n-progress
          type="line"
          :percentage="task.progress"
          :status="getUploadProgressStatus(task.status)"
          :show-indicator="true"
          style="flex: 1; margin: 0 12px"
        />
        <span class="upload-task-status">{{ getUploadStatusText(task.status) }}</span>
      </div>
    </div>

    <div v-if="!searchMode" class="files-container">
      <div v-if="viewMode === 'grid'" class="grid-view">
        <div
          v-for="folder in folders"
          :key="'folder-' + folder.id"
          class="grid-item folder-item"
          @dblclick="openFolder(folder.id)"
          @click="selectedItem = { type: 'folder', data: folder }"
          :class="{ selected: selectedItem?.type === 'folder' && selectedItem?.data?.id === folder.id }"
        >
          <n-dropdown
            :options="getFolderMenuOptions(folder)"
            trigger="click"
            @select="(key) => handleFolderAction(key, folder)"
          >
            <div class="grid-card">
              <div class="folder-thumb">
                <n-icon size="64" color="#f59e0b"><FolderOutline /></n-icon>
              </div>
              <div class="grid-item-name" :title="folder.name">{{ folder.name }}</div>
              <div class="grid-item-meta">{{ formatTime(folder.created_at) }}</div>
            </div>
          </n-dropdown>
        </div>

        <div
          v-for="file in files"
          :key="'file-' + file.id"
          class="grid-item file-item"
          @dblclick="openFile(file)"
          @click="selectedItem = { type: 'file', data: file }"
          :class="{ selected: selectedItem?.type === 'file' && selectedItem?.data?.id === file.id }"
        >
          <n-dropdown
            :options="getFileMenuOptions(file)"
            trigger="click"
            @select="(key) => handleFileAction(key, file)"
          >
            <div class="grid-card">
              <div class="file-thumb">
                <img
                  v-if="file.file_type === 'image'"
                  :src="getFilePreviewUrl(file.file_path)"
                  class="thumb-image"
                  @error="($event) => ($event.target.style.display = 'none')"
                />
                <n-icon v-else size="56" :color="getFileIconColor(file.file_type)">
                  <component :is="getFileIcon(file.file_type)" />
                </n-icon>
              </div>
              <div class="grid-item-name" :title="file.name">{{ file.name }}</div>
              <div class="grid-item-meta">{{ formatFileSize(file.file_size) }}</div>
            </div>
          </n-dropdown>
        </div>
      </div>

      <div v-else class="list-view">
        <n-data-table
          :columns="listColumns"
          :data="listData"
          :pagination="false"
          :row-props="(row) => ({ onClick: () => handleRowClick(row) })"
          size="medium"
          class="files-table"
        >
          <template #empty>
            <n-empty description="暂无文件，点击右上角上传文件" />
          </template>
        </n-data-table>
      </div>
    </div>

    <div v-else class="search-results">
      <div v-if="searchResult.folders.length > 0" class="search-section">
        <div class="search-section-title">文件夹</div>
        <div class="grid-view">
          <div
            v-for="folder in searchResult.folders"
            :key="'sfolder-' + folder.id"
            class="grid-item folder-item"
            @dblclick="goToFolderInSearch(folder)"
          >
            <div class="grid-card">
              <div class="folder-thumb">
                <n-icon size="64" color="#f59e0b"><FolderOutline /></n-icon>
              </div>
              <div class="grid-item-name" :title="folder.name">{{ folder.name }}</div>
              <div class="grid-item-meta">{{ formatTime(folder.created_at) }}</div>
            </div>
          </div>
        </div>
      </div>
      <div v-if="searchResult.files.length > 0" class="search-section">
        <div class="search-section-title">文件</div>
        <div class="grid-view">
          <div
            v-for="file in searchResult.files"
            :key="'sfile-' + file.id"
            class="grid-item file-item"
            @dblclick="openFile(file)"
          >
            <div class="grid-card">
              <div class="file-thumb">
                <img
                  v-if="file.file_type === 'image'"
                  :src="getFilePreviewUrl(file.file_path)"
                  class="thumb-image"
                  @error="($event) => ($event.target.style.display = 'none')"
                />
                <n-icon v-else size="56" :color="getFileIconColor(file.file_type)">
                  <component :is="getFileIcon(file.file_type)" />
                </n-icon>
              </div>
              <div class="grid-item-name" :title="file.name">{{ file.name }}</div>
              <div class="grid-item-meta">{{ formatFileSize(file.file_size) }}</div>
            </div>
          </div>
        </div>
      </div>
      <n-empty v-if="searchResult.folders.length === 0 && searchResult.files.length === 0" description="未找到匹配的文件或文件夹" />
    </div>

    <n-modal v-model:show="showCreateFolder" preset="card" title="新建文件夹" style="width: 420px">
      <n-form ref="createFolderFormRef" :model="createFolderForm" :rules="createFolderRules">
        <n-form-item label="文件夹名称" path="name">
          <n-input v-model:value="createFolderForm.name" placeholder="请输入文件夹名称" maxlength="100" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateFolder = false">取消</n-button>
          <n-button type="primary" :loading="createFolderLoading" @click="handleCreateFolder">确定</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="showRenameModal" preset="card" title="重命名" style="width: 420px">
      <n-form ref="renameFormRef" :model="renameForm" :rules="renameRules">
        <n-form-item label="新名称" path="name">
          <n-input v-model:value="renameForm.name" placeholder="请输入新名称" maxlength="100" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showRenameModal = false">取消</n-button>
          <n-button type="primary" :loading="renameLoading" @click="handleRename">确定</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="showMoveModal" preset="card" title="移动到" style="width: 520px">
      <div class="move-modal-content">
        <div class="move-target-info">
          当前项：<strong>{{ moveTarget?.name }}</strong>
        </div>
        <n-tree
          :data="folderTreeData"
          :selected-keys="moveTargetFolderId ? [moveTargetFolderId] : []"
          :default-expand-all="true"
          block-line
          @update:selected-keys="handleMoveFolderSelect"
        />
      </div>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showMoveModal = false">取消</n-button>
          <n-button type="primary" :loading="moveLoading" @click="handleMove">确定移动</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="showPreviewModal" preset="card" :title="previewFile?.name" style="width: 80%; max-width: 1000px">
      <div v-if="previewFile" class="preview-content">
        <div v-if="previewFile.file_type === 'image'" class="image-preview">
          <img :src="getFilePreviewUrl(previewFile.file_path)" :alt="previewFile.name" />
        </div>
        <div v-else-if="previewFile.file_type === 'pdf'" class="pdf-preview">
          <iframe :src="getFilePreviewUrl(previewFile.file_path)" class="pdf-frame" />
        </div>
        <div v-else class="file-info-card">
          <div class="info-header">
            <n-icon size="80" :color="getFileIconColor(previewFile.file_type)">
              <component :is="getFileIcon(previewFile.file_type)" />
            </n-icon>
          </div>
          <n-descriptions :column="1" bordered size="large" class="info-desc">
            <n-descriptions-item label="文件名">{{ previewFile.name }}</n-descriptions-item>
            <n-descriptions-item label="类型">{{ getFileTypeLabel(previewFile.file_type) }}</n-descriptions-item>
            <n-descriptions-item label="大小">{{ formatFileSize(previewFile.file_size) }}</n-descriptions-item>
            <n-descriptions-item label="上传人">{{ previewFile.creator?.name || '-' }}</n-descriptions-item>
            <n-descriptions-item label="上传时间">{{ formatTime(previewFile.created_at) }}</n-descriptions-item>
            <n-descriptions-item label="MIME 类型">{{ previewFile.mime_type || '-' }}</n-descriptions-item>
          </n-descriptions>
          <div class="download-action">
            <n-button type="primary" size="large" @click="downloadFile(previewFile)">
              <template #icon>
                <n-icon><DownloadOutline /></n-icon>
              </template>
              下载文件
            </n-button>
          </div>
        </div>
      </div>
      <template #footer>
        <n-space justify="end">
          <n-button type="primary" @click="downloadFile(previewFile)">下载</n-button>
          <n-button @click="showPreviewModal = false">关闭</n-button>
        </n-space>
      </template>
    </n-modal>

    <input
      ref="fileInputRef"
      type="file"
      multiple
      style="display: none"
      @change="handleFileSelect"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, h, watch } from 'vue'
import { useApi } from '../../utils/request'
import {
  listFilesApi,
  createFolderApi,
  updateFolderApi,
  deleteFolderApi,
  uploadFilesApi,
  updateFileApi,
  deleteFileApi,
  getFileDownloadUrl,
  getFilePreviewUrl,
  searchFilesApi,
  getFolderTreeApi,
} from '../../api/files.js'
import {
  FolderOutline,
  AddOutline,
  CloudUploadOutline,
  GridOutline,
  ListOutline,
  SearchOutline,
  DocumentTextOutline,
  AlertCircleOutline,
  DownloadOutline,
  CreateOutline,
  MoveOutline,
  TrashOutline,
  EyeOutline,
  FileTrayFullOutline,
  FileTrayStackedOutline,
  VideocamOutline,
  MusicalNoteOutline,
  CodeSlashOutline,
  ArchiveOutline,
  HelpCircleOutline,
  DocumentOutline,
} from '@vicons/ionicons5'
import { NIcon, NButton } from 'naive-ui'

const { message, dialog, handleError } = useApi()

const folders = ref([])
const files = ref([])
const breadcrumb = ref([])
const currentFolderId = ref(null)
const viewMode = ref('grid')
const selectedItem = ref(null)
const searchKeyword = ref('')
const searchMode = ref(false)
const searchResult = ref({ folders: [], files: [] })
const searchTimer = ref(null)

const showCreateFolder = ref(false)
const createFolderForm = ref({ name: '' })
const createFolderLoading = ref(false)
const createFolderRules = {
  name: [{ required: true, message: '请输入文件夹名称', trigger: 'blur' }],
}

const showRenameModal = ref(false)
const renameTarget = ref(null)
const renameForm = ref({ name: '' })
const renameLoading = ref(false)
const renameRules = {
  name: [{ required: true, message: '请输入新名称', trigger: 'blur' }],
}

const showMoveModal = ref(false)
const moveTarget = ref(null)
const moveTargetType = ref(null)
const moveTargetFolderId = ref(null)
const moveLoading = ref(false)
const folderTreeData = ref([])

const showPreviewModal = ref(false)
const previewFile = ref(null)

const fileInputRef = ref(null)
const uploadTasks = ref([])

const fetchFiles = async () => {
  try {
    const params = {}
    if (currentFolderId.value) {
      params.folder_id = currentFolderId.value
    }
    const res = await listFilesApi(params)
    folders.value = res.folders || []
    files.value = res.files || []
    breadcrumb.value = res.breadcrumb || []
  } catch (e) {
    handleError(e, '加载文件列表失败')
  }
}

const navigateTo = (folderId) => {
  currentFolderId.value = folderId
  fetchFiles()
}

const openFolder = (folderId) => {
  currentFolderId.value = folderId
  fetchFiles()
}

const goToFolderInSearch = (folder) => {
  searchMode.value = false
  searchKeyword.value = ''
  currentFolderId.value = folder.parent_id
  fetchFiles()
  setTimeout(() => {
    navigateTo(folder.id)
  }, 100)
}

const triggerUpload = () => {
  fileInputRef.value?.click()
}

const handleFileSelect = (event) => {
  const selectedFiles = Array.from(event.target.files || [])
  if (selectedFiles.length === 0) return

  const params = {}
  if (currentFolderId.value) {
    params.folder_id = currentFolderId.value
  }

  selectedFiles.forEach((file) => {
    const taskId = Date.now() + Math.random()
    const task = {
      id: taskId,
      name: file.name,
      size: file.size,
      progress: 0,
      status: 'uploading',
      file: file,
    }
    uploadTasks.value.push(task)

    uploadFilesApi([file], params, (percent) => {
      const found = uploadTasks.value.find((t) => t.id === taskId)
      if (found) {
        found.progress = percent
      }
    })
      .then(() => {
        const found = uploadTasks.value.find((t) => t.id === taskId)
        if (found) {
          found.status = 'done'
          found.progress = 100
        }
        message.success(`${file.name} 上传成功`)
        fetchFiles()
      })
      .catch((e) => {
        const found = uploadTasks.value.find((t) => t.id === taskId)
        if (found) {
          found.status = 'error'
        }
        handleError(e, `${file.name} 上传失败`)
      })
  })

  event.target.value = ''
}

const clearDoneUploads = () => {
  uploadTasks.value = uploadTasks.value.filter((t) => t.status !== 'done')
}

const getUploadIconColor = (status) => {
  if (status === 'error') return '#ef4444'
  if (status === 'done') return '#22c55e'
  return '#3b82f6'
}

const getUploadProgressStatus = (status) => {
  if (status === 'error') return 'error'
  if (status === 'done') return 'success'
  return 'default'
}

const getUploadStatusText = (status) => {
  if (status === 'error') return '失败'
  if (status === 'done') return '完成'
  return '上传中'
}

const handleCreateFolder = async () => {
  if (!createFolderForm.value.name?.trim()) {
    message.error('请输入文件夹名称')
    return
  }
  try {
    createFolderLoading.value = true
    const data = { name: createFolderForm.value.name.trim() }
    if (currentFolderId.value) {
      data.parent_id = currentFolderId.value
    }
    await createFolderApi(data)
    message.success('创建成功')
    showCreateFolder.value = false
    createFolderForm.value.name = ''
    fetchFiles()
  } catch (e) {
    handleError(e, '创建文件夹失败')
  } finally {
    createFolderLoading.value = false
  }
}

const getFileIcon = (type) => {
  const map = {
    image: FileTrayFullOutline,
    pdf: DocumentOutline,
    doc: FileTrayStackedOutline,
    xls: FileTrayStackedOutline,
    ppt: FileTrayStackedOutline,
    video: VideocamOutline,
    audio: MusicalNoteOutline,
    code: CodeSlashOutline,
    zip: ArchiveOutline,
    other: HelpCircleOutline,
  }
  return map[type] || HelpCircleOutline
}

const getFileIconColor = (type) => {
  const map = {
    image: '#ec4899',
    pdf: '#ef4444',
    doc: '#3b82f6',
    xls: '#22c55e',
    ppt: '#f97316',
    video: '#8b5cf6',
    audio: '#06b6d4',
    code: '#64748b',
    zip: '#eab308',
    other: '#94a3b8',
  }
  return map[type] || '#94a3b8'
}

const getFileTypeLabel = (type) => {
  const map = {
    image: '图片',
    pdf: 'PDF 文档',
    doc: 'Word 文档',
    xls: 'Excel 表格',
    ppt: 'PPT 演示',
    video: '视频',
    audio: '音频',
    code: '代码',
    zip: '压缩包',
    other: '其他',
  }
  return map[type] || '其他'
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(size < 10 && unitIndex > 0 ? 2 : 1)} ${units[unitIndex]}`
}

const formatTime = (time) => {
  if (!time) return '-'
  const d = new Date(time)
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const openFile = (file) => {
  previewFile.value = file
  showPreviewModal.value = true
}

const downloadFile = (file) => {
  if (!file) return
  const url = getFileDownloadUrl(file.id)
  const token = localStorage.getItem('zhihui_token')
  const a = document.createElement('a')
  a.href = url
  a.download = file.name
  if (token) {
    const headers = new Headers()
    headers.append('Authorization', `Bearer ${token}`)
    fetch(url, { headers })
      .then((res) => res.blob())
      .then((blob) => {
        const blobUrl = window.URL.createObjectURL(blob)
        a.href = blobUrl
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(blobUrl)
      })
  } else {
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
  }
}

const getFolderMenuOptions = (folder) => [
  {
    label: '打开',
    key: 'open',
    icon: () => h(NIcon, null, { default: () => h(FolderOutline) }),
  },
  {
    label: '重命名',
    key: 'rename',
    icon: () => h(NIcon, null, { default: () => h(CreateOutline) }),
  },
  {
    label: '移动',
    key: 'move',
    icon: () => h(NIcon, null, { default: () => h(MoveOutline) }),
  },
  {
    label: '删除',
    key: 'delete',
    icon: () => h(NIcon, null, { default: () => h(TrashOutline) }),
  },
]

const getFileMenuOptions = (file) => [
  {
    label: '预览',
    key: 'preview',
    icon: () => h(NIcon, null, { default: () => h(EyeOutline) }),
  },
  {
    label: '下载',
    key: 'download',
    icon: () => h(NIcon, null, { default: () => h(DownloadOutline) }),
  },
  {
    label: '重命名',
    key: 'rename',
    icon: () => h(NIcon, null, { default: () => h(CreateOutline) }),
  },
  {
    label: '移动',
    key: 'move',
    icon: () => h(NIcon, null, { default: () => h(MoveOutline) }),
  },
  {
    label: '删除',
    key: 'delete',
    icon: () => h(NIcon, null, { default: () => h(TrashOutline) }),
  },
]

const handleFolderAction = (key, folder) => {
  if (key === 'open') {
    openFolder(folder.id)
  } else if (key === 'rename') {
    startRename('folder', folder)
  } else if (key === 'move') {
    startMove('folder', folder)
  } else if (key === 'delete') {
    confirmDelete('folder', folder)
  }
}

const handleFileAction = (key, file) => {
  if (key === 'preview') {
    openFile(file)
  } else if (key === 'download') {
    downloadFile(file)
  } else if (key === 'rename') {
    startRename('file', file)
  } else if (key === 'move') {
    startMove('file', file)
  } else if (key === 'delete') {
    confirmDelete('file', file)
  }
}

const startRename = (type, data) => {
  renameTarget.value = { type, data }
  renameForm.value.name = data.name
  showRenameModal.value = true
}

const handleRename = async () => {
  if (!renameForm.value.name?.trim()) {
    message.error('请输入新名称')
    return
  }
  try {
    renameLoading.value = true
    const { type, data } = renameTarget.value
    const newName = renameForm.value.name.trim()
    if (type === 'folder') {
      await updateFolderApi(data.id, { name: newName })
    } else {
      await updateFileApi(data.id, { name: newName })
    }
    message.success('重命名成功')
    showRenameModal.value = false
    fetchFiles()
  } catch (e) {
    handleError(e, '重命名失败')
  } finally {
    renameLoading.value = false
  }
}

const startMove = async (type, data) => {
  moveTarget.value = data
  moveTargetType.value = type
  moveTargetFolderId.value = null
  try {
    const params = {}
    if (type === 'folder') {
      params.exclude_folder_id = data.id
    }
    const res = await getFolderTreeApi(params)
    folderTreeData.value = buildTreeOptions(res.folders || [])
    showMoveModal.value = true
  } catch (e) {
    handleError(e, '加载文件夹树失败')
  }
}

const buildTreeOptions = (folders) => {
  const buildLabel = (folder) => {
    return () =>
      h(
        'span',
        { style: 'display: inline-flex; align-items: center; gap: 6px' },
        [h('span', { style: 'color: #f59e0b' }, '📁'), h('span', folder.name)]
      )
  }
  return folders.map((f) => ({
    key: f.id,
    label: buildLabel(f),
    children: f.children && f.children.length > 0 ? buildTreeOptions(f.children) : undefined,
  }))
}

const handleMoveFolderSelect = (keys) => {
  moveTargetFolderId.value = keys.length > 0 ? keys[0] : null
}

const handleMove = async () => {
  try {
    moveLoading.value = true
    const parentId = moveTargetFolderId.value || null
    if (moveTargetType.value === 'folder') {
      await updateFolderApi(moveTarget.value.id, { parent_id: parentId })
    } else {
      await updateFileApi(moveTarget.value.id, { parent_id: parentId })
    }
    message.success('移动成功')
    showMoveModal.value = false
    fetchFiles()
  } catch (e) {
    handleError(e, '移动失败')
  } finally {
    moveLoading.value = false
  }
}

const confirmDelete = (type, data) => {
  dialog.warning({
    title: '确认删除',
    content: type === 'folder'
      ? `确定要删除文件夹「${data.name}」吗？其下所有子文件夹和文件都将被删除，此操作不可恢复。`
      : `确定要删除文件「${data.name}」吗？此操作不可恢复。`,
    positiveText: '删除',
    negativeText: '取消',
    positiveButtonProps: { type: 'error' },
    onPositiveClick: async () => {
      try {
        if (type === 'folder') {
          await deleteFolderApi(data.id)
        } else {
          await deleteFileApi(data.id)
        }
        message.success('删除成功')
        fetchFiles()
      } catch (e) {
        handleError(e, '删除失败')
      }
    },
  })
}

const handleSearch = () => {
  if (searchTimer.value) {
    clearTimeout(searchTimer.value)
  }
  searchTimer.value = setTimeout(() => {
    doSearch()
  }, 300)
}

const handleClearSearch = () => {
  searchMode.value = false
  searchResult.value = { folders: [], files: [] }
}

const clearSearch = () => {
  searchKeyword.value = ''
  searchMode.value = false
  searchResult.value = { folders: [], files: [] }
}

const doSearch = async () => {
  const keyword = searchKeyword.value?.trim()
  if (!keyword) {
    searchMode.value = false
    searchResult.value = { folders: [], files: [] }
    return
  }
  try {
    const res = await searchFilesApi({ keyword })
    searchResult.value = {
      folders: res.folders || [],
      files: res.files || [],
    }
    searchMode.value = true
  } catch (e) {
    handleError(e, '搜索失败')
  }
}

const handleRowClick = (row) => {
  if (row._type === 'folder') {
    openFolder(row.id)
  } else {
    selectedItem.value = { type: 'file', data: row._raw }
  }
}

const listColumns = [
  {
    title: '名称',
    key: 'name',
    render: (row) => {
      return h(
        'div',
        {
          style: 'display: flex; align-items: center; gap: 10px; cursor: pointer',
          onClick: () => handleRowClick(row),
        },
        [
          h(NIcon, { size: 20, color: row._type === 'folder' ? '#f59e0b' : getFileIconColor(row.file_type) }, {
            default: () => h(row._type === 'folder' ? FolderOutline : getFileIcon(row.file_type)),
          }),
          h('span', {
            style: 'font-weight: 500',
            title: row.name,
          }, row.name),
        ]
      )
    },
  },
  {
    title: '类型',
    key: 'file_type',
    render: (row) => row._type === 'folder' ? '文件夹' : getFileTypeLabel(row.file_type),
    width: 100,
  },
  {
    title: '大小',
    key: 'size',
    render: (row) => (row._type === 'folder' ? '-' : formatFileSize(row.file_size)),
    width: 100,
  },
  {
    title: '上传人',
    key: 'creator',
    render: (row) => row.creator?.name || '-',
    width: 120,
  },
  {
    title: '上传时间',
    key: 'created_at',
    render: (row) => formatTime(row.created_at),
    width: 170,
  },
  {
    title: '操作',
    key: 'actions',
    width: 220,
    render: (row) => {
      return h(
        'div',
        { style: 'display: flex; gap: 8px' },
        [
          row._type === 'folder'
            ? h(
                NButton,
                {
                  text: true,
                  size: 'small',
                  onClick: () => openFolder(row.id),
                },
                { default: () => '打开' }
              )
            : h(
                NButton,
                {
                  text: true,
                  size: 'small',
                  type: 'primary',
                  onClick: () => openFile(row._raw),
                },
                { default: () => '预览' }
              ),
          row._type === 'folder'
            ? null
            : h(
                NButton,
                {
                  text: true,
                  size: 'small',
                  onClick: () => downloadFile(row._raw),
                },
                { default: () => '下载' }
              ),
          h(
            NButton,
            {
              text: true,
              size: 'small',
              onClick: () => startRename(row._type, row._raw),
            },
            { default: () => '重命名' }
          ),
          h(
            NButton,
            {
              text: true,
              size: 'small',
              type: 'error',
              onClick: () => confirmDelete(row._type, row._raw),
            },
            { default: () => '删除' }
          ),
        ].filter(Boolean)
      )
    },
  },
]

const listData = computed(() => {
  const folderData = folders.value.map((f) => ({
    ...f,
    _type: 'folder',
    _raw: f,
  }))
  const fileData = files.value.map((f) => ({
    ...f,
    _type: 'file',
    _raw: f,
  }))
  return [...folderData, ...fileData]
})

watch(currentFolderId, () => {
  selectedItem.value = null
})

onMounted(() => {
  fetchFiles()
})
</script>

<style lang="scss" scoped>
.files-page {
  width: 100%;
}

.page-header {
  background: #fff;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.breadcrumb-area {
  :deep(.n-breadcrumb-separator) {
    margin: 0 8px;
  }
}

.breadcrumb-root,
.breadcrumb-link {
  cursor: pointer;
  transition: color 0.2s;
  &:hover {
    color: #3b82f6;
  }
}

.breadcrumb-root {
  font-weight: 600;
  color: #1e293b;
}

.header-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.search-input {
  max-width: 320px;
  flex-shrink: 0;
}

.view-toggle {
  margin-left: 4px;
}

.search-results-header {
  background: #eff6ff;
  border-radius: 8px;
  padding: 10px 16px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 14px;
  color: #1e40af;
}

.upload-panel {
  background: #fff;
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 16px;
  border: 1px solid #e2e8f0;
}

.upload-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

.upload-task {
  display: flex;
  align-items: center;
  padding: 8px 0;
  border-top: 1px solid #f1f5f9;
  &:first-of-type {
    border-top: none;
  }
}

.upload-task-info {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 280px;
  flex-shrink: 0;
}

.upload-icon {
  flex-shrink: 0;
}

.upload-task-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 13px;
  color: #1e293b;
}

.upload-task-size {
  width: 70px;
  text-align: right;
  font-size: 12px;
  color: #94a3b8;
  flex-shrink: 0;
}

.upload-task-status {
  width: 50px;
  text-align: right;
  font-size: 12px;
  color: #64748b;
  flex-shrink: 0;
}

.files-container {
  background: #fff;
  border-radius: 12px;
  padding: 16px 20px;
  min-height: 400px;
}

.grid-view {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 16px;
}

.grid-item {
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid transparent;

  &:hover {
    background: #f8fafc;
    .grid-card {
      transform: translateY(-2px);
    }
  }

  &.selected {
    border-color: #3b82f6;
    background: #eff6ff;
  }
}

.grid-card {
  padding: 16px 12px;
  text-align: center;
  transition: transform 0.2s ease;
}

.folder-thumb,
.file-thumb {
  height: 88px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 10px;
  border-radius: 8px;
  background: #f8fafc;
}

.thumb-image {
  max-width: 100%;
  max-height: 88px;
  object-fit: contain;
  border-radius: 6px;
}

.grid-item-name {
  font-size: 13px;
  font-weight: 500;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}

.grid-item-meta {
  font-size: 11px;
  color: #94a3b8;
  margin-top: 4px;
}

.list-view {
  min-height: 300px;
}

.files-table {
  :deep(.n-data-table-tr) {
    cursor: pointer;
    transition: background 0.2s;
  }
}

.search-results {
  background: #fff;
  border-radius: 12px;
  padding: 16px 20px;
  min-height: 400px;
}

.search-section {
  margin-bottom: 24px;
  &:last-child {
    margin-bottom: 0;
  }
}

.search-section-title {
  font-size: 14px;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 12px;
  padding-left: 4px;
}

.move-modal-content {
  .move-target-info {
    padding: 10px 12px;
    background: #f8fafc;
    border-radius: 8px;
    margin-bottom: 14px;
    font-size: 13px;
    color: #64748b;
  }
  :deep(.n-tree) {
    max-height: 360px;
    overflow-y: auto;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 8px;
  }
}

.preview-content {
  max-height: 65vh;
  overflow: auto;
}

.image-preview {
  text-align: center;
  padding: 16px;
  img {
    max-width: 100%;
    max-height: 60vh;
    object-fit: contain;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  }
}

.pdf-preview {
  .pdf-frame {
    width: 100%;
    height: 65vh;
    border: none;
    border-radius: 8px;
  }
}

.file-info-card {
  padding: 24px;
  .info-header {
    text-align: center;
    margin-bottom: 24px;
  }
  .download-action {
    text-align: center;
    margin-top: 20px;
  }
}
</style>
