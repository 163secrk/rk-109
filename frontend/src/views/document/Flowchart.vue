<template>
  <div class="page-card">
    <div class="page-header">
      <div class="page-title">流程图</div>
      <n-button type="primary" @click="handleCreate">
        <template #icon>
          <n-icon><AddOutline /></n-icon>
        </template>
        新建流程图
      </n-button>
    </div>

    <div v-if="loading" class="empty-wrap">
      <n-spin />
    </div>

    <div v-else-if="charts.length === 0" class="empty-wrap">
      <n-empty description="暂无流程图，点击右上角新建">
        <n-button type="primary" size="small" @click="handleCreate">立即创建</n-button>
      </n-empty>
    </div>

    <div v-else class="chart-grid">
      <div
        v-for="chart in charts"
        :key="chart.id"
        class="chart-card"
        @click="handleOpen(chart.id)"
      >
        <div class="chart-thumb" :style="thumbStyle(chart)">
          <svg viewBox="0 0 200 140" class="thumb-svg" preserveAspectRatio="xMidYMid meet">
            <rect x="60" y="10" width="80" height="30" rx="15" fill="#dbeafe" stroke="#2563eb" stroke-width="2" />
            <text x="100" y="29" text-anchor="middle" font-size="11" fill="#1e40af">开始</text>
            <line x1="100" y1="40" x2="100" y2="58" stroke="#94a3b8" stroke-width="2" />
            <polygon points="100,58 96,52 104,52" fill="#94a3b8" />
            <rect x="50" y="60" width="100" height="30" fill="#e0f2fe" stroke="#0284c7" stroke-width="2" />
            <text x="100" y="79" text-anchor="middle" font-size="11" fill="#075985">处理步骤</text>
            <line x1="100" y1="90" x2="100" y2="103" stroke="#94a3b8" stroke-width="2" />
            <polygon points="100,103 96,97 104,97" fill="#94a3b8" />
            <polygon points="100,105 135,125 100,145 65,125" fill="#fef3c7" stroke="#d97706" stroke-width="2" />
            <text x="100" y="130" text-anchor="middle" font-size="10" fill="#92400e">结束</text>
          </svg>
        </div>
        <div class="chart-info">
          <div class="chart-name" :title="chart.name">
            <n-input
              v-if="editingId === chart.id"
              v-model:value="editingName"
              size="small"
              @click.stop
              @blur="handleRenameBlur(chart)"
              @keyup.enter="handleRenameBlur(chart)"
              :autofocus="true"
              ref="renameInput"
            />
            <span v-else>{{ chart.name }}</span>
          </div>
          <div class="chart-meta">
            <span>创建人: {{ chart.creator?.name || '-' }}</span>
            <span>{{ formatTime(chart.updated_at) }}</span>
          </div>
          <div class="chart-actions" @click.stop>
            <n-button text size="tiny" type="primary" @click="handleOpen(chart.id)">编辑</n-button>
            <n-button text size="tiny" @click="startRename(chart)">重命名</n-button>
            <n-popconfirm @positive-click="handleDelete(chart.id)">
              <template #trigger>
                <n-button text size="tiny" type="error">删除</n-button>
              </template>
              确定删除该流程图吗？
            </n-popconfirm>
          </div>
        </div>
      </div>
    </div>

    <n-modal v-model:show="showCreateDialog" preset="card" title="新建流程图" style="width: 420px">
      <n-form ref="createForm" :model="createForm" :rules="createRules">
        <n-form-item label="流程图名称" path="name">
          <n-input v-model:value="createForm.name" placeholder="请输入流程图名称" maxlength="255" />
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
import { ref, onMounted, h, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, useDialog, useLoadingBar } from 'naive-ui'
import {
  AddOutline,
} from '@vicons/ionicons5'
import { NIcon } from 'naive-ui'
import {
  listFlowchartsApi,
  createFlowchartApi,
  updateFlowchartApi,
  deleteFlowchartApi,
} from '../../api/document'

const router = useRouter()
const message = useMessage()
const loadingBar = useLoadingBar()

const loading = ref(false)
const charts = ref([])
const showCreateDialog = ref(false)
const creating = ref(false)
const editingId = ref(null)
const editingName = ref('')
const createForm = ref({ name: '' })
const createRules = {
  name: [
    { required: true, message: '请输入流程图名称', trigger: 'blur' },
    { min: 1, max: 255, message: '名称长度1-255', trigger: 'blur' },
  ],
}

const fetchCharts = async () => {
  loading.value = true
  try {
    charts.value = await listFlowchartsApi()
  } catch (e) {
    message.error(e?.detail || e?.message || '获取列表失败')
  } finally {
    loading.value = false
  }
}

const thumbStyle = (chart) => {
  if (chart.thumbnail) {
    return { backgroundImage: `url(${chart.thumbnail})`, backgroundSize: 'cover', backgroundPosition: 'center' }
  }
  return {}
}

const formatTime = (t) => {
  if (!t) return '-'
  const d = new Date(t)
  return d.toLocaleString('zh-CN')
}

const handleCreate = () => {
  createForm.value = { name: '' }
  showCreateDialog.value = true
}

const submitCreate = async () => {
  if (!createForm.value.name?.trim()) {
    message.warning('请输入流程图名称')
    return
  }
  creating.value = true
  loadingBar.start()
  try {
    const res = await createFlowchartApi({ name: createForm.value.name.trim() })
    message.success('创建成功')
    showCreateDialog.value = false
    router.push(`/document/flowchart/${res.id}`)
  } catch (e) {
    message.error(e?.detail || e?.message || '创建失败')
  } finally {
    creating.value = false
    loadingBar.finish()
  }
}

const handleOpen = (id) => {
  router.push(`/document/flowchart/${id}`)
}

const startRename = (chart) => {
  editingId.value = chart.id
  editingName.value = chart.name
}

const handleRenameBlur = async (chart) => {
  const newName = editingName.value?.trim()
  if (!newName) {
    message.warning('名称不能为空')
    editingName.value = chart.name
    editingId.value = null
    return
  }
  if (newName === chart.name) {
    editingId.value = null
    return
  }
  try {
    await updateFlowchartApi(chart.id, { name: newName })
    chart.name = newName
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
    await deleteFlowchartApi(id)
    charts.value = charts.value.filter((c) => c.id !== id)
    message.success('删除成功')
  } catch (e) {
    message.error(e?.detail || e?.message || '删除失败')
  } finally {
    loadingBar.finish()
  }
}

onMounted(fetchCharts)
</script>

<style lang="scss" scoped>
.page-card {
  min-height: 100%;
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

.empty-wrap {
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}

.chart-card {
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

.chart-thumb {
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

.chart-info {
  padding: 12px 14px;
}

.chart-name {
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 6px;
  min-height: 28px;
}

.chart-meta {
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

.chart-actions {
  display: flex;
  gap: 4px;
  padding-top: 8px;
  border-top: 1px solid #f1f5f9;
}
</style>
