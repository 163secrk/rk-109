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
          v-model:value="chartName"
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
        <n-button size="small" @click="handleFit" title="自适应">
          <template #icon><n-icon><ExpandOutline /></n-icon></template>
          自适应
        </n-button>
        <n-button size="small" @click="handleExport" title="导出PNG">
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
      <div class="shape-panel">
        <div class="panel-title">图形组件</div>
        <div class="shape-list">
          <div
            v-for="shape in shapeList"
            :key="shape.type"
            class="shape-item"
            draggable="true"
            @dragstart="(e) => handleShapeDragStart(e, shape)"
          >
            <svg class="shape-icon" viewBox="0 0 80 50">
              <component :is="shape.comp" :x="40" :y="25" :w="64" :h="36" fill="#e0f2fe" stroke="#0284c7" sw="2" />
            </svg>
            <span class="shape-label">{{ shape.label }}</span>
          </div>
          <div class="shape-item" @click="setConnectionMode(true)" :class="{ active: connectionMode }">
            <svg class="shape-icon" viewBox="0 0 80 50">
              <line x1="10" y1="25" x2="70" y2="25" stroke="#64748b" stroke-width="2" marker-end="url(#panelArrow)" />
              <defs>
                <marker id="panelArrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                  <path d="M 0 0 L 10 5 L 0 10 z" fill="#64748b" />
                </marker>
              </defs>
            </svg>
            <span class="shape-label">连线工具</span>
          </div>
        </div>

        <div v-if="selectedNode" class="property-panel">
          <div class="panel-title">节点属性</div>
          <div class="prop-row">
            <span class="prop-label">填充色</span>
            <div class="color-list">
              <div
                v-for="c in fillColors"
                :key="c"
                class="color-item"
                :style="{ background: c }"
                :class="{ active: selectedNode.fill === c }"
                @click="updateNodeProp('fill', c)"
              />
            </div>
          </div>
          <div class="prop-row">
            <span class="prop-label">边框色</span>
            <div class="color-list">
              <div
                v-for="c in strokeColors"
                :key="c"
                class="color-item"
                :style="{ background: c }"
                :class="{ active: selectedNode.stroke === c }"
                @click="updateNodeProp('stroke', c)"
              />
            </div>
          </div>
          <n-button size="tiny" type="error" block @click="handleDeleteSelected" style="margin-top: 8px">
            <template #icon><n-icon><TrashOutline /></n-icon></template>
            删除节点
          </n-button>
        </div>

        <div v-if="selectedEdge" class="property-panel">
          <div class="panel-title">连线属性</div>
          <div class="prop-row">
            <span class="prop-label">标签文字</span>
            <n-input
              v-model:value="edgeLabelInput"
              size="tiny"
              placeholder="如：是/否"
              @blur="updateEdgeLabel"
              @keyup.enter="updateEdgeLabel"
            />
          </div>
          <div class="prop-row">
            <span class="prop-label">颜色</span>
            <div class="color-list">
              <div
                v-for="c in strokeColors"
                :key="c"
                class="color-item"
                :style="{ background: c }"
                :class="{ active: selectedEdge.stroke === c }"
                @click="updateEdgeProp('stroke', c)"
              />
            </div>
          </div>
          <n-button size="tiny" type="error" block @click="handleDeleteEdge" style="margin-top: 8px">
            <template #icon><n-icon><TrashOutline /></n-icon></template>
            删除连线
          </n-button>
        </div>
      </div>

      <div
        class="canvas-wrap"
        ref="canvasWrapRef"
        @dragover.prevent
        @drop="handleCanvasDrop"
        @click="handleCanvasClick"
        @mousedown="handleCanvasMouseDown"
        @mousemove="handleCanvasMouseMove"
        @mouseup="handleCanvasMouseUp"
        @wheel.prevent="handleWheel"
        :class="{ 'connect-mode': connectionMode }"
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
              <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e2e8f0" stroke-width="0.5" />
              </pattern>
              <marker id="arrowhead" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" :fill="arrowColor" />
              </marker>
            </defs>
            <rect x="0" y="0" :width="canvasSize.w" :height="canvasSize.h" fill="url(#grid)" />

            <g class="edges-layer">
              <g
                v-for="edge in edges"
                :key="edge.id"
                class="edge-group"
                :class="{ selected: selectedEdge?.id === edge.id }"
                @click.stop="selectEdge(edge)"
                @mousedown.stop
              >
                <path
                  :d="getEdgePath(edge)"
                  fill="none"
                  :stroke="edge.stroke"
                  stroke-width="2"
                  marker-end="url(#arrowhead)"
                  class="edge-path"
                />
                <path
                  :d="getEdgePath(edge)"
                  fill="none"
                  stroke="transparent"
                  stroke-width="16"
                  class="edge-hit"
                />
                <g
                  v-if="edge.label"
                  class="edge-label"
                  @dblclick.stop="startEditEdgeLabel(edge)"
                >
                  <rect
                    :x="getEdgeLabelPos(edge).x - 20"
                    :y="getEdgeLabelPos(edge).y - 12"
                    width="40"
                    height="24"
                    rx="4"
                    fill="#fff"
                    :stroke="edge.stroke"
                    stroke-width="1"
                  />
                  <text
                    :x="getEdgeLabelPos(edge).x"
                    :y="getEdgeLabelPos(edge).y + 4"
                    text-anchor="middle"
                    font-size="12"
                    :fill="edge.stroke"
                    font-weight="500"
                  >
                    {{ edge.label }}
                  </text>
                </g>
                <foreignObject
                  v-if="editingEdgeLabelId === edge.id"
                  :x="getEdgeLabelPos(edge).x - 25"
                  :y="getEdgeLabelPos(edge).y - 14"
                  width="50"
                  height="28"
                >
                  <input
                    v-model="edgeLabelInput"
                    @blur="finishEditEdgeLabel(edge)"
                    @keyup.enter="finishEditEdgeLabel(edge)"
                    class="edge-label-input"
                    autofocus
                    style="width: 48px; height: 24px; border: 1px solid #2563eb; border-radius: 4px; padding: 0 4px; font-size: 12px; outline: none;"
                  />
                </foreignObject>
              </g>

              <path
                v-if="connecting"
                :d="connectingPath"
                fill="none"
                stroke="#2563eb"
                stroke-width="2"
                stroke-dasharray="5,5"
                marker-end="url(#arrowhead)"
              />
            </g>

            <g class="nodes-layer">
              <g
                v-for="node in nodes"
                :key="node.id"
                class="node-group"
                :transform="`translate(${node.x}, ${node.y})`"
                :class="{ selected: selectedNode?.id === node.id, editing: editingNodeId === node.id }"
                @mousedown.stop="(e) => handleNodeMouseDown(e, node)"
                @click.stop="selectNode(node)"
                @dblclick.stop="startEditNode(node)"
              >
                <foreignObject
                  v-if="editingNodeId === node.id"
                  :x="-node.w / 2"
                  :y="-node.h / 2"
                  :width="node.w"
                  :height="node.h"
                >
                  <textarea
                    v-model="nodeEditingText"
                    class="node-textarea"
                    @blur="finishEditNode(node)"
                    @keyup.enter.ctrl.exact="finishEditNode(node)"
                    @mousedown.stop
                    autofocus
                    :style="nodeTextareaStyle(node)"
                  />
                </foreignObject>
                <template v-else>
                  <component
                    :is="getNodeShape(node.type)"
                    :x="0"
                    :y="0"
                    :w="node.w"
                    :h="node.h"
                    :fill="node.fill"
                    :stroke="node.stroke"
                    :sw="selectedNode?.id === node.id ? 3 : 2"
                  />
                  <foreignObject
                    :x="-node.w / 2 + 6"
                    :y="-node.h / 2 + 6"
                    :width="node.w - 12"
                    :height="node.h - 12"
                  >
                    <div
                      class="node-text"
                    >{{ node.text }}</div>
                  </foreignObject>
                </template>

                <template v-if="selectedNode?.id === node.id && editingNodeId !== node.id">
                  <circle
                    v-for="(p, idx) in getHandlePoints(node)"
                    :key="'h-' + idx"
                    class="resize-handle"
                    :cx="p.x"
                    :cy="p.y"
                    r="5"
                    fill="#fff"
                    stroke="#2563eb"
                    stroke-width="2"
                    @mousedown.stop="(e) => startResize(e, node, idx)"
                    :style="{ cursor: getResizeCursor(idx) }"
                  />
                  <circle
                    v-for="(p, idx) in getConnectionPoints(node)"
                    :key="'c-' + idx"
                    class="connection-point"
                    :cx="p.x"
                    :cy="p.y"
                    r="6"
                    fill="#fff"
                    stroke="#2563eb"
                    stroke-width="2"
                    @mousedown.stop="(e) => startConnection(e, node, idx)"
                  />
                </template>
              </g>
            </g>
          </svg>
        </div>
      </div>
    </div>
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
} from '@vicons/ionicons5'
import { NIcon } from 'naive-ui'
import {
  getFlowchartApi,
  updateFlowchartApi,
} from '../../api/document'

const route = useRoute()
const router = useRouter()
const message = useMessage()
const loadingBar = useLoadingBar()

const chartId = computed(() => parseInt(route.params.chartId))
const chartName = ref('')
const chartInfo = ref(null)
const loading = ref(true)
const saving = ref(false)
const lastSaved = ref(null)

const nodes = ref([])
const edges = ref([])
let idCounter = 1
const genId = (prefix) => `${prefix}_${Date.now()}_${idCounter++}`

const scale = ref(1)
const offset = reactive({ x: 0, y: 0 })
const canvasSize = reactive({ w: 4000, h: 3000 })

const selectedNode = ref(null)
const selectedEdge = ref(null)
const editingNodeId = ref(null)
const nodeEditingText = ref('')
const edgeLabelInput = ref('')
const editingEdgeLabelId = ref(null)
const connectionMode = ref(false)

const undoStack = ref([])
const redoStack = ref([])
const MAX_HISTORY = 50

const shapeList = [
  { type: 'start', label: '开始/结束', comp: 'RoundedRectShape' },
  { type: 'process', label: '处理步骤', comp: 'RectShape' },
  { type: 'decision', label: '判断', comp: 'DiamondShape' },
  { type: 'io', label: '输入输出', comp: 'ParallelogramShape' },
]

const fillColors = [
  '#ffffff', '#dbeafe', '#e0f2fe', '#fef3c7', '#dcfce7',
  '#fce7f3', '#ede9fe', '#fee2e2', '#f1f5f9', '#fef9c3',
]

const strokeColors = [
  '#2563eb', '#0284c7', '#d97706', '#16a34a',
  '#db2777', '#7c3aed', '#dc2626', '#475569',
]

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
  origW: 0,
  origH: 0,
  handleIdx: -1,
})

const connecting = ref(false)
const connectingData = reactive({
  fromNodeId: null,
  fromPointIdx: -1,
  toX: 0,
  toY: 0,
})

const arrowColor = computed(() => selectedEdge.value?.stroke || '#64748b')

const RoundedRectShape = (props) => h('rect', {
  x: -props.w / 2, y: -props.h / 2, width: props.w, height: props.h,
  rx: Math.min(props.h / 2, 20), ry: Math.min(props.h / 2, 20),
  fill: props.fill, stroke: props.stroke, 'stroke-width': props.sw || 2,
})

const RectShape = (props) => h('rect', {
  x: -props.w / 2, y: -props.h / 2, width: props.w, height: props.h,
  fill: props.fill, stroke: props.stroke, 'stroke-width': props.sw || 2,
})

const DiamondShape = (props) => {
  const hw = props.w / 2, hh = props.h / 2
  return h('polygon', {
    points: `0,${-hh} ${hw},0 0,${hh} ${-hw},0`,
    fill: props.fill, stroke: props.stroke, 'stroke-width': props.sw || 2,
  })
}

const ParallelogramShape = (props) => {
  const hw = props.w / 2, hh = props.h / 2
  const skew = 16
  return h('polygon', {
    points: `${-hw + skew},${-hh} ${hw},${-hh} ${hw - skew},${hh} ${-hw},${hh}`,
    fill: props.fill, stroke: props.stroke, 'stroke-width': props.sw || 2,
  })
}

const shapeComponents = {
  start: RoundedRectShape,
  process: RectShape,
  decision: DiamondShape,
  io: ParallelogramShape,
}

const defaultShapeStyles = {
  start: { w: 120, h: 50, fill: '#dbeafe', stroke: '#2563eb', text: '开始' },
  process: { w: 140, h: 60, fill: '#e0f2fe', stroke: '#0284c7', text: '处理步骤' },
  decision: { w: 120, h: 90, fill: '#fef3c7', stroke: '#d97706', text: '判断' },
  io: { w: 140, h: 50, fill: '#dcfce7', stroke: '#16a34a', text: '输入/输出' },
}

const getNodeShape = (type) => shapeComponents[type] || RectShape
const getHandlePoints = (node) => {
  const hw = node.w / 2, hh = node.h / 2
  return [
    { x: -hw, y: -hh }, { x: 0, y: -hh }, { x: hw, y: -hh },
    { x: -hw, y: 0 }, { x: hw, y: 0 },
    { x: -hw, y: hh }, { x: 0, y: hh }, { x: hw, y: hh },
  ]
}
const getConnectionPoints = (node) => {
  const hw = node.w / 2, hh = node.h / 2
  return [
    { x: 0, y: -hh },
    { x: hw, y: 0 },
    { x: 0, y: hh },
    { x: -hw, y: 0 },
  ]
}
const getResizeCursor = (idx) => ['nwse-resize', 'ns-resize', 'nesw-resize', 'ew-resize', 'ew-resize', 'nesw-resize', 'ns-resize', 'nwse-resize'][idx] || 'move'

const snapshot = () => ({
  nodes: JSON.parse(JSON.stringify(nodes.value)),
  edges: JSON.parse(JSON.stringify(edges.value)),
})

const restore = (snap) => {
  nodes.value = JSON.parse(JSON.stringify(snap.nodes))
  edges.value = JSON.parse(JSON.stringify(snap.edges))
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
}

const handleRedo = () => {
  if (redoStack.value.length === 0) return
  undoStack.value.push(snapshot())
  restore(redoStack.value.pop())
  clearSelection()
}

const clearSelection = () => {
  selectedNode.value = null
  selectedEdge.value = null
  editingNodeId.value = null
  editingEdgeLabelId.value = null
}

const selectNode = (node) => {
  selectedNode.value = node
  selectedEdge.value = null
}

const selectEdge = (edge) => {
  selectedEdge.value = edge
  selectedNode.value = null
  edgeLabelInput.value = edge.label || ''
}

const startEditNode = (node) => {
  editingNodeId.value = node.id
  nodeEditingText.value = node.text
}

const finishEditNode = (node) => {
  if (editingNodeId.value !== node.id) return
  const newText = nodeEditingText.value.trim()
  if (newText && newText !== node.text) {
    pushHistory()
    node.text = newText
  }
  editingNodeId.value = null
}

const nodeTextareaStyle = (node) => ({
  width: `${node.w - 12}px`,
  height: `${node.h - 12}px`,
  resize: 'none',
  border: '2px solid #2563eb',
  borderRadius: '4px',
  padding: '4px',
  textAlign: 'center',
  fontSize: '13px',
  fontFamily: 'inherit',
  outline: 'none',
  background: 'rgba(255,255,255,0.95)',
  boxSizing: 'border-box',
  overflow: 'hidden',
})

const startEditEdgeLabel = (edge) => {
  editingEdgeLabelId.value = edge.id
  edgeLabelInput.value = edge.label || ''
}

const finishEditEdgeLabel = (edge) => {
  if (editingEdgeLabelId.value !== edge.id) return
  const newLabel = edgeLabelInput.value.trim()
  if (newLabel !== edge.label) {
    pushHistory()
    edge.label = newLabel
  }
  editingEdgeLabelId.value = null
}

const updateEdgeLabel = () => {
  if (!selectedEdge.value) return
  if (edgeLabelInput.value.trim() !== (selectedEdge.value.label || '')) {
    pushHistory()
    selectedEdge.value.label = edgeLabelInput.value.trim()
  }
}

const handleShapeDragStart = (e, shape) => {
  e.dataTransfer.setData('shape', JSON.stringify(shape))
  connectionMode.value = false
}

const handleCanvasDrop = (e) => {
  const data = e.dataTransfer.getData('shape')
  if (!data) return
  const shape = JSON.parse(data)
  const rect = canvasWrapRef.value.getBoundingClientRect()
  const x = (e.clientX - rect.left - offset.x) / scale
  const y = (e.clientY - rect.top - offset.y) / scale
  addNode(shape.type, x, y)
}

const addNode = (type, x, y) => {
  pushHistory()
  const def = defaultShapeStyles[type] || defaultShapeStyles.process
  const node = {
    id: genId('n'),
    type,
    x: Math.round(x),
    y: Math.round(y),
    w: def.w,
    h: def.h,
    fill: def.fill,
    stroke: def.stroke,
    text: def.text,
  }
  nodes.value.push(node)
  selectedNode.value = node
  selectedEdge.value = null
}

const handleCanvasClick = (e) => {
  if (e.target === canvasWrapRef.value || e.target === canvasContainerRef.value ||
      e.target.tagName === 'svg' || e.target.tagName === 'rect' && e.target.getAttribute('fill') === 'url(#grid)') {
    clearSelection()
  }
  connectionMode.value = false
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
  if (e.target.closest('.node-group') || e.target.closest('.edge-group')) return
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

  if (dragState.type === 'move' && dragState.nodeId) {
    const node = nodes.value.find((n) => n.id === dragState.nodeId)
    if (node) {
      const delta = (e.clientX - dragState.startX) / scale.value
      const deltay = (e.clientY - dragState.startY) / scale.value
      node.x = Math.round(dragState.origX + delta)
      node.y = Math.round(dragState.origY + deltay)
    }
    return
  }

  if (dragState.type === 'resize' && dragState.nodeId) {
    const node = nodes.value.find((n) => n.id === dragState.nodeId)
    if (!node) return
    const dx = (e.clientX - dragState.startX) / scale.value
    const dy = (e.clientY - dragState.startY) / scale.value
    let nx = dragState.origX, ny = dragState.origY, nw = dragState.origW, nh = dragState.origH
    const minW = 60, minH = 40
    const idx = dragState.handleIdx
    if (idx === 0) { nw = Math.max(minW, dragState.origW - dx); nh = Math.max(minH, dragState.origH - dy); nx = dragState.origX + (dragState.origW - nw) / 2 + dx / 2; ny = dragState.origY + (dragState.origH - nh) / 2 + dy / 2 }
    else if (idx === 1) { nh = Math.max(minH, dragState.origH - dy); ny = dragState.origY + dy / 2 }
    else if (idx === 2) { nw = Math.max(minW, dragState.origW + dx); nh = Math.max(minH, dragState.origH - dy); nx = dragState.origX + (nw - dragState.origW) / 2 + dx / 2; ny = dragState.origY + (dragState.origH - nh) / 2 + dy / 2 }
    else if (idx === 3) { nw = Math.max(minW, dragState.origW - dx); nx = dragState.origX + dx / 2 }
    else if (idx === 4) { nw = Math.max(minW, dragState.origW + dx); nx = dragState.origX + (nw - dragState.origW) / 2 + dx / 2 }
    else if (idx === 5) { nw = Math.max(minW, dragState.origW - dx); nh = Math.max(minH, dragState.origH + dy); nx = dragState.origX + (dragState.origW - nw) / 2 + dx / 2; ny = dragState.origY + (nh - dragState.origH) / 2 + dy / 2 }
    else if (idx === 6) { nh = Math.max(minH, dragState.origH + dy); ny = dragState.origY + (nh - dragState.origH) / 2 + dy / 2 }
    else if (idx === 7) { nw = Math.max(minW, dragState.origW + dx); nh = Math.max(minH, dragState.origH + dy); nx = dragState.origX + (nw - dragState.origW) / 2 + dx / 2; ny = dragState.origY + (nh - dragState.origH) / 2 + dy / 2 }
    node.x = Math.round(nx)
    node.y = Math.round(ny)
    node.w = Math.round(nw)
    node.h = Math.round(nh)
    return
  }

  if (connecting.value) {
    const pos = screenToCanvas(e.clientX, e.clientY)
    connectingData.toX = pos.x
    connectingData.toY = pos.y
  }
}

const handleCanvasMouseUp = (e) => {
  if (dragState.type === 'move' || dragState.type === 'resize') {
    const node = nodes.value.find((n) => n.id === dragState.nodeId)
    if (node && (node.x !== dragState.origX || node.y !== dragState.origY || node.w !== dragState.origW || node.h !== dragState.origH)) {
      pushHistory()
    }
  }

  if (connecting.value && connectingData.fromNodeId) {
    const pos = screenToCanvas(e.clientX, e.clientY)
    let target = null
    let targetPointIdx = -1
    for (const node of nodes.value) {
      if (node.id === connectingData.fromNodeId) continue
      const pts = getConnectionPoints(node)
      for (let i = 0; i < pts.length; i++) {
        const dx = (node.x + pts[i].x) - pos.x
        const dy = (node.y + pts[i].y) - pos.y
        if (Math.sqrt(dx * dx + dy * dy) < 15) {
          target = node
          targetPointIdx = i
          break
        }
      }
      if (target) break
    }
    if (target) {
      pushHistory()
      edges.value.push({
        id: genId('e'),
        from: connectingData.fromNodeId,
        fromPoint: connectingData.fromPointIdx,
        to: target.id,
        toPoint: targetPointIdx,
        label: '',
        stroke: '#64748b',
      })
    }
    connecting.value = false
    connectingData.fromNodeId = null
    return
  }

  dragState.type = null
  dragState.nodeId = null
}

const handleNodeMouseDown = (e, node) => {
  if (e.button !== 0) return
  if (editingNodeId.value === node.id) return
  if (connectionMode.value) return

  dragState.type = 'move'
  dragState.startX = e.clientX
  dragState.startY = e.clientY
  dragState.nodeId = node.id
  dragState.origX = node.x
  dragState.origY = node.y
  selectedNode.value = node
  selectedEdge.value = null
}

const startResize = (e, node, idx) => {
  dragState.type = 'resize'
  dragState.startX = e.clientX
  dragState.startY = e.clientY
  dragState.nodeId = node.id
  dragState.origX = node.x
  dragState.origY = node.y
  dragState.origW = node.w
  dragState.origH = node.h
  dragState.handleIdx = idx
}

const startConnection = (e, node, idx) => {
  connecting.value = true
  connectingData.fromNodeId = node.id
  connectingData.fromPointIdx = idx
  const pts = getConnectionPoints(node)
  connectingData.toX = node.x + pts[idx].x
  connectingData.toY = node.y + pts[idx].y
  e.preventDefault()
}

const setConnectionMode = (v) => {
  connectionMode.value = v
  if (v) message.info('连线模式：点击节点连接点拖拽到另一个节点')
}

const getNodeConnPoint = (node, idx) => {
  const pts = getConnectionPoints(node)
  return { x: node.x + pts[idx].x, y: node.y + pts[idx].y }
}

const getEdgePath = (edge) => {
  const fromNode = nodes.value.find((n) => n.id === edge.from)
  const toNode = nodes.value.find((n) => n.id === edge.to)
  if (!fromNode || !toNode) return 'M 0 0 L 0 0'
  const p1 = getNodeConnPoint(fromNode, edge.fromPoint ?? 2)
  const p2 = getNodeConnPoint(toNode, edge.toPoint ?? 0)
  const midY = (p1.y + p2.y) / 2
  const dx = Math.abs(p2.x - p1.x)
  const dy = Math.abs(p2.y - p1.y)
  let path
  if (dx > dy) {
    const midX = (p1.x + p2.x) / 2
    path = `M ${p1.x} ${p1.y} C ${midX} ${p1.y}, ${midX} ${p2.y}, ${p2.x} ${p2.y}`
  } else {
    path = `M ${p1.x} ${p1.y} C ${p1.x} ${midY}, ${p2.x} ${midY}, ${p2.x} ${p2.y}`
  }
  return path
}

const getEdgeLabelPos = (edge) => {
  const fromNode = nodes.value.find((n) => n.id === edge.from)
  const toNode = nodes.value.find((n) => n.id === edge.to)
  if (!fromNode || !toNode) return { x: 0, y: 0 }
  const p1 = getNodeConnPoint(fromNode, edge.fromPoint ?? 2)
  const p2 = getNodeConnPoint(toNode, edge.toPoint ?? 0)
  return { x: (p1.x + p2.x) / 2, y: (p1.y + p2.y) / 2 }
}

const connectingPath = computed(() => {
  if (!connecting.value || !connectingData.fromNodeId) return ''
  const fromNode = nodes.value.find((n) => n.id === connectingData.fromNodeId)
  if (!fromNode) return ''
  const p1 = getNodeConnPoint(fromNode, connectingData.fromPointIdx)
  const p2 = { x: connectingData.toX, y: connectingData.toY }
  const midY = (p1.y + p2.y) / 2
  return `M ${p1.x} ${p1.y} C ${p1.x} ${midY}, ${p2.x} ${midY}, ${p2.x} ${p2.y}`
})

const updateNodeProp = (key, value) => {
  if (!selectedNode.value) return
  pushHistory()
  selectedNode.value[key] = value
}

const updateEdgeProp = (key, value) => {
  if (!selectedEdge.value) return
  pushHistory()
  selectedEdge.value[key] = value
}

const handleDeleteSelected = () => {
  if (!selectedNode.value) return
  pushHistory()
  const id = selectedNode.value.id
  edges.value = edges.value.filter((e) => e.from !== id && e.to !== id)
  nodes.value = nodes.value.filter((n) => n.id !== id)
  selectedNode.value = null
}

const handleDeleteEdge = () => {
  if (!selectedEdge.value) return
  pushHistory()
  edges.value = edges.value.filter((e) => e.id !== selectedEdge.value.id)
  selectedEdge.value = null
}

const handleZoomIn = () => { scale.value = Math.min(3, scale.value + 0.1) }
const handleZoomOut = () => { scale.value = Math.max(0.2, scale.value - 0.1) }

const handleWheel = (e) => {
  const delta = e.deltaY > 0 ? -0.1 : 0.1
  scale.value = Math.max(0.2, Math.min(3, scale.value + delta))
}

const handleFit = () => {
  if (nodes.value.length === 0) {
    scale.value = 1
    offset.x = 0
    offset.y = 0
    return
  }
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
  for (const n of nodes.value) {
    minX = Math.min(minX, n.x - n.w / 2)
    minY = Math.min(minY, n.y - n.h / 2)
    maxX = Math.max(maxX, n.x + n.w / 2)
    maxY = Math.max(maxY, n.y + n.h / 2)
  }
  const rect = canvasWrapRef.value.getBoundingClientRect()
  const pad = 80
  const sc = Math.min((rect.width - pad) / (maxX - minX + pad), (rect.height - pad) / (maxY - minY + pad), 1)
  scale.value = sc
  offset.x = rect.width / 2 - ((minX + maxX) / 2) * sc
  offset.y = rect.height / 2 - ((minY + maxY) / 2) * sc
}

const handleExport = async () => {
  try {
    if (nodes.value.length === 0) {
      message.warning('画布为空，无法导出')
      return
    }
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity
    for (const n of nodes.value) {
      minX = Math.min(minX, n.x - n.w / 2 - 30)
      minY = Math.min(minY, n.y - n.h / 2 - 30)
      maxX = Math.max(maxX, n.x + n.w / 2 + 30)
      maxY = Math.max(maxY, n.y + n.h / 2 + 30)
    }
    const w = maxX - minX, h = maxY - minY
    const svgEl = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
    svgEl.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
    svgEl.setAttribute('width', w)
    svgEl.setAttribute('height', h)
    svgEl.setAttribute('viewBox', `0 0 ${w} ${h}`)
    const bg = document.createElementNS('http://www.w3.org/2000/svg', 'rect')
    bg.setAttribute('x', 0); bg.setAttribute('y', 0); bg.setAttribute('width', w); bg.setAttribute('height', h); bg.setAttribute('fill', '#ffffff')
    svgEl.appendChild(bg)
    const rootG = document.createElementNS('http://www.w3.org/2000/svg', 'g')
    rootG.setAttribute('transform', `translate(${-minX}, ${-minY})`)
    const marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker')
    marker.setAttribute('id', 'exp-arrow')
    marker.setAttribute('viewBox', '0 0 10 10')
    marker.setAttribute('refX', '9'); marker.setAttribute('refY', '5')
    marker.setAttribute('markerWidth', '7'); marker.setAttribute('markerHeight', '7')
    marker.setAttribute('orient', 'auto-start-reverse')
    const mp = document.createElementNS('http://www.w3.org/2000/svg', 'path')
    mp.setAttribute('d', 'M 0 0 L 10 5 L 0 10 z'); mp.setAttribute('fill', '#64748b')
    marker.appendChild(mp)
    const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs')
    defs.appendChild(marker); svgEl.appendChild(defs); svgEl.appendChild(rootG)
    const edgesG = document.createElementNS('http://www.w3.org/2000/svg', 'g')
    for (const edge of edges.value) {
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path')
      path.setAttribute('d', getEdgePath(edge))
      path.setAttribute('fill', 'none'); path.setAttribute('stroke', edge.stroke); path.setAttribute('stroke-width', '2')
      path.setAttribute('marker-end', 'url(#exp-arrow)')
      edgesG.appendChild(path)
      if (edge.label) {
        const pos = getEdgeLabelPos(edge)
        const lbg = document.createElementNS('http://www.w3.org/2000/svg', 'rect')
        lbg.setAttribute('x', pos.x - 20); lbg.setAttribute('y', pos.y - 12)
        lbg.setAttribute('width', 40); lbg.setAttribute('height', 24); lbg.setAttribute('rx', 4)
        lbg.setAttribute('fill', '#fff'); lbg.setAttribute('stroke', edge.stroke); lbg.setAttribute('stroke-width', '1')
        const lt = document.createElementNS('http://www.w3.org/2000/svg', 'text')
        lt.setAttribute('x', pos.x); lt.setAttribute('y', pos.y + 4)
        lt.setAttribute('text-anchor', 'middle'); lt.setAttribute('font-size', '12')
        lt.setAttribute('fill', edge.stroke); lt.setAttribute('font-weight', '500')
        lt.textContent = edge.label
        edgesG.appendChild(lbg); edgesG.appendChild(lt)
      }
    }
    rootG.appendChild(edgesG)
    const nodesG = document.createElementNS('http://www.w3.org/2000/svg', 'g')
    for (const node of nodes.value) {
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g')
      g.setAttribute('transform', `translate(${node.x}, ${node.y})`)
      let shapeEl
      const hw = node.w / 2, hh = node.h / 2
      if (node.type === 'start') {
        shapeEl = document.createElementNS('http://www.w3.org/2000/svg', 'rect')
        shapeEl.setAttribute('x', -hw); shapeEl.setAttribute('y', -hh); shapeEl.setAttribute('width', node.w); shapeEl.setAttribute('height', node.h)
        shapeEl.setAttribute('rx', Math.min(node.h / 2, 20)); shapeEl.setAttribute('ry', Math.min(node.h / 2, 20))
      } else if (node.type === 'decision') {
        shapeEl = document.createElementNS('http://www.w3.org/2000/svg', 'polygon')
        shapeEl.setAttribute('points', `0,${-hh} ${hw},0 0,${hh} ${-hw},0`)
      } else if (node.type === 'io') {
        shapeEl = document.createElementNS('http://www.w3.org/2000/svg', 'polygon')
        shapeEl.setAttribute('points', `${-hw + 16},${-hh} ${hw},${-hh} ${hw - 16},${hh} ${-hw},${hh}`)
      } else {
        shapeEl = document.createElementNS('http://www.w3.org/2000/svg', 'rect')
        shapeEl.setAttribute('x', -hw); shapeEl.setAttribute('y', -hh); shapeEl.setAttribute('width', node.w); shapeEl.setAttribute('height', node.h)
      }
      shapeEl.setAttribute('fill', node.fill); shapeEl.setAttribute('stroke', node.stroke); shapeEl.setAttribute('stroke-width', '2')
      g.appendChild(shapeEl)
      const t = document.createElementNS('http://www.w3.org/2000/svg', 'foreignObject')
      t.setAttribute('x', -node.w / 2 + 6); t.setAttribute('y', -node.h / 2 + 6)
      t.setAttribute('width', node.w - 12); t.setAttribute('height', node.h - 12)
      const div = document.createElement('div')
      div.setAttribute('xmlns', 'http://www.w3.org/1999/xhtml')
      div.style.cssText = 'width:100%;height:100%;display:flex;align-items:center;justify-content:center;font-size:13px;font-family:inherit;color:#1e293b;text-align:center;word-break:break-all;overflow:hidden;'
      div.textContent = node.text
      t.appendChild(div); g.appendChild(t); nodesG.appendChild(g)
    }
    rootG.appendChild(nodesG)
    const data = new XMLSerializer().serializeToString(svgEl)
    const svg64 = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(data)
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      canvas.width = w * 2; canvas.height = h * 2
      const ctx = canvas.getContext('2d')
      ctx.scale(2, 2); ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, w, h); ctx.drawImage(img, 0, 0)
      canvas.toBlob((blob) => {
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url; a.download = `${chartName.value || 'flowchart'}.png`; a.click()
        URL.revokeObjectURL(url)
        message.success('导出成功')
      }, 'image/png')
    }
    img.src = svg64
  } catch (e) {
    console.error(e)
    message.error('导出失败')
  }
}

const handleBack = () => {
  router.push('/document/flowchart')
}

const handleNameChange = async () => {
  if (!chartInfo.value) return
  if (!chartName.value?.trim()) {
    chartName.value = chartInfo.value.name
    message.warning('名称不能为空')
    return
  }
  if (chartName.value.trim() === chartInfo.value.name) return
  try {
    saving.value = true
    await updateFlowchartApi(chartId.value, { name: chartName.value.trim() })
    chartInfo.value.name = chartName.value.trim()
    message.success('已更新名称')
    lastSaved.value = new Date()
  } catch (e) {
    message.error(e?.detail || e?.message || '更新失败')
  } finally {
    saving.value = false
  }
}

const buildContent = () => JSON.stringify({ nodes: nodes.value, edges: edges.value, version: 1 })

const parseContent = (s) => {
  try {
    const d = JSON.parse(s || '{}')
    return { nodes: d.nodes || [], edges: d.edges || [] }
  } catch { return { nodes: [], edges: [] } }
}

let saveTimer = null
const contentChanged = ref(false)

const doSave = async (showMsg = false) => {
  if (!chartInfo.value) return
  try {
    saving.value = true
    const content = buildContent()
    await updateFlowchartApi(chartId.value, { content })
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
  if ((e.key === 'Delete' || e.key === 'Backspace') && !editingNodeId.value && !editingEdgeLabelId.value) {
    const tag = (e.target.tagName || '').toLowerCase()
    if (tag === 'input' || tag === 'textarea') return
    if (selectedNode.value) { e.preventDefault(); handleDeleteSelected() }
    else if (selectedEdge.value) { e.preventDefault(); handleDeleteEdge() }
  }
  if (e.key === 'Escape') {
    clearSelection()
    connectionMode.value = false
    connecting.value = false
  }
}

const formatTime = (t) => {
  if (!t) return ''
  const d = new Date(t)
  return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const loadChart = async () => {
  loading.value = true
  try {
    const res = await getFlowchartApi(chartId.value)
    chartInfo.value = res
    chartName.value = res.name
    const data = parseContent(res.content)
    nodes.value = data.nodes
    edges.value = data.edges
    if (nodes.value.length > 0) {
      await nextTick()
      handleFit()
    }
  } catch (e) {
    message.error(e?.detail || e?.message || '加载失败')
    router.push('/document/flowchart')
  } finally {
    loading.value = false
  }
}

watch([nodes, edges], () => {
  contentChanged.value = true
}, { deep: true })

onMounted(() => {
  loadChart()
  window.addEventListener('keydown', onKeyDown)
  saveTimer = setInterval(() => {
    if (contentChanged.value && !loading.value) {
      doSave(false)
    }
  }, 60000)
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeyDown)
  if (saveTimer) clearInterval(saveTimer)
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
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  border-bottom: 1px solid #e2e8f0;
  background: #fff;
  flex-shrink: 0;
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
  overflow: hidden;
}

.shape-panel {
  width: 220px;
  border-right: 1px solid #e2e8f0;
  background: #f8fafc;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.panel-title {
  padding: 12px 16px 8px;
  font-size: 12px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.shape-list {
  padding: 0 12px 12px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.shape-item {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 10px 6px;
  text-align: center;
  cursor: grab;
  transition: all 0.15s;
  user-select: none;

  &:hover {
    border-color: #2563eb;
    background: #eff6ff;
    transform: translateY(-1px);
  }

  &:active {
    cursor: grabbing;
  }

  &.active {
    border-color: #2563eb;
    background: #dbeafe;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2);
  }
}

.shape-icon {
  width: 100%;
  height: 36px;
  display: block;
  margin-bottom: 4px;
}

.shape-label {
  font-size: 11px;
  color: #475569;
  font-weight: 500;
}

.property-panel {
  border-top: 1px solid #e2e8f0;
  padding: 0 16px 16px;
  margin-top: 4px;
}

.prop-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.prop-label {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.color-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.color-item {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.15s;
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.05);

  &:hover {
    transform: scale(1.1);
  }

  &.active {
    border-color: #2563eb;
    box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.3);
  }
}

.canvas-wrap {
  flex: 1;
  background: #f1f5f9;
  position: relative;
  overflow: hidden;
  cursor: default;

  &.connect-mode {
    cursor: crosshair;
  }
}

.canvas-container {
  transform-origin: 0 0;
  position: absolute;
  top: 0;
  left: 0;
  cursor: grab;

  &:active {
    cursor: grabbing;
  }
}

.canvas-svg {
  display: block;
  user-select: none;
}

.node-group {
  cursor: move;

  &.selected {
    filter: drop-shadow(0 0 6px rgba(37, 99, 235, 0.5));
  }

  &.editing {
    cursor: default;
  }
}

.node-text {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #1e293b;
  text-align: center;
  word-break: break-all;
  overflow: hidden;
  line-height: 1.3;
}

.node-textarea {
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.resize-handle {
  cursor: ew-resize;
  stroke-opacity: 0.9;
}

.connection-point {
  cursor: crosshair;
  opacity: 0.8;
  transition: all 0.15s;

  &:hover {
    opacity: 1;
    r: 8;
    fill: #2563eb;
  }
}

.edge-group {
  cursor: pointer;

  .edge-path {
    transition: stroke-width 0.15s;
  }

  &:hover .edge-path {
    stroke-width: 3;
  }

  &.selected .edge-path {
    stroke-width: 3;
    filter: drop-shadow(0 0 4px rgba(37, 99, 235, 0.4));
  }
}

.edge-hit {
  cursor: pointer;
}

.edge-label {
  cursor: pointer;
}
</style>
