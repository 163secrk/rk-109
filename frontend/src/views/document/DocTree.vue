<template>
  <div class="doc-tree">
    <div class="tree-header">
      <span>文档目录</span>
      <n-button text size="tiny" @click="$emit('refresh')">↻ 刷新</n-button>
    </div>
    <div class="tree-container">
      <n-tree
        ref="treeRef"
        block-line
        :data="data"
        :selected-keys="selectedKeys"
        :expanded-keys="expandedKeys"
        key-field="id"
        label-field="title"
        children-field="children"
        draggable
        :render-prefix="renderTreePrefix"
        @update:selected-keys="(keys) => $emit('update:selectedKeys', keys)"
        @update:expanded-keys="(keys) => $emit('update:expandedKeys', keys)"
        @drop="handleDrop"
      >
        <template #="{ option }">
          <n-dropdown
            trigger="contextmenu"
            :options="getNodeMenuOptions(option)"
            placement="right-start"
            @select="(key) => handleNodeMenuSelect(key, option)"
          >
            <div class="tree-node-label">
              {{ option.title }}
            </div>
          </n-dropdown>
        </template>
      </n-tree>
      <n-empty v-if="data.length === 0" description="暂无文档，点击右上角新建" style="padding: 40px 0" />
    </div>
  </div>
</template>

<script setup>
import { ref, h } from 'vue'
import { findSiblings } from './utils'

const props = defineProps({
  data: { type: Array, default: () => [] },
  selectedKeys: { type: Array, default: () => [] },
  expandedKeys: { type: Array, default: () => [] },
})

const emit = defineEmits([
  'update:selectedKeys',
  'update:expandedKeys',
  'refresh',
  'create',
  'rename',
  'delete',
  'move',
])

const treeRef = ref(null)

function renderTreePrefix({ option }) {
  return h(
    'span',
    { style: 'margin-right: 4px; display: inline-block; width: 16px; text-align: center' },
    option.doc_type === 'folder' ? '📁' : '📄'
  )
}

function getNodeMenuOptions(option) {
  const options = []

  if (option.doc_type === 'folder') {
    options.push({ label: '📄 新建子文档', key: 'create-doc' })
    options.push({ label: '📁 新建子目录', key: 'create-folder' })
    options.push({ type: 'divider', key: 'd1' })
    options.push({ label: '✏️ 编辑', key: 'rename' })
    options.push({ type: 'divider', key: 'd2' })
    options.push({
      label: '🗑️ 删除目录',
      key: 'delete',
      props: { style: { color: '#ef4444' } },
    })
  } else {
    options.push({ label: '✏️ 重命名', key: 'rename' })
    options.push({ type: 'divider', key: 'd1' })
    options.push({
      label: '🗑️ 删除文档',
      key: 'delete',
      props: { style: { color: '#ef4444' } },
    })
  }

  return options
}

function handleNodeMenuSelect(key, option) {
  if (key === 'create-doc') {
    emit('create', { doc_type: 'doc', parent_id: option.id })
  } else if (key === 'create-folder') {
    emit('create', { doc_type: 'folder', parent_id: option.id })
  } else if (key === 'rename') {
    emit('rename', option)
  } else if (key === 'delete') {
    emit('delete', option)
  }
}

function getNodeId(node) {
  if (!node) return null
  if (node.id !== undefined) return node.id
  if (node.rawNode?.id !== undefined) return node.rawNode.id
  if (node.data?.id !== undefined) return node.data.id
  if (node.props?.id !== undefined) return node.props.id
  return null
}

function getNodeRaw(node) {
  if (!node) return null
  if (node.rawNode) return node.rawNode
  if (node.data) return node.data
  if (node.id !== undefined) return node
  return null
}

function handleDrop(info) {
  const { node, dragNode, dropPosition } = info

  const dragNodeRaw = getNodeRaw(dragNode)
  const targetNodeRaw = getNodeRaw(node)

  const dragId = dragNodeRaw?.id
  const targetId = targetNodeRaw?.id
  const targetParentId = targetNodeRaw?.parent_id ?? null
  const targetChildren = targetNodeRaw?.children || []

  if (!dragId || !targetNodeRaw) {
    console.warn('拖拽节点数据异常', info)
    return
  }

  let newParentId = null
  let sortOrder = 0

  if (dropPosition === 0) {
    newParentId = targetId
    sortOrder = targetChildren.length
  } else {
    newParentId = targetParentId
    const siblings = findSiblings(props.data, targetParentId)
    const targetIndex = siblings.findIndex((s) => s.id === targetId)
    sortOrder = dropPosition < 0 ? Math.max(0, targetIndex) : targetIndex + 1
  }

  emit('move', { dragId, parentId: newParentId, sortOrder })
}
</script>

<style lang="scss" scoped>
.doc-tree {
  background: #fafbfc;
  display: flex;
  flex-direction: column;
  height: 100%;

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
    position: relative;
  }
}

.tree-node-label {
  flex: 1;
  user-select: none;
  cursor: default;
}
</style>
