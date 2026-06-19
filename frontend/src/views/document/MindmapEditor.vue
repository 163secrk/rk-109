<template>
  <div class="editor-container" ref="containerRef">
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <n-button text @click="handleBack">
          <template #icon><n-icon><ArrowBackOutline /></n-icon></template>
          返回
        </n-button>
        <n-divider vertical />
        <n-input
          v-model:value="mapName"
          size="small"
          style="width: 260px"
          @blur="handleNameChange"
          @keyup.enter="handleNameChange"
        />
        <n-tag v-if="saving" size="small" type="info" :bordered="false">
          <template #icon><n-spin size="12" /></template>保存中...
        </n-tag>
        <n-tag v-else-if="lastSaved" size="small" type="success" :bordered="false">
          已保存 {{ formatTime(lastSaved) }}
        </n-tag>
      </div>
      <div class="toolbar-right">
        <n-button-group size="small">
          <n-button :disabled="undoStack.length === 0" @click="handleUndo" title="撤销 (Ctrl+Z)">
            <template #icon><n-icon><ChevronBackOutline /></n-icon></template>
          </n-button>
          <n-button :disabled="redoStack.length === 0" @click="handleRedo" title="重做 (Ctrl+Y)">
            <template #icon><n-icon><ChevronForwardOutline /></n-icon></template>
          </n-button>
        </n-button-group>
        <n-divider vertical />
        <n-button-group size="small">
          <n-button @click="handleZoomOut" title="缩小">
            <template #icon><n-icon><RemoveOutline /></n-icon></template>
          </n-button>
          <n-button style="min-width: 56px" disabled>{{ Math.round(scale * 100) }}%</n-button>
          <n-button @click="handleZoomIn" title="放大">
            <template #icon><n-icon><AddOutline /></n-icon></template>
          </n-button>
        </n-button-group>
        <n-button size="small" @click="handleFit" title="适应画布">
          <template #icon><n-icon><ExpandOutline /></n-icon></template>
          适应
        </n-button>
        <n-button size="small" @click="handleExport" title="导出为PNG">
          <template #icon><n-icon><DownloadOutline /></n-icon></template>
          导出
        </n-button>
        <n-button size="small" type="primary" :loading="saving" @click="handleManualSave">
          <template #icon><n-icon><ArchiveOutline /></n-icon></template>
          保存
        </n-button>
      </div>
    </div>

    <div class="editor-body">
      <div
        class="canvas-wrap"
        ref="canvasWrapRef"
        @click="handleCanvasClick"
        @mousedown="handleCanvasMouseDown"
        @mousemove="handleCanvasMouseMove"
        @mouseup="handleCanvasMouseUp"
        @wheel.prevent="handleWheel"
        @contextmenu.prevent
      >
        <div
          class="canvas-container"
          ref="canvasContainerRef"
          :style="{ transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})` }"
        >
          <svg
            class="canvas-svg"
            ref="svgRef"
            :width="canvasSize.w"
            :height="canvasSize.h"
            xmlns="http://www.w3.org/2000/svg"
          >
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#e2e8f0" stroke-width="0.5" />
              </pattern>
            </defs>
            <rect x="0" y="0" :width="canvasSize.w" :height="canvasSize.h" fill="url(#grid)" />

            <g class="edges-layer">
              <path
                v-for="edge in edgeList"
                :key="edge.id"
                :d="edge.path"
                fill="none"
                :stroke="edge.color"
                stroke-width="2"
                stroke-linecap="round"
              />
            </g>
          </svg>

          <div class="nodes-layer">
            <div
              v-for="node in nodeList"
              :key="node.id"
              class="node-wrapper"
              :style="getNodeStyle(node)"
              :class="{
                selected: selectedNodeId === node.id,
                editing: editingNodeId === node.id,
                dragging: dragState.type === 'node' && dragState.nodeId === node.id,
                'is-root': !node.parentId,
              }"
              @mousedown.stop="(e) => handleNodeMouseDown(e, node)"
              @click.stop="(e) => handleNodeClick(e, node)"
              @dblclick.stop="(e) => startEditNode(node)"
              @contextmenu.stop.prevent="(e) => showContextMenu(e, node)"
            >
              <div
                v-if="editingNodeId !== node.id"
                class="node-content"
                :style="getNodeContentStyle(node)"
              >
                <n-icon v-if="node.icon" class="node-icon" size="16">
                  <component :is="iconMap[node.icon] || StarOutline" />
                </n-icon>
                <span class="node-text" :title="node.text">{{ node.text }}</span>
                <n-icon
                  v-if="node.link"
                  class="node-link-icon"
                  size="12"
                  @click.stop="openNodeLink(node)"
                >
                  <LinkOutline />
                </n-icon>
              </div>
              <div v-else class="node-edit-wrap">
                <n-input
                  v-model:value="nodeEditingText"
                  size="small"
                  autofocus
                  @blur="finishEditNode(node)"
                  @keyup.enter="finishEditNode(node)"
                  @keyup.esc="cancelEditNode"
                  @mousedown.stop
                />
              </div>
              <div
                v-if="selectedNodeId === node.id && editingNodeId !== node.id && !node.parentId"
                class="add-child-hint"
              >
                双击编辑 · Tab添加子节点 · Enter添加同级
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="contextMenuVisible"
      class="context-menu"
      :style="contextMenuStyle"
      @click.stop
    >
      <div class="context-item" @click="startEditNodeFromMenu">
        <n-icon size="16"><PencilOutline /></n-icon>
        <span>编辑文字</span>
      </div>
      <div class="ctx-divider"></div>
      <div class="context-submenu">
        <div class="context-item with-arrow">
          <n-icon size="16"><ColorPaletteOutline /></n-icon>
          <span>改变颜色</span>
          <n-icon size="12" class="arrow"><ChevronForwardOutline /></n-icon>
        </div>
        <div class="submenu-panel">
          <div class="color-grid">
            <div
              v-for="c in nodeColors"
              :key="c.bg"
              class="color-option"
              :style="{ background: c.bg, color: c.text }"
              :class="{ active: selectedNode?.color === c.bg && selectedNode?.textColor === c.text }"
              @click="changeNodeColor(c)"
            >
              Aa
            </div>
          </div>
        </div>
      </div>
      <div class="context-submenu">
        <div class="context-item with-arrow">
          <n-icon size="16"><StarOutline /></n-icon>
          <span>添加图标</span>
          <n-icon size="12" class="arrow"><ChevronForwardOutline /></n-icon>
        </div>
        <div class="submenu-panel icons-panel">
          <div class="icon-grid">
            <div
              v-for="(ic, key) in iconMap"
              :key="key"
              class="icon-option"
              :class="{ active: selectedNode?.icon === key }"
              @click="changeNodeIcon(key)"
              :title="iconLabels[key]"
            >
              <n-icon size="18"><component :is="ic" /></n-icon>
            </div>
            <div
              v-if="selectedNode?.icon"
              class="icon-option remove-icon"
              @click="changeNodeIcon('')"
              title="移除图标"
            >
              <n-icon size="18"><CloseOutline /></n-icon>
            </div>
          </div>
        </div>
      </div>
      <div class="context-item" @click="insertNodeLink">
        <n-icon size="16"><LinkOutline /></n-icon>
        <span>{{ selectedNode?.link ? '编辑链接' : '插入链接' }}</span>
      </div>
      <div class="ctx-divider"></div>
      <div class="context-item" @click="handleAddChildFromMenu">
        <n-icon size="16"><ReturnDownForwardOutline /></n-icon>
        <span>添加子节点 (Tab)</span>
      </div>
      <div v-if="selectedNode?.parentId" class="context-item" @click="handleAddSiblingFromMenu">
        <n-icon size="16"><ArrowDownOutline /></n-icon>
        <span>添加同级节点 (Enter)</span>
      </div>
      <div class="ctx-divider"></div>
      <div
        v-if="selectedNode?.parentId"
        class="context-item danger"
        @click="handleDeleteSelected"
      >
        <n-icon size="16"><TrashOutline /></n-icon>
        <span>删除节点 (Delete)</span>
      </div>
    </div>

    <n-modal
      v-model:show="linkDialogVisible"
      preset="card"
      title="设置链接"
      style="width: 420px"
    >
      <n-form>
        <n-form-item label="链接地址">
          <n-input
            v-model:value="linkInput"
            placeholder="https:// 或 http://"
            @keyup.enter="submitLink"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="linkDialogVisible = false">取消</n-button>
          <n-button type="primary" @click="submitLink">确定</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, h, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMessage, useLoadingBar } from 'naive-ui'
import {
  ArrowBackOutline,
  ChevronBackOutline,
  ChevronForwardOutline,
  AddOutline,
  RemoveOutline,
  ExpandOutline,
  DownloadOutline,
  ArchiveOutline,
  TrashOutline,
  PencilOutline,
  ColorPaletteOutline,
  StarOutline,
  LinkOutline,
  CloseOutline,
  ReturnDownForwardOutline,
  ArrowDownOutline,
  HeartOutline,
  CheckmarkCircleOutline,
  AlertCircleOutline,
  FlagOutline,
  RocketOutline,
  BulbOutline,
  DocumentTextOutline,
  FolderOutline,
  BookmarkOutline,
} from '@vicons/ionicons5'
import { NIcon } from 'naive-ui'
import {
  getMindmapApi,
  updateMindmapApi,
} from '../../api/document'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const loadingBar = useLoadingBar()

const mapId = computed(() => parseInt(route.params.mapId))
const mapName = ref('')
const mapInfo = ref(null)
const loading = ref(true)
const saving = ref(false)
const lastSaved = ref(null)

const nodes = ref({})
const rootId = ref(null)

let idCounter = 1
const genNodeId = () => `n_${Date.now()}_${idCounter++}`

const scale = ref(1)
const offset = reactive({ x: 0, y: 0 })
const canvasSize = reactive({ w: 5000, h: 4000 })

const selectedNodeId = ref(null)
const editingNodeId = ref(null)
const nodeEditingText = ref('')

const contextMenuVisible = ref(false)
const contextMenuPos = reactive({ x: 0, y: 0 })
const linkDialogVisible = ref(false)
const linkInput = ref('')

const undoStack = ref([])
const redoStack = ref([])
const MAX_HISTORY = 50

const containerRef = ref(null)
const canvasWrapRef = ref(null)
const canvasContainerRef = ref(null)
const svgRef = ref(null)

const dragState = reactive({
  type: null,
  startX: 0,
  startY: 0,
  nodeId: null,
  origX: 0,
  origY: 0,
  origParentId: null,
  origSiblingIndex: 0,
})

const iconMap = {
  star: StarOutline,
  heart: HeartOutline,
  check: CheckmarkCircleOutline,
  alert: AlertCircleOutline,
  flag: FlagOutline,
  rocket: RocketOutline,
  bulb: BulbOutline,
  doc: DocumentTextOutline,
  folder: FolderOutline,
  bookmark: BookmarkOutline,
}

const iconLabels = {
  star: '星标',
  heart: '收藏',
  check: '完成',
  alert: '警告',
  flag: '标记',
  rocket: '重要',
  bulb: '想法',
  doc: '文档',
  folder: '文件夹',
  bookmark: '书签',
}

const nodeColors = [
  { bg: '#2563eb', text: '#ffffff' },
  { bg: '#0284c7', text: '#ffffff' },
  { bg: '#0891b2', text: '#ffffff' },
  { bg: '#0d9488', text: '#ffffff' },
  { bg: '#16a34a', text: '#ffffff' },
  { bg: '#65a30d', text: '#ffffff' },
  { bg: '#ca8a04', text: '#ffffff' },
  { bg: '#d97706', text: '#ffffff' },
  { bg: '#ea580c', text: '#ffffff' },
  { bg: '#dc2626', text: '#ffffff' },
  { bg: '#db2777', text: '#ffffff' },
  { bg: '#c026d3', text: '#ffffff' },
  { bg: '#9333ea', text: '#ffffff' },
  { bg: '#7c3aed', text: '#ffffff' },
  { bg: '#4f46e5', text: '#ffffff' },
  { bg: '#475569', text: '#ffffff' },
  { bg: '#ffffff', text: '#1e293b' },
  { bg: '#f1f5f9', text: '#1e293b' },
  { bg: '#eff6ff', text: '#1e40af' },
  { bg: '#dcfce7', text: '#166534' },
  { bg: '#fef3c7', text: '#92400e' },
  { bg: '#fee2e2', text: '#991b1b' },
  { bg: '#fce7f3', text: '#9d174d' },
  { bg: '#ede9fe', text: '#6b21a8' },
]

const randomColor = () => {
  const pool = nodeColors.filter((c) => c.bg !== '#ffffff' && c.bg !== '#f1f5f9')
  return pool[Math.floor(Math.random() * pool.length)]
}

const selectedNode = computed(() => {
  if (!selectedNodeId.value) return null
  return nodes.value[selectedNodeId.value] || null
})

const contextMenuStyle = computed(() => ({
  left: `${contextMenuPos.x}px`,
  top: `${contextMenuPos.y}px`,
}))

const nodeList = computed(() => Object.values(nodes.value))

const edgeList = computed(() => {
  const edges = []
  for (const node of Object.values(nodes.value)) {
    if (!node.parentId) continue
    const parent = nodes.value[node.parentId]
    if (!parent) continue

    const px = parent.x
    const py = parent.y
    const nx = node.x
    const ny = node.y
    const pw = Math.max(parent.w, 80)
    const nw = Math.max(node.w, 80)

    const isRight = nx >= px
    let startX, endX
    if (isRight) {
      startX = px + pw / 2
      endX = nx - nw / 2
    } else {
      startX = px - pw / 2
      endX = nx + nw / 2
    }

    const midX = (startX + endX) / 2
    const path = `M ${startX} ${py} C ${midX} ${py}, ${midX} ${ny}, ${endX} ${ny}`

    edges.push({
      id: `e_${parent.id}_${node.id}`,
      path,
      color: parent.color || '#94a3b8',
    })
  }
  return edges
})

const snapshot = () => ({
  nodes: JSON.parse(JSON.stringify(nodes.value)),
  rootId: rootId.value,
})

const restore = (snap) => {
  nodes.value = JSON.parse(JSON.stringify(snap.nodes))
  rootId.value = snap.rootId
}

const pushHistory = () => {
  undoStack.value.push(snapshot())
  if (undoStack.value.length > MAX_HISTORY) undoStack.value.shift()
  redoStack.value = []
}

const handleUndo = () => {
  if (undoStack.value.length === 0) return
  redoStack.value.push(snapshot())
  restore(undoStack.value.pop())
  clearSelection()
  scheduleAutoSave()
}

const handleRedo = () => {
  if (redoStack.value.length === 0) return
  undoStack.value.push(snapshot())
  restore(redoStack.value.pop())
  clearSelection()
  scheduleAutoSave()
}

const clearSelection = () => {
  selectedNodeId.value = null
  editingNodeId.value = null
  hideContextMenu()
}

const getNodeStyle = (node) => {
  const w = Math.max(node.w || 100, 60)
  const h = Math.max(node.h || 40, 32)
  return {
    left: `${node.x - w / 2}px`,
    top: `${node.y - h / 2}px`,
    width: `${w}px`,
    minHeight: `${h}px`,
  }
}

const getNodeContentStyle = (node) => ({
  background: node.color || '#eff6ff',
  color: node.textColor || '#1e40af',
  borderColor: hexToRgba(node.color || '#2563eb', 0.3),
})

const hexToRgba = (hex, alpha) => {
  if (!hex || hex[0] !== '#') return `rgba(37, 99, 235, ${alpha})`
  const r = parseInt(hex.slice(1, 3), 16)
  const g = parseInt(hex.slice(3, 5), 16)
  const b = parseInt(hex.slice(5, 7), 16)
  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}

const handleCanvasClick = (e) => {
  if (e.target === canvasWrapRef.value ||
      e.target === canvasContainerRef.value ||
      e.target.tagName === 'svg' ||
      e.target.tagName === 'rect' ||
      e.target.classList.contains('canvas-wrap') ||
      e.target.classList.contains('nodes-layer')) {
    clearSelection()
  }
}

const screenToCanvas = (sx, sy) => {
  const rect = canvasWrapRef.value.getBoundingClientRect()
  return {
    x: (sx - rect.left - offset.x) / scale.value,
    y: (sy - rect.top - offset.y) / scale.value,
  }
}

const handleCanvasMouseDown = (e) => {
  if (e.button !== 0) return
  if (e.target.closest('.node-wrapper')) return
  if (e.target.closest('.context-menu')) return

  dragState.type = 'pan'
  dragState.startX = e.clientX
  dragState.startY = e.clientY
  dragState.origX = offset.x
  dragState.origY = offset.y
}

const handleCanvasMouseMove = (e) => {
  if (dragState.type === 'pan') {
    offset.x = dragState.origX + (e.clientX - dragState.startX)
    offset.y = dragState.origY + (e.clientY - dragState.startY)
    return
  }

  if (dragState.type === 'node' && dragState.nodeId) {
    const node = nodes.value[dragState.nodeId]
    if (!node) return
    const delta = (e.clientX - dragState.startX) / scale.value
    const deltay = (e.clientY - dragState.startY) / scale.value
    node.x = Math.round(dragState.origX + delta)
    node.y = Math.round(dragState.origY + deltay)
    return
  }
}

const handleCanvasMouseUp = (e) => {
  if (dragState.type === 'node' && dragState.nodeId) {
    const node = nodes.value[dragState.nodeId]
    if (node && (node.x !== dragState.origX || node.y !== dragState.origY)) {
      pushHistory()
      scheduleAutoSave()
    }

    if (node) {
      const pos = screenToCanvas(e.clientX, e.clientY)
      let hoveredNode = null
      for (const n of Object.values(nodes.value)) {
        if (n.id === node.id) continue
        if (!n.parentId && !node.parentId) continue
        const nw = Math.max(n.w || 100, 60)
        const nh = Math.max(n.h || 40, 32)
        if (
          pos.x >= n.x - nw / 2 - 10 &&
          pos.x <= n.x + nw / 2 + 10 &&
          pos.y >= n.y - nh / 2 - 10 &&
          pos.y <= n.y + nh / 2 + 10
        ) {
          hoveredNode = n
          break
        }
      }
      if (hoveredNode && !isDescendant(node.id, hoveredNode.id)) {
        attachToParent(node, hoveredNode)
      }
    }
  }

  dragState.type = null
  dragState.nodeId = null
}

const isDescendant = (ancestorId, nodeId) => {
  let current = nodes.value[nodeId]
  while (current) {
    if (current.id === ancestorId) return true
    current = current.parentId ? nodes.value[current.parentId] : null
  }
  return false
}

const attachToParent = (node, newParent) => {
  if (node.parentId === newParent.id) return
  pushHistory()

  if (node.parentId) {
    const oldParent = nodes.value[node.parentId]
    if (oldParent) {
      oldParent.children = oldParent.children.filter((id) => id !== node.id)
    }
  }

  node.parentId = newParent.id
  newParent.children.push(node.id)

  const color = randomColor()
  node.color = color.bg
  node.textColor = color.text

  message.success(`已挂载到「${newParent.text}」下`)
  scheduleAutoSave()
}

const handleNodeMouseDown = (e, node) => {
  if (e.button !== 0) return
  if (editingNodeId.value === node.id) return

  dragState.type = 'node'
  dragState.startX = e.clientX
  dragState.startY = e.clientY
  dragState.nodeId = node.id
  dragState.origX = node.x
  dragState.origY = node.y
  selectedNodeId.value = node.id
  hideContextMenu()
}

const handleNodeClick = (e, node) => {
  selectedNodeId.value = node.id
  hideContextMenu()
}

const startEditNode = (node) => {
  editingNodeId.value = node.id
  nodeEditingText.value = node.text
  hideContextMenu()
}

const startEditNodeFromMenu = () => {
  if (!selectedNode.value) return
  startEditNode(selectedNode.value)
}

const finishEditNode = (node) => {
  if (editingNodeId.value !== node.id) return
  const newText = nodeEditingText.value.trim()
  if (newText && newText !== node.text) {
    pushHistory()
    node.text = newText
    const padding = 32
    node.w = Math.max(60, Math.min(260, newText.length * 14 + padding))
    scheduleAutoSave()
  }
  editingNodeId.value = null
}

const cancelEditNode = () => {
  editingNodeId.value = null
}

const addChildNode = (parentNode) => {
  pushHistory()
  const id = genNodeId()
  const color = randomColor()
  const padding = 32
  const defaultText = '新节点'
  const w = defaultText.length * 14 + padding

  const childCount = parentNode.children.length
  const isRight = childCount === 0 ? Math.random() > 0.5 : childCount % 2 === 0
  const direction = isRight ? 1 : -1

  const parentW = Math.max(parentNode.w || 100, 60)
  const level = getNodeLevel(parentNode) + 1

  const x = parentNode.x + direction * (parentW / 2 + 160 + level * 20)
  const y = parentNode.y + (childCount - (parentNode.children.length - 1) / 2) * 70

  const node = {
    id,
    text: defaultText,
    parentId: parentNode.id,
    children: [],
    color: color.bg,
    textColor: color.text,
    x: Math.round(x),
    y: Math.round(y),
    w,
    h: 44,
    icon: '',
    link: '',
  }

  nodes.value[id] = node
  parentNode.children.push(id)
  selectedNodeId.value = id
  scheduleAutoSave()
  nextTick(() => startEditNode(node))
}

const addSiblingNode = (node) => {
  if (!node.parentId) return
  pushHistory()
  const parent = nodes.value[node.parentId]
  if (!parent) return

  const id = genNodeId()
  const color = randomColor()
  const padding = 32
  const defaultText = '新节点'
  const w = defaultText.length * 14 + padding

  const isRight = node.x >= parent.x
  const direction = isRight ? 1 : -1
  const level = getNodeLevel(node)

  const parentW = Math.max(parent.w || 100, 60)
  const idx = parent.children.indexOf(node.id)

  const x = parent.x + direction * (parentW / 2 + 160 + level * 20)
  const y = node.y + 70

  const newNode = {
    id,
    text: defaultText,
    parentId: parent.id,
    children: [],
    color: color.bg,
    textColor: color.text,
    x: Math.round(x),
    y: Math.round(y),
    w,
    h: 44,
    icon: '',
    link: '',
  }

  nodes.value[id] = newNode
  parent.children.splice(idx + 1, 0, id)
  selectedNodeId.value = id
  scheduleAutoSave()
  nextTick(() => startEditNode(newNode))
}

const getNodeLevel = (node) => {
  let level = 0
  let current = node
  while (current && current.parentId) {
    current = nodes.value[current.parentId]
    level++
  }
  return level
}

const handleAddChildFromMenu = () => {
  if (!selectedNode.value) return
  addChildNode(selectedNode.value)
}

const handleAddSiblingFromMenu = () => {
  if (!selectedNode.value) return
  addSiblingNode(selectedNode.value)
}

const handleDeleteSelected = () => {
  if (!selectedNode.value) return
  const node = selectedNode.value
  if (!node.parentId) {
    message.warning('根节点不能删除')
    return
  }
  pushHistory()
  deleteNodeRecursive(node.id)
  hideContextMenu()
  scheduleAutoSave()
}

const deleteNodeRecursive = (nodeId) => {
  const node = nodes.value[nodeId]
  if (!node) return

  for (const childId of [...node.children]) {
    deleteNodeRecursive(childId)
  }

  if (node.parentId) {
    const parent = nodes.value[node.parentId]
    if (parent) {
      parent.children = parent.children.filter((id) => id !== nodeId)
    }
  }

  delete nodes.value[nodeId]
  if (selectedNodeId.value === nodeId) selectedNodeId.value = null
}

const showContextMenu = (e, node) => {
  selectedNodeId.value = node.id
  const rect = containerRef.value.getBoundingClientRect()
  contextMenuPos.x = e.clientX - rect.left
  contextMenuPos.y = e.clientY - rect.top
  contextMenuVisible.value = true

  setTimeout(() => {
    const menu = document.querySelector('.context-menu')
    if (menu) {
      const menuRect = menu.getBoundingClientRect()
      if (menuRect.right > window.innerWidth - 10) {
        contextMenuPos.x = e.clientX - rect.left - menuRect.width - 10
      }
      if (menuRect.bottom > window.innerHeight - 10) {
        contextMenuPos.y = e.clientY - rect.top - menuRect.height - 10
      }
    }
  }, 10)
}

const hideContextMenu = () => {
  contextMenuVisible.value = false
}

const changeNodeColor = (c) => {
  if (!selectedNode.value) return
  pushHistory()
  selectedNode.value.color = c.bg
  selectedNode.value.textColor = c.text
  hideContextMenu()
  scheduleAutoSave()
}

const changeNodeIcon = (iconKey) => {
  if (!selectedNode.value) return
  pushHistory()
  selectedNode.value.icon = iconKey
  hideContextMenu()
  scheduleAutoSave()
}

const insertNodeLink = () => {
  if (!selectedNode.value) return
  linkInput.value = selectedNode.value.link || ''
  linkDialogVisible.value = true
  hideContextMenu()
}

const submitLink = () => {
  if (!selectedNode.value) return
  let url = linkInput.value.trim()
  if (url && !/^https?:\/\//i.test(url)) {
    url = 'https://' + url
  }
  pushHistory()
  selectedNode.value.link = url
  linkDialogVisible.value = false
  scheduleAutoSave()
}

const openNodeLink = (node) => {
  if (node.link) {
    window.open(node.link, '_blank')
  }
}

const handleZoomIn = () => { scale.value = Math.min(3, scale.value + 0.1) }
const handleZoomOut = () => { scale.value = Math.max(0.2, scale.value - 0.1) }

const handleWheel = (e) => {
  const delta = e.deltaY > 0 ? -0.1 : 0.1
  scale.value = Math.max(0.2, Math.min(3, scale.value + delta))
}

const handleFit = () => {
  const allNodes = Object.values(nodes.value)
  if (allNodes.length === 0) {
    scale.value = 1
    offset.x = 0
    offset.y = 0
    return
  }
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
  for (const n of allNodes) {
    const w = Math.max(n.w || 100, 60)
    const h = Math.max(n.h || 40, 32)
    minX = Math.min(minX, n.x - w / 2)
    minY = Math.min(minY, n.y - h / 2)
    maxX = Math.max(maxX, n.x + w / 2)
    maxY = Math.max(maxY, n.y + h / 2)
  }
  const rect = canvasWrapRef.value.getBoundingClientRect()
  if (rect.width <= 0 || rect.height <= 0) {
    scale.value = 1
    offset.x = 0
    offset.y = 0
    return
  }
  const pad = 120
  const contentW = Math.max(maxX - minX, 1)
  const contentH = Math.max(maxY - minY, 1)
  const sc = Math.min((rect.width - pad) / (contentW + pad), (rect.height - pad) / (contentH + pad), 1.2)
  scale.value = Math.max(0.3, sc)
  offset.x = rect.width / 2 - ((minX + maxX) / 2) * scale.value
  offset.y = rect.height / 2 - ((minY + maxY) / 2) * scale.value
}

const handleExport = async () => {
  try {
    const allNodes = Object.values(nodes.value)
    if (allNodes.length === 0) {
      message.warning('画布为空，无法导出')
      return
    }
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
    for (const n of allNodes) {
      const w = Math.max(n.w || 100, 60)
      const h = Math.max(n.h || 40, 32)
      minX = Math.min(minX, n.x - w / 2 - 60)
      minY = Math.min(minY, n.y - h / 2 - 60)
      maxX = Math.max(maxX, n.x + w / 2 + 60)
      maxY = Math.max(maxY, n.y + h / 2 + 60)
    }
    const w = maxX - minX
    const h = maxY - minY

    const svgEl = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
    svgEl.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
    svgEl.setAttribute('width', w)
    svgEl.setAttribute('height', h)
    svgEl.setAttribute('viewBox', `0 0 ${w} ${h}`)

    const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect')
    bg.setAttribute('x', 0); bg.setAttribute('y', 0); bg.setAttribute('width', w); bg.setAttribute('height', h)
    bg.setAttribute('fill', '#ffffff')
    svgEl.appendChild(bg)

    for (const edge of edgeList.value) {
      const pathEl = document.createElementNS('http://www.w3.org/2000/svg', 'path')
      const newPath = edge.path.replace(/[MLC] (-?\d+\.?\d*) (-?\d+\.?\d*)/g, (match, cmd, x, y) => {
        return `${cmd} ${parseFloat(x) - minX} ${parseFloat(y) - minY}`
      })
      pathEl.setAttribute('d', newPath)
      pathEl.setAttribute('fill', 'none')
      pathEl.setAttribute('stroke', edge.color)
      pathEl.setAttribute('stroke-width', '2')
      pathEl.setAttribute('stroke-linecap', 'round')
      svgEl.appendChild(pathEl)
    }

    for (const n of allNodes) {
      const nw = Math.max(n.w || 100, 60)
      const nh = Math.max(n.h || 40, 32)
      const nx = n.x - minX - nw / 2
      const ny = n.y - minY - nh / 2

      const foreign = document.createElementNS('http://www.w3.org/2000/svg', 'foreignObject')
      foreign.setAttribute('x', nx)
      foreign.setAttribute('y', ny)
      foreign.setAttribute('width', nw)
      foreign.setAttribute('height', nh)

      const div = document.createElement('div')
      div.setAttribute('xmlns', 'http://www.w3.org/1999/xhtml')
      div.style.cssText = `
        width:100%;height:100%;display:flex;align-items:center;justify-content:center;gap:4px;
        padding:8px 16px;border-radius:12px;font-size:14px;font-family:inherit;
        font-weight:500;text-align:center;box-sizing:border-box;overflow:hidden;
        background:${n.color || '#eff6ff'};color:${n.textColor || '#1e40af'};
        border:2px solid ${hexToRgba(n.color || '#2563eb', 0.3)};
        white-space:nowrap;text-overflow:ellipsis;
      `
      if (n.icon) {
        const iconSpan = document.createElement('span')
        iconSpan.textContent = '●'
        div.appendChild(iconSpan)
      }
      const textSpan = document.createElement('span')
      textSpan.textContent = n.text
      div.appendChild(textSpan)
      foreign.appendChild(div)
      svgEl.appendChild(foreign)
    }

    const data = new XMLSerializer().serializeToString(svgEl)
    const svg64 = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(data)
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      const dpr = 2
      canvas.width = w * dpr; canvas.height = h * dpr
      const ctx = canvas.getContext('2d')
      ctx.scale(dpr, dpr); ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, w, h); ctx.drawImage(img, 0, 0)
      canvas.toBlob((blob) => {
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url; a.download = `${mapName.value || 'mindmap'}.png`; a.click()
        URL.revokeObjectURL(url)
        message.success('导出成功')
      }, 'image/png')
    }
    img.onerror = () => {
      message.error('导出失败')
    }
    img.src = svg64
  } catch (e) {
    console.error(e)
    message.error('导出失败')
  }
}

const handleBack = () => {
  router.push('/document/mindmap')
}

const handleNameChange = async () => {
  if (!mapInfo.value) return
  if (!mapName.value?.trim()) {
    mapName.value = mapInfo.value.name
    message.warning('名称不能为空')
    return
  }
  if (mapName.value.trim() === mapInfo.value.name) return
  try {
    saving.value = true
    const payload = { name: mapName.value.trim() }
    if (mapInfo.value.project_id) payload.project_id = mapInfo.value.project_id
    await updateMindmapApi(mapId.value, payload)
    mapInfo.value.name = mapName.value.trim()
    lastSaved.value = new Date()
  } catch (e) {
    message.error(e?.detail || e?.message || '更新失败')
  } finally {
    saving.value = false
  }
}

const buildContent = () => JSON.stringify({
  nodes: nodes.value,
  rootId: rootId.value,
  version: 1,
})

const parseContent = (s) => {
  try {
    const d = JSON.parse(s || '{}')
    if (d.nodes && typeof d.nodes === 'object') {
      return { nodes: d.nodes, rootId: d.rootId || null }
    }
    return { nodes: {}, rootId: null }
  } catch { return { nodes: {}, rootId: null } }
}

let saveTimer = null
const contentChanged = ref(false)

const scheduleAutoSave = () => {
  contentChanged.value = true
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(() => {
    doSave(false)
  }, 3000)
}

const doSave = async (showMsg = false) => {
  if (!mapInfo.value) return
  try {
    saving.value = true
    const content = buildContent()
    await updateMindmapApi(mapId.value, { content })
    lastSaved.value = new Date()
    contentChanged.value = false
    if (showMsg) message.success('保存成功')
  } catch (e) {
    console.error(e)
    if (showMsg) message.error(e?.detail || e?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleManualSave = () => doSave(true)

const onKeyDown = (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
    e.preventDefault(); handleUndo(); return
  }
  if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
    e.preventDefault(); handleRedo(); return
  }
  if ((e.ctrlKey || e.metaKey) && e.key === 's') {
    e.preventDefault(); doSave(true); return
  }

  const tag = (e.target.tagName || '').toLowerCase()
  if (tag === 'input' || tag === 'textarea' || editingNodeId.value) return

  if ((e.key === 'Delete' || e.key === 'Backspace') && selectedNode.value) {
    if (selectedNode.value.parentId) {
      e.preventDefault()
      handleDeleteSelected()
    }
    return
  }

  if (e.key === 'Tab' && selectedNode.value) {
    e.preventDefault()
    addChildNode(selectedNode.value)
    return
  }

  if (e.key === 'Enter' && selectedNode.value) {
    e.preventDefault()
    if (selectedNode.value.parentId) {
      addSiblingNode(selectedNode.value)
    } else {
      addChildNode(selectedNode.value)
    }
    return
  }

  if (e.key === 'Escape') {
    clearSelection()
  }
}

const onDocClick = () => {
  hideContextMenu()
}

const formatTime = (t) => {
  if (!t) return ''
  const d = new Date(t)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const loadMap = async () => {
  loading.value = true
  try {
    const res = await getMindmapApi(mapId.value)
    mapInfo.value = res
    mapName.value = res.name
    const data = parseContent(res.content)
    nodes.value = data.nodes
    rootId.value = data.rootId
    if (Object.keys(nodes.value).length > 0) {
      await nextTick()
      requestAnimationFrame(() => {
        handleFit()
        requestAnimationFrame(() => handleFit())
      })
    }
  } catch (e) {
    message.error(e?.detail || e?.message || '加载失败')
    router.push('/document/mindmap')
  } finally {
    loading.value = false
  }
}

watch(nodes, () => {
  contentChanged.value = true
}, { deep: true })

onMounted(() => {
  loadMap()
  window.addEventListener('keydown', onKeyDown)
  document.addEventListener('click', onDocClick)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeyDown)
  document.removeEventListener('click', onDocClick)
  if (saveTimer) clearTimeout(saveTimer)
  if (contentChanged.value && !loading.value) doSave(false)
})
</script>

<style lang="scss" scoped>
.editor-container {
  width: 100%;
  height: calc(100vh - 104px);
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  border-bottom: 1px solid #e2e8f0;
  background: #fff;
  flex-shrink: 0;
  z-index: 10;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.editor-body {
  flex: 1;
  display: flex;
  overflow: auto;
}

.canvas-wrap {
  flex: 1;
  background: #f8fafc;
  position: relative;
  overflow: auto;
  cursor: default;
  min-width: 100%;
  min-height: 100%;
}

.canvas-container {
  transform-origin: 0 0;
  position: relative;
  top: 0;
  left: 0;
  cursor: grab;
  width: 5000px;
  height: 4000px;

  &:active {
    cursor: grabbing;
  }
}

.canvas-svg {
  display: block;
  user-select: none;
  position: absolute;
  top: 0;
  left: 0;
  pointer-events: none;
}

.nodes-layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.node-wrapper {
  position: absolute;
  cursor: move;
  transition: box-shadow 0.15s;
  user-select: none;

  &.is-root {
    z-index: 5;
  }

  &:hover {
    z-index: 10;
  }

  &.selected {
    z-index: 20;

    .node-content {
      box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.25);
    }
  }

  &.editing {
    z-index: 30;
  }

  &.dragging {
    opacity: 0.85;
    z-index: 100;
  }
}

.node-content {
  width: 100%;
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 18px;
  border-radius: 14px;
  font-size: 14px;
  font-weight: 500;
  border: 2px solid transparent;
  box-sizing: border-box;
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
  transition: transform 0.1s;
}

.node-wrapper.is-root .node-content {
  padding: 14px 28px;
  font-size: 16px;
  font-weight: 700;
  border-radius: 18px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.08);
}

.node-icon {
  flex-shrink: 0;
}

.node-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.node-link-icon {
  flex-shrink: 0;
  opacity: 0.8;
  cursor: pointer;

  &:hover {
    opacity: 1;
  }
}

.node-edit-wrap {
  width: 100%;
  min-height: 100%;
  padding: 2px;
}

.add-child-hint {
  position: absolute;
  top: calc(100% + 6px);
  left: 50%;
  transform: translateX(-50%);
  font-size: 11px;
  color: #94a3b8;
  white-space: nowrap;
  background: rgba(255, 255, 255, 0.9);
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid #e2e8f0;
  pointer-events: none;
}

.context-menu {
  position: absolute;
  z-index: 1000;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 6px;
  min-width: 200px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12);
}

.ctx-divider {
  height: 1px;
  background: #f1f5f9;
  margin: 4px 4px;
}

.context-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  color: #334155;
  cursor: pointer;
  transition: all 0.15s;

  &:hover {
    background: #f1f5f9;
    color: #0f172a;
  }

  &.danger {
    color: #dc2626;

    &:hover {
      background: #fef2f2;
    }
  }

  &.with-arrow {
    justify-content: space-between;

    .arrow {
      opacity: 0.5;
      margin-left: auto;
    }
  }
}

.context-submenu {
  position: relative;

  &:hover {
    .submenu-panel {
      display: block;
    }
  }
}

.submenu-panel {
  display: none;
  position: absolute;
  left: 100%;
  top: -6px;
  margin-left: 8px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 10px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.12);
  z-index: 1001;
}

.color-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  width: 200px;
}

.color-option {
  width: 40px;
  height: 32px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  border: 2px solid transparent;
  transition: all 0.15s;

  &:hover {
    transform: scale(1.1);
  }

  &.active {
    border-color: #2563eb;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.3);
  }
}

.icons-panel {
  width: 240px;
}

.icon-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 6px;
}

.icon-option {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #475569;
  border: 2px solid transparent;
  transition: all 0.15s;

  &:hover {
    background: #f1f5f9;
    color: #0f172a;
  }

  &.active {
    background: #dbeafe;
    border-color: #2563eb;
    color: #2563eb;
  }

  &.remove-icon {
    color: #dc2626;

    &:hover {
      background: #fef2f2;
    }
  }
}
</style>
