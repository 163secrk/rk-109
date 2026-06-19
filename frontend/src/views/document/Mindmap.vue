<template>
  <div class="page-card">
    <div class="page-header">
      <div class="page-title">思维导图</div>
      <div class="header-actions">
        <n-space>
          <n-select
            v-model:value="filterProjectId"
            :options="projectOptions"
            placeholder="按项目筛选"
            clearable
            size="small"
            style="width: 180px"
            @update:value="fetchMaps"
          />
          <n-input
            v-model:value="searchKeyword"
            placeholder="搜索导图..."
            size="small"
            style="width: 220px"
            clearable
            @keyup.enter="fetchMaps"
            @clear="fetchMaps"
          >
            <template #prefix>
              <n-icon><SearchOutline /></n-icon>
            </template>
          </n-input>
          <n-button type="primary" @click="handleCreate">
            <template #icon>
              <n-icon><AddOutline /></n-icon>
            </template>
            新建导图
          </n-button>
        </n-space>
      </div>
    </div>

    <div v-if="loading" class="empty-wrap">
      <n-spin />
    </div>

    <div v-else-if="maps.length === 0" class="empty-wrap">
      <n-empty description="暂无思维导图，点击右上角新建">
        <n-button type="primary" size="small" @click="handleCreate">立即创建</n-button>
      </n-empty>
    </div>

    <div v-else class="map-grid">
      <div
        v-for="map in maps"
        :key="map.id"
        class="map-card"
        @click="handleOpen(map.id)"
      >
        <div class="map-thumb" :style="thumbStyle(map)">
          <svg v-if="!map.thumbnail" viewBox="0 0 260 160" class="thumb-svg" preserveAspectRatio="xMidYMid meet">
            <rect x="80" y="60" width="100" height="40" rx="20" fill="#2563eb" />
            <text x="130" y="85" text-anchor="middle" font-size="13" fill="#fff" font-weight="600">{{ truncate(map.name, 8) }}</text>
            <path d="M 80 80 C 50 80, 40 50, 20 50" fill="none" stroke="#94a3b8" stroke-width="2" />
            <circle cx="20" cy="50" r="16" fill="#dbeafe" stroke="#3b82f6" stroke-width="2" />
            <text x="20" y="54" text-anchor="middle" font-size="9" fill="#1e40af">子1</text>
            <path d="M 80 80 C 50 80, 40 110, 20 110" fill="none" stroke="#94a3b8" stroke-width="2" />
            <circle cx="20" cy="110" r="16" fill="#dcfce7" stroke="#16a34a" stroke-width="2" />
            <text x="20" y="114" text-anchor="middle" font-size="9" fill="#166534">子2</text>
            <path d="M 180 80 C 210 80, 220 50, 240 50" fill="none" stroke="#94a3b8" stroke-width="2" />
            <circle cx="240" cy="50" r="16" fill="#fef3c7" stroke="#d97706" stroke-width="2" />
            <text x="240" y="54" text-anchor="middle" font-size="9" fill="#92400e">子3</text>
            <path d="M 180 80 C 210 80, 220 110, 240 110" fill="none" stroke="#94a3b8" stroke-width="2" />
            <circle cx="240" cy="110" r="16" fill="#fce7f3" stroke="#db2777" stroke-width="2" />
            <text x="240" y="114" text-anchor="middle" font-size="9" fill="#9d174d">子4</text>
          </svg>
        </div>
        <div class="map-info">
          <div class="map-name-row">
            <div class="map-name" :title="map.name">
              <n-input
                v-if="editingId === map.id"
                v-model:value="editingName"
                size="small"
                @click.stop
                @blur="handleRenameBlur(map)"
                @keyup.enter="handleRenameBlur(map)"
                :autofocus="true"
                ref="renameInput"
              />
              <span v-else>{{ map.name }}</span>
            </div>
            <n-tag v-if="map.project" :color="map.project.cover_color" size="tiny" :bordered="false" text-color="#fff">
              {{ truncate(map.project.name, 6) }}
            </n-tag>
          </div>
          <div class="map-meta">
            <span>创建人: {{ map.creator?.name || '-' }}</span>
            <span>{{ formatTime(map.updated_at) }}</span>
          </div>
          <div class="map-actions" @click.stop>
            <n-button text size="tiny" type="primary" @click="handleOpen(map.id)">编辑</n-button>
            <n-button text size="tiny" @click="startRename(map)">重命名</n-button>
            <n-popconfirm @positive-click="handleDelete(map.id)">
              <template #trigger>
                <n-button text size="tiny" type="error">删除</n-button>
              </template>
              确定删除该思维导图吗？
            </n-popconfirm>
          </div>
        </div>
      </div>
    </div>

    <n-modal v-model:show="showCreateDialog" preset="card" title="新建思维导图" style="width: 460px">
      <n-form ref="createForm" :model="createForm" :rules="createRules">
        <n-form-item label="导图名称" path="name">
          <n-input v-model:value="createForm.name" placeholder="请输入导图名称" maxlength="255" />
        </n-form-item>
        <n-form-item label="关联项目" path="project_id">
          <n-select
            v-model:value="createForm.project_id"
            :options="projectOptions"
            placeholder="可选择关联项目（可选）"
            clearable
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateDialog = false">取消</n-button>
          <n-button type="primary" :loading="creating" @click="submitCreate">确定</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, h } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, useLoadingBar } from 'naive-ui'
import {
  AddOutline,
  SearchOutline,
} from '@vicons/ionicons5'
import { NIcon } from 'naive-ui'
import {
  listMindmapsApi,
  createMindmapApi,
  updateMindmapApi,
  deleteMindmapApi,
} from '../../api/document'
import { listProjectsApi } from '../../api/project'

const router = useRouter()
const message = useMessage()
const loadingBar = useLoadingBar()

const loading = ref(false)
const maps = ref([])
const projects = ref([])
const showCreateDialog = ref(false)
const creating = ref(false)
const editingId = ref(null)
const editingName = ref('')
const searchKeyword = ref('')
const filterProjectId = ref(null)
const createForm = ref({ name: '', project_id: null })
const createRules = {
  name: [
    { required: true, message: '请输入导图名称', trigger: 'blur' },
    { min: 1, max: 255, message: '名称长度1-255', trigger: 'blur' },
  ],
}

const projectOptions = computed(() => [
  { label: '未分类', value: 0 },
  ...projects.value.map((p) => ({ label: p.name, value: p.id })),
])

const fetchProjects = async () => {
  try {
    projects.value = await listProjectsApi()
  } catch (e) {
    console.error('获取项目列表失败', e)
  }
}

const fetchMaps = async () => {
  loading.value = true
  try {
    const params = {}
    if (searchKeyword.value) params.search = searchKeyword.value
    if (filterProjectId.value !== null && filterProjectId.value !== undefined) params.project_id = filterProjectId.value
    maps.value = await listMindmapsApi(params)
  } catch (e) {
    message.error(e?.detail || e?.message || '获取列表失败')
  } finally {
    loading.value = false
  }
}

const thumbStyle = (map) => {
  if (map.thumbnail) {
    return { backgroundImage: `url(${map.thumbnail})`, backgroundSize: 'cover', backgroundPosition: 'center' }
  }
  return {}
}

const formatTime = (t) => {
  if (!t) return '-'
  const d = new Date(t)
  return d.toLocaleString('zh-CN')
}

const truncate = (s, n) => {
  if (!s) return ''
  return s.length > n ? s.slice(0, n) + '...' : s
}

const handleCreate = () => {
  createForm.value = { name: '', project_id: null }
  showCreateDialog.value = true
}

const submitCreate = async () => {
  if (!createForm.value.name?.trim()) {
    message.warning('请输入导图名称')
    return
  }
  creating.value = true
  loadingBar.start()
  try {
    const payload = { name: createForm.value.name.trim() }
    if (createForm.value.project_id && createForm.value.project_id !== 0) {
      payload.project_id = createForm.value.project_id
    }
    const res = await createMindmapApi(payload)
    message.success('创建成功')
    showCreateDialog.value = false
    router.push(`/document/mindmap/${res.id}`)
  } catch (e) {
    message.error(e?.detail || e?.message || '创建失败')
  } finally {
    creating.value = false
    loadingBar.finish()
  }
}

const handleOpen = (id) => {
  router.push(`/document/mindmap/${id}`)
}

const startRename = (map) => {
  editingId.value = map.id
  editingName.value = map.name
}

const handleRenameBlur = async (map) => {
  const newName = editingName.value?.trim()
  if (!newName) {
    message.warning('名称不能为空')
    editingName.value = map.name
    editingId.value = null
    return
  }
  if (newName === map.name) {
    editingId.value = null
    return
  }
  try {
    const payload = { name: newName }
    if (map.project_id) payload.project_id = map.project_id
    await updateMindmapApi(map.id, payload)
    map.name = newName
    message.success('重命名成功')
  } catch (e) {
    message.error(e?.detail || e?.message || '重命名失败')
  } finally {
    editingId.value = null
  }
}

const handleDelete = async (id) => {
  loadingBar.start()
  try {
    await deleteMindmapApi(id)
    maps.value = maps.value.filter((m) => m.id !== id)
    message.success('删除成功')
  } catch (e) {
    message.error(e?.detail || e?.message || '删除失败')
  } finally {
    loadingBar.finish()
  }
}

onMounted(async () => {
  await fetchProjects()
  await fetchMaps()
})
</script>

<style lang="scss" scoped>
.page-card {
  min-height: 100%;
  overflow-y: auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-title {
  font-size: 20px;
  font-weight: 700;
  color: #1e293b;
}

.header-actions {
  display: flex;
  align-items: center;
}

.empty-wrap {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.map-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.map-card {
  background: #fff;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    border-color: #2563eb;
    transform: translateY(-2px);
  }
}

.map-thumb {
  height: 160px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-bottom: 1px solid #e2e8f0;
  position: relative;
  overflow: hidden;
}

.thumb-svg {
  width: 100%;
  height: 100%;
}

.map-info {
  padding: 12px 14px;
}

.map-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
  min-height: 28px;
}

.map-name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.map-meta {
  font-size: 12px;
  color: #94a3b8;
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;

  span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 48%;
  }
}

.map-actions {
  display: flex;
  gap: 4px;
  padding-top: 8px;
  border-top: 1px solid #f1f5f9;
}
</style>
