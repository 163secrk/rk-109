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
          <div
            class="tree-node-label"
            @contextmenu.prevent="handleContextMenu($event, option)"
          >
            {{ option.title }}
          </div>
        </template>
      </n-tree>
      <n-empty v-if="data.length === 0" description="暂无文档，点击右上角新建" style="padding: 40px 0" />

      <n-dropdown
        placement="bottom-start"
        trigger="manual"
        :show="contextMenu.show"
        :options="contextMenuOptions"
        :x="contextMenu.x"
        :y="contextMenu.y"
        @select="(key) => handleMenuSelect(key)"
        @clickoutside="closeContextMenu"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, h } from 'vue'
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
  'select-folder',
  'create',
  'rename',
  'delete',
  'move',
])

const treeRef = ref(null)
const contextMenu = ref({ show: false, x: 0, y: 0, node: null })

const contextMenuOptions = computed(() => {
  const node = contextMenu.value.node
  if (!node) return []

  const options = []

  if (node.doc_type === 'folder') {
    options.push({ label: '📄 新建子文档', key: 'create-doc' })
    options.push({ label: '📁 新建子目录', key: 'create-folder' })
    options.push({ type: 'divider', key: 'd1' })
    options.push({ label: '✏️ 编辑', key: 'rename' })
  } else {
    options.push({ label: '✏️ 重命名', key: 'rename' })
  }

  options.push({
    label: node.doc_type === 'folder' ? '🗑️ 删除目录' : '🗑️ 删除文档',
    key: 'delete',
    props: { style: { color: '#ef4444' } },
  })

  return options
})

function renderTreePrefix({ option }) {
  return h(
    'span',
    { style: 'margin-right: 4px; display: inline-block; width: 16px; text-align: center' },
    option.doc_type === 'folder' ? '📁' : '📄'
  )
}

function handleContextMenu(e, option) {
  contextMenu.value = {
    show: true,
    x: e.clientX,
    y: e.clientY,
    node: option,
  }
}

function closeContextMenu() {
  contextMenu.value.show = false
}

function handleMenuSelect(key) {
  const node = contextMenu.value.node
  closeContextMenu()
  if (!node) return

  if (key === 'create-doc') {
    emit('create', { doc_type: 'doc', parent_id: node.id })
  } else if (key === 'create-folder') {
    emit('create', { doc_type: 'folder', parent_id: node.id })
  } else if (key === 'rename') {
    emit('rename', node)
  } else if (key === 'delete') {
    emit('delete', node)
  }
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
    const siblings = findSiblings(props.data, targetParentId)
    const targetIndex = siblings.findIndex((s) => s.id === node.rawNode.id)
    sortOrder = dropPosition < 0 ? Math.max(0, targetIndex) : targetIndex + 1
  }

  emit('move', { dragId, parentId: targetParentId, sortOrder })
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
}
</style>
