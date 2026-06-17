<template>
  <div class="page-card">
    <div class="page-title">项目模板</div>
    <n-grid :cols="3" :x-gap="20" :y-gap="20">
      <n-gi v-for="tpl in templates" :key="tpl.name">
        <n-card hoverable>
          <template #header>
            <div class="tpl-header">
              <n-icon size="20" :color="tpl.color">
                <component :is="tpl.icon" />
              </n-icon>
              <span>{{ tpl.name }}</span>
            </div>
          </template>
          <div style="color: #64748b; font-size: 13px">{{ tpl.desc }}</div>
        </n-card>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup>
import { RocketOutline, ColorPaletteOutline, CodeSlashOutline } from '@vicons/ionicons5'

const templates = [
  { name: '软件开发', desc: '敏捷开发、需求管理、Bug跟踪', icon: CodeSlashOutline, color: '#2563eb' },
  { name: '产品设计', desc: '设计流程、评审、版本管理', icon: ColorPaletteOutline, color: '#8b5cf6' },
  { name: '运营活动', desc: '活动策划、执行、复盘', icon: RocketOutline, color: '#f59e0b' },
]
</script>

<style lang="scss" scoped>
.tpl-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}
</style>
