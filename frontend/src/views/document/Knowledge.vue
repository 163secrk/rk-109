<template>
  <div class="page-card knowledge-page">
    <div class="page-header">
      <div class="page-title">知识库</div>
      <div class="header-actions">
        <n-dropdown :options="createDropdownOptions" @select="handleCreateSelect" trigger="click">
          <n-button type="primary">
            <template #icon>
              <n-icon><AddOutline /></n-icon>
            </template>
            新建
          </n-button>
        </n-dropdown>
      </div>
    </div>

    <n-layout has-sider class="knowledge-layout">
      <n-layout-sider width="280" bordered>
        <DocTree
          :data="treeData"
          v-model:selectedKeys="selectedKeys"
          v-model:expandedKeys="expandedKeys"
          @refresh="fetchTree"
          @create="handleTreeCreate"
          @rename="handleTreeRename"
          @delete="handleTreeDelete"
          @move="handleTreeMove"
        />
      </n-layout-sider>

      <n-layout-content class="editor-content">
        <DocEditor
          v-if="currentDoc"
          :doc="currentDoc"
          :save-status="saveStatus"
          :saving-version="savingVersion"
          @change="handleEditorChange"
          @save-version="handleSaveVersion"
          @show-versions="showVersions = true"
        />
        <div v-else class="empty-state">
          <n-empty description="请选择左侧文档或创建新文档">
            <template #extra>
              <n-button type="primary" @click="openCreateModal('doc')">
                <template #icon>
                  <n-icon><AddOutline /></n-icon>
                </template>
                创建新文档
              </n-button>
            </template>
          </n-empty>
        </div>
      </n-layout-content>
    </n-layout>

    <n-modal v-model:show="showCreateDocModal" preset="card" title="新建文档" style="width: 480px">
      <n-form ref="createFormRef" :model="createForm" label-placement="top">
        <n-form-item label="父目录">
          <n-tag>{{ createFormParentTitle }}</n-tag>
        </n-form-item>
        <n-form-item label="文档标题" path="title" :rule="{ required: true, message: '请输入文档标题' }">
          <n-input v-model:value="createForm.title" placeholder="请输入文档标题" />
        </n-form-item>
        <n-form-item label="类型">
          <n-radio-group v-model:value="createForm.doc_type">
            <n-radio value="doc">文档</n-radio>
            <n-radio value="folder">文件夹</n-radio>
          </n-radio-group>
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateDocModal = false">取消</n-button>
          <n-button type="primary" :loading="creating" @click="handleCreateDoc">创建</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="showSaveVersionModal" preset="card" title="保存版本" style="width: 480px">
      <n-form :model="versionForm" label-placement="top">
        <n-form-item label="版本说明">
          <n-input v-model:value="versionForm.change_summary" type="textarea" :rows="3" placeholder="请输入本次修改的说明（可选）" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showSaveVersionModal = false">取消</n-button>
          <n-button type="primary" :loading="savingVersion" @click="confirmSaveVersion">确认保存</n-button>
        </n-space>
      </template>
    </n-modal>

    <VersionDrawer
      v-model:show="showVersions"
      :versions="versions"
      :loading="loadingVersions"
      @rollback="handleRollback"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useApi } from '../../utils/request'
import {
  listKnowledgeTreeApi,
  getKnowledgeDocApi,
  createKnowledgeDocApi,
  updateKnowledgeDocApi,
  moveKnowledgeDocApi,
  deleteKnowledgeDocApi,
  listKnowledgeVersionsApi,
  createKnowledgeVersionApi,
  rollbackKnowledgeVersionApi,
} from '../../api/document'
import { buildNodeIdMap, collectFolderIds } from './utils'
import { AddOutline } from '@vicons/ionicons5'
import DocTree from './DocTree.vue'
import DocEditor from './DocEditor.vue'
import VersionDrawer from './VersionDrawer.vue'

const { message, dialog, handleError } = useApi()

const createFormRef = ref(null)

const treeData = ref([])
const selectedKeys = ref([])
const expandedKeys = ref([])
const selectedFolderId = ref(null)
const currentDoc = ref(null)
const saveStatus = ref('saved')
const showCreateDocModal = ref(false)
const showSaveVersionModal = ref(false)
const showVersions = ref(false)
const creating = ref(false)
const savingVersion = ref(false)
const loadingVersions = ref(false)
const versions = ref([])
const autoSaveTimer = ref(null)
const dirty = ref(false)
const nodeIdMap = ref({})

const createForm = reactive({
  title: '',
  doc_type: 'doc',
  parent_id: null,
})

const versionForm = reactive({
  change_summary: '',
})

const createDropdownOptions = [
  { label: '📄 新建文档', key: 'doc' },
  { label: '📁 新建文件夹', key: 'folder' },
]

const createFormParentTitle = computed(() => {
  if (!createForm.parent_id) return '根目录'
  const node = nodeIdMap.value[createForm.parent_id]
  return node ? node.title : '未知目录'
})

async function fetchTree() {
  try {
    const res = await listKnowledgeTreeApi()
    treeData.value = res
    nodeIdMap.value = buildNodeIdMap(res)
    const ids = collectFolderIds(res)
    expandedKeys.value = ids
  } catch (e) {
    handleError(e, '获取文档列表失败')
  }
}

watch(selectedKeys, async (keys) => {
  if (keys.length === 0) {
    currentDoc.value = null
    return
  }
  const docId = keys[0]
  const node = nodeIdMap.value[docId]
  if (node && node.doc_type === 'folder') {
    selectedFolderId.value = docId
    currentDoc.value = null
    toggleFolderExpand(docId, node)
    return
  }
  selectedFolderId.value = node?.parent_id || null
  try {
    const res = await getKnowledgeDocApi(docId)
    currentDoc.value = res
    saveStatus.value = 'saved'
    dirty.value = false
  } catch (e) {
    handleError(e, '获取文档失败')
  }
})

function toggleFolderExpand(docId, node) {
  if (!expandedKeys.value.includes(docId)) {
    expandedKeys.value = [...expandedKeys.value, docId]
  } else if (node.children && node.children.length > 0) {
    expandedKeys.value = expandedKeys.value.filter((id) => id !== docId)
  }
}

function handleCreateSelect(key) {
  openCreateModal(key)
}

function openCreateModal(docType) {
  const selectedId = selectedKeys.value[0]
  if (selectedId) {
    const node = nodeIdMap.value[selectedId]
    if (node && node.doc_type === 'folder') {
      createForm.parent_id = selectedId
    } else if (node) {
      createForm.parent_id = node.parent_id
    } else {
      createForm.parent_id = selectedFolderId.value
    }
  } else {
    createForm.parent_id = selectedFolderId.value
  }
  createForm.doc_type = docType
  createForm.title = ''
  showCreateDocModal.value = true
}

async function handleCreateDoc() {
  try {
    await createFormRef.value?.validate()
  } catch (e) {
    return
  }
  creating.value = true
  try {
    const res = await createKnowledgeDocApi({
      title: createForm.title,
      doc_type: createForm.doc_type,
      parent_id: createForm.parent_id,
      content: '',
    })
    message.success('创建成功')
    showCreateDocModal.value = false
    const parentId = createForm.parent_id
    await fetchTree()
    if (parentId && !expandedKeys.value.includes(parentId)) {
      expandedKeys.value = [...expandedKeys.value, parentId]
    }
    selectedKeys.value = [res.id]
    selectedFolderId.value = createForm.doc_type === 'folder' ? res.id : parentId
  } catch (e) {
    handleError(e, '创建失败')
  } finally {
    creating.value = false
  }
}

function handleTreeCreate({ doc_type, parent_id }) {
  createForm.doc_type = doc_type
  createForm.parent_id = parent_id
  selectedFolderId.value = parent_id
  createForm.title = ''
  showCreateDocModal.value = true
}

async function handleTreeRename(node) {
  const newName = prompt('请输入新名称：', node.title)
  if (newName && newName !== node.title) {
    try {
      await updateKnowledgeDocApi(node.id, { title: newName })
      message.success('重命名成功')
      await fetchTree()
      if (currentDoc.value?.id === node.id) {
        currentDoc.value.title = newName
      }
    } catch (e) {
      handleError(e, '重命名失败')
    }
  }
}

function handleTreeDelete(node) {
  dialog.warning({
    title: '确认删除',
    content: node.doc_type === 'folder'
      ? `确定要删除文件夹"${node.title}"吗？其下所有内容都将被删除，无法恢复。`
      : `确定要删除文档"${node.title}"吗？删除后无法恢复。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await deleteKnowledgeDocApi(node.id)
        message.success('删除成功')
        if (currentDoc.value?.id === node.id) {
          currentDoc.value = null
          selectedKeys.value = []
        }
        await fetchTree()
      } catch (e) {
        handleError(e, '删除失败')
      }
    },
  })
}

async function handleTreeMove({ dragId, parentId, sortOrder }) {
  try {
    await moveKnowledgeDocApi(dragId, { parent_id: parentId, sort_order: sortOrder })
    message.success('移动成功')
    await fetchTree()
  } catch (e) {
    handleError(e, '移动失败')
  }
}

function handleEditorChange({ title, content }) {
  if (title !== undefined) currentDoc.value.title = title
  if (content !== undefined) currentDoc.value.content = content
  dirty.value = true
  saveStatus.value = 'unsaved'
  triggerAutoSave()
}

function triggerAutoSave() {
  if (autoSaveTimer.value) clearTimeout(autoSaveTimer.value)
  autoSaveTimer.value = setTimeout(() => {
    autoSave()
  }, 30000)
}

async function autoSave() {
  if (!currentDoc.value || !dirty.value) return
  saveStatus.value = 'saving'
  try {
    await updateKnowledgeDocApi(currentDoc.value.id, {
      title: currentDoc.value.title,
      content: currentDoc.value.content,
    })
    saveStatus.value = 'saved'
    dirty.value = false
  } catch (e) {
    saveStatus.value = 'unsaved'
    console.error('自动保存失败', e)
  }
}

async function manualSave() {
  if (!currentDoc.value) return false
  saveStatus.value = 'saving'
  try {
    await updateKnowledgeDocApi(currentDoc.value.id, {
      title: currentDoc.value.title,
      content: currentDoc.value.content,
    })
    saveStatus.value = 'saved'
    dirty.value = false
    return true
  } catch (e) {
    saveStatus.value = 'unsaved'
    handleError(e, '保存失败')
    return false
  }
}

function handleSaveVersion() {
  versionForm.change_summary = ''
  showSaveVersionModal.value = true
}

async function confirmSaveVersion() {
  if (!currentDoc.value) return
  savingVersion.value = true
  try {
    if (dirty.value) {
      const saved = await manualSave()
      if (!saved) return
    }
    await createKnowledgeVersionApi(currentDoc.value.id, {
      change_summary: versionForm.change_summary,
    })
    message.success('版本保存成功')
    showSaveVersionModal.value = false
    if (showVersions.value) {
      await fetchVersions()
    }
  } catch (e) {
    handleError(e, '保存版本失败')
  } finally {
    savingVersion.value = false
  }
}

watch(showVersions, async (val) => {
  if (val && currentDoc.value) {
    await fetchVersions()
  }
})

async function fetchVersions() {
  if (!currentDoc.value) return
  loadingVersions.value = true
  try {
    const res = await listKnowledgeVersionsApi(currentDoc.value.id)
    versions.value = res
  } catch (e) {
    handleError(e, '获取版本列表失败')
  } finally {
    loadingVersions.value = false
  }
}

async function handleRollback(ver) {
  dialog.warning({
    title: '确认回滚',
    content: `确定要回滚到 v${ver.version} 版本吗？当前未保存的更改将丢失。`,
    positiveText: '回滚',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        const res = await rollbackKnowledgeVersionApi(currentDoc.value.id, { version_id: ver.id })
        currentDoc.value = res
        dirty.value = false
        saveStatus.value = 'saved'
        message.success('回滚成功')
        await fetchVersions()
      } catch (e) {
        handleError(e, '回滚失败')
      }
    },
  })
}

onMounted(async () => {
  await fetchTree()
})

onBeforeUnmount(() => {
  if (autoSaveTimer.value) {
    clearTimeout(autoSaveTimer.value)
    autoSaveTimer.value = null
  }
  if (dirty.value && currentDoc.value) {
    autoSave()
  }
})
</script>

<style lang="scss" scoped>
.knowledge-page {
  padding: 20px;
  min-height: calc(100vh - 140px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;

  .page-title {
    font-size: 20px;
    font-weight: 600;
    color: #1f2937;
  }
}

.knowledge-layout {
  height: calc(100vh - 220px);
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.editor-content {
  display: flex;
  flex-direction: column;
  background: #fff;
  overflow: hidden;
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
