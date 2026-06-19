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
      <n-layout-sider width="280" bordered class="tree-sider">
        <div class="tree-header">
          <span>文档目录</span>
          <n-button text size="tiny" @click="fetchTree">↻ 刷新</n-button>
        </div>
        <div class="tree-container">
          <n-tree
            ref="treeRef"
            block-line
            :data="treeData"
            :selected-keys="selectedKeys"
            :expanded-keys="expandedKeys"
            :key-field="'id'"
            :label-field="'title'"
            :children-field="'children'"
            draggable
            :render-prefix="renderTreePrefix"
            @update:selected-keys="handleSelect"
            @update:expanded-keys="handleExpand"
            @drop="handleDrop"
          >
            <template #="{ option }">
              <div class="tree-node-label" @contextmenu.prevent="handleNodeContextMenu($event, option)">
                {{ option.title }}
                <n-dropdown
                  trigger="manual"
                  :show="contextMenuShow === option.id"
                  :options="getNodeMenuOptions(option)"
                  :x="contextMenuX"
                  :y="contextMenuY"
                  placement="bottom-start"
                  @select="(key) => handleNodeMenuSelect(key, option)"
                  @clickoutside="handleContextMenuClose"
                />
              </div>
            </template>
          </n-tree>
          <n-empty v-if="treeData.length === 0" description="暂无文档，点击右上角新建" style="padding: 40px 0" />
        </div>
      </n-layout-sider>

      <n-layout-content class="editor-content">
        <template v-if="currentDoc">
          <div class="editor-header">
            <div class="doc-title-row">
              <n-input
                v-model:value="currentDoc.title"
                size="large"
                :bordered="false"
                class="doc-title-input"
                placeholder="请输入文档标题"
                @update:value="handleTitleChange"
              />
              <div class="save-status" :class="saveStatus">
                <span v-if="saveStatus === 'saving'">⏳</span>
                <span v-else-if="saveStatus === 'saved'">✓</span>
                <span v-else>●</span>
                <span>{{ saveStatusText }}</span>
              </div>
            </div>
            <div class="editor-actions">
              <n-button size="small" @click="showVersions = true">🕘 历史版本</n-button>
              <n-button size="small" type="primary" :loading="savingVersion" @click="handleSaveVersion">💾 保存版本</n-button>
            </div>
          </div>

          <div class="editor-toolbar">
            <n-button-group size="small">
              <n-button @click="insertMarkdown('**', '**')" title="加粗"><strong>B</strong></n-button>
              <n-button @click="insertMarkdown('*', '*')" title="斜体"><em>I</em></n-button>
              <n-button @click="insertMarkdown('~~', '~~')" title="删除线"><s>S</s></n-button>
            </n-button-group>
            <n-divider vertical />
            <n-button-group size="small">
              <n-button @click="insertMarkdown('# ', '')" title="一级标题">H1</n-button>
              <n-button @click="insertMarkdown('## ', '')" title="二级标题">H2</n-button>
              <n-button @click="insertMarkdown('### ', '')" title="三级标题">H3</n-button>
            </n-button-group>
            <n-divider vertical />
            <n-button-group size="small">
              <n-button @click="insertMarkdown('- ', '')" title="无序列表">• 列表</n-button>
              <n-button @click="insertMarkdown('1. ', '')" title="有序列表">1. 序</n-button>
              <n-button @click="insertMarkdown('- [ ] ', '')" title="任务列表">☐ 任务</n-button>
            </n-button-group>
            <n-divider vertical />
            <n-button-group size="small">
              <n-button @click="handleInsertLink" title="插入链接">
                <n-icon><LinkOutline /></n-icon>
              </n-button>
              <n-button @click="handleInsertImage" title="插入图片">
                <n-icon><ImageOutline /></n-icon>
              </n-button>
              <n-button @click="insertMarkdown('\n```\n', '\n```\n')" title="代码块">代码块</n-button>
              <n-button @click="insertMarkdown('`', '`')" title="行内代码">行内代码</n-button>
              <n-button @click="insertMarkdown('> ', '')" title="引用">❝ 引用</n-button>
            </n-button-group>
          </div>

          <div class="editor-body">
            <div class="editor-pane">
              <div class="pane-header">编辑</div>
              <n-input
                ref="editorRef"
                v-model:value="editContent"
                type="textarea"
                :autosize="{ minRows: 20 }"
                class="markdown-editor"
                placeholder="开始编写 Markdown 内容..."
                @update:value="handleContentChange"
              />
            </div>
            <div class="preview-pane">
              <div class="pane-header">预览</div>
              <div class="markdown-preview" v-html="renderedContent"></div>
            </div>
          </div>
        </template>

        <div v-else class="empty-state">
          <n-empty description="请选择左侧文档或创建新文档">
            <template #extra>
              <n-button type="primary" @click="showCreateDocModal = true">
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
      <n-form ref="versionFormRef" :model="versionForm" label-placement="top">
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

    <n-drawer v-model:show="showVersions" :width="480" placement="right">
      <n-drawer-content title="历史版本" :closable="true">
        <n-spin :show="loadingVersions">
          <n-empty v-if="versions.length === 0 && !loadingVersions" description="暂无历史版本" />
          <n-timeline v-else>
            <n-timeline-item
              v-for="ver in versions"
              :key="ver.id"
              :type="ver === versions[0] ? 'success' : 'default'"
            >
              <template #header>
                <div class="version-header">
                  <span class="version-title">v{{ ver.version }} - {{ ver.title }}</span>
                  <n-space>
                    <n-button
                      size="tiny"
                      type="primary"
                      ghost
                      :disabled="ver === versions[0]"
                      @click="handleRollback(ver)"
                    >
                      回滚到此版本
                    </n-button>
                  </n-space>
                </div>
              </template>
              <div class="version-meta">
                <n-avatar round size="small" style="background-color: #2563eb">
                  {{ ver.creator?.name?.charAt(0) || 'U' }}
                </n-avatar>
                <span>{{ ver.creator?.name || '未知用户' }}</span>
                <span class="version-time">{{ formatTime(ver.created_at) }}</span>
              </div>
              <div class="version-summary" v-if="ver.change_summary">{{ ver.change_summary }}</div>
            </n-timeline-item>
          </n-timeline>
        </n-spin>
      </n-drawer-content>
    </n-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onBeforeUnmount, nextTick, h } from 'vue'
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
import {
  AddOutline,
  ImageOutline,
  LinkOutline,
} from '@vicons/ionicons5'
import { NIcon } from 'naive-ui'

const { message, dialog, handleError } = useApi()

const treeRef = ref(null)
const editorRef = ref(null)
const createFormRef = ref(null)
const versionFormRef = ref(null)

const treeData = ref([])
const selectedKeys = ref([])
const expandedKeys = ref([])
const selectedFolderId = ref(null)
const currentDoc = ref(null)
const editContent = ref('')
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

const contextMenuShow = ref(null)
const contextMenuX = ref(0)
const contextMenuY = ref(0)

const createForm = reactive({
  title: '',
  doc_type: 'doc',
  parent_id: null,
})

const createFormParentTitle = computed(() => {
  if (!createForm.parent_id) return '根目录'
  const node = nodeIdMap.value[createForm.parent_id]
  return node ? node.title : '未知目录'
})

const versionForm = reactive({
  change_summary: '',
})

const createDropdownOptions = [
  {
    label: '📄 新建文档',
    key: 'doc',
  },
  {
    label: '📁 新建文件夹',
    key: 'folder',
  },
]

const saveStatusText = computed(() => {
  if (saveStatus.value === 'saving') return '保存中...'
  if (saveStatus.value === 'saved') return '已保存'
  if (saveStatus.value === 'unsaved') return '未保存'
  return ''
})

const renderedContent = computed(() => {
  return renderMarkdown(editContent.value)
})

function renderMarkdown(text) {
  if (!text) return ''
  let html = escapeHtml(text)
  html = html.replace(/```([\s\S]*?)```/g, (match, code) => {
    return `<pre><code>${code.trim()}</code></pre>`
  })
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>')
  html = html.replace(/^###### (.*)$/gm, '<h6>$1</h6>')
  html = html.replace(/^##### (.*)$/gm, '<h5>$1</h5>')
  html = html.replace(/^#### (.*)$/gm, '<h4>$1</h4>')
  html = html.replace(/^### (.*)$/gm, '<h3>$1</h3>')
  html = html.replace(/^## (.*)$/gm, '<h2>$1</h2>')
  html = html.replace(/^# (.*)$/gm, '<h1>$1</h1>')
  html = html.replace(/^\s*[-*+]\s+\[x\]\s+(.*)$/gim, '<li class="task-done"><input type="checkbox" checked disabled> $1</li>')
  html = html.replace(/^\s*[-*+]\s+\[ \]\s+(.*)$/gim, '<li class="task"><input type="checkbox" disabled> $1</li>')
  html = html.replace(/^\s*[-*+]\s+(.*)$/gm, '<li>$1</li>')
  html = html.replace(/^\s*\d+\.\s+(.*)$/gm, '<li>$1</li>')
  html = html.replace(/^> (.*)$/gm, '<blockquote>$1</blockquote>')
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>')
  html = html.replace(/~~([^~]+)~~/g, '<del>$1</del>')
  html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" style="max-width: 100%">')
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>')
  html = html.replace(/\n\n/g, '</p><p>')
  html = html.replace(/\n/g, '<br>')
  html = '<p>' + html + '</p>'
  html = html.replace(/(<\/?h[1-6]>|<\/?pre>|<\/?blockquote>|<\/?ul>|<\/?ol>|<li>.*?<\/li>)/g, (match) => {
    return match.replace(/^<p>|<\/p>$/g, '')
  })
  return html
}

function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

function renderTreePrefix({ option }) {
  return h('span', { style: 'margin-right: 4px; display: inline-block; width: 16px; text-align: center' }, option.doc_type === 'folder' ? '📁' : '📄')
}

async function fetchTree() {
  try {
    const res = await listKnowledgeTreeApi()
    treeData.value = res
    buildNodeIdMap(res)
    const ids = []
    collectAllIds(res, ids)
    expandedKeys.value = ids
  } catch (e) {
    handleError(e, '获取文档列表失败')
  }
}

function buildNodeIdMap(nodes) {
  const map = {}
  const walk = (list) => {
    for (const node of list) {
      map[node.id] = node
      if (node.children && node.children.length > 0) {
        walk(node.children)
      }
    }
  }
  walk(nodes)
  nodeIdMap.value = map
}

function collectAllIds(nodes, ids) {
  for (const node of nodes) {
    if (node.children && node.children.length > 0) {
      if (!ids.includes(node.id)) ids.push(node.id)
      collectAllIds(node.children, ids)
    }
  }
}

async function handleSelect(keys) {
  if (keys.length === 0) {
    currentDoc.value = null
    return
  }
  const docId = keys[0]
  const node = nodeIdMap.value[docId]
  if (node && node.doc_type === 'folder') {
    selectedFolderId.value = docId
    currentDoc.value = null
    if (!expandedKeys.value.includes(docId)) {
      expandedKeys.value = [...expandedKeys.value, docId]
    } else if (node.children && node.children.length > 0) {
      expandedKeys.value = expandedKeys.value.filter((id) => id !== docId)
    }
    return
  }
  selectedFolderId.value = node?.parent_id || null
  try {
    const res = await getKnowledgeDocApi(docId)
    currentDoc.value = res
    editContent.value = res.content || ''
    saveStatus.value = 'saved'
    dirty.value = false
  } catch (e) {
    handleError(e, '获取文档失败')
  }
}

function handleExpand(keys) {
  expandedKeys.value = keys
}

async function handleDrop({ node, dragNode, dropPosition }) {
  const dragId = dragNode.rawNode.id
  let targetParentId = null
  let sortOrder = 0

  if (dropPosition === 0) {
    targetParentId = node.rawNode.id
    sortOrder = (node.rawNode.children || []).length
  } else {
    targetParentId = node.rawNode.parent_id || null
    const siblings = findSiblings(treeData.value, targetParentId)
    const targetIndex = siblings.findIndex((s) => s.id === node.rawNode.id)
    sortOrder = dropPosition < 0 ? Math.max(0, targetIndex) : targetIndex + 1
  }

  try {
    await moveKnowledgeDocApi(dragId, { parent_id: targetParentId, sort_order: sortOrder })
    message.success('移动成功')
    await fetchTree()
  } catch (e) {
    handleError(e, '移动失败')
  }
}

function findSiblings(nodes, parentId) {
  if (!parentId) return nodes
  for (const node of nodes) {
    if (node.id === parentId) return node.children || []
    if (node.children) {
      const found = findSiblings(node.children, parentId)
      if (found) return found
    }
  }
  return []
}

function handleCreateSelect(key) {
  createForm.doc_type = key
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
    if (createForm.doc_type === 'doc') {
      selectedKeys.value = [res.id]
      selectedFolderId.value = parentId
      await handleSelect([res.id])
    } else {
      selectedKeys.value = [res.id]
      selectedFolderId.value = res.id
    }
  } catch (e) {
    handleError(e, '创建失败')
  } finally {
    creating.value = false
  }
}

function handleTitleChange() {
  dirty.value = true
  saveStatus.value = 'unsaved'
  triggerAutoSave()
}

function handleContentChange() {
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
      content: editContent.value,
    })
    saveStatus.value = 'saved'
    dirty.value = false
  } catch (e) {
    saveStatus.value = 'unsaved'
    console.error('自动保存失败', e)
  }
}

async function manualSave() {
  if (!currentDoc.value) return
  saveStatus.value = 'saving'
  try {
    await updateKnowledgeDocApi(currentDoc.value.id, {
      title: currentDoc.value.title,
      content: editContent.value,
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
        editContent.value = res.content
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

function insertMarkdown(prefix, suffix) {
  if (!editorRef.value) return
  const textarea = editorRef.value.$el?.querySelector('textarea') || document.activeElement
  if (!textarea || textarea.tagName !== 'TEXTAREA') return
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const value = editContent.value
  const selected = value.substring(start, end)
  const newText = value.substring(0, start) + prefix + selected + suffix + value.substring(end)
  editContent.value = newText
  nextTick(() => {
    textarea.focus()
    const newStart = start + prefix.length
    const newEnd = newStart + selected.length
    textarea.setSelectionRange(newStart, newEnd)
  })
}

function handleInsertLink() {
  if (!editorRef.value) return
  const url = prompt('请输入链接地址：', 'https://')
  if (!url) return
  insertMarkdown(`[链接文本](${url})`, '')
}

function handleInsertImage() {
  if (!editorRef.value) return
  const url = prompt('请输入图片地址：', 'https://')
  if (!url) return
  insertMarkdown(`![图片描述](${url})`, '')
}

function handleNodeContextMenu(e, option) {
  e.preventDefault()
  contextMenuShow.value = option.id
  contextMenuX.value = e.clientX
  contextMenuY.value = e.clientY
}

function handleContextMenuClose() {
  contextMenuShow.value = null
}

function getNodeMenuOptions(option) {
  const options = [
    {
      label: '📄 新建文档',
      key: 'new-doc',
    },
  ]
  if (option.doc_type === 'folder') {
    options.push({
      label: '📁 新建文件夹',
      key: 'new-folder',
    })
  }
  options.push({
    label: '✏️ 重命名',
    key: 'rename',
  })
  options.push({
    label: '🗑️ 删除',
    key: 'delete',
  })
  return options
}

async function handleNodeMenuSelect(key, option) {
  handleContextMenuClose()
  if (key === 'new-doc' || key === 'new-folder') {
    createForm.doc_type = key === 'new-doc' ? 'doc' : 'folder'
    createForm.parent_id = option.id
    selectedFolderId.value = option.id
    createForm.title = ''
    showCreateDocModal.value = true
  } else if (key === 'rename') {
    const newName = prompt('请输入新名称：', option.title)
    if (newName && newName !== option.title) {
      try {
        await updateKnowledgeDocApi(option.id, { title: newName })
        message.success('重命名成功')
        await fetchTree()
        if (currentDoc.value?.id === option.id) {
          currentDoc.value.title = newName
        }
      } catch (e) {
        handleError(e, '重命名失败')
      }
    }
  } else if (key === 'delete') {
    dialog.warning({
      title: '确认删除',
      content: option.doc_type === 'folder'
        ? `确定要删除文件夹"${option.title}"吗？其下所有内容都将被删除，无法恢复。`
        : `确定要删除文档"${option.title}"吗？删除后无法恢复。`,
      positiveText: '删除',
      negativeText: '取消',
      onPositiveClick: async () => {
        try {
          await deleteKnowledgeDocApi(option.id)
          message.success('删除成功')
          if (currentDoc.value?.id === option.id) {
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
}

function formatTime(time) {
  if (!time) return ''
  const d = new Date(time)
  return d.toLocaleString('zh-CN')
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

.tree-sider {
  background: #fafbfc;
  display: flex;
  flex-direction: column;

  .tree-header {
    padding: 12px 16px;
    border-bottom: 1px solid #f1f5f9;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: 600;
    font-size: 14px;
    color: #1f2937;
  }

  .tree-container {
    flex: 1;
    overflow-y: auto;
    padding: 8px;
  }
}

.tree-node-label {
  flex: 1;
  position: relative;
}

.editor-content {
  display: flex;
  flex-direction: column;
  background: #fff;
  overflow: hidden;
}

.editor-header {
  padding: 12px 20px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;

  .doc-title-row {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 12px;

    .doc-title-input {
      font-size: 18px;
      font-weight: 600;
      flex: 1;
    }

    .save-status {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 12px;
      white-space: nowrap;

      &.saved {
        color: #16a34a;
      }

      &.saving {
        color: #2563eb;
      }

      &.unsaved {
        color: #f59e0b;
      }
    }
  }

  .editor-actions {
    display: flex;
    gap: 8px;
  }
}

.editor-toolbar {
  padding: 8px 20px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.editor-body {
  flex: 1;
  display: flex;
  overflow: hidden;

  .editor-pane,
  .preview-pane {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .editor-pane {
    border-right: 1px solid #f1f5f9;
  }

  .pane-header {
    padding: 8px 16px;
    background: #f8fafc;
    font-size: 12px;
    font-weight: 600;
    color: #64748b;
    border-bottom: 1px solid #f1f5f9;
  }

  .markdown-editor {
    flex: 1;
    border: none;
    padding: 16px;

    :deep(.n-input__textarea),
    :deep(.n-input__textarea-el) {
      height: 100% !important;
      resize: none;
      font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      font-size: 14px;
      line-height: 1.6;
    }
  }

  .markdown-preview {
    flex: 1;
    padding: 16px 20px;
    overflow-y: auto;
    font-size: 14px;
    line-height: 1.8;
    color: #1f2937;

    h1, h2, h3, h4, h5, h6 {
      margin-top: 24px;
      margin-bottom: 12px;
      font-weight: 600;
      line-height: 1.3;
    }

    h1 { font-size: 28px; border-bottom: 1px solid #e5e7eb; padding-bottom: 8px; }
    h2 { font-size: 22px; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; }
    h3 { font-size: 18px; }
    h4 { font-size: 16px; }
    h5 { font-size: 14px; }
    h6 { font-size: 13px; color: #64748b; }

    p {
      margin: 12px 0;
    }

    a {
      color: #2563eb;
      text-decoration: none;
      &:hover { text-decoration: underline; }
    }

    code {
      background: #f1f5f9;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
      font-size: 13px;
    }

    pre {
      background: #1e293b;
      color: #e2e8f0;
      padding: 16px;
      border-radius: 8px;
      overflow-x: auto;
      margin: 12px 0;

      code {
        background: none;
        padding: 0;
        color: inherit;
      }
    }

    blockquote {
      border-left: 4px solid #2563eb;
      padding: 8px 16px;
      margin: 12px 0;
      background: #eff6ff;
      color: #1e40af;
      border-radius: 0 6px 6px 0;
    }

    ul, ol {
      padding-left: 24px;
      margin: 12px 0;
    }

    li {
      margin: 4px 0;

      &.task-done {
        list-style: none;
        margin-left: -20px;
        text-decoration: line-through;
        color: #94a3b8;
      }

      &.task {
        list-style: none;
        margin-left: -20px;
      }
    }

    img {
      max-width: 100%;
      border-radius: 8px;
      margin: 12px 0;
    }

    strong { font-weight: 600; }
    em { font-style: italic; }
    del { text-decoration: line-through; color: #94a3b8; }
  }
}

.empty-state {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.version-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  color: #1f2937;

  .version-title {
    font-size: 14px;
  }
}

.version-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: #64748b;
  margin-top: 4px;

  .version-time {
    margin-left: auto;
  }
}

.version-summary {
  margin-top: 8px;
  padding: 8px 12px;
  background: #f8fafc;
  border-radius: 6px;
  font-size: 13px;
  color: #475569;
}
</style>
