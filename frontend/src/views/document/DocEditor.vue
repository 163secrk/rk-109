<template>
  <div class="doc-editor">
    <div class="editor-header">
      <div class="doc-title-row">
        <n-input
          v-model:value="doc.title"
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
        <n-button size="small" @click="$emit('show-versions')">🕘 历史版本</n-button>
        <n-button size="small" type="primary" :loading="savingVersion" @click="$emit('save-version')">💾 保存版本</n-button>
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
        <n-button @click="handleInsertLink" title="插入链接">🔗 链接</n-button>
        <n-button @click="handleInsertImage" title="插入图片">🖼️ 图片</n-button>
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
          :value="doc.content"
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
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { renderMarkdown } from './utils'

const props = defineProps({
  doc: { type: Object, required: true },
  saveStatus: { type: String, default: 'saved' },
  savingVersion: { type: Boolean, default: false },
})

const emit = defineEmits(['change', 'save-version', 'show-versions'])

const editorRef = ref(null)

const saveStatusText = computed(() => {
  if (props.saveStatus === 'saving') return '保存中...'
  if (props.saveStatus === 'saved') return '已保存'
  if (props.saveStatus === 'unsaved') return '未保存'
  return ''
})

const renderedContent = computed(() => renderMarkdown(props.doc.content || ''))

function handleTitleChange(val) {
  emit('change', { title: val })
}

function handleContentChange(val) {
  emit('change', { content: val })
}

function insertMarkdown(prefix, suffix) {
  const textarea = editorRef.value?.$el?.querySelector('textarea')
  if (!textarea) return
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const value = props.doc.content || ''
  const selected = value.substring(start, end)
  const newText = value.substring(0, start) + prefix + selected + suffix + value.substring(end)
  emit('change', { content: newText })
  nextTick(() => {
    textarea.focus()
    const newStart = start + prefix.length
    const newEnd = newStart + selected.length
    textarea.setSelectionRange(newStart, newEnd)
  })
}

function handleInsertLink() {
  const url = prompt('请输入链接地址：', 'https://')
  if (!url) return
  insertMarkdown(`[链接文本](${url})`, '')
}

function handleInsertImage() {
  const url = prompt('请输入图片地址：', 'https://')
  if (!url) return
  insertMarkdown(`![图片描述](${url})`, '')
}
</script>

<style lang="scss" scoped>
.doc-editor {
  display: flex;
  flex-direction: column;
  background: #fff;
  overflow: hidden;
  height: 100%;
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

      &.saved { color: #16a34a; }
      &.saving { color: #2563eb; }
      &.unsaved { color: #f59e0b; }
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

    p { margin: 12px 0; }

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
</style>
