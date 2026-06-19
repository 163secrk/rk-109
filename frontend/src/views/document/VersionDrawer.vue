<template>
  <n-drawer :show="show" :width="480" placement="right" @update:show="(v) => $emit('update:show', v)">
    <n-drawer-content title="历史版本" :closable="true">
      <n-spin :show="loading">
        <n-empty v-if="versions.length === 0 && !loading" description="暂无历史版本" />
        <n-timeline v-else>
          <n-timeline-item
            v-for="(ver, idx) in versions"
            :key="ver.id"
            :type="idx === 0 ? 'success' : 'default'"
          >
            <template #header>
              <div class="version-header">
                <span class="version-title">v{{ ver.version }} - {{ ver.title }}</span>
                <n-button
                  size="tiny"
                  type="primary"
                  ghost
                  :disabled="idx === 0"
                  @click="$emit('rollback', ver)"
                >
                  回滚到此版本
                </n-button>
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
</template>

<script setup>
import { formatTime } from './utils'

defineProps({
  show: { type: Boolean, default: false },
  versions: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

defineEmits(['update:show', 'rollback'])
</script>

<style lang="scss" scoped>
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
